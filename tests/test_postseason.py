from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crawler import build_schedule_dataframe, enrich_record_with_game_list  # noqa: E402
from dashboard import (  # noqa: E402
	build_matchup_records,
	build_postseason_matchup_history,
	canonical_postseason_team,
	postseason_series_summaries,
)


class PostseasonCrawlerTests(unittest.TestCase):
	def test_game_list_metadata_identifies_round_and_game_number(self) -> None:
		record = {
			"game_id": "20251026HHLG0",
			"away_team": "한화",
			"home_team": "LG",
			"game_start_time": "14:00",
			"competition_type": "postseason",
		}
		game_list = [
			{
				"G_ID": "20251026HHLG0",
				"SR_ID": 7,
				"GAME_SC_ID": 19,
				"GAME_SC_NM": "KS1",
				"G_TM": "14:00",
				"G_DT": "20251026",
				"AWAY_NM": "한화",
				"HOME_NM": "LG",
				"CANCEL_SC_NM": "정상경기",
				"GAME_RESULT_CK": 1,
			}
		]

		result = enrich_record_with_game_list(record, game_list, set())

		self.assertEqual(result["series_id"], "7")
		self.assertEqual(result["series_code"], "KS")
		self.assertEqual(result["series_name"], "한국시리즈")
		self.assertEqual(result["series_game_no"], 1)
		self.assertEqual(result["round_order"], 4)

	def test_schedule_dataframe_preserves_competition_fields(self) -> None:
		frame = build_schedule_dataframe(
			[
				{
					"game_id": "game",
					"season_year": 2025,
					"competition_type": "postseason",
					"series_id": "4",
					"series_code": "WC",
					"series_name": "와일드카드 결정전",
					"series_game_code": "WC2",
					"series_game_no": 2,
					"round_order": 1,
				}
			]
		)

		self.assertEqual(frame.loc[0, "competition_type"], "postseason")
		self.assertEqual(frame.loc[0, "series_code"], "WC")
		self.assertEqual(frame.loc[0, "series_game_no"], 2)


class PostseasonSeriesTests(unittest.TestCase):
	def test_matchup_history_combines_predecessor_team_names(self) -> None:
		team = pd.DataFrame(
			[
				{
					"game_id": "2015-game",
					"season_year": 2015,
					"is_final": True,
					"team": "SK",
					"opponent": "넥센",
					"home_away": "home",
					"win_flag": 1,
					"loss_flag": 0,
					"draw_flag": 0,
				},
				{
					"game_id": "2015-game",
					"season_year": 2015,
					"is_final": True,
					"team": "넥센",
					"opponent": "SK",
					"home_away": "away",
					"win_flag": 0,
					"loss_flag": 1,
					"draw_flag": 0,
				},
				{
					"game_id": "2022-game",
					"season_year": 2022,
					"is_final": True,
					"team": "SSG",
					"opponent": "키움",
					"home_away": "away",
					"win_flag": 0,
					"loss_flag": 1,
					"draw_flag": 0,
				},
				{
					"game_id": "2022-game",
					"season_year": 2022,
					"is_final": True,
					"team": "키움",
					"opponent": "SSG",
					"home_away": "home",
					"win_flag": 1,
					"loss_flag": 0,
					"draw_flag": 0,
				},
			]
		)

		history = build_postseason_matchup_history(team, 2025, ["SSG", "키움"])
		matchups = build_matchup_records(history)
		ssg_record = matchups[(matchups["team"] == "SSG") & (matchups["opponent"] == "키움")].iloc[0]

		self.assertEqual(canonical_postseason_team("SK"), "SSG")
		self.assertEqual(canonical_postseason_team("넥센"), "키움")
		self.assertEqual(int(ssg_record["overall_games"]), 2)
		self.assertEqual(int(ssg_record["overall_wins"]), 1)
		self.assertEqual(int(ssg_record["overall_losses"]), 1)

	def test_fourth_seed_advances_after_splitting_wild_card_games(self) -> None:
		schedule = pd.DataFrame(
			[
				{
					"series_code": "WC",
					"game_date": pd.Timestamp("2025-10-06"),
					"series_game_no": 1,
					"game_start_time": "14:00",
					"away_team": "5위팀",
					"home_team": "4위팀",
					"away_score": 4,
					"home_score": 1,
					"game_status": "final",
				},
				{
					"series_code": "WC",
					"game_date": pd.Timestamp("2025-10-07"),
					"series_game_no": 2,
					"game_start_time": "14:00",
					"away_team": "5위팀",
					"home_team": "4위팀",
					"away_score": 0,
					"home_score": 3,
					"game_status": "final",
				},
			]
		)
		seed_order = ["1위팀", "2위팀", "3위팀", "4위팀", "5위팀"]

		wild_card = postseason_series_summaries(schedule, seed_order)[0]

		self.assertEqual(wild_card["wins"], {"4위팀": 1, "5위팀": 1})
		self.assertEqual(wild_card["winner"], "4위팀")
		self.assertEqual(wild_card["state"], "종료")
		self.assertIn("4위 어드밴티지", wild_card["note"])


if __name__ == "__main__":
	unittest.main()
