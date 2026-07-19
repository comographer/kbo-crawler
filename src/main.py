from __future__ import annotations

import argparse
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from crawler import SCOREBOARD_DETAIL_KEYS, build_schedule_dataframe, crawl_season, output_paths, write_schedule_workbook
from team_sheets import build_team_sheet_rows, write_team_workbook


DEFAULT_HISTORY_YEARS = "2015-2025"
DEFAULT_HISTORY_MONTHS = "1-12"
SCOREBOARD_CACHE_REQUIRED_KEYS = ("game_duration_min", "innings_played", "away_hits", "home_hits")
SCOREBOARD_CACHE_REFRESH_DAYS = 3


class GitCommandError(RuntimeError):
	def __init__(self, args: list[str], result: subprocess.CompletedProcess[str]) -> None:
		self.args_list = args
		self.result = result
		details = (result.stderr or result.stdout or "No Git output.").strip()
		super().__init__(f"git {' '.join(args)} failed ({result.returncode}):\n{details}")


def parse_int_list(value: str) -> list[int]:
	value = value.strip()
	if "-" in value:
		start_text, end_text = value.split("-", 1)
		return list(range(int(start_text), int(end_text) + 1))
	item_list = [int(part.strip()) for part in value.split(",") if part.strip()]
	return item_list


def parse_months(value: str) -> list[int]:
	month_list = parse_int_list(value)
	return month_list or list(range(1, 13))


def parse_years(value: str) -> list[int]:
	year_list = parse_int_list(value)
	return year_list or [datetime.now().year]


def build_argument_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Crawl KBO season data and build per-team sheets.")
	parser.add_argument("--year", type=int, default=datetime.now().year, help="Season year to crawl.")
	parser.add_argument("--years", help="Season years to crawl, for example 2021-2026 or 2024,2025,2026.")
	parser.add_argument("--series-ids", default="0,9,6", help="Comma-separated series IDs used by KBO.")
	parser.add_argument("--team-id", default="", help="Optional team filter passed to the KBO endpoint.")
	parser.add_argument("--months", default="1-12", help="Month range to crawl, for example 3-12 or 1,2,3.")
	parser.add_argument("--daily", action="store_true", help="Crawl live season data only and merge it with frozen historical data.")
	parser.add_argument("--refresh-history", action="store_true", help="Rebuild the frozen historical schedule workbook before writing outputs.")
	parser.add_argument("--history-years", default=DEFAULT_HISTORY_YEARS, help="Historical seasons stored in the frozen workbook.")
	parser.add_argument("--history-months", default=DEFAULT_HISTORY_MONTHS, help="Month range to crawl when refreshing historical data.")
	parser.add_argument("--push", action="store_true", help="Commit generated data files and push the current branch.")
	return parser


def repo_root() -> Path:
	return Path(__file__).resolve().parents[1]


def run_git(args: list[str], root: Path) -> subprocess.CompletedProcess[str]:
	result = subprocess.run(
		["git", *args],
		cwd=root,
		check=False,
		text=True,
		capture_output=True,
	)
	if result.returncode != 0:
		raise GitCommandError(args, result)
	return result


def current_branch(root: Path) -> str:
	branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], root).stdout.strip()
	if not branch or branch == "HEAD":
		raise RuntimeError("--push requires a checked-out branch; detached HEAD is not supported.")
	return branch


def branch_ahead_behind(root: Path, remote_ref: str) -> tuple[int, int]:
	output = run_git(["rev-list", "--left-right", "--count", f"HEAD...{remote_ref}"], root).stdout.strip()
	try:
		ahead_text, behind_text = output.split()
		return int(ahead_text), int(behind_text)
	except (TypeError, ValueError) as exc:
		raise RuntimeError(f"Could not parse Git ahead/behind counts: {output!r}") from exc


def changed_paths(root: Path, revision_range: str) -> list[str]:
	output = run_git(["diff", "--name-only", revision_range], root).stdout
	return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def is_generated_data_path(path: str) -> bool:
	normalized = path.replace("\\", "/")
	if normalized.startswith("data/raw/"):
		return True
	if not normalized.startswith("data/output/") or not normalized.endswith(".xlsx"):
		return False
	name = normalized.rsplit("/", 1)[-1]
	return (
		name in {"kbo_schedule.xlsx", "kbo_team_sheets.xlsx"}
		or name.startswith("kbo_schedule_history_")
		or name.startswith("kbo_schedule_")
		or name.startswith("kbo_team_sheets_")
	)


def merge_remote_generated_data(root: Path, remote_ref: str) -> None:
	local_paths = changed_paths(root, f"{remote_ref}...HEAD")
	unsafe_paths = [path for path in local_paths if not is_generated_data_path(path)]
	if unsafe_paths:
		formatted = "\n".join(f"- {path}" for path in unsafe_paths)
		raise RuntimeError(
			"Local and remote branches have diverged, and local commits include non-generated files. "
			"Automatic merge was skipped:\n"
			f"{formatted}"
		)
	try:
		run_git(["merge", "--no-edit", "-X", "ours", remote_ref], root)
	except GitCommandError:
		subprocess.run(
			["git", "merge", "--abort"],
			cwd=root,
			check=False,
			text=True,
			capture_output=True,
		)
		raise


def prepare_publish_branch(root: Path) -> str:
	status_lines = run_git(["status", "--porcelain"], root).stdout.splitlines()
	if status_lines:
		formatted = "\n".join(f"- {line}" for line in status_lines[:20])
		raise RuntimeError(
			"--push requires a clean working tree before crawling. Commit or stash these changes first:\n"
			f"{formatted}"
		)

	branch = current_branch(root)
	run_git(["fetch", "origin", branch], root)
	remote_ref = f"origin/{branch}"
	ahead, behind = branch_ahead_behind(root, remote_ref)
	if behind == 0:
		print(f"Git preflight: {branch} is up to date with {remote_ref}.")
		return branch
	if ahead == 0:
		run_git(["merge", "--ff-only", remote_ref], root)
		print(f"Git preflight: fast-forwarded {branch} to {remote_ref}.")
		return branch

	merge_remote_generated_data(root, remote_ref)
	print(f"Git preflight: merged {remote_ref}; local generated data will be refreshed now.")
	return branch


def push_branch_with_retry(root: Path, branch: str) -> None:
	try:
		run_git(["push", "-u", "origin", branch], root)
		return
	except GitCommandError as exc:
		details = f"{exc.result.stdout}\n{exc.result.stderr}".lower()
		if "non-fast-forward" not in details and "fetch first" not in details:
			raise

	print("Remote changed during the crawl; fetching and retrying once.")
	run_git(["fetch", "origin", branch], root)
	remote_ref = f"origin/{branch}"
	_, behind = branch_ahead_behind(root, remote_ref)
	if behind:
		merge_remote_generated_data(root, remote_ref)
	run_git(["push", "-u", "origin", branch], root)


def has_staged_changes(root: Path) -> bool:
	result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root)
	if result.returncode == 0:
		return False
	if result.returncode == 1:
		return True
	result.check_returncode()
	return False


def legacy_output_paths(years: list[int], output_dir: Path) -> list[Path]:
	paths: list[Path] = []
	for year in years:
		paths.extend(
			[
				output_dir / f"kbo_schedule_{year}.xlsx",
				output_dir / f"kbo_team_sheets_{year}.xlsx",
			]
		)
	return paths


def remove_existing_files(paths: list[Path]) -> list[Path]:
	removed: list[Path] = []
	for path in paths:
		if path.exists():
			path.unlink()
			removed.append(path)
	return removed


def range_summary(values: list[int]) -> str:
	if not values:
		return "none"
	ordered = sorted(set(values))
	if ordered == list(range(ordered[0], ordered[-1] + 1)):
		return f"{ordered[0]:02d}-{ordered[-1]:02d}"
	return ",".join(str(value) for value in ordered)


def month_summary(months: list[int]) -> str:
	if not months:
		return "none"
	ordered = sorted(set(months))
	if ordered == list(range(ordered[0], ordered[-1] + 1)):
		return f"{ordered[0]:02d}-{ordered[-1]:02d}"
	return ",".join(f"{month:02d}" for month in ordered)


def history_cache_label(years: list[int]) -> str:
	ordered = sorted(set(years))
	if not ordered:
		return "none"
	if ordered == list(range(ordered[0], ordered[-1] + 1)):
		return f"{ordered[0]}_{ordered[-1]}"
	return "_".join(str(year) for year in ordered)


def history_cache_path(years: list[int], output_dir: Path) -> Path:
	return output_dir / f"kbo_schedule_history_{history_cache_label(years)}.xlsx"


def crawl_years(
	years: list[int],
	months: list[int],
	series_ids: str,
	team_id: str,
	scoreboard_cache_by_year: dict[int, dict[str, dict]] | None = None,
) -> list[dict]:
	records = []
	for year in years:
		records.extend(
			crawl_season(
				year,
				months,
				series_ids=series_ids,
				team_id=team_id,
				cached_game_details=(scoreboard_cache_by_year or {}).get(year),
			)
		)
	return records


def read_history_schedule(path: Path, history_years: list[int]) -> pd.DataFrame:
	if not path.exists():
		raise FileNotFoundError(
			f"Frozen history workbook not found: {path}. "
			"Run with --refresh-history once before using --daily."
		)

	frame = pd.read_excel(path)
	if "season_year" not in frame.columns:
		raise ValueError(f"Frozen history workbook is missing season_year: {path}")

	frame["season_year"] = pd.to_numeric(frame["season_year"], errors="coerce").astype("Int64")
	return frame[frame["season_year"].isin(sorted(set(history_years)))].copy()


def read_cached_scoreboard_details(path: Path, years: list[int]) -> dict[int, dict[str, dict]]:
	if not path.exists():
		return {}
	try:
		frame = pd.read_excel(path)
	except (OSError, ValueError) as exc:
		print(f"Could not read the existing schedule cache; using a full detail refresh: {exc}")
		return {}

	required_columns = {
		"game_id",
		"season_year",
		"game_date",
		"game_status",
		*SCOREBOARD_CACHE_REQUIRED_KEYS,
	}
	if not required_columns.issubset(frame.columns):
		return {}

	frame["season_year"] = pd.to_numeric(frame["season_year"], errors="coerce").astype("Int64")
	frame["game_date_parsed"] = pd.to_datetime(frame["game_date"], errors="coerce")
	refresh_cutoff = pd.Timestamp(date.today() - timedelta(days=SCOREBOARD_CACHE_REFRESH_DAYS))
	cached = frame[
		frame["season_year"].isin(sorted(set(years)))
		& frame["game_status"].eq("final")
		& frame["game_date_parsed"].lt(refresh_cutoff)
	].copy()
	for column in SCOREBOARD_CACHE_REQUIRED_KEYS:
		cached = cached[cached[column].notna()]

	result: dict[int, dict[str, dict]] = {}
	available_detail_keys = [key for key in SCOREBOARD_DETAIL_KEYS if key in cached.columns]
	for row in cached.to_dict(orient="records"):
		game_id = str(row.get("game_id") or "").strip()
		season_year = row.get("season_year")
		if not game_id or pd.isna(season_year):
			continue
		year = int(season_year)
		result.setdefault(year, {})[game_id] = {key: row.get(key) for key in available_detail_keys}

	cache_count = sum(len(values) for values in result.values())
	if cache_count:
		print(
			f"Reusing {cache_count} completed-game scoreboards older than "
			f"{SCOREBOARD_CACHE_REFRESH_DAYS} days."
		)
	return result


def combine_schedule_frames(history_frame: pd.DataFrame | None, live_frame: pd.DataFrame) -> pd.DataFrame:
	frames = [frame for frame in (history_frame, live_frame) if frame is not None and not frame.empty]
	if not frames:
		return pd.DataFrame()

	combined = pd.concat(frames, ignore_index=True, sort=False)
	sort_columns = [
		column
		for column in ("season_year", "game_date", "game_start_time", "game_id")
		if column in combined.columns
	]
	if sort_columns:
		combined = combined.sort_values(sort_columns, kind="stable").reset_index(drop=True)
	return combined


def raw_month_paths(years: list[int], months: list[int]) -> list[Path]:
	root = repo_root()
	return [
		root / "data" / "raw" / str(year) / f"schedule_{year}_{month:02d}.json"
		for year in years
		for month in months
	]


def unique_paths(paths: list[Path]) -> list[Path]:
	unique: list[Path] = []
	seen: set[Path] = set()
	for path in paths:
		if path in seen:
			continue
		seen.add(path)
		unique.append(path)
	return unique


def commit_and_push_outputs(
	years: list[int],
	months: list[int],
	output_files: list[Path],
) -> None:
	root = repo_root()
	if not output_files:
		print("No generated files found to commit.")
		return

	relative_files = [str(path.relative_to(root)) for path in unique_paths(output_files)]
	run_git(["add", "-A", "--", *relative_files], root)

	if has_staged_changes(root):
		message = f"Update KBO data {range_summary(years)} months {month_summary(months)}"
		run_git(["commit", "-m", message], root)
		print(f"Committed generated data: {message}")
	else:
		print("No generated data changes to commit.")

	branch = current_branch(root)
	push_branch_with_retry(root, branch)
	print(f"Pushed {branch} to origin.")


def main() -> int:
	parser = build_argument_parser()
	args = parser.parse_args()
	if args.push:
		prepare_publish_branch(repo_root())

	months = parse_months(args.months)
	years = parse_years(args.years) if args.years else [args.year]
	history_years = parse_years(args.history_years)
	history_months = parse_months(args.history_months)
	paths = output_paths(years[-1])
	scoreboard_cache_by_year = read_cached_scoreboard_details(paths.xlsx_path, years) if args.daily else {}
	requested_history_workbook_path = history_cache_path(history_years, paths.xlsx_path.parent)
	history_workbook_path: Path | None = None
	history_frame: pd.DataFrame | None = None

	if args.refresh_history:
		history_records = crawl_years(
			history_years,
			history_months,
			series_ids=args.series_ids,
			team_id=args.team_id,
		)
		history_frame = build_schedule_dataframe(history_records)
		history_workbook_path = write_schedule_workbook(history_frame, requested_history_workbook_path)
	elif args.daily:
		try:
			history_frame = read_history_schedule(requested_history_workbook_path, history_years)
			history_workbook_path = requested_history_workbook_path
		except (FileNotFoundError, ValueError) as exc:
			parser.error(str(exc))

	live_records = crawl_years(
		years,
		months,
		series_ids=args.series_ids,
		team_id=args.team_id,
		scoreboard_cache_by_year=scoreboard_cache_by_year,
	)
	live_frame = build_schedule_dataframe(live_records)
	if history_frame is not None and not history_frame.empty and "season_year" in history_frame.columns:
		history_frame = history_frame[~history_frame["season_year"].isin(sorted(set(years)))].copy()
	season_frame = combine_schedule_frames(history_frame, live_frame)
	season_workbook_path = write_schedule_workbook(season_frame, paths.xlsx_path)
	team_frame = build_team_sheet_rows(season_frame)
	requested_team_workbook_path = paths.xlsx_path.with_name("kbo_team_sheets.xlsx")
	team_workbook_path = write_team_workbook(team_frame, requested_team_workbook_path)
	output_years = sorted(set(years) | (set(history_years) if history_frame is not None else set()))
	legacy_paths = legacy_output_paths(output_years, paths.xlsx_path.parent)
	removed_legacy_paths: list[Path] = []
	if season_workbook_path == paths.xlsx_path and team_workbook_path == requested_team_workbook_path:
		removed_legacy_paths = remove_existing_files(legacy_paths)

	if history_frame is not None:
		print(f"Frozen history rows: {len(history_frame)}")
		print(f"Live crawl rows: {len(live_frame)}")
	print(f"Saved {len(season_frame)} games")
	if history_workbook_path is not None:
		print(f"Frozen history workbook: {history_workbook_path}")
		if history_workbook_path != requested_history_workbook_path:
			print(f"Original frozen history workbook was locked: {requested_history_workbook_path}")
	print(f"Season workbook: {season_workbook_path}")
	if season_workbook_path != paths.xlsx_path:
		print(f"Original season workbook was locked: {paths.xlsx_path}")
	print(f"Team workbook: {team_workbook_path}")
	if team_workbook_path != requested_team_workbook_path:
		print(f"Original team workbook was locked: {requested_team_workbook_path}")
	if removed_legacy_paths:
		print("Removed legacy output files:")
		for path in removed_legacy_paths:
			print(f"- {path}")
	if args.push:
		history_workbook_locked = args.refresh_history and history_workbook_path != requested_history_workbook_path
		if season_workbook_path != paths.xlsx_path or team_workbook_path != requested_team_workbook_path or history_workbook_locked:
			print("Skipped git push because one or more canonical workbook files were locked.")
		else:
			raw_month_files = raw_month_paths(years, months)
			history_output_files: list[Path] = []
			if args.refresh_history:
				history_output_files = [requested_history_workbook_path, *raw_month_paths(history_years, history_months)]
			commit_years = sorted(set(years) | (set(history_years) if history_frame is not None else set()))
			commit_months = sorted(set(months) | (set(history_months) if args.refresh_history else set()))
			commit_and_push_outputs(
				commit_years,
				commit_months,
				[
					paths.xlsx_path,
					requested_team_workbook_path,
					*raw_month_files,
					*history_output_files,
					*removed_legacy_paths,
				],
			)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
