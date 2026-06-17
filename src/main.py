from __future__ import annotations

import argparse
from datetime import datetime

from crawler import build_schedule_dataframe, crawl_season, output_paths, write_schedule_workbook
from team_sheets import build_team_sheet_rows, write_team_workbook


def parse_months(value: str) -> list[int]:
	value = value.strip()
	if "-" in value:
		start_text, end_text = value.split("-", 1)
		return list(range(int(start_text), int(end_text) + 1))
	month_list = [int(part.strip()) for part in value.split(",") if part.strip()]
	return month_list or list(range(1, 13))


def build_argument_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Crawl KBO season data and build per-team sheets.")
	parser.add_argument("--year", type=int, default=datetime.now().year, help="Season year to crawl.")
	parser.add_argument("--series-ids", default="0,9,6", help="Comma-separated series IDs used by KBO.")
	parser.add_argument("--team-id", default="", help="Optional team filter passed to the KBO endpoint.")
	parser.add_argument("--months", default="1-12", help="Month range to crawl, for example 3-12 or 1,2,3.")
	return parser


def main() -> int:
	parser = build_argument_parser()
	args = parser.parse_args()

	months = parse_months(args.months)
	paths = output_paths(args.year)
	records = crawl_season(
		args.year,
		months,
		series_ids=args.series_ids,
		team_id=args.team_id,
	)
	season_frame = build_schedule_dataframe(records)
	season_workbook_path = write_schedule_workbook(season_frame, paths.xlsx_path)
	team_frame = build_team_sheet_rows(season_frame)
	requested_team_workbook_path = paths.xlsx_path.with_name(f"kbo_team_sheets_{args.year}.xlsx")
	team_workbook_path = write_team_workbook(team_frame, requested_team_workbook_path)

	print(f"Saved {len(season_frame)} games")
	print(f"Season workbook: {season_workbook_path}")
	if season_workbook_path != paths.xlsx_path:
		print(f"Original season workbook was locked: {paths.xlsx_path}")
	print(f"Team workbook: {team_workbook_path}")
	if team_workbook_path != requested_team_workbook_path:
		print(f"Original team workbook was locked: {requested_team_workbook_path}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
