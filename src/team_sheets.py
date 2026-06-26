from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from excel_output import write_with_permission_fallback


TEAM_COLUMNS = [
	"game_id",
	"season_year",
	"source_month",
	"game_date",
	"weekday_ko",
	"weekday_en",
	"game_duration_min",
	"crowd",
	"innings_played",
	"extra_inning_flag",
	"team",
	"opponent",
	"home_away",
	"runs_for",
	"runs_against",
	"run_diff",
	"total_runs",
	"result",
	"win_flag",
	"loss_flag",
	"draw_flag",
	"cancellation_flag",
	"home_flag",
	"away_flag",
	"one_run_game",
	"shutout_win",
	"shutout_loss",
	"hits_for",
	"hits_against",
	"errors_for",
	"errors_against",
	"bases_on_balls_for",
	"bases_on_balls_against",
	"first_5_runs_for",
	"first_5_runs_against",
	"after_5_runs_for",
	"after_5_runs_against",
	"first_3_runs_for",
	"first_3_runs_against",
	"middle_3_runs_for",
	"middle_3_runs_against",
	"late_runs_for",
	"late_runs_against",
	"score_after_5_for",
	"score_after_5_against",
	"score_after_6_for",
	"score_after_6_against",
	"score_after_7_for",
	"score_after_7_against",
	"comeback_win",
	"blown_loss",
]


def _to_int(value: Any) -> int | None:
	try:
		if pd.isna(value):
			return None
	except TypeError:
		pass
	if value is None or value == "":
		return None
	try:
		return int(value)
	except (TypeError, ValueError):
		return None


def _result_flags(game_status: str, runs_for: int | None, runs_against: int | None) -> tuple[str, int, int, int, int, int, int, int, int]:
	if game_status == "cancelled":
		return "Cancel", 0, 0, 0, 1, 0, 0, 0, 0
	if runs_for is None or runs_against is None:
		return "Cancel", 0, 0, 0, 1, 0, 0, 0, 0
	if runs_for > runs_against:
		one_run_game = 1 if runs_for - runs_against == 1 else 0
		shutout_win = 1 if runs_against == 0 else 0
		return "W", 1, 0, 0, 0, 1 if one_run_game else 0, shutout_win, 0, 0
	if runs_for < runs_against:
		shutout_loss = 1 if runs_for == 0 else 0
		return "L", 0, 1, 0, 0, 0, 0, 0, shutout_loss
	return "D", 0, 0, 1, 0, 0, 0, 0, 0


def _prefixed_int(row: pd.Series, prefix: str, suffix: str) -> int | None:
	return _to_int(row.get(f"{prefix}_{suffix}"))


def _inning_score_states(row: pd.Series, prefix: str, opponent_prefix: str) -> list[tuple[int, int]]:
	score_for = 0
	score_against = 0
	states: list[tuple[int, int]] = []
	innings_played = _to_int(row.get("innings_played")) or 12

	for inning in range(1, min(innings_played, 12) + 1):
		runs_for = _prefixed_int(row, prefix, f"runs_{inning}")
		runs_against = _prefixed_int(row, opponent_prefix, f"runs_{inning}")
		if runs_for is None and runs_against is None:
			continue
		score_for += runs_for or 0
		score_against += runs_against or 0
		if inning < innings_played:
			states.append((score_for, score_against))
	return states


def _comeback_flags(
	row: pd.Series,
	result: str,
	prefix: str,
	opponent_prefix: str,
) -> tuple[int, int]:
	states = _inning_score_states(row, prefix, opponent_prefix)
	comeback_win = 1 if result == "W" and any(score_for < score_against for score_for, score_against in states) else 0
	blown_loss = 1 if result == "L" and any(score_for > score_against for score_for, score_against in states) else 0
	return comeback_win, blown_loss


def build_team_sheet_rows(schedule_frame: pd.DataFrame) -> pd.DataFrame:
	rows: list[dict[str, Any]] = []

	for _, row in schedule_frame.iterrows():
		game_id = row.get("game_id")
		season_year = row.get("season_year")
		source_month = row.get("source_month")
		game_date = row.get("game_date")
		weekday_ko = row.get("weekday_ko")
		weekday_en = row.get("weekday_en")
		game_duration_min = _to_int(row.get("game_duration_min"))
		crowd = _to_int(row.get("crowd"))
		innings_played = _to_int(row.get("innings_played"))
		extra_inning_flag = 1 if _to_int(row.get("extra_inning_flag")) == 1 else 0
		away_team = row.get("away_team")
		home_team = row.get("home_team")
		away_score = _to_int(row.get("away_score"))
		home_score = _to_int(row.get("home_score"))
		game_status = str(row.get("game_status") or "")

		for team, opponent, home_away, runs_for, runs_against, prefix, opponent_prefix in (
			(away_team, home_team, "away", away_score, home_score, "away", "home"),
			(home_team, away_team, "home", home_score, away_score, "home", "away"),
		):
			result, win_flag, loss_flag, draw_flag, cancellation_flag, one_run_game, shutout_win, _, shutout_loss = _result_flags(
				game_status,
				runs_for,
				runs_against,
			)
			score_after_6_for = _prefixed_int(row, prefix, "score_after_6")
			score_after_6_against = _prefixed_int(row, opponent_prefix, "score_after_6")
			comeback_win, blown_loss = _comeback_flags(
				row,
				result,
				prefix,
				opponent_prefix,
			)
			rows.append(
				{
					"game_id": game_id,
					"season_year": season_year,
					"source_month": source_month,
					"game_date": game_date,
					"weekday_ko": weekday_ko,
					"weekday_en": weekday_en,
					"game_duration_min": game_duration_min,
					"crowd": crowd,
					"innings_played": innings_played,
					"extra_inning_flag": extra_inning_flag,
					"team": team,
					"opponent": opponent,
					"home_away": home_away,
					"runs_for": runs_for,
					"runs_against": runs_against,
					"run_diff": None if runs_for is None or runs_against is None else runs_for - runs_against,
					"total_runs": None if runs_for is None or runs_against is None else runs_for + runs_against,
					"result": result,
					"win_flag": win_flag,
					"loss_flag": loss_flag,
					"draw_flag": draw_flag,
					"cancellation_flag": cancellation_flag,
					"home_flag": 1 if home_away == "home" else 0,
					"away_flag": 1 if home_away == "away" else 0,
					"one_run_game": one_run_game,
					"shutout_win": shutout_win,
					"shutout_loss": shutout_loss,
					"hits_for": _prefixed_int(row, prefix, "hits"),
					"hits_against": _prefixed_int(row, opponent_prefix, "hits"),
					"errors_for": _prefixed_int(row, prefix, "errors"),
					"errors_against": _prefixed_int(row, opponent_prefix, "errors"),
					"bases_on_balls_for": _prefixed_int(row, prefix, "bases_on_balls"),
					"bases_on_balls_against": _prefixed_int(row, opponent_prefix, "bases_on_balls"),
					"first_5_runs_for": _prefixed_int(row, prefix, "first_5_runs"),
					"first_5_runs_against": _prefixed_int(row, opponent_prefix, "first_5_runs"),
					"after_5_runs_for": _prefixed_int(row, prefix, "after_5_runs"),
					"after_5_runs_against": _prefixed_int(row, opponent_prefix, "after_5_runs"),
					"first_3_runs_for": _prefixed_int(row, prefix, "first_3_runs"),
					"first_3_runs_against": _prefixed_int(row, opponent_prefix, "first_3_runs"),
					"middle_3_runs_for": _prefixed_int(row, prefix, "middle_3_runs"),
					"middle_3_runs_against": _prefixed_int(row, opponent_prefix, "middle_3_runs"),
					"late_runs_for": _prefixed_int(row, prefix, "late_runs"),
					"late_runs_against": _prefixed_int(row, opponent_prefix, "late_runs"),
					"score_after_5_for": _prefixed_int(row, prefix, "score_after_5"),
					"score_after_5_against": _prefixed_int(row, opponent_prefix, "score_after_5"),
					"score_after_6_for": score_after_6_for,
					"score_after_6_against": score_after_6_against,
					"score_after_7_for": _prefixed_int(row, prefix, "score_after_7"),
					"score_after_7_against": _prefixed_int(row, opponent_prefix, "score_after_7"),
					"comeback_win": comeback_win,
					"blown_loss": blown_loss,
				}
			)

	team_frame = pd.DataFrame(rows)
	if not team_frame.empty:
		team_frame = team_frame[TEAM_COLUMNS]
	else:
		team_frame = pd.DataFrame(columns=TEAM_COLUMNS)
	return team_frame


def write_team_workbook(team_frame: pd.DataFrame, workbook_path: Path) -> Path:
	def write(path: Path) -> None:
		with pd.ExcelWriter(path, engine="openpyxl") as writer:
			team_frame.to_excel(writer, sheet_name="Total", index=False)
			for team_name in sorted(team_frame["team"].dropna().unique()):
				team_frame[team_frame["team"] == team_name].to_excel(writer, sheet_name=str(team_name)[:31], index=False)

	return write_with_permission_fallback(workbook_path, write)
