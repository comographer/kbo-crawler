from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from excel_output import write_with_permission_fallback


TEAM_COLUMNS = [
	"game_id",
	"source_month",
	"game_date",
	"weekday_ko",
	"weekday_en",
	"game_duration_min",
	"crowd",
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


def build_team_sheet_rows(schedule_frame: pd.DataFrame) -> pd.DataFrame:
	rows: list[dict[str, Any]] = []

	for _, row in schedule_frame.iterrows():
		game_id = row.get("game_id")
		source_month = row.get("source_month")
		game_date = row.get("game_date")
		weekday_ko = row.get("weekday_ko")
		weekday_en = row.get("weekday_en")
		game_duration_min = _to_int(row.get("game_duration_min"))
		crowd = _to_int(row.get("crowd"))
		away_team = row.get("away_team")
		home_team = row.get("home_team")
		away_score = _to_int(row.get("away_score"))
		home_score = _to_int(row.get("home_score"))
		game_status = str(row.get("game_status") or "")

		for team, opponent, home_away, runs_for, runs_against in (
			(away_team, home_team, "away", away_score, home_score),
			(home_team, away_team, "home", home_score, away_score),
		):
			result, win_flag, loss_flag, draw_flag, cancellation_flag, one_run_game, shutout_win, _, shutout_loss = _result_flags(
				game_status,
				runs_for,
				runs_against,
			)
			rows.append(
				{
					"game_id": game_id,
					"source_month": source_month,
					"game_date": game_date,
					"weekday_ko": weekday_ko,
					"weekday_en": weekday_en,
					"game_duration_min": game_duration_min,
					"crowd": crowd,
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
