from __future__ import annotations

import hashlib
import html
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]


def first_existing_path(*paths: Path) -> Path:
	for path in paths:
		if path.exists():
			return path
	return paths[0]


def file_signature(path: Path) -> tuple[int, str]:
	digest = hashlib.sha256()
	with path.open("rb") as file:
		for chunk in iter(lambda: file.read(1024 * 1024), b""):
			digest.update(chunk)
	return path.stat().st_size, digest.hexdigest()


SCHEDULE_PATH = first_existing_path(
	ROOT / "data" / "output" / "kbo_schedule.xlsx",
	ROOT / "data" / "output" / "kbo_schedule_2026.xlsx",
)
TEAM_PATH = first_existing_path(
	ROOT / "data" / "output" / "kbo_team_sheets.xlsx",
	ROOT / "data" / "output" / "kbo_team_sheets_2026.xlsx",
)
FINAL_RESULTS = {"W", "L", "D"}
RESULT_COLORS = {
	"W": "#3D7A5F",
	"L": "#B85C5C",
	"D": "#7A7F87",
	"Cancel": "#A97846",
}
HEATMAP_CLASS_COLORS = {
	"light": {
		"negative": "#E7AAAA",
		"neutral": "#D8DEE2",
		"positive": "#A9DDB6",
	},
	"dark": {
		"negative": "#7C3A3A",
		"neutral": "#4A565D",
		"positive": "#345F3E",
	},
}
TEAM_COLORS = {
	"KIA": "#EA0029",
	"KT": "#000000",
	"LG": "#C30452",
	"NC": "#315288",
	"SSG": "#CE0E2D",
	"두산": "#1A1748",
	"롯데": "#041E42",
	"삼성": "#074CA1",
	"키움": "#570514",
	"한화": "#FC4E00",
}
HOME_AWAY_LABELS = {"home": "홈", "away": "원정"}
STATUS_LABELS = {"final": "종료", "preview": "예정", "cancelled": "취소", "unknown": "미상"}
WEEKDAY_LABELS = {
	"Mon": "월",
	"Tue": "화",
	"Wed": "수",
	"Thu": "목",
	"Fri": "금",
	"Sat": "토",
	"Sun": "일",
}
HOME_AWAY_ORDER = ["홈", "원정"]
WEEKDAY_ORDER = ["월", "화", "수", "목", "금", "토", "일"]
RESULT_LEGEND_ORDER = ["W", "L", "D"]
RESULT_BAR_ORDER = ["L", "W", "D"]
GREEN_SCALE = ["#F3FAF4", "#DCEFE1", "#B9DFC3", "#86C995", "#4CA764", "#1F7A3B"]
SOFT_GREEN_SCALE = ["#F6FBF7", "#E7F4EA", "#CFE8D5", "#A8D2B5", "#73B584"]
PLOT_TEMPLATE = "plotly_white"
ACTIVE_DARK_MODE = False
ACTIVE_TEAM_COLORS = TEAM_COLORS.copy()
ACTIVE_GREEN_SCALE = GREEN_SCALE
ACTIVE_SOFT_GREEN_SCALE = SOFT_GREEN_SCALE
ACTIVE_PLOT_TEMPLATE = PLOT_TEMPLATE


def hex_to_rgb(value: str) -> tuple[int, int, int]:
	value = value.strip().lstrip("#")
	return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def rgb_to_hex(red: int, green: int, blue: int) -> str:
	return f"#{red:02X}{green:02X}{blue:02X}"


def mix_hex(color: str, target: str, amount: float) -> str:
	red, green, blue = hex_to_rgb(color)
	target_red, target_green, target_blue = hex_to_rgb(target)
	return rgb_to_hex(
		round(red + (target_red - red) * amount),
		round(green + (target_green - green) * amount),
		round(blue + (target_blue - blue) * amount),
	)


def filtered_team_colors(dark_mode: bool) -> dict[str, str]:
	if not dark_mode:
		return TEAM_COLORS.copy()
	return {
		team: mix_hex(color, "#ECEFF1", 0.52 if team == "KT" else 0.34)
		for team, color in TEAM_COLORS.items()
	}


def set_visual_mode(dark_mode: bool) -> None:
	global ACTIVE_DARK_MODE, ACTIVE_TEAM_COLORS, ACTIVE_GREEN_SCALE, ACTIVE_SOFT_GREEN_SCALE, ACTIVE_PLOT_TEMPLATE
	ACTIVE_DARK_MODE = dark_mode
	ACTIVE_TEAM_COLORS = filtered_team_colors(dark_mode)
	ACTIVE_GREEN_SCALE = ["#18261C", "#21402A", "#2D5C38", "#3F7E49", "#63A869", "#A6D7A8"] if dark_mode else GREEN_SCALE
	ACTIVE_SOFT_GREEN_SCALE = ["#1B2420", "#25352C", "#35513E", "#4B7258", "#76A684"] if dark_mode else SOFT_GREEN_SCALE
	ACTIVE_PLOT_TEMPLATE = "plotly_dark" if dark_mode else PLOT_TEMPLATE


def active_team_colors() -> dict[str, str]:
	return ACTIVE_TEAM_COLORS


def active_green_scale() -> list[str]:
	return ACTIVE_GREEN_SCALE


def active_soft_green_scale() -> list[str]:
	return ACTIVE_SOFT_GREEN_SCALE


def theme_css(dark_mode: bool) -> str:
	if dark_mode:
		return """
		<style>
		.stApp {background-color: #0E1519; color: #E6ECEF;}
		header[data-testid="stHeader"] {background-color: #0E1519;}
		[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
			background-color: #0E1519;
			color: #D7E0E5;
		}
		.block-container {padding-top: 1.5rem; padding-bottom: 1.5rem;}
		h1, h2, h3, h4, h5, h6, p, label, span, div {
			color: #DCE5E9;
		}
		[data-testid="stCaptionContainer"], [data-testid="stMarkdownContainer"] {
			color: #C6D2D8;
		}
		[data-testid="stMetricValue"] {font-size: 1.55rem; color: #F4F7F8;}
		[data-testid="stMetricLabel"] {color: #B6C4CB;}
		.stTabs [data-baseweb="tab-list"] {gap: 0.5rem;}
		.stTabs [data-baseweb="tab"] p {color: #D6E0E5; font-size: 1.06rem; font-weight: 650;}
		.stTabs [aria-selected="true"] p {color: #F4F7F8;}
		section[data-testid="stSidebar"] {background-color: #111A1F;}
		div[data-baseweb="select"] > div,
		section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
			background-color: #182329;
			border-color: #3B4B54;
			color: #E6ECEF;
		}
		div[data-baseweb="select"] input,
		div[data-baseweb="select"] span,
		div[data-baseweb="select"] svg {
			color: #E6ECEF;
			fill: #E6ECEF;
		}
		div[data-baseweb="popover"],
		div[data-baseweb="popover"] ul,
		div[data-baseweb="popover"] li {
			background-color: #182329;
			color: #E6ECEF;
		}
		li[role="option"]:hover {
			background-color: #263640;
		}
		section[data-testid="stSidebar"] [data-baseweb="tag"] {
			background-color: #263238;
			border: 1px solid #42545D;
			color: #E6ECEF;
		}
		section[data-testid="stSidebar"] [data-baseweb="tag"] span {color: #E6ECEF;}
		section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p {
			color: #D2DCE1;
		}
		[data-testid="stDataFrame"], [data-testid="stTable"] {
			background-color: #111A1F;
			color: #DCE5E9;
		}
		.kbo-table-wrap {
			max-height: 520px;
			overflow: auto;
			border: 1px solid #2B3A42;
			border-radius: 6px;
			background-color: #111A1F;
		}
		.kbo-table {
			width: 100%;
			border-collapse: collapse;
			font-size: 0.88rem;
		}
		.kbo-table th {
			position: sticky;
			top: 0;
			background-color: #1A252B;
			color: #EAF0F3;
			border-bottom: 1px solid #344650;
			padding: 0.45rem 0.55rem;
			text-align: left;
			white-space: nowrap;
		}
		.kbo-table td {
			background-color: #111A1F;
			color: #DCE5E9;
			border-bottom: 1px solid #24333B;
			padding: 0.4rem 0.55rem;
			white-space: nowrap;
		}
		.kbo-table tr:nth-child(even) td {
			background-color: #152027;
		}
		.standings-table-wrap {
			border: 1px solid #2B3A42;
			border-radius: 8px;
			overflow: hidden;
			background-color: #111A1F;
		}
		.standings-table {
			width: 100%;
			border-collapse: collapse;
			font-size: 0.9rem;
		}
		.standings-table th {
			background-color: #1A252B;
			color: #EAF0F3;
			border-bottom: 1px solid #344650;
			padding: 0.55rem 0.6rem;
			text-align: left;
			white-space: nowrap;
		}
		.standings-table td {
			background-color: #111A1F;
			color: #DCE5E9;
			border-bottom: 1px solid #24333B;
			padding: 0.48rem 0.6rem;
			white-space: nowrap;
		}
		.standings-table tr:nth-child(even) td {
			background-color: #152027;
		}
		.team-chip {
			display: inline-flex;
			align-items: center;
			gap: 0.4rem;
			font-weight: 700;
		}
		.team-dot {
			display: inline-block;
			width: 0.65rem;
			height: 0.65rem;
			border-radius: 999px;
		}
		.tone-positive {
			background-color: rgba(74, 138, 88, 0.32) !important;
			color: #BDE4C3 !important;
			font-weight: 700;
		}
		.tone-negative {
			background-color: rgba(178, 82, 82, 0.3) !important;
			color: #F0B6B6 !important;
			font-weight: 700;
		}
		.tone-neutral {
			background-color: rgba(128, 143, 151, 0.28) !important;
			color: #D5DEE3 !important;
			font-weight: 700;
		}
		.recent-table-wrap {
			border: 1px solid #2B3A42;
			border-radius: 8px;
			overflow: hidden;
			background-color: #111A1F;
		}
		.recent-table {
			width: 100%;
			border-collapse: collapse;
			font-size: 0.92rem;
		}
		.recent-table th {
			background-color: #1A252B;
			color: #EAF0F3;
			border-bottom: 1px solid #344650;
			padding: 0.65rem 0.7rem;
			text-align: left;
			white-space: nowrap;
		}
		.recent-table td {
			background-color: #111A1F;
			color: #DCE5E9;
			border-bottom: 1px solid #24333B;
			padding: 0.6rem 0.7rem;
			white-space: nowrap;
		}
		.recent-table tr:nth-child(even) td {
			background-color: #152027;
		}
		.result-badge {
			display: inline-flex;
			align-items: center;
			justify-content: center;
			min-width: 2rem;
			padding: 0.15rem 0.45rem;
			border-radius: 999px;
			font-weight: 700;
			color: #FFFFFF;
		}
		.result-W {background-color: #3D7A5F;}
		.result-L {background-color: #B85C5C;}
		.result-D {background-color: #7A7F87;}
		.diff-plus {color: #9FD5AA; font-weight: 700;}
		.diff-minus {color: #E3A0A0; font-weight: 700;}
		.diff-zero {color: #C7D0D5; font-weight: 700;}
		</style>
		"""
	return """
	<style>
	.block-container {padding-top: 1.5rem; padding-bottom: 1.5rem;}
	[data-testid="stMetricValue"] {font-size: 1.55rem;}
		.stTabs [data-baseweb="tab-list"] {gap: 0.5rem;}
		.stTabs [data-baseweb="tab"] p {font-size: 1.06rem; font-weight: 650;}
	section[data-testid="stSidebar"] [data-baseweb="tag"] {
		background-color: #ECEFF1;
		border: 1px solid #CFD8DC;
		color: #263238;
	}
	section[data-testid="stSidebar"] [data-baseweb="tag"] span {
		color: #263238;
	}
	section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
		border-color: #D5DBDF;
	}
	.standings-table-wrap {
		border: 1px solid #DDE4E8;
		border-radius: 8px;
		overflow: hidden;
		background-color: #FFFFFF;
	}
	.standings-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.9rem;
	}
	.standings-table th {
		background-color: #F4F7F8;
		color: #263238;
		border-bottom: 1px solid #DDE4E8;
		padding: 0.55rem 0.6rem;
		text-align: left;
		white-space: nowrap;
	}
	.standings-table td {
		background-color: #FFFFFF;
		color: #263238;
		border-bottom: 1px solid #E9EEF1;
		padding: 0.48rem 0.6rem;
		white-space: nowrap;
	}
	.standings-table tr:nth-child(even) td {
		background-color: #FAFBFC;
	}
	.team-chip {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		font-weight: 700;
	}
	.team-dot {
		display: inline-block;
		width: 0.65rem;
		height: 0.65rem;
		border-radius: 999px;
	}
	.tone-positive {
		background-color: #DDF1E2 !important;
		color: #2E7D32 !important;
		font-weight: 700;
	}
	.tone-negative {
		background-color: #F4DADA !important;
		color: #B85C5C !important;
		font-weight: 700;
	}
	.tone-neutral {
		background-color: #E8EDF0 !important;
		color: #607D8B !important;
		font-weight: 700;
	}
	.recent-table-wrap {
		border: 1px solid #DDE4E8;
		border-radius: 8px;
		overflow: hidden;
		background-color: #FFFFFF;
	}
	.recent-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.92rem;
	}
	.recent-table th {
		background-color: #F4F7F8;
		color: #263238;
		border-bottom: 1px solid #DDE4E8;
		padding: 0.65rem 0.7rem;
		text-align: left;
		white-space: nowrap;
	}
	.recent-table td {
		background-color: #FFFFFF;
		color: #263238;
		border-bottom: 1px solid #E9EEF1;
		padding: 0.6rem 0.7rem;
		white-space: nowrap;
	}
	.recent-table tr:nth-child(even) td {
		background-color: #FAFBFC;
	}
	.result-badge {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 2rem;
		padding: 0.15rem 0.45rem;
		border-radius: 999px;
		font-weight: 700;
		color: #FFFFFF;
	}
	.result-W {background-color: #3D7A5F;}
	.result-L {background-color: #B85C5C;}
	.result-D {background-color: #7A7F87;}
	.diff-plus {color: #2E7D32; font-weight: 700;}
	.diff-minus {color: #B85C5C; font-weight: 700;}
	.diff-zero {color: #6D7A80; font-weight: 700;}
	</style>
	"""


def month_label(value: Any) -> str:
	if pd.isna(value):
		return ""
	try:
		return f"{int(float(value)):02d}"
	except (TypeError, ValueError):
		text = str(value).strip()
		return text.zfill(2) if text.isdigit() else text


def year_label(value: Any) -> str:
	if pd.isna(value):
		return ""
	try:
		return str(int(float(value)))
	except (TypeError, ValueError):
		return str(value).strip()


def ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
	for column in columns:
		if column not in frame.columns:
			frame[column] = pd.NA
	return frame


def to_numeric(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
	for column in columns:
		if column in frame.columns:
			frame[column] = pd.to_numeric(frame[column], errors="coerce")
	return frame


def prepare_schedule(frame: pd.DataFrame) -> pd.DataFrame:
	frame = frame.copy()
	frame = ensure_columns(
		frame,
		[
			"game_id",
			"season_year",
			"source_month",
			"game_date",
			"game_start_time",
			"weekday_ko",
			"weekday_en",
			"game_duration_min",
			"crowd",
			"away_team",
			"away_score",
			"home_score",
			"home_team",
			"game_status",
			"stadium",
			"broadcast",
			"note",
		],
	)
	frame = to_numeric(frame, ["season_year", "game_duration_min", "crowd", "away_score", "home_score"])
	frame["game_date"] = pd.to_datetime(frame["game_date"], errors="coerce")
	frame["season_year_label"] = frame["season_year"].map(year_label)
	frame["source_month_label"] = frame["source_month"].map(month_label)
	frame["game_status"] = frame["game_status"].fillna("unknown").astype(str)
	frame["game_status_label"] = frame["game_status"].map(STATUS_LABELS).fillna(frame["game_status"])
	frame["total_runs"] = frame["away_score"] + frame["home_score"]
	frame["matchup"] = frame["away_team"].fillna("").astype(str) + " @ " + frame["home_team"].fillna("").astype(str)
	return frame


def read_team_workbook(path: Path) -> pd.DataFrame:
	book = pd.ExcelFile(path)
	if "Total" in book.sheet_names:
		return pd.read_excel(path, sheet_name="Total")
	frames = [pd.read_excel(path, sheet_name=sheet_name) for sheet_name in book.sheet_names]
	return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def prepare_team(frame: pd.DataFrame) -> pd.DataFrame:
	frame = frame.copy()
	frame = ensure_columns(
		frame,
		[
			"game_id",
			"season_year",
			"source_month",
			"game_date",
			"weekday_ko",
			"weekday_en",
			"game_duration_min",
			"crowd",
			"stadium",
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
		],
	)
	frame = to_numeric(
		frame,
		[
			"season_year",
			"game_duration_min",
			"crowd",
			"runs_for",
			"runs_against",
			"run_diff",
			"total_runs",
			"win_flag",
			"loss_flag",
			"draw_flag",
			"cancellation_flag",
			"home_flag",
			"away_flag",
			"one_run_game",
			"shutout_win",
			"shutout_loss",
		],
	)
	frame["game_date"] = pd.to_datetime(frame["game_date"], errors="coerce")
	frame["season_year_label"] = frame["season_year"].map(year_label)
	frame["source_month_label"] = frame["source_month"].map(month_label)
	frame["result"] = frame["result"].fillna("Cancel").astype(str)
	frame["is_final"] = frame["result"].isin(FINAL_RESULTS)
	frame["home_away_label"] = frame["home_away"].map(HOME_AWAY_LABELS).fillna(frame["home_away"])
	frame["weekday_label"] = frame["weekday_en"].map(WEEKDAY_LABELS).fillna(frame["weekday_ko"])
	frame["one_run_loss"] = ((frame["loss_flag"] == 1) & (frame["run_diff"] == -1)).astype(int)
	return frame


@st.cache_data(show_spinner=False)
def load_data(
	schedule_path: str,
	team_path: str,
	schedule_signature: tuple[int, str],
	team_signature: tuple[int, str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
	# Signature args are intentionally part of the Streamlit cache key.
	schedule = prepare_schedule(pd.read_excel(schedule_path))
	team_source = read_team_workbook(Path(team_path))
	lookup_columns = ["game_id"] + [column for column in ("season_year", "stadium") if column in schedule.columns]
	schedule_lookup = schedule[lookup_columns].drop_duplicates("game_id") if "game_id" in schedule.columns else pd.DataFrame()
	for column in ("season_year", "stadium"):
		if column in schedule_lookup.columns and column not in team_source.columns:
			team_source = team_source.merge(schedule_lookup[["game_id", column]], on="game_id", how="left")
	team = prepare_team(team_source)
	return schedule, team


def format_int(value: Any) -> str:
	if pd.isna(value):
		return "-"
	return f"{int(value):,}"


def format_float(value: Any, digits: int = 1) -> str:
	if pd.isna(value):
		return "-"
	return f"{float(value):,.{digits}f}"


def format_pct(value: Any) -> str:
	if pd.isna(value):
		return "-"
	return f"{float(value):.3f}"


def _safe_int(value: Any) -> int | None:
	try:
		if pd.isna(value):
			return None
	except TypeError:
		pass
	try:
		return int(value)
	except (TypeError, ValueError):
		return None


def format_cell(value: Any) -> str:
	if pd.isna(value):
		return ""
	if isinstance(value, pd.Timestamp):
		return value.strftime("%Y-%m-%d")
	if hasattr(value, "strftime") and not isinstance(value, str):
		try:
			return value.strftime("%Y-%m-%d")
		except TypeError:
			pass
	if isinstance(value, float):
		if value.is_integer():
			return f"{int(value):,}"
		return f"{value:,.3f}".rstrip("0").rstrip(".")
	if isinstance(value, int):
		return f"{value:,}"
	return str(value)


def render_table(frame: pd.DataFrame, column_config: dict[str, Any] | None = None) -> None:
	if not ACTIVE_DARK_MODE:
		st.dataframe(
			frame,
			hide_index=True,
			width="stretch",
			column_config=column_config,
		)
		return

	display = frame.copy()
	for column in display.columns:
		display[column] = display[column].map(format_cell)
	html = display.to_html(index=False, escape=True, classes="kbo-table")
	st.markdown(f'<div class="kbo-table-wrap">{html}</div>', unsafe_allow_html=True)


def render_recent_games_table(recent: pd.DataFrame) -> None:
	headers = ["날짜", "상대", "홈/원정", "결과", "스코어", "득실차", "경기시간", "관중"]
	rows = []
	for _, row in recent.iterrows():
		result = str(row.get("result") or "")
		run_diff = row.get("run_diff")
		diff_value = _safe_int(run_diff)
		if diff_value is None or diff_value == 0:
			diff_class = "diff-zero"
		elif diff_value > 0:
			diff_class = "diff-plus"
		else:
			diff_class = "diff-minus"
		score = f"{format_int(row.get('runs_for'))} - {format_int(row.get('runs_against'))}"
		duration = f"{format_int(row.get('game_duration_min'))}분" if not pd.isna(row.get("game_duration_min")) else "-"
		cells = [
			format_cell(row.get("game_date")),
			html.escape(str(row.get("opponent") or "")),
			html.escape(str(row.get("home_away_label") or "")),
			f'<span class="result-badge result-{html.escape(result)}">{html.escape(result)}</span>',
			html.escape(score),
			f'<span class="{diff_class}">{html.escape(format_int(diff_value))}</span>',
			html.escape(duration),
			html.escape(format_int(row.get("crowd"))),
		]
		rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

	header_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
	body_html = "".join(rows)
	st.markdown(
		f'<div class="recent-table-wrap"><table class="recent-table"><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>',
		unsafe_allow_html=True,
	)


def tone_class(value: Any, threshold: float) -> str:
	try:
		if pd.isna(value):
			return "tone-neutral"
	except TypeError:
		pass
	if float(value) > threshold:
		return "tone-positive"
	if float(value) < threshold:
		return "tone-negative"
	return "tone-neutral"


def render_standings_table(standings: pd.DataFrame) -> None:
	headers = ["팀", "경기", "승", "패", "무", "승률", "연속", "득점", "실점", "득실차", "평균 득점", "평균 실점"]
	rows = []
	for _, row in standings.iterrows():
		team = str(row.get("team") or "")
		color = team_color(team)
		win_pct = row.get("win_pct")
		run_diff = row.get("run_diff")
		cells = [
			f'<span class="team-chip" style="color:{html.escape(color)}"><span class="team-dot" style="background-color:{html.escape(color)}"></span>{html.escape(team)}</span>',
			html.escape(format_int(row.get("games"))),
			html.escape(format_int(row.get("wins"))),
			html.escape(format_int(row.get("losses"))),
			html.escape(format_int(row.get("draws"))),
			f'<span>{html.escape(format_pct(win_pct))}</span>',
			html.escape(str(row.get("streak") or "-")),
			html.escape(format_int(row.get("runs_for"))),
			html.escape(format_int(row.get("runs_against"))),
			f'<span>{html.escape(format_int(run_diff))}</span>',
			html.escape(format_float(row.get("avg_runs_for"), 2)),
			html.escape(format_float(row.get("avg_runs_against"), 2)),
		]
		cell_classes = ["", "", "", "", "", tone_class(win_pct, 0.5), "", "", "", tone_class(run_diff, 0), "", ""]
		rows.append(
			"<tr>"
			+ "".join(
				f'<td class="{cell_class}">{cell}</td>' if cell_class else f"<td>{cell}</td>"
				for cell, cell_class in zip(cells, cell_classes)
			)
			+ "</tr>"
		)
	header_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
	body_html = "".join(rows)
	st.markdown(
		f'<div class="standings-table-wrap"><table class="standings-table"><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>',
		unsafe_allow_html=True,
	)


def team_color(team: Any) -> str:
	return active_team_colors().get(str(team), "#8FA3AD" if ACTIVE_DARK_MODE else "#607D8B")


def add_bar_labels(fig: go.Figure, textposition: str = "outside") -> go.Figure:
	fig.update_traces(texttemplate="%{y:,.0f}", textposition=textposition, cliponaxis=False)
	return fig


def add_horizontal_bar_labels(fig: go.Figure) -> go.Figure:
	fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
	return fig


def team_metric_bar(
	frame: pd.DataFrame,
	x: str,
	y: str,
	labels: dict[str, str],
	height: int = 360,
	sort_by: str | None = None,
	texttemplate: str | None = None,
) -> go.Figure:
	plot_frame = frame.copy()
	if sort_by:
		plot_frame = plot_frame.sort_values(sort_by, ascending=False)
	fig = px.bar(
		plot_frame,
		x=x,
		y=y,
		color=x,
		color_discrete_map=active_team_colors(),
		text=y,
		labels=labels,
	)
	fig.update_layout(showlegend=False)
	if texttemplate is None:
		texttemplate = "%{text:,.2f}" if plot_frame[y].dtype.kind == "f" else "%{text:,.0f}"
	fig.update_traces(texttemplate=texttemplate, textposition="outside", cliponaxis=False)
	return apply_layout(fig, height=height)


def paired_team_bar(
	frame: pd.DataFrame,
	team_column: str,
	first_column: str,
	second_column: str,
	first_name: str,
	second_name: str,
	title_y: str,
) -> go.Figure:
	plot_frame = frame.sort_values(first_column, ascending=False).copy()
	teams = plot_frame[team_column].astype(str).tolist()
	colors = [team_color(team) for team in teams]
	fig = go.Figure()
	fig.add_bar(
		x=teams,
		y=plot_frame[first_column],
		name=first_name,
		marker_color=colors,
		text=plot_frame[first_column],
		textposition="outside",
		cliponaxis=False,
	)
	fig.add_bar(
		x=teams,
		y=plot_frame[second_column],
		name=second_name,
		marker_color=colors,
		marker_pattern_shape="/",
		marker_pattern_solidity=0.25,
		text=plot_frame[second_column],
		textposition="outside",
		cliponaxis=False,
	)
	fig.update_traces(texttemplate="%{text:,.0f}")
	fig.update_layout(barmode="group", yaxis_title=title_y, xaxis_title="팀")
	return apply_layout(fig)


def result_count_bar(counts: pd.DataFrame, category_column: str, x_title: str) -> go.Figure:
	plot_frame = counts.copy()
	categories = plot_frame[category_column].astype(str).tolist()
	wins = plot_frame["W"] if "W" in plot_frame.columns else pd.Series(0, index=plot_frame.index)
	losses = plot_frame["L"] if "L" in plot_frame.columns else pd.Series(0, index=plot_frame.index)
	draws = plot_frame["D"] if "D" in plot_frame.columns else pd.Series(0, index=plot_frame.index)
	totals = wins + losses + draws
	decision_games = wins + losses
	win_pct_labels = [
		f"{win / decision:.3f}" if decision else ""
		for win, decision in zip(wins, decision_games)
	]
	fig = go.Figure()
	for result in RESULT_BAR_ORDER:
		values = plot_frame[result] if result in plot_frame.columns else pd.Series(0, index=plot_frame.index)
		fig.add_bar(
			x=categories,
			y=values,
			name=result,
			legendrank=RESULT_LEGEND_ORDER.index(result) if result in RESULT_LEGEND_ORDER else 99,
			marker_color=RESULT_COLORS[result],
			text=[format_int(value) if value else "" for value in values],
			textposition="inside",
			insidetextanchor="middle",
			cliponaxis=False,
		)
	fig.update_traces(texttemplate="%{text}", textfont_color="#F8FAFB" if ACTIVE_DARK_MODE else "#FFFFFF")
	fig.add_trace(
		go.Scatter(
			x=categories,
			y=totals,
			mode="text",
			text=win_pct_labels,
			textposition="top center",
			textfont=dict(color="#DCE5E9" if ACTIVE_DARK_MODE else "#37474F", size=12),
			hoverinfo="skip",
			showlegend=False,
		)
	)
	if not totals.empty and totals.max() > 0:
		fig.update_yaxes(range=[0, max(1, totals.max() * 1.22)])
	fig.update_layout(
		barmode="stack",
		legend_traceorder="normal",
		xaxis_title=x_title,
		yaxis_title="경기",
		uniformtext_minsize=11,
		uniformtext_mode="hide",
	)
	return apply_layout(fig)


def build_result_counts(frame: pd.DataFrame, category_column: str, categories: list[str] | None = None) -> pd.DataFrame:
	counts = (
		frame.groupby([category_column, "result"])
		.size()
		.unstack(fill_value=0)
		.reset_index()
	)
	for result in RESULT_LEGEND_ORDER:
		if result not in counts.columns:
			counts[result] = 0
	if categories is not None:
		counts[category_column] = pd.Categorical(counts[category_column], categories=categories, ordered=True)
		counts = counts.sort_values(category_column)
	return counts[[category_column, *RESULT_LEGEND_ORDER]]


def order_by_reference(values: list[str], reference: list[str]) -> list[str]:
	value_set = set(values)
	ordered = [value for value in reference if value in value_set]
	ordered.extend(value for value in sorted(value_set) if value not in ordered)
	return ordered


def format_heatmap_value(value: Any, metric: str) -> str:
	if pd.isna(value):
		return ""
	if metric == "승률":
		return f"{float(value):.3f}"
	if metric in {"득실차", "경기 수"}:
		return f"{int(value):,}"
	return f"{float(value):.1f}"


def classified_heatmap(value_frame: pd.DataFrame, metric: str, threshold: float, height: int) -> go.Figure:
	colors = HEATMAP_CLASS_COLORS["dark" if ACTIVE_DARK_MODE else "light"]
	class_frame = pd.DataFrame(0.0, index=value_frame.index, columns=value_frame.columns)
	class_frame[value_frame > threshold] = 1
	class_frame[value_frame < threshold] = -1
	class_frame[value_frame.isna()] = float("nan")
	text_frame = value_frame.apply(lambda column: column.map(lambda value: format_heatmap_value(value, metric)))
	colorscale = [
		[0.0, colors["negative"]],
		[0.499, colors["negative"]],
		[0.5, colors["neutral"]],
		[0.501, colors["positive"]],
		[1.0, colors["positive"]],
	]
	fig = go.Figure(
		data=go.Heatmap(
			z=class_frame,
			x=value_frame.columns,
			y=value_frame.index,
			text=text_frame,
			customdata=text_frame,
			texttemplate="%{text}",
			hovertemplate="<b>%{y} vs %{x}</b><br>" + metric + ": %{customdata}<extra></extra>",
			colorscale=colorscale,
			zmin=-1,
			zmax=1,
			showscale=False,
			xgap=1,
			ygap=1,
		)
	)
	fig.update_traces(textfont_color="#F8FAFB" if ACTIVE_DARK_MODE else "#263238")
	fig = apply_layout(fig, height=height)
	fig.update_xaxes(title_text="")
	fig.update_yaxes(title_text="", autorange="reversed")
	return fig


def build_streaks(team_frame: pd.DataFrame) -> pd.DataFrame:
	decision_frame = team_frame[team_frame["result"].isin({"W", "L"})].copy()
	if decision_frame.empty:
		return pd.DataFrame(columns=["team", "streak"])

	latest_year = decision_frame["season_year"].max()
	latest_year_frame = decision_frame[decision_frame["season_year"] == latest_year]
	latest_month = latest_year_frame["source_month"].max()
	latest_frame = latest_year_frame[latest_year_frame["source_month"] == latest_month].copy()
	sort_columns = [column for column in ["team", "game_date", "game_id"] if column in latest_frame.columns]
	latest_frame = latest_frame.sort_values(sort_columns, ascending=[True, False, False][: len(sort_columns)])

	streaks = []
	for team, group in latest_frame.groupby("team", dropna=False):
		results = group["result"].astype(str).tolist()
		if not results:
			continue
		latest_result = results[0]
		count = 0
		for result in results:
			if result != latest_result:
				break
			count += 1
		label = f"{count}연승" if latest_result == "W" else f"{count}연패"
		streaks.append({"team": team, "streak": label})
	return pd.DataFrame(streaks)


def build_standings(team_frame: pd.DataFrame) -> pd.DataFrame:
	final_frame = team_frame[team_frame["is_final"]].copy()
	if final_frame.empty:
		return pd.DataFrame()

	standings = (
		final_frame.groupby("team", dropna=False)
		.agg(
			games=("game_id", "count"),
			wins=("win_flag", "sum"),
			losses=("loss_flag", "sum"),
			draws=("draw_flag", "sum"),
			runs_for=("runs_for", "sum"),
			runs_against=("runs_against", "sum"),
			run_diff=("run_diff", "sum"),
			avg_runs_for=("runs_for", "mean"),
			avg_runs_against=("runs_against", "mean"),
			one_run_games=("one_run_game", "sum"),
			one_run_losses=("one_run_loss", "sum"),
			shutout_wins=("shutout_win", "sum"),
			shutout_losses=("shutout_loss", "sum"),
			avg_duration=("game_duration_min", "mean"),
			avg_crowd=("crowd", "mean"),
		)
		.reset_index()
	)
	decision_games = standings["wins"] + standings["losses"]
	standings["win_pct"] = standings["wins"].div(decision_games.where(decision_games > 0))
	streaks = build_streaks(final_frame)
	if not streaks.empty:
		standings = standings.merge(streaks, on="team", how="left")
	else:
		standings["streak"] = pd.NA
	return standings.sort_values(["win_pct", "wins", "run_diff"], ascending=[False, False, False])


def display_standings_table(standings: pd.DataFrame) -> None:
	if standings.empty:
		st.info("선택한 조건에 완료 경기 데이터가 없습니다.")
		return
	render_standings_table(standings)


def plot_empty(message: str) -> None:
	st.info(message)


def apply_layout(fig: go.Figure, height: int = 360) -> go.Figure:
	if ACTIVE_DARK_MODE:
		paper_color = "#11181C"
		plot_color = "#151E23"
		font_color = "#E6ECEF"
		grid_color = "#2A3A42"
	else:
		paper_color = "#FFFFFF"
		plot_color = "#FFFFFF"
		font_color = "#263238"
		grid_color = "#E6ECEF"
	fig.update_layout(
		template=ACTIVE_PLOT_TEMPLATE,
		height=height,
		margin=dict(l=10, r=10, t=42, b=10),
		legend_title_text="",
		legend=dict(font=dict(color=font_color, size=13), bgcolor="rgba(0,0,0,0)"),
		paper_bgcolor=paper_color,
		plot_bgcolor=plot_color,
		font_color=font_color,
	)
	fig.update_xaxes(gridcolor=grid_color, zerolinecolor=grid_color)
	fig.update_yaxes(gridcolor=grid_color, zerolinecolor=grid_color)
	return fig


def filter_data(schedule: pd.DataFrame, team: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
	schedule = schedule[schedule["game_status"] == "final"].copy()
	team = team[team["is_final"]].copy()
	year_options = sorted(schedule["season_year_label"].dropna().unique().tolist())
	default_years = ["2026"] if "2026" in year_options else year_options[-1:]
	month_options = sorted(schedule["source_month_label"].dropna().unique().tolist())
	team_options = sorted(team["team"].dropna().astype(str).unique().tolist())

	with st.sidebar:
		st.header("필터")
		selected_years = st.multiselect("연도", year_options, default=default_years)
		selected_months = st.multiselect("월", month_options, default=month_options)
		selected_teams = st.multiselect("팀", team_options, default=team_options)
		selected_home_away = st.multiselect("홈/원정", HOME_AWAY_ORDER, default=HOME_AWAY_ORDER)

	schedule_mask = schedule["season_year_label"].isin(selected_years) & schedule["source_month_label"].isin(selected_months)
	if selected_teams:
		schedule_mask &= schedule["away_team"].isin(selected_teams) | schedule["home_team"].isin(selected_teams)

	attendance_schedule_mask = schedule["season_year_label"].isin(selected_years) & schedule["source_month_label"].isin(selected_months)
	if selected_teams:
		attendance_schedule_mask &= schedule["home_team"].isin(selected_teams)

	rank_mask = (
		team["season_year_label"].isin(selected_years)
		& team["source_month_label"].isin(selected_months)
		& team["home_away_label"].isin(selected_home_away)
	)
	rank_standings = build_standings(team[rank_mask].copy())
	rank_order = rank_standings["team"].astype(str).tolist() if not rank_standings.empty else []

	team_mask = rank_mask.copy()
	if selected_teams:
		team_mask &= team["team"].isin(selected_teams)

	attendance_team_mask = (
		team["season_year_label"].isin(selected_years)
		& team["source_month_label"].isin(selected_months)
		& (team["home_away_label"] == "홈")
	)
	if selected_teams:
		attendance_team_mask &= team["team"].isin(selected_teams)

	return (
		schedule[schedule_mask].copy(),
		team[team_mask].copy(),
		schedule[attendance_schedule_mask].copy(),
		team[attendance_team_mask].copy(),
		rank_order,
	)


def render_overview(schedule: pd.DataFrame, team: pd.DataFrame) -> None:
	standings = build_standings(team)

	metric_cols = st.columns(4)
	metric_cols[0].metric("경기 수", format_int(len(schedule)))
	metric_cols[1].metric("총 관중 수", format_int(schedule["crowd"].sum()))
	metric_cols[2].metric("평균 관중", format_int(schedule["crowd"].mean()))
	metric_cols[3].metric("평균 경기 시간", f"{format_float(schedule['game_duration_min'].mean(), 0)}분")

	left, right = st.columns([1.25, 1])
	with left:
		st.subheader("팀 순위")
		display_standings_table(standings)
	with right:
		st.subheader("팀별 승률")
		if standings.empty:
			plot_empty("승률 데이터가 없습니다.")
		else:
			fig = team_metric_bar(
				standings,
				x="team",
				y="win_pct",
				labels={"team": "팀", "win_pct": "승률"},
				sort_by="win_pct",
				texttemplate="%{text:.3f}",
			)
			fig.update_yaxes(range=[0, max(0.75, standings["win_pct"].max() * 1.18)])
			st.plotly_chart(fig, width="stretch")

	left, right = st.columns(2)
	with left:
		st.subheader("1점차 승리 / 패배")
		if standings.empty:
			plot_empty("1점차 경기 데이터가 없습니다.")
		else:
			fig = paired_team_bar(
				standings,
				team_column="team",
				first_column="one_run_games",
				second_column="one_run_losses",
				first_name="1점차 승리",
				second_name="1점차 패배",
				title_y="경기",
			)
			st.plotly_chart(fig, width="stretch")
	with right:
		st.subheader("영봉승 / 무득점패")
		if standings.empty:
			plot_empty("완봉 데이터가 없습니다.")
		else:
			fig = paired_team_bar(
				standings,
				team_column="team",
				first_column="shutout_wins",
				second_column="shutout_losses",
				first_name="영봉승",
				second_name="무득점패",
				title_y="경기",
			)
			st.plotly_chart(fig, width="stretch")


def render_team_detail(team: pd.DataFrame, rank_order: list[str]) -> None:
	teams = order_by_reference(team["team"].dropna().astype(str).unique().tolist(), rank_order)
	if not teams:
		st.info("선택한 조건에 팀 데이터가 없습니다.")
		return
	selected_team = st.selectbox("팀", teams)
	team_frame = team[team["team"] == selected_team].copy()
	final_frame = team_frame[team_frame["is_final"]].copy()

	wins = int(final_frame["win_flag"].sum()) if not final_frame.empty else 0
	losses = int(final_frame["loss_flag"].sum()) if not final_frame.empty else 0
	draws = int(final_frame["draw_flag"].sum()) if not final_frame.empty else 0
	win_pct = wins / (wins + losses) if wins + losses else pd.NA
	run_diff = final_frame["run_diff"].sum() if not final_frame.empty else pd.NA

	metric_cols = st.columns(6)
	metric_cols[0].metric("전적", f"{wins}-{losses}-{draws}")
	metric_cols[1].metric("승률", format_pct(win_pct))
	metric_cols[2].metric("득실차", format_int(run_diff))
	metric_cols[3].metric("평균 득점", format_float(final_frame["runs_for"].mean()))
	metric_cols[4].metric("평균 실점", format_float(final_frame["runs_against"].mean()))
	metric_cols[5].metric("1점차", f"{format_int(final_frame['one_run_game'].sum())}승 / {format_int(final_frame['one_run_loss'].sum())}패")

	left, right = st.columns(2)
	with left:
		st.subheader("월별 성적")
		month_categories = sorted(final_frame["source_month_label"].dropna().astype(str).unique().tolist())
		monthly = build_result_counts(final_frame, "source_month_label", month_categories) if not final_frame.empty else pd.DataFrame()
		if monthly.empty:
			plot_empty("월별 성적 데이터가 없습니다.")
		else:
			st.plotly_chart(result_count_bar(monthly, "source_month_label", "월"), width="stretch")
	with right:
		st.subheader("홈/원정 성적")
		home_away = build_result_counts(final_frame, "home_away_label", HOME_AWAY_ORDER) if not final_frame.empty else pd.DataFrame()
		if home_away.empty:
			plot_empty("홈/원정 데이터가 없습니다.")
		else:
			st.plotly_chart(result_count_bar(home_away, "home_away_label", "구분"), width="stretch")

	left, right = st.columns(2)
	with left:
		st.subheader("경기장별 성적")
		stadium_categories = (
			final_frame.dropna(subset=["stadium"]).groupby("stadium").size().sort_values(ascending=False).index.astype(str).tolist()
			if not final_frame.empty
			else []
		)
		stadium = build_result_counts(final_frame.dropna(subset=["stadium"]), "stadium", stadium_categories) if stadium_categories else pd.DataFrame()
		if stadium.empty:
			plot_empty("경기장별 성적 데이터가 없습니다.")
		else:
			st.plotly_chart(result_count_bar(stadium, "stadium", "경기장"), width="stretch")
	with right:
		st.subheader("요일별 성적")
		weekday = build_result_counts(final_frame.dropna(subset=["weekday_label"]), "weekday_label", WEEKDAY_ORDER) if not final_frame.empty else pd.DataFrame()
		if weekday.empty:
			plot_empty("요일별 성적 데이터가 없습니다.")
		else:
			st.plotly_chart(result_count_bar(weekday, "weekday_label", "요일"), width="stretch")

	st.subheader("최근 10경기")
	recent = final_frame.sort_values(["game_date", "game_id"]).tail(10).copy()
	if recent.empty:
		plot_empty("최근 경기 데이터가 없습니다.")
		return

	recent_wins = int(recent["win_flag"].sum())
	recent_losses = int(recent["loss_flag"].sum())
	recent_draws = int(recent["draw_flag"].sum())
	recent_metric_cols = st.columns(5)
	recent_metric_cols[0].metric("최근 전적", f"{recent_wins}-{recent_losses}-{recent_draws}")
	recent_metric_cols[1].metric("최근 승률", format_pct(recent_wins / (recent_wins + recent_losses) if recent_wins + recent_losses else pd.NA))
	recent_metric_cols[2].metric("평균 득점", format_float(recent["runs_for"].mean()))
	recent_metric_cols[3].metric("평균 실점", format_float(recent["runs_against"].mean()))
	recent_metric_cols[4].metric("득실차", format_int(recent["run_diff"].sum()))

	recent = recent.sort_values(["game_date", "game_id"], ascending=[False, False]).reset_index(drop=True)
	render_recent_games_table(recent)


def render_matchups(team: pd.DataFrame, rank_order: list[str]) -> None:
	final_frame = team[team["is_final"]].copy()
	if final_frame.empty:
		st.info("선택한 조건에 상대전적 데이터가 없습니다.")
		return

	matchups = (
		final_frame.groupby(["team", "opponent"])
		.agg(
			games=("game_id", "count"),
			wins=("win_flag", "sum"),
			losses=("loss_flag", "sum"),
			draws=("draw_flag", "sum"),
			run_diff=("run_diff", "sum"),
			avg_runs_for=("runs_for", "mean"),
			avg_runs_against=("runs_against", "mean"),
		)
		.reset_index()
	)
	matchups["win_pct"] = matchups["wins"].div((matchups["wins"] + matchups["losses"]).where((matchups["wins"] + matchups["losses"]) > 0))

	metric = st.selectbox("지표", ["승률", "득실차", "평균 득점", "경기 수"])
	metric_map = {"승률": "win_pct", "득실차": "run_diff", "평균 득점": "avg_runs_for", "경기 수": "games"}
	pivot = matchups.pivot(index="team", columns="opponent", values=metric_map[metric])
	row_order = [team_name for team_name in rank_order if team_name in pivot.index]
	row_order += [team_name for team_name in pivot.index if team_name not in row_order]
	column_order = [team_name for team_name in rank_order if team_name in pivot.columns]
	column_order += [team_name for team_name in pivot.columns if team_name not in column_order]
	pivot = pivot.reindex(index=row_order, columns=column_order)
	height = max(260, min(520, 150 + len(pivot.index) * 38))
	if metric == "승률":
		fig = classified_heatmap(pivot, metric, 0.5, height)
	elif metric == "득실차":
		fig = classified_heatmap(pivot, metric, 0, height)
	else:
		fig = px.imshow(
			pivot,
			text_auto=".2f" if metric == "평균 득점" else True,
			aspect="auto",
			color_continuous_scale=active_green_scale(),
			labels=dict(x="상대", y="팀", color=metric),
		)
		fig.update_layout(coloraxis_showscale=False)
		fig = apply_layout(fig, height=height)
		fig.update_xaxes(title_text="")
		fig.update_yaxes(title_text="", autorange="reversed")
	st.plotly_chart(fig, width="stretch")


def render_attendance(schedule: pd.DataFrame, home_team_source: pd.DataFrame, duration_team: pd.DataFrame) -> None:
	final_schedule = schedule[schedule["game_status"] == "final"].dropna(subset=["crowd"]).copy()
	home_team = home_team_source[(home_team_source["is_final"]) & (home_team_source["home_away"] == "home")].dropna(subset=["crowd"]).copy()

	metric_cols = st.columns(4)
	metric_cols[0].metric("총 관중", format_int(final_schedule["crowd"].sum()))
	metric_cols[1].metric("평균 관중", format_int(final_schedule["crowd"].mean()))
	metric_cols[2].metric("평균 경기시간", f"{format_float(final_schedule['game_duration_min'].mean(), 0)}분")
	metric_cols[3].metric("관중 집계 경기", format_int(len(final_schedule)))

	left, right = st.columns(2)
	with left:
		st.subheader("구장별 평균 관중")
		stadium = final_schedule.groupby("stadium").agg(games=("game_id", "count"), avg_crowd=("crowd", "mean")).reset_index()
		if stadium.empty:
			plot_empty("구장별 관중 데이터가 없습니다.")
		else:
			fig = px.bar(
				stadium.sort_values("avg_crowd", ascending=False),
				x="stadium",
				y="avg_crowd",
				color="avg_crowd",
				color_continuous_scale=active_soft_green_scale(),
				text="avg_crowd",
				labels={"stadium": "구장", "avg_crowd": "평균 관중"},
			)
			fig.update_layout(coloraxis_showscale=False)
			fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
			st.plotly_chart(apply_layout(fig), width="stretch")
	with right:
		st.subheader("홈팀별 평균 관중")
		home_crowd = home_team.groupby("team").agg(games=("game_id", "count"), avg_crowd=("crowd", "mean")).reset_index()
		if home_crowd.empty:
			plot_empty("홈팀 관중 데이터가 없습니다.")
		else:
			fig = px.bar(
				home_crowd.sort_values("avg_crowd", ascending=False),
				x="team",
				y="avg_crowd",
				color="team",
				color_discrete_map=active_team_colors(),
				text="avg_crowd",
				labels={"team": "팀", "avg_crowd": "평균 관중", "games": "경기"},
			)
			fig.update_layout(showlegend=False)
			fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
			st.plotly_chart(apply_layout(fig), width="stretch")

	left, right = st.columns(2)
	with left:
		st.subheader("요일별 홈 관중")
		weekday_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
		weekday = home_team.groupby("weekday_en").agg(games=("game_id", "count"), avg_crowd=("crowd", "mean")).reset_index()
		if weekday.empty:
			plot_empty("요일별 관중 데이터가 없습니다.")
		else:
			weekday["weekday_en"] = pd.Categorical(weekday["weekday_en"], categories=weekday_order, ordered=True)
			weekday = weekday.sort_values("weekday_en")
			weekday["weekday_label"] = weekday["weekday_en"].map(WEEKDAY_LABELS)
			fig = px.line(
				weekday,
				x="weekday_label",
				y="avg_crowd",
				markers=True,
				color_discrete_sequence=["#00695C"],
				labels={"weekday_label": "요일", "avg_crowd": "평균 관중"},
			)
			st.plotly_chart(apply_layout(fig), width="stretch")
	with right:
		st.subheader("팀별 평균 경기시간")
		team_duration = (
			duration_team[duration_team["is_final"]]
			.dropna(subset=["game_duration_min"])
			.groupby("team")
			.agg(games=("game_id", "count"), avg_duration=("game_duration_min", "mean"))
			.reset_index()
			.sort_values("avg_duration", ascending=False)
		)
		if team_duration.empty:
			plot_empty("팀별 경기시간 데이터가 없습니다.")
		else:
			fig = px.bar(
				team_duration,
				x="team",
				y="avg_duration",
				color="team",
				color_discrete_map=active_team_colors(),
				text="avg_duration",
				labels={"team": "팀", "avg_duration": "평균 경기시간(분)", "games": "경기"},
			)
			fig.update_layout(showlegend=False)
			fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
			st.plotly_chart(apply_layout(fig), width="stretch")


def render_games(schedule: pd.DataFrame) -> None:
	final_schedule = schedule[schedule["game_status"] == "final"].copy()
	left, right = st.columns(2)
	with left:
		st.subheader("관중 상위 경기")
		top_crowd = final_schedule.sort_values("crowd", ascending=False).head(15)
		render_table(
			top_crowd[["game_date", "matchup", "stadium", "crowd", "total_runs", "game_duration_min"]],
			column_config={
				"game_date": st.column_config.DateColumn("날짜"),
				"matchup": "경기",
				"stadium": "구장",
				"crowd": st.column_config.NumberColumn("관중", format="%d"),
				"total_runs": st.column_config.NumberColumn("총 득점", format="%.0f"),
				"game_duration_min": st.column_config.NumberColumn("시간(분)", format="%.0f"),
			},
		)
	with right:
		st.subheader("고득점 경기")
		high_scoring = final_schedule.sort_values("total_runs", ascending=False).head(15)
		render_table(
			high_scoring[["game_date", "matchup", "away_score", "home_score", "total_runs", "stadium"]],
			column_config={
				"game_date": st.column_config.DateColumn("날짜"),
				"matchup": "경기",
				"away_score": st.column_config.NumberColumn("원정 득점", format="%.0f"),
				"home_score": st.column_config.NumberColumn("홈 득점", format="%.0f"),
				"total_runs": st.column_config.NumberColumn("총 득점", format="%.0f"),
				"stadium": "구장",
			},
		)

	st.subheader("경기 목록")
	table = schedule.sort_values(["season_year", "game_date", "game_start_time", "game_id"])[
		[
			"season_year_label",
			"game_id",
			"source_month_label",
			"game_date",
			"weekday_en",
			"game_start_time",
			"matchup",
			"away_score",
			"home_score",
			"game_status_label",
			"stadium",
			"crowd",
			"game_duration_min",
			"broadcast",
			"note",
		]
	].rename(
		columns={
			"season_year_label": "연도",
			"game_id": "game_id",
			"source_month_label": "월",
			"game_date": "날짜",
			"weekday_en": "요일",
			"game_start_time": "시작",
			"matchup": "경기",
			"away_score": "원정",
			"home_score": "홈",
			"game_status_label": "상태",
			"stadium": "구장",
			"crowd": "관중",
			"game_duration_min": "시간(분)",
			"broadcast": "중계",
			"note": "비고",
		}
	)
	render_table(table)


def main() -> None:
	st.set_page_config(page_title="KBO Dashboard by Como", layout="wide")
	with st.sidebar:
		dark_mode = st.toggle("다크모드", value=False)
	set_visual_mode(dark_mode)
	st.markdown(theme_css(dark_mode), unsafe_allow_html=True)
	st.title("KBO Dashboard by Como")

	if not SCHEDULE_PATH.exists() or not TEAM_PATH.exists():
		st.error("data/output 폴더에 필요한 엑셀 파일이 없습니다.")
		return

	schedule_signature = file_signature(SCHEDULE_PATH)
	team_signature = file_signature(TEAM_PATH)
	schedule, team = load_data(str(SCHEDULE_PATH), str(TEAM_PATH), schedule_signature, team_signature)
	filtered_schedule, filtered_team, attendance_schedule, attendance_team, rank_order = filter_data(schedule, team)

	if filtered_schedule.empty and filtered_team.empty:
		st.warning("선택한 조건에 데이터가 없습니다.")
		return

	st.caption(
		f"종료 경기 기준 · Schedule {len(filtered_schedule):,} games · Team rows {len(filtered_team):,} · "
		f"{SCHEDULE_PATH.name} / {TEAM_PATH.name}"
	)

	overview_tab, team_tab, matchup_tab, attendance_tab, games_tab = st.tabs(
		["요약", "팀", "상대전적", "관중/구장", "경기"]
	)

	with overview_tab:
		render_overview(filtered_schedule, filtered_team)
	with team_tab:
		render_team_detail(filtered_team, rank_order)
	with matchup_tab:
		render_matchups(filtered_team, rank_order)
	with attendance_tab:
		render_attendance(attendance_schedule, attendance_team, filtered_team)
	with games_tab:
		render_games(filtered_schedule)


if __name__ == "__main__":
	main()
