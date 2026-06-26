from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

from excel_output import write_with_permission_fallback


BASE_URL = "https://www.koreabaseball.com"
SCHEDULE_PAGE_URL = f"{BASE_URL}/Schedule/Schedule.aspx"
SCHEDULE_API_URL = f"{BASE_URL}/ws/Schedule.asmx/GetScheduleList"
GAME_LIST_API_URL = f"{BASE_URL}/ws/Main.asmx/GetKboGameList"
SCOREBOARD_API_URL = f"{BASE_URL}/ws/Schedule.asmx/GetScoreBoardScroll"
DEFAULT_SERIES_IDS = "0,9,6"
DEFAULT_LEAGUE_ID = "1"
DEFAULT_SCOREBOARD_TYPE = "3"
SCOREBOARD_DETAIL_KEYS = (
	"crowd",
	"game_start_time",
	"game_finish_time",
	"game_duration_min",
	"stadium",
	"innings_played",
	"extra_inning_flag",
	"walkoff_flag",
	*(
		f"{prefix}_{suffix}"
		for prefix in ("away", "home")
		for suffix in (
			"hits",
			"errors",
			"bases_on_balls",
			"first_5_runs",
			"after_5_runs",
			"first_3_runs",
			"middle_3_runs",
			"late_runs",
			"score_after_5",
			"score_after_6",
			"score_after_7",
		)
	),
	*(f"{prefix}_runs_{inning}" for prefix in ("away", "home") for inning in range(1, 13)),
)
WEEKDAY_EN = {
	"월": "Mon",
	"화": "Tue",
	"수": "Wed",
	"목": "Thu",
	"금": "Fri",
	"토": "Sat",
	"일": "Sun",
}


@dataclass(frozen=True)
class OutputPaths:
	xlsx_path: Path
	raw_dir: Path


def build_session() -> requests.Session:
	session = requests.Session()
	session.get(SCHEDULE_PAGE_URL, timeout=30)
	return session


def schedule_headers() -> dict[str, str]:
	return {
		"Referer": SCHEDULE_PAGE_URL,
		"X-Requested-With": "XMLHttpRequest",
		"Accept": "application/json, text/javascript, */*; q=0.01",
	}


def scoreboard_headers(year: int, game_id: str, sr_id: str) -> dict[str, str]:
	return {
		"Referer": f"{BASE_URL}/Schedule/GameCenter/ReviewNew.aspx?leId={DEFAULT_LEAGUE_ID}&srId={sr_id}&seasonId={year}&gameId={game_id}",
		"X-Requested-With": "XMLHttpRequest",
		"Accept": "application/json, text/javascript, */*; q=0.01",
	}


def strip_html(value: str | None) -> str:
	if not value:
		return ""
	return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)


def parse_date_string(year: int, value: str) -> tuple[str, str]:
	match = re.search(r"(?P<month>\d{2})\.(?P<day>\d{2})\((?P<weekday>.)\)", value)
	if not match:
		return "", ""
	month = int(match.group("month"))
	day = int(match.group("day"))
	weekday = match.group("weekday")
	return datetime(year, month, day).date().isoformat(), weekday


def weekday_en(weekday_ko: str) -> str:
	return WEEKDAY_EN.get(weekday_ko, "")


def extract_game_id(cells: list[dict[str, Any]]) -> str:
	for cell in cells:
		text = cell.get("Text") or ""
		match = re.search(r"gameId=([^&'\"]+)", text)
		if match:
			return match.group(1)
	return ""


def parse_duration_to_minutes(value: str | None) -> int | None:
	if not value:
		return None
	match = re.fullmatch(r"(?:(?P<hours>\d+):)?(?P<minutes>\d{1,2})", value.strip())
	if not match:
		return None
	hours = int(match.group("hours") or 0)
	minutes = int(match.group("minutes"))
	return hours * 60 + minutes


def parse_scoreboard_int(value: Any) -> int | None:
	text = strip_html(str(value)).strip() if value is not None else ""
	if not text or text == "-":
		return None
	try:
		return int(text.replace(",", ""))
	except ValueError:
		return None


def parse_scoreboard_table(value: Any) -> list[list[str]]:
	if not value:
		return []
	if isinstance(value, str):
		try:
			data = json.loads(value)
		except json.JSONDecodeError:
			return []
	elif isinstance(value, dict):
		data = value
	else:
		return []

	rows: list[list[str]] = []
	for row in data.get("rows", []):
		rows.append([strip_html(cell.get("Text")) for cell in row.get("row", [])])
	return rows


def inning_sum(values: list[int | None], start: int, end: int | None = None) -> int | None:
	selected = [value for value in values[start:end] if value is not None]
	if not selected:
		return None
	return sum(selected)


def score_after(values: list[int | None], inning: int) -> int | None:
	return inning_sum(values, 0, inning)


def innings_played(away_values: list[int | None], home_values: list[int | None]) -> int | None:
	last_inning = 0
	for index in range(max(len(away_values), len(home_values))):
		away_value = away_values[index] if index < len(away_values) else None
		home_value = home_values[index] if index < len(home_values) else None
		if away_value is not None or home_value is not None:
			last_inning = index + 1
	return last_inning or None


def walkoff_flag(record: dict[str, Any], home_values: list[int | None]) -> int:
	innings = record.get("innings_played")
	away_score = parse_scoreboard_int(record.get("away_score"))
	home_score = parse_scoreboard_int(record.get("home_score"))
	if not innings or away_score is None or home_score is None or home_score <= away_score:
		return 0
	if innings > len(home_values):
		return 0
	home_runs_final = home_values[innings - 1]
	if home_runs_final is None or home_runs_final <= 0:
		return 0
	home_score_before_final = home_score - home_runs_final
	return 1 if home_score_before_final <= away_score else 0


def enrich_record_with_linescore(record: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
	inning_rows = parse_scoreboard_table(data.get("table2"))
	if len(inning_rows) >= 2:
		away_values = [parse_scoreboard_int(value) for value in inning_rows[0]]
		home_values = [parse_scoreboard_int(value) for value in inning_rows[1]]
		for inning in range(1, 13):
			record[f"away_runs_{inning}"] = away_values[inning - 1] if inning <= len(away_values) else None
			record[f"home_runs_{inning}"] = home_values[inning - 1] if inning <= len(home_values) else None
		for prefix, values in (("away", away_values), ("home", home_values)):
			record[f"{prefix}_first_5_runs"] = inning_sum(values, 0, 5)
			record[f"{prefix}_after_5_runs"] = inning_sum(values, 5)
			record[f"{prefix}_first_3_runs"] = inning_sum(values, 0, 3)
			record[f"{prefix}_middle_3_runs"] = inning_sum(values, 3, 6)
			record[f"{prefix}_late_runs"] = inning_sum(values, 6)
			record[f"{prefix}_score_after_5"] = score_after(values, 5)
			record[f"{prefix}_score_after_6"] = score_after(values, 6)
			record[f"{prefix}_score_after_7"] = score_after(values, 7)
		record["innings_played"] = innings_played(away_values, home_values)
		record["extra_inning_flag"] = 1 if (record.get("innings_played") or 0) > 9 else 0
		record["walkoff_flag"] = walkoff_flag(record, home_values)

	total_rows = parse_scoreboard_table(data.get("table3"))
	if len(total_rows) >= 2:
		for prefix, values in (("away", total_rows[0]), ("home", total_rows[1])):
			record[f"{prefix}_hits"] = parse_scoreboard_int(values[1]) if len(values) > 1 else None
			record[f"{prefix}_errors"] = parse_scoreboard_int(values[2]) if len(values) > 2 else None
			record[f"{prefix}_bases_on_balls"] = parse_scoreboard_int(values[3]) if len(values) > 3 else None

	return record


def has_value(value: Any) -> bool:
	if value is None:
		return False
	try:
		if pd.isna(value):
			return False
	except TypeError:
		pass
	return value != ""


def parse_play_cell(value: str | None) -> dict[str, Any]:
	if not value:
		return {
			"away_team": "",
			"away_score": None,
			"home_score": None,
			"home_team": "",
			"game_status": "unknown",
		}

	root = BeautifulSoup(f"<div>{value}</div>", "html.parser").div
	if root is None:
		return {
			"away_team": "",
			"away_score": None,
			"home_score": None,
			"home_team": "",
			"game_status": "unknown",
		}

	outer_spans = [child for child in root.children if getattr(child, "name", None) == "span"]
	em = root.find("em")

	away_team = outer_spans[0].get_text(" ", strip=True) if outer_spans else ""
	home_team = outer_spans[-1].get_text(" ", strip=True) if len(outer_spans) > 1 else ""
	away_score: int | None = None
	home_score: int | None = None
	game_status = "preview"

	if em is not None:
		score_spans = [span for span in em.find_all("span") if span.get_text(strip=True).isdigit()]
		if len(score_spans) >= 2:
			away_score = int(score_spans[0].get_text(strip=True))
			home_score = int(score_spans[1].get_text(strip=True))
			game_status = "final"

	return {
		"away_team": away_team,
		"away_score": away_score,
		"home_score": home_score,
		"home_team": home_team,
		"game_status": game_status,
	}


def fetch_schedule_month(
	session: requests.Session,
	year: int,
	month: int,
	series_ids: str = DEFAULT_SERIES_IDS,
	league_id: str = DEFAULT_LEAGUE_ID,
	team_id: str = "",
) -> dict[str, Any]:
	response = session.post(
		SCHEDULE_API_URL,
		data={
			"leId": league_id,
			"srIdList": series_ids,
			"seasonId": str(year),
			"gameMonth": f"{month:02d}",
			"teamId": team_id,
		},
		headers=schedule_headers(),
		timeout=30,
	)
	response.raise_for_status()
	return response.json()


def fetch_game_list(session: requests.Session, date_key: str) -> list[dict[str, Any]]:
	response = session.post(
		GAME_LIST_API_URL,
		data={"leId": DEFAULT_LEAGUE_ID, "srId": "0,1,3,4,5,6,7,8,9", "date": date_key},
		headers=schedule_headers(),
		timeout=30,
	)
	response.raise_for_status()
	return response.json().get("game", [])


def _match_game_list_record(record: dict[str, Any], game_list: list[dict[str, Any]], used_game_ids: set[str]) -> dict[str, Any] | None:
	game_id = record.get("game_id") or ""
	away_team = record.get("away_team") or ""
	home_team = record.get("home_team") or ""
	start_time = record.get("game_start_time") or ""

	if game_id:
		for game in game_list:
			if game.get("G_ID") == game_id:
				return game

	candidates = [
		game
		for game in game_list
		if game.get("AWAY_NM") == away_team and game.get("HOME_NM") == home_team and game.get("G_TM") == start_time
	]
	for game in candidates:
		candidate_id = str(game.get("G_ID") or "")
		if candidate_id and candidate_id not in used_game_ids:
			used_game_ids.add(candidate_id)
			return game

	for game in game_list:
		candidate_id = str(game.get("G_ID") or "")
		if candidate_id and candidate_id not in used_game_ids and game.get("AWAY_NM") == away_team and game.get("HOME_NM") == home_team:
			used_game_ids.add(candidate_id)
			return game

	for game in game_list:
		candidate_id = str(game.get("G_ID") or "")
		if candidate_id and candidate_id not in used_game_ids:
			used_game_ids.add(candidate_id)
			return game

	return None


def enrich_record_with_game_list(record: dict[str, Any], game_list: list[dict[str, Any]], used_game_ids: set[str]) -> dict[str, Any]:
	match = _match_game_list_record(record, game_list, used_game_ids)
	if match is None:
		return record

	record["game_id"] = match.get("G_ID") or record.get("game_id", "")
	record["sr_id"] = str(match.get("SR_ID") if match.get("SR_ID") is not None else record.get("sr_id") or "0")
	record["game_start_time"] = match.get("G_TM") or record.get("game_start_time", "")
	record["game_date_key"] = match.get("G_DT") or record.get("game_date_key", "")

	cancel_reason = (match.get("CANCEL_SC_NM") or "").strip()
	if cancel_reason and cancel_reason != "정상경기":
		record["game_status"] = "cancelled"
		record["status_reason"] = cancel_reason
	elif match.get("GAME_RESULT_CK") == 0 and record.get("game_status") == "preview":
		record["game_status"] = "preview"

	return record


def fetch_scoreboard_scroll(session: requests.Session, record: dict[str, Any]) -> dict[str, Any]:
	game_id = record.get("game_id") or ""
	if not game_id:
		return record

	sr_id = str(record.get("sr_id") or "0")
	response = session.post(
		SCOREBOARD_API_URL,
		data={
			"type": DEFAULT_SCOREBOARD_TYPE,
			"leId": DEFAULT_LEAGUE_ID,
			"srId": sr_id,
			"seasonId": str(record.get("season_year") or ""),
			"gameId": game_id,
		},
		headers=scoreboard_headers(int(record.get("season_year") or 0), game_id, sr_id),
		timeout=30,
	)
	response.raise_for_status()
	data = response.json()
	if str(data.get("code") or "") != "100":
		return record

	crowd_text = data.get("CROWD_CN")
	record["crowd"] = int(str(crowd_text).replace(",", "")) if crowd_text not in (None, "") else None
	start_time = data.get("START_TM")
	end_time = data.get("END_TM")
	duration_value = data.get("USE_TM")
	if start_time:
		record["game_start_time"] = start_time
	record["game_finish_time"] = end_time or ""
	record["game_duration_min"] = parse_duration_to_minutes(duration_value)
	if data.get("S_NM"):
		record["stadium"] = data.get("S_NM")
	record = enrich_record_with_linescore(record, data)
	return record


def parse_schedule_rows(year: int, month: int, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	parsed_rows: list[dict[str, Any]] = []
	current_date = ""
	current_weekday = ""

	for row in rows:
		cells = row.get("row", [])
		if not cells:
			continue

		first_text = strip_html(cells[0].get("Text"))
		first_class = cells[0].get("Class") or ""

		if first_class == "day":
			current_date, current_weekday = parse_date_string(year, first_text)
			time_index = 1
		else:
			time_index = 0

		if len(cells) <= time_index + 1:
			continue

		time_text = strip_html(cells[time_index].get("Text"))
		play_cell = cells[time_index + 1]
		relay_cell = cells[time_index + 2] if len(cells) > time_index + 2 else {}
		highlight_cell = cells[time_index + 3] if len(cells) > time_index + 3 else {}
		broadcast_cell = cells[time_index + 4] if len(cells) > time_index + 4 else {}
		extra_cell = cells[time_index + 5] if len(cells) > time_index + 5 else {}
		stadium_cell = cells[time_index + 6] if len(cells) > time_index + 6 else {}
		note_cell = cells[time_index + 7] if len(cells) > time_index + 7 else {}

		play_data = parse_play_cell(play_cell.get("Text"))
		note_text = strip_html(note_cell.get("Text"))
		status_reason = note_text if any(keyword in note_text for keyword in ("우천", "취소", "연기", "서스펜디드", "콜드", "몰수")) else ""
		game_status = "cancelled" if status_reason else play_data["game_status"]
		game_id = extract_game_id(cells)

		parsed_rows.append(
			{
				"season_year": year,
				"game_id": game_id,
				"sr_id": "",
				"source_month": f"{month:02d}",
				"game_date": current_date,
				"game_date_key": current_date.replace("-", ""),
				"weekday_ko": current_weekday,
				"weekday_en": weekday_en(current_weekday),
				"game_start_time": time_text,
				"game_finish_time": "",
				"game_duration_min": pd.NA,
				"crowd": pd.NA,
				"away_team": play_data["away_team"],
				"away_score": play_data["away_score"],
				"home_score": play_data["home_score"],
				"home_team": play_data["home_team"],
				"game_status": game_status,
				"status_reason": status_reason,
				"stadium": strip_html(stadium_cell.get("Text")),
				"broadcast": strip_html(broadcast_cell.get("Text")),
				"extra": strip_html(extra_cell.get("Text")),
				"note": note_text,
				"raw_row_json": json.dumps(row, ensure_ascii=False),
			}
		)

	return parsed_rows


def output_paths(year: int) -> OutputPaths:
	root = Path(__file__).resolve().parents[1]
	output_dir = root / "data" / "output"
	raw_dir = root / "data" / "raw" / str(year)
	output_dir.mkdir(parents=True, exist_ok=True)
	raw_dir.mkdir(parents=True, exist_ok=True)
	return OutputPaths(
		xlsx_path=output_dir / "kbo_schedule.xlsx",
		raw_dir=raw_dir,
	)


def save_raw_month(year: int, month: int, payload: dict[str, Any], raw_dir: Path) -> Path:
	path = raw_dir / f"schedule_{year}_{month:02d}.json"
	path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
	return path


def parse_months(value: str) -> list[int]:
	value = value.strip()
	if "-" in value:
		start_text, end_text = value.split("-", 1)
		return list(range(int(start_text), int(end_text) + 1))
	month_list = [int(part.strip()) for part in value.split(",") if part.strip()]
	return month_list or list(range(1, 13))


def crawl_season(
	year: int,
	months: list[int],
	series_ids: str = DEFAULT_SERIES_IDS,
	team_id: str = "",
) -> list[dict[str, Any]]:
	session = build_session()
	records: list[dict[str, Any]] = []
	seen_ids: set[str] = set()
	game_list_cache: dict[str, list[dict[str, Any]]] = {}
	used_game_ids_by_date: dict[str, set[str]] = {}
	game_details_cache: dict[str, dict[str, Any]] = {}
	paths = output_paths(year)

	for month in months:
		payload = fetch_schedule_month(
			session,
			year,
			month,
			series_ids=series_ids,
			team_id=team_id,
		)
		save_raw_month(year, month, payload, paths.raw_dir)
		month_records = parse_schedule_rows(year, month, payload.get("rows", []))

		for record in month_records:
			date_key = record["game_date_key"]
			if date_key not in game_list_cache:
				game_list_cache[date_key] = fetch_game_list(session, date_key)
			if date_key not in used_game_ids_by_date:
				used_game_ids_by_date[date_key] = set()
			record = enrich_record_with_game_list(record, game_list_cache[date_key], used_game_ids_by_date[date_key])
			if record.get("game_id") and record["game_id"] not in game_details_cache:
				game_details_cache[record["game_id"]] = fetch_scoreboard_scroll(session, record)
			if record.get("game_id") and record["game_id"] in game_details_cache:
				details = game_details_cache[record["game_id"]]
				for key in SCOREBOARD_DETAIL_KEYS:
					if has_value(details.get(key)):
						record[key] = details[key]

			dedupe_key = record["game_id"] or f"{record['game_date_key']}|{record['game_start_time']}|{record['away_team']}|{record['home_team']}"
			if dedupe_key in seen_ids:
				continue
			seen_ids.add(dedupe_key)
			records.append(record)

	return records


def build_schedule_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
	frame = pd.DataFrame(records)
	frame = frame.drop(columns=["raw_row_json", "sr_id"], errors="ignore")

	numeric_columns = (
		"away_score",
		"home_score",
		"game_duration_min",
		"crowd",
		"innings_played",
		"extra_inning_flag",
		"walkoff_flag",
		*(
			f"{prefix}_{suffix}"
			for prefix in ("away", "home")
			for suffix in (
				"hits",
				"errors",
				"bases_on_balls",
				"first_5_runs",
				"after_5_runs",
				"first_3_runs",
				"middle_3_runs",
				"late_runs",
				"score_after_5",
				"score_after_6",
				"score_after_7",
			)
		),
		*(f"{prefix}_runs_{inning}" for prefix in ("away", "home") for inning in range(1, 13)),
	)
	for column in numeric_columns:
		if column in frame.columns:
			frame[column] = frame[column].astype("Int64")

	if not frame.empty:
		desired_columns = [
			"game_id",
			"season_year",
			"source_month",
			"game_date",
			"game_date_key",
			"weekday_ko",
			"weekday_en",
			"game_start_time",
			"game_finish_time",
			"game_duration_min",
			"crowd",
			"innings_played",
			"extra_inning_flag",
			"walkoff_flag",
			"away_team",
			"away_score",
			"home_score",
			"home_team",
			"away_hits",
			"home_hits",
			"away_errors",
			"home_errors",
			"away_bases_on_balls",
			"home_bases_on_balls",
			"away_first_5_runs",
			"home_first_5_runs",
			"away_after_5_runs",
			"home_after_5_runs",
			"away_first_3_runs",
			"home_first_3_runs",
			"away_middle_3_runs",
			"home_middle_3_runs",
			"away_late_runs",
			"home_late_runs",
			"away_score_after_5",
			"home_score_after_5",
			"away_score_after_6",
			"home_score_after_6",
			"away_score_after_7",
			"home_score_after_7",
			*(f"away_runs_{inning}" for inning in range(1, 13)),
			*(f"home_runs_{inning}" for inning in range(1, 13)),
			"game_status",
			"status_reason",
			"stadium",
			"broadcast",
			"extra",
			"note",
		]
		ordered_columns = [column for column in desired_columns if column in frame.columns]
		remainder = [column for column in frame.columns if column not in ordered_columns]
		frame = frame[ordered_columns + remainder]

	return frame


def write_schedule_workbook(frame: pd.DataFrame, workbook_path: Path) -> Path:
	return write_with_permission_fallback(workbook_path, lambda path: frame.to_excel(path, index=False))
