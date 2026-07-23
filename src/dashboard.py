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
KBO_SEASON_GAMES = 144
POSTSEASON_TARGETS = {
	1: ("한국시리즈 직행", "korean-series"),
	2: ("플레이오프 직행", "playoff"),
	3: ("준플레이오프 직행", "semi-playoff"),
	4: ("와일드카드결정전", "wild-card"),
	5: ("와일드카드결정전", "wild-card"),
}
RANK_TARGETS = tuple(range(1, 10))
RESULT_COLORS = {
	"W": "#3D7A5F",
	"L": "#B85C5C",
	"D": "#7A7F87",
	"Cancel": "#A97846",
}
TEAM_COLORS = {
	"KIA": "#EA0029",
	"KT": "#000000",
	"LG": "#C30452",
	"NC": "#315288",
	"SK": "#CE0E2D",
	"SSG": "#CE0E2D",
	"넥센": "#570514",
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
DEFAULT_DARK_MODE = True
DARK_GREEN_SCALE = ["#18261C", "#21402A", "#2D5C38", "#3F7E49", "#63A869", "#A6D7A8"]
DARK_SOFT_GREEN_SCALE = ["#1B2420", "#25352C", "#35513E", "#4B7258", "#76A684"]
DARK_PLOT_TEMPLATE = "plotly_dark"


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


def hex_to_rgba(color: str, alpha: float) -> str:
	red, green, blue = hex_to_rgb(color)
	return f"rgba({red}, {green}, {blue}, {alpha})"


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
	ACTIVE_GREEN_SCALE = DARK_GREEN_SCALE if dark_mode else GREEN_SCALE
	ACTIVE_SOFT_GREEN_SCALE = DARK_SOFT_GREEN_SCALE if dark_mode else SOFT_GREEN_SCALE
	ACTIVE_PLOT_TEMPLATE = DARK_PLOT_TEMPLATE if dark_mode else PLOT_TEMPLATE


set_visual_mode(DEFAULT_DARK_MODE)


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
		[data-testid="stMetricLabel"] {color: #B6C4CB; font-size: 0.875rem;}
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
			overflow-x: auto;
			background-color: #111A1F;
		}
		.standings-table {
			width: 100%;
			min-width: 900px;
			border-collapse: collapse;
			font-size: 0.8rem;
			table-layout: fixed;
		}
		.standings-table th {
			background-color: #1A252B;
			color: #EAF0F3;
			border-bottom: 1px solid #344650;
			padding: 0.42rem 0.32rem;
			text-align: left;
			white-space: nowrap;
		}
		.standings-table td {
			background-color: #111A1F;
			color: #DCE5E9;
			border-bottom: 1px solid #24333B;
			padding: 0.36rem 0.32rem;
			white-space: nowrap;
			overflow: hidden;
			text-overflow: ellipsis;
		}
		.standings-table tr:nth-child(even) td {
			background-color: #152027;
		}
		.standings-table .col-team {width: 5.8rem;}
		.standings-table .col-compact {width: 2.65rem; text-align: right;}
		.standings-table .col-win-pct {width: 3.55rem; text-align: right;}
		.standings-table .col-games-behind {width: 3.45rem; text-align: right;}
		.standings-table .col-streak {width: 3.55rem;}
		.standings-table .col-score {width: 3.25rem; text-align: right;}
		.standings-table .col-run-diff {width: 3.65rem; text-align: right;}
		.standings-table .col-average {width: 4.15rem; text-align: right;}
		.standings-table .col-recent-form {width: 5.5rem;}
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
			overflow-x: auto;
			background-color: #111A1F;
		}
		.recent-table {
			width: 100%;
			min-width: 960px;
			border-collapse: collapse;
			font-size: 0.86rem;
		}
		.recent-table th {
			background-color: #1A252B;
			color: #EAF0F3;
			border-bottom: 1px solid #344650;
			padding: 0.5rem 0.55rem;
			text-align: left;
			white-space: nowrap;
		}
		.recent-table td {
			background-color: #111A1F;
			color: #DCE5E9;
			border-bottom: 1px solid #24333B;
			padding: 0.48rem 0.55rem;
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
		.form-result {
			display: inline-flex;
			align-items: center;
			justify-content: center;
			min-width: 1.02rem;
			margin-right: 0.06rem;
			font-weight: 800;
		}
		.form-W {color: #9FD5AA;}
		.form-L {color: #E3A0A0;}
		.form-D {color: #C7D0D5;}
		.league-leader-card {
			padding-top: 0.1rem;
		}
		.league-leader-label {
			color: #B6C4CB;
			font-size: 0.875rem;
			font-weight: 400;
			line-height: 1.25;
			margin-bottom: 0.16rem;
		}
		.league-leader-value {
			display: inline-flex;
			align-items: center;
			gap: 0.42rem;
			color: #F4F7F8;
			font-size: 1.55rem;
			font-weight: 700;
			line-height: 1.2;
		}
		.league-leader-pct {
			color: #B6C4CB;
			font-size: 1rem;
			font-weight: 650;
		}
		.diff-plus {color: #9FD5AA; font-weight: 700;}
		.diff-minus {color: #E3A0A0; font-weight: 700;}
		.diff-zero {color: #C7D0D5; font-weight: 700;}
		</style>
		"""
	return """
	<style>
	.stApp {background-color: #FFFFFF; color: #263238;}
	header[data-testid="stHeader"] {background-color: #FFFFFF;}
	[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
		background-color: #FFFFFF;
		color: #263238;
	}
	h1, h2, h3, h4, h5, h6, p, label, span, div {
		color: #263238;
	}
	section[data-testid="stSidebar"] {background-color: #F5F7F8;}
	.block-container {padding-top: 1.5rem; padding-bottom: 1.5rem;}
	[data-testid="stMetricValue"] {font-size: 1.55rem;}
	[data-testid="stMetricLabel"] {color: #6D7A80; font-size: 0.875rem;}
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
		overflow-x: auto;
		background-color: #FFFFFF;
	}
		.standings-table {
			width: 100%;
			min-width: 900px;
			border-collapse: collapse;
			font-size: 0.8rem;
			table-layout: fixed;
		}
		.standings-table th {
			background-color: #F4F7F8;
			color: #263238;
			border-bottom: 1px solid #DDE4E8;
			padding: 0.42rem 0.32rem;
			text-align: left;
			white-space: nowrap;
		}
		.standings-table td {
			background-color: #FFFFFF;
			color: #263238;
			border-bottom: 1px solid #E9EEF1;
			padding: 0.36rem 0.32rem;
			white-space: nowrap;
			overflow: hidden;
			text-overflow: ellipsis;
		}
		.standings-table tr:nth-child(even) td {
			background-color: #FAFBFC;
		}
		.standings-table .col-team {width: 5.8rem;}
		.standings-table .col-compact {width: 2.65rem; text-align: right;}
		.standings-table .col-win-pct {width: 3.55rem; text-align: right;}
		.standings-table .col-games-behind {width: 3.45rem; text-align: right;}
		.standings-table .col-streak {width: 3.55rem;}
		.standings-table .col-score {width: 3.25rem; text-align: right;}
		.standings-table .col-run-diff {width: 3.65rem; text-align: right;}
		.standings-table .col-average {width: 4.15rem; text-align: right;}
		.standings-table .col-recent-form {width: 5.5rem;}
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
		overflow-x: auto;
		background-color: #FFFFFF;
	}
	.recent-table {
		width: 100%;
		min-width: 960px;
		border-collapse: collapse;
		font-size: 0.86rem;
	}
	.recent-table th {
		background-color: #F4F7F8;
		color: #263238;
		border-bottom: 1px solid #DDE4E8;
		padding: 0.5rem 0.55rem;
		text-align: left;
		white-space: nowrap;
	}
	.recent-table td {
		background-color: #FFFFFF;
		color: #263238;
		border-bottom: 1px solid #E9EEF1;
		padding: 0.48rem 0.55rem;
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
	.form-result {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 1.02rem;
		margin-right: 0.06rem;
		font-weight: 800;
	}
	.form-W {color: #2E7D32;}
	.form-L {color: #B85C5C;}
	.form-D {color: #6D7A80;}
	.league-leader-card {
		padding-top: 0.1rem;
	}
	.league-leader-label {
		color: #6D7A80;
		font-size: 0.875rem;
		font-weight: 400;
		line-height: 1.25;
		margin-bottom: 0.16rem;
	}
	.league-leader-value {
		display: inline-flex;
		align-items: center;
		gap: 0.42rem;
		color: #263238;
		font-size: 1.55rem;
		font-weight: 700;
		line-height: 1.2;
	}
	.league-leader-pct {
		color: #607D8B;
		font-size: 1rem;
		font-weight: 650;
	}
	.diff-plus {color: #2E7D32; font-weight: 700;}
	.diff-minus {color: #B85C5C; font-weight: 700;}
	.diff-zero {color: #6D7A80; font-weight: 700;}
	</style>
	"""


def team_pill_color_rules(container_selector: str, team_options: list[str]) -> str:
	team_rules = []
	for index, team in enumerate(team_options, start=1):
		color = active_team_colors().get(team, "#8FA3AD" if ACTIVE_DARK_MODE else "#607D8B")
		faded = hex_to_rgba(color, 0.46 if ACTIVE_DARK_MODE else 0.5)
		team_rules.append(
			f"""
	{container_selector} [role] > button[data-testid="stBaseButton-pills"]:nth-of-type({index}) {{
		background-color: {hex_to_rgba(color, 0.04)} !important;
		border-color: {hex_to_rgba(color, 0.22)} !important;
		color: {faded} !important;
	}}
	{container_selector} [role] > button[data-testid="stBaseButton-pillsActive"]:nth-of-type({index}) {{
		background-color: {hex_to_rgba(color, 0.2 if ACTIVE_DARK_MODE else 0.12)} !important;
		border-color: {hex_to_rgba(color, 0.86)} !important;
		box-shadow: inset 0 0 0 1px {hex_to_rgba(color, 0.38)} !important;
		color: {color} !important;
	}}
	{container_selector} [role] > button[data-testid="stBaseButton-pills"]:nth-of-type({index}) p,
	{container_selector} [role] > button[data-testid="stBaseButton-pills"]:nth-of-type({index}) span {{
		color: {faded} !important;
		font-weight: 650;
	}}
	{container_selector} [role] > button[data-testid="stBaseButton-pillsActive"]:nth-of-type({index}) p,
	{container_selector} [role] > button[data-testid="stBaseButton-pillsActive"]:nth-of-type({index}) span {{
		color: {color} !important;
		font-weight: 760;
	}}
"""
		)
	return "".join(team_rules)


def sidebar_filter_css(team_options: list[str]) -> str:
	return (
		"""
	<style>
	section[data-testid="stSidebar"] .stButtonGroup div[role="group"],
	section[data-testid="stSidebar"] .stButtonGroup div[role="radiogroup"] {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		justify-content: flex-start !important;
	}
	section[data-testid="stSidebar"] [data-testid^="stBaseButton-pills"] {
		min-height: 2.08rem;
		border-radius: 999px;
		flex-grow: 0 !important;
		flex-shrink: 0 !important;
		justify-content: center;
		line-height: 1.15;
		padding: 0.2rem 0.56rem;
	}
	section[data-testid="stSidebar"] [data-testid^="stBaseButton-pills"] p {
		line-height: 1.15;
		text-align: center;
		width: 100%;
	}
	section[data-testid="stSidebar"] .st-key-filter_years [data-testid^="stBaseButton-pills"] {
		flex-basis: 4rem !important;
		max-width: 4rem !important;
		min-width: 4rem !important;
		width: 4rem !important;
	}
	section[data-testid="stSidebar"] .st-key-filter_months [data-testid^="stBaseButton-pills"] {
		flex-basis: 3rem !important;
		max-width: 3rem !important;
		min-width: 3rem !important;
		width: 3rem !important;
	}
	section[data-testid="stSidebar"] .st-key-filter_teams [data-testid^="stBaseButton-pills"] {
		flex-basis: 4rem !important;
		max-width: 4rem !important;
		min-width: 4rem !important;
		width: 4rem !important;
	}
	section[data-testid="stSidebar"] .st-key-filter_home_away [data-testid^="stBaseButton-pills"] {
		flex-basis: 4rem !important;
		max-width: 4rem !important;
		min-width: 4rem !important;
		width: 4rem !important;
	}
"""
		+ team_pill_color_rules('section[data-testid="stSidebar"] .st-key-filter_teams', team_options)
		+ "\n\t</style>"
	)


def magic_number_css() -> str:
	if ACTIVE_DARK_MODE:
		colors = {
			"surface": "#11181C",
			"surface_alt": "#151F24",
			"border": "#2E3D45",
			"muted": "#9FB0B9",
			"text": "#E8EEF1",
			"magic_bg": "rgba(77, 166, 104, 0.14)",
			"magic": "#80C991",
			"tragic_bg": "rgba(184, 92, 92, 0.14)",
			"tragic": "#E09898",
			"secured_bg": "#274A72",
			"secured": "#C6DCF5",
			"unavailable_bg": "#5B282B",
			"unavailable": "#F0C2C4",
		}
	else:
		colors = {
			"surface": "#FFFFFF",
			"surface_alt": "#F7F9FA",
			"border": "#D9E0E4",
			"muted": "#65747C",
			"text": "#263238",
			"magic_bg": "#EAF5ED",
			"magic": "#2E7D47",
			"tragic_bg": "#F8EAEA",
			"tragic": "#A84444",
			"secured_bg": "#D8E8F8",
			"secured": "#245B91",
			"unavailable_bg": "#E7C2C4",
			"unavailable": "#842F34",
		}
	return f"""
	<style>
	.magic-number-note {{
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.55rem;
		margin: 0.2rem 0 0.8rem;
		color: {colors['muted']};
		font-size: 0.8rem;
	}}
	.magic-number-note > span {{flex: 0 0 auto; white-space: nowrap;}}
	.magic-number-note .legend-mark {{font-weight: 800;}}
	.magic-number-note .legend-magic {{color: {colors['magic']};}}
	.magic-number-note .legend-tragic {{color: {colors['tragic']};}}
	.magic-number-note .legend-secured {{color: {colors['secured']};}}
	.magic-number-note .legend-unavailable {{color: {colors['unavailable']};}}
	.magic-table-wrap {{
		width: 100%;
		overflow-x: auto;
		border: 1px solid {colors['border']};
		border-radius: 6px;
		background: {colors['surface']};
	}}
	.magic-table {{
		width: 100%;
		min-width: 1120px;
		border-collapse: collapse;
		table-layout: fixed;
		font-size: 0.82rem;
	}}
	.magic-table th {{
		padding: 0.68rem 0.24rem 0.58rem;
		border-bottom: 1px solid {colors['border']};
		background: {colors['surface_alt']};
		color: {colors['text']};
		text-align: center;
		vertical-align: bottom;
	}}
	.magic-table th .target-rank {{display: block; font-size: 0.92rem; font-weight: 800;}}
	.magic-table th .target-path {{display: block; margin-top: 0.18rem; color: {colors['muted']}; font-size: 0.6rem; font-weight: 600; white-space: nowrap;}}
	.magic-table th.target-korean-series {{border-top: 3px solid #D6A63A;}}
	.magic-table th.target-playoff {{border-top: 3px solid #4C8CCB;}}
	.magic-table th.target-semi-playoff {{border-top: 3px solid #54A66A;}}
	.magic-table th.target-wild-card {{border-top: 3px solid #C77A42;}}
	.magic-table th.target-regular {{border-top: 3px solid {colors['border']};}}
	.magic-table td {{
		padding: 0.54rem 0.24rem;
		border-bottom: 1px solid {colors['border']};
		color: {colors['text']};
		text-align: center;
		vertical-align: middle;
	}}
	.magic-table tbody tr:last-child td {{border-bottom: 0;}}
	.magic-table tbody tr:nth-child(even) td {{background: {colors['surface_alt']};}}
	.magic-table .col-current {{width: 3.4rem; text-align: center;}}
	.magic-table .col-team {{width: 4.2rem; text-align: left;}}
	.magic-table .col-record {{width: 4.4rem;}}
	.magic-table .col-remaining {{width: 3.2rem;}}
	.magic-table .col-target {{width: 6.1rem;}}
	.magic-table th.col-current,
	.magic-table td.col-current {{position: sticky; left: 0;}}
	.magic-table th.col-team,
	.magic-table td.col-team {{position: sticky; left: 3.4rem;}}
	.magic-table th.col-current,
	.magic-table th.col-team {{z-index: 4; background: {colors['surface_alt']};}}
	.magic-table td.col-current,
	.magic-table td.col-team {{z-index: 2; background: {colors['surface']};}}
	.magic-table tbody tr:nth-child(even) td.col-current,
	.magic-table tbody tr:nth-child(even) td.col-team {{background: {colors['surface_alt']};}}
	.magic-table th.col-team,
	.magic-table td.col-team {{box-shadow: 1px 0 0 {colors['border']};}}
	.seed-line {{display: flex; align-items: center; justify-content: center; min-height: 1.8rem;}}
	.seed-badge {{
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 2.45rem;
		height: 1.55rem;
		border: 1px solid {colors['border']};
		border-radius: 4px;
		font-weight: 800;
	}}
	.seed-korean-series {{border-color: #D6A63A; color: #E1B852;}}
	.seed-playoff {{border-color: #4C8CCB; color: #75ACE0;}}
	.seed-semi-playoff {{border-color: #54A66A; color: #7BC98E;}}
	.seed-wild-card {{border-color: #C77A42; color: #DE9A67;}}
	.seed-outside {{color: {colors['muted']};}}
	.number-cell {{
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 2rem;
		border-radius: 5px;
	}}
	.number-cell.magic {{background: {colors['magic_bg']}; color: {colors['magic']};}}
	.number-cell.tragic {{background: {colors['tragic_bg']}; color: {colors['tragic']};}}
	.number-value {{font-size: 1rem; font-weight: 800; line-height: 1.05;}}
	.magic-status-cell {{padding: 0.54rem 0.34rem !important;}}
	.magic-status {{
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 2rem;
		border-radius: 5px;
		font-size: 0.9rem;
		font-weight: 800;
		white-space: nowrap;
	}}
	.magic-status.secured {{background: {colors['secured_bg']}; color: {colors['secured']};}}
	.magic-status.unavailable {{background: {colors['unavailable_bg']}; color: {colors['unavailable']};}}
	</style>
	"""


def matchup_matrix_css() -> str:
	if ACTIVE_DARK_MODE:
		colors = {
			"surface": "#11181C",
			"surface_alt": "#151F24",
			"border": "#2E3D45",
			"text": "#E8EEF1",
			"muted": "#A3B1B8",
			"deep_red_bg": "#47191D",
			"deep_red": "#F1A3A8",
			"red_bg": "#54272A",
			"red": "#EDB5B8",
			"neutral_bg": "#29343A",
			"neutral": "#D1DADF",
			"green_bg": "#203D2C",
			"green": "#A2D8B1",
			"deep_green_bg": "#123321",
			"deep_green": "#7ED19A",
		}
	else:
		colors = {
			"surface": "#FFFFFF",
			"surface_alt": "#F7F9FA",
			"border": "#D9E0E4",
			"text": "#263238",
			"muted": "#65747C",
			"deep_red_bg": "#E4B5B8",
			"deep_red": "#6F1F25",
			"red_bg": "#F3D7D9",
			"red": "#8F333A",
			"neutral_bg": "#E8ECEE",
			"neutral": "#4E5D64",
			"green_bg": "#D8EEDF",
			"green": "#27673C",
			"deep_green_bg": "#AFD6BA",
			"deep_green": "#174C2B",
		}
	return f"""
	<style>
	.matchup-legend {{
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.45rem 0.8rem;
		margin: 0.15rem 0 0.75rem;
		color: {colors['muted']};
		font-size: 0.76rem;
	}}
	.matchup-legend-item {{display: inline-flex; align-items: center; gap: 0.28rem; white-space: nowrap;}}
	.matchup-legend-swatch {{width: 0.72rem; height: 0.72rem; border-radius: 2px; border: 1px solid {colors['border']};}}
	.matchup-legend-swatch.rate-deep-red {{background: {colors['deep_red_bg']};}}
	.matchup-legend-swatch.rate-red {{background: {colors['red_bg']};}}
	.matchup-legend-swatch.rate-neutral {{background: {colors['neutral_bg']};}}
	.matchup-legend-swatch.rate-green {{background: {colors['green_bg']};}}
	.matchup-legend-swatch.rate-deep-green {{background: {colors['deep_green_bg']};}}
	.matchup-table-wrap {{
		width: 100%;
		max-height: 720px;
		overflow: auto;
		border: 1px solid {colors['border']};
		border-radius: 6px;
		background: {colors['surface']};
	}}
	.matchup-table {{
		width: 100%;
		border-collapse: separate;
		border-spacing: 0;
		table-layout: fixed;
		font-size: 0.76rem;
	}}
	.matchup-table th,
	.matchup-table td {{
		border-right: 1px solid {colors['border']};
		border-bottom: 1px solid {colors['border']};
		text-align: center;
		vertical-align: middle;
	}}
	.matchup-table tr > :last-child {{border-right: 0;}}
	.matchup-table tbody tr:last-child > * {{border-bottom: 0;}}
	.matchup-table thead th {{
		position: sticky;
		top: 0;
		z-index: 3;
		height: 2.7rem;
		padding: 0.35rem 0.28rem;
		background: {colors['surface_alt']};
		color: {colors['text']};
		white-space: nowrap;
	}}
	.matchup-table .matchup-team-column {{
		position: sticky;
		left: 0;
		z-index: 2;
		width: 4.6rem;
		padding: 0.45rem 0.36rem;
		background: {colors['surface']};
	}}
	.matchup-table thead .matchup-team-column {{z-index: 5; background: {colors['surface_alt']};}}
	.matchup-table tbody tr:nth-child(even) .matchup-team-column {{background: {colors['surface_alt']};}}
	.matchup-table .matchup-opponent-column {{width: 8rem;}}
	.matchup-table td {{height: 4.65rem; padding: 0.36rem 0.28rem; color: {colors['text']};}}
	.matchup-table td.rate-deep-red {{background: {colors['deep_red_bg']}; color: {colors['deep_red']};}}
	.matchup-table td.rate-red {{background: {colors['red_bg']}; color: {colors['red']};}}
	.matchup-table td.rate-neutral {{background: {colors['neutral_bg']}; color: {colors['neutral']};}}
	.matchup-table td.rate-green {{background: {colors['green_bg']}; color: {colors['green']};}}
	.matchup-table td.rate-deep-green {{background: {colors['deep_green_bg']}; color: {colors['deep_green']};}}
	.matchup-table td.rate-empty,
	.matchup-table td.matchup-diagonal {{background: {colors['surface_alt']}; color: {colors['muted']};}}
	.matchup-record {{display: flex; flex-direction: column; align-items: center; gap: 0.16rem; line-height: 1.15;}}
	.matchup-record-line {{white-space: nowrap;}}
	.matchup-record-line.overall {{font-size: 0.79rem; font-weight: 800;}}
	.matchup-record-line.split {{color: inherit; opacity: 0.9;}}
	.matchup-scope {{display: inline-block; min-width: 1.42rem; margin-right: 0.13rem; font-weight: 700;}}
	.matchup-diagonal-mark {{font-size: 1rem; font-weight: 800;}}
	.matchup-table .team-chip {{justify-content: center; white-space: nowrap;}}
	@media (max-width: 640px) {{
		.matchup-table-wrap {{max-height: 640px;}}
		.matchup-table {{font-size: 0.72rem;}}
		.matchup-table .matchup-opponent-column {{width: 7.8rem;}}
	}}
	</style>
	"""


def team_selector_css(team_options: list[str]) -> str:
	return (
		"""
	<style>
	.st-key-team_detail_selector .stButtonGroup div[role="group"],
	.st-key-team_detail_selector .stButtonGroup div[role="radiogroup"] {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
		justify-content: flex-start !important;
	}
	.st-key-team_detail_selector [data-testid^="stBaseButton-pills"] {
		min-height: 2.2rem;
		border-radius: 999px;
		flex: 0 0 4.4rem !important;
		max-width: 4.4rem !important;
		min-width: 4.4rem !important;
		width: 4.4rem !important;
		justify-content: center;
		line-height: 1.15;
		padding: 0.22rem 0.58rem;
	}
	.st-key-team_detail_selector [data-testid^="stBaseButton-pills"] p {
		line-height: 1.15;
		text-align: center;
		width: 100%;
	}
"""
		+ team_pill_color_rules(".st-key-team_detail_selector", team_options)
		+ "\n\t</style>"
	)


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
			"game_status",
			"stadium",
			"broadcast",
			"note",
		],
	)
	frame = to_numeric(
		frame,
		[
			"season_year",
			"game_duration_min",
			"crowd",
			"innings_played",
			"extra_inning_flag",
			"walkoff_flag",
			"away_score",
			"home_score",
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
		],
	)
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
			"innings_played",
			"extra_inning_flag",
			"walkoff_flag",
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
			"walkoff_win",
			"walkoff_loss",
		],
	)
	frame = to_numeric(
		frame,
		[
			"season_year",
			"game_duration_min",
			"crowd",
			"innings_played",
			"extra_inning_flag",
			"walkoff_flag",
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
			"walkoff_win",
			"walkoff_loss",
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
	headers = ["날짜", "상대", "홈/원정", "결과", "스코어", "득실차", "안타/실책", "경기시간", "구장", "관중"]
	result_labels = {"W": "승", "L": "패", "D": "무"}
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
			f'<span class="result-badge result-{html.escape(result)}">{html.escape(result_labels.get(result, result))}</span>',
			html.escape(score),
			f'<span class="{diff_class}">{html.escape(format_int(diff_value))}</span>',
			html.escape(f"{format_int(row.get('hits_for'))} / {format_int(row.get('errors_for'))}"),
			html.escape(duration),
			html.escape(str(row.get("stadium") or "")),
			html.escape(format_int(row.get("crowd"))),
		]
		rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

	header_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
	body_html = "".join(rows)
	st.markdown(
		f'<div class="recent-table-wrap"><table class="recent-table"><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>',
		unsafe_allow_html=True,
	)


def render_league_recent10_table(summary: pd.DataFrame) -> None:
	if summary.empty:
		plot_empty("최근 10경기 데이터가 없습니다.")
		return

	headers = ["팀", "최근 10경기 (승/패/무)", "득점", "실점", "득실차", "평균 득점", "평균 실점", "평균 안타"]
	rows = []
	for _, row in summary.iterrows():
		team = str(row.get("team") or "")
		run_diff = row.get("run_diff")
		cells = [
			team_chip_html(team),
			html.escape(f"{format_int(row.get('wins'))}-{format_int(row.get('losses'))}-{format_int(row.get('draws'))}"),
			html.escape(format_int(row.get("runs_for"))),
			html.escape(format_int(row.get("runs_against"))),
			f'<span class="{tone_class(run_diff, 0)}">{html.escape(format_int(run_diff))}</span>',
			html.escape(format_float(row.get("avg_runs_for"), 2)),
			html.escape(format_float(row.get("avg_runs_against"), 2)),
			html.escape(format_float(row.get("avg_hits_for"), 2)),
		]
		rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

	header_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
	body_html = "".join(rows)
	st.markdown(
		f'<div class="kbo-table-wrap"><table class="kbo-table"><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>',
		unsafe_allow_html=True,
	)


def build_team_extreme_games(team: pd.DataFrame, metric_column: str, ascending: bool) -> pd.DataFrame:
	final_frame = team[team["is_final"]].dropna(subset=[metric_column]).copy()
	if final_frame.empty:
		return pd.DataFrame()

	team_sorted = final_frame.sort_values(
		["team", metric_column, "game_date", "game_id"],
		ascending=[True, ascending, False, False],
	)
	extreme = team_sorted.groupby("team", dropna=False).head(1).copy()
	return extreme.sort_values(
		[metric_column, "game_date", "game_id", "team"],
		ascending=[ascending, False, False, True],
	).reset_index(drop=True)


def prepare_team_extreme_table(
	frame: pd.DataFrame,
	metric_column: str,
	metric_label: str,
	ascending: bool,
) -> pd.DataFrame:
	if frame.empty:
		return pd.DataFrame()
	display = frame.copy()
	display["순위"] = display[metric_column].rank(method="min", ascending=ascending).astype("Int64")
	display["스코어"] = display.apply(lambda row: f"{format_int(row.get('runs_for'))} - {format_int(row.get('runs_against'))}", axis=1)
	table = display[
		[
			"순위",
			"team",
			"game_date",
			metric_column,
			"opponent",
			"home_away_label",
			"result",
			"스코어",
			"stadium",
			"crowd",
		]
	].rename(
		columns={
			"team": "팀",
			"game_date": "날짜",
			metric_column: metric_label,
			"opponent": "상대",
			"home_away_label": "홈/원정",
			"result": "결과",
			"stadium": "구장",
			"crowd": "관중",
		}
	)
	return table


def render_team_extreme_table(
	frame: pd.DataFrame,
	metric_column: str,
	metric_label: str,
	empty_message: str,
	ascending: bool = False,
) -> None:
	table = prepare_team_extreme_table(frame, metric_column, metric_label, ascending)
	if table.empty:
		plot_empty(empty_message)
		return
	render_table(
		table,
		column_config={
			"순위": st.column_config.NumberColumn("순위", format="%d"),
			"날짜": st.column_config.DateColumn("날짜"),
			metric_label: st.column_config.NumberColumn(metric_label, format="%.0f"),
			"관중": st.column_config.NumberColumn("관중", format="%d"),
		},
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


def team_chip_html(team: Any) -> str:
	team_name = str(team or "")
	color = team_color(team_name)
	return (
		f'<span class="team-chip" style="color:{html.escape(color)}">'
		f'<span class="team-dot" style="background-color:{html.escape(color)}"></span>{html.escape(team_name)}</span>'
	)


def render_recent_form_html(value: Any) -> str:
	if pd.isna(value):
		return "-"
	result_labels = {"W": "승", "L": "패", "D": "무"}
	results = [result for result in str(value).split(",") if result]
	if not results:
		return "-"
	return "".join(
		f'<span class="form-result form-{html.escape(result)}">{html.escape(result_labels.get(result, result))}</span>'
		for result in results
	)


def render_standings_table(standings: pd.DataFrame) -> None:
	columns = [
		("팀", "col-team"),
		("경기", "col-compact"),
		("승", "col-compact"),
		("패", "col-compact"),
		("무", "col-compact"),
		("승률", "col-win-pct"),
		("게임차", "col-games-behind"),
		("연속", "col-streak"),
		("득점", "col-score"),
		("실점", "col-score"),
		("득실차", "col-run-diff"),
		("평균득점", "col-average"),
		("평균실점", "col-average"),
		("최근 5경기", "col-recent-form"),
	]
	rows = []
	for _, row in standings.iterrows():
		team = str(row.get("team") or "")
		color = team_color(team)
		win_pct = row.get("win_pct")
		run_diff = row.get("run_diff")
		games_behind = row.get("games_behind")
		cells = [
			f'<span class="team-chip" style="color:{html.escape(color)}"><span class="team-dot" style="background-color:{html.escape(color)}"></span>{html.escape(team)}</span>',
			html.escape(format_int(row.get("games"))),
			html.escape(format_int(row.get("wins"))),
			html.escape(format_int(row.get("losses"))),
			html.escape(format_int(row.get("draws"))),
			f'<span>{html.escape(format_pct(win_pct))}</span>',
			html.escape("-" if pd.isna(games_behind) or float(games_behind) == 0 else format_float(games_behind, 1)),
			html.escape(str(row.get("streak") or "-")),
			html.escape(format_int(row.get("runs_for"))),
			html.escape(format_int(row.get("runs_against"))),
			f'<span>{html.escape(format_int(run_diff))}</span>',
			html.escape(format_float(row.get("avg_runs_for"), 2)),
			html.escape(format_float(row.get("avg_runs_against"), 2)),
			render_recent_form_html(row.get("recent_5")),
		]
		cell_classes = [
			"col-team",
			"col-compact",
			"col-compact",
			"col-compact",
			"col-compact",
			f"col-win-pct {tone_class(win_pct, 0.5)}".strip(),
			"col-games-behind",
			"col-streak",
			"col-score",
			"col-score",
			f"col-run-diff {tone_class(run_diff, 0)}".strip(),
			"col-average",
			"col-average",
			"col-recent-form",
		]
		rows.append(
			"<tr>"
			+ "".join(
				f'<td class="{cell_class}">{cell}</td>' if cell_class else f"<td>{cell}</td>"
				for cell, cell_class in zip(cells, cell_classes)
			)
			+ "</tr>"
		)
	header_html = "".join(
		f'<th class="{column_class}">{html.escape(header)}</th>' for header, column_class in columns
	)
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


def two_value_bar(first_name: str, first_value: Any, second_name: str, second_value: Any, title_y: str = "경기") -> go.Figure:
	values = [0 if pd.isna(first_value) else first_value, 0 if pd.isna(second_value) else second_value]
	fig = go.Figure()
	fig.add_bar(
		x=[first_name, second_name],
		y=values,
		marker_color=[RESULT_COLORS["W"], RESULT_COLORS["L"]],
		text=values,
		textposition="outside",
		cliponaxis=False,
	)
	fig.update_traces(texttemplate="%{text:,.0f}")
	fig.update_layout(showlegend=False, yaxis_title=title_y, xaxis_title="")
	return apply_layout(fig, height=300)


def opponent_win_pct_bar(final_frame: pd.DataFrame) -> go.Figure:
	summary = (
		final_frame.groupby("opponent", dropna=False)
		.agg(
			games=("game_id", "count"),
			wins=("win_flag", "sum"),
			losses=("loss_flag", "sum"),
			draws=("draw_flag", "sum"),
		)
		.reset_index()
	)
	decision_games = summary["wins"] + summary["losses"]
	summary["win_pct"] = summary["wins"].div(decision_games.where(decision_games > 0))
	summary = summary.sort_values(["win_pct", "wins", "games"], ascending=[False, False, False]).copy()
	opponents = summary["opponent"].astype(str).tolist()
	values = summary["win_pct"].fillna(0)
	fig = go.Figure()
	fig.add_bar(
		x=opponents,
		y=values,
		marker_color=[team_color(opponent) for opponent in opponents],
		text=[format_pct(value) for value in summary["win_pct"]],
		textposition="outside",
		cliponaxis=False,
	)
	fig.update_traces(texttemplate="%{text}")
	if not values.empty:
		fig.update_yaxes(range=[0, max(0.75, values.max() * 1.18)])
	fig.update_layout(showlegend=False, xaxis_title="상대", yaxis_title="승률")
	return apply_layout(fig, height=320)


def turnaround_walkoff_bar(flow_row: pd.Series) -> go.Figure:
	categories = ["역전", "끝내기"]
	win_values = [
		0 if pd.isna(flow_row.get("comeback_win")) else flow_row.get("comeback_win"),
		0 if pd.isna(flow_row.get("walkoff_win")) else flow_row.get("walkoff_win"),
	]
	loss_values = [
		-(0 if pd.isna(flow_row.get("blown_loss")) else flow_row.get("blown_loss")),
		-(0 if pd.isna(flow_row.get("walkoff_loss")) else flow_row.get("walkoff_loss")),
	]
	fig = go.Figure()
	fig.add_bar(
		x=categories,
		y=win_values,
		name="승",
		marker_color=RESULT_COLORS["W"],
		text=win_values,
		textposition="outside",
		cliponaxis=False,
	)
	fig.add_bar(
		x=categories,
		y=loss_values,
		name="패",
		marker_color=RESULT_COLORS["L"],
		text=[abs(value) for value in loss_values],
		textposition="outside",
		cliponaxis=False,
	)
	fig.update_traces(texttemplate="%{text:,.0f}")
	max_abs = max(1, max([abs(value) for value in [*win_values, *loss_values]]) * 1.3)
	fig.update_yaxes(range=[-max_abs, max_abs], zeroline=True, zerolinewidth=1)
	fig.update_layout(barmode="relative", xaxis_title="", yaxis_title="경기", legend_traceorder="normal")
	return apply_layout(fig, height=320)


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


def build_streaks(team_frame: pd.DataFrame) -> pd.DataFrame:
	final_frame = team_frame[team_frame["result"].isin({"W", "L", "D"})].copy()
	if final_frame.empty:
		return pd.DataFrame(columns=["team", "streak"])

	sort_columns = [column for column in ["team", "game_date", "game_start_time", "game_id"] if column in final_frame.columns]
	final_frame = final_frame.sort_values(sort_columns, ascending=[True, *([False] * (len(sort_columns) - 1))])

	streaks = []
	for team, group in final_frame.groupby("team", dropna=False):
		results = group["result"].astype(str).tolist()
		if not results:
			continue
		latest_result = next((result for result in results if result in {"W", "L"}), None)
		if latest_result is None:
			streaks.append({"team": team, "streak": "무"})
			continue
		count = 0
		for result in results:
			if result == "D":
				continue
			if result != latest_result:
				break
			count += 1
		label = f"{count}연승" if latest_result == "W" else f"{count}연패"
		streaks.append({"team": team, "streak": label})
	return pd.DataFrame(streaks)


def build_recent_results(team_frame: pd.DataFrame, n: int = 5) -> pd.DataFrame:
	final_frame = team_frame[team_frame["result"].isin({"W", "L", "D"})].copy()
	if final_frame.empty:
		return pd.DataFrame(columns=["team", "recent_5"])

	sort_columns = [column for column in ["team", "game_date", "game_id"] if column in final_frame.columns]
	final_frame = final_frame.sort_values(sort_columns)
	recent_rows = final_frame.groupby("team", dropna=False).tail(n).copy()
	recent = (
		recent_rows.groupby("team", dropna=False)["result"]
		.apply(lambda values: ",".join(values.astype(str).tolist()))
		.reset_index(name="recent_5")
	)
	return recent


def build_team_recent_summary(team_frame: pd.DataFrame, n: int = 10) -> pd.DataFrame:
	final_frame = team_frame[team_frame["result"].isin({"W", "L", "D"})].copy()
	if final_frame.empty:
		return pd.DataFrame()

	sort_columns = [column for column in ["team", "game_date", "game_start_time", "game_id"] if column in final_frame.columns]
	final_frame = final_frame.sort_values(sort_columns)
	recent = final_frame.groupby("team", dropna=False).tail(n).copy()
	summary = (
		recent.groupby("team", dropna=False)
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
			avg_hits_for=("hits_for", "mean"),
		)
		.reset_index()
	)
	decision_games = summary["wins"] + summary["losses"]
	summary["recent_win_pct"] = summary["wins"].div(decision_games.where(decision_games > 0))
	return summary.sort_values(
		["recent_win_pct", "wins", "run_diff", "runs_for"],
		ascending=[False, False, False, False],
		na_position="last",
	)


def build_period_streak_extremes(team_frame: pd.DataFrame) -> pd.DataFrame:
	decision_frame = team_frame[team_frame["result"].isin({"W", "L"})].copy()
	if decision_frame.empty:
		return pd.DataFrame(columns=["team", "max_win_streak", "max_loss_streak"])

	sort_columns = [column for column in ["team", "game_date", "game_start_time", "game_id"] if column in decision_frame.columns]
	decision_frame = decision_frame.sort_values(sort_columns)
	rows = []
	for team, group in decision_frame.groupby("team", dropna=False):
		max_win = 0
		max_loss = 0
		current_result = None
		current_count = 0
		for result in group["result"].astype(str):
			if result == current_result:
				current_count += 1
			else:
				current_result = result
				current_count = 1
			if result == "W":
				max_win = max(max_win, current_count)
			elif result == "L":
				max_loss = max(max_loss, current_count)
		rows.append({"team": team, "max_win_streak": max_win, "max_loss_streak": max_loss})
	return pd.DataFrame(rows)


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
	recent = build_recent_results(final_frame, 5)
	if not recent.empty:
		standings = standings.merge(recent, on="team", how="left")
	else:
		standings["recent_5"] = pd.NA
	standings = standings.sort_values(["win_pct", "wins", "run_diff"], ascending=[False, False, False]).reset_index(drop=True)
	if standings.empty:
		standings["games_behind"] = pd.NA
	else:
		leader = standings.iloc[0]
		standings["games_behind"] = ((leader["wins"] - standings["wins"]) + (standings["losses"] - leader["losses"])) / 2
	return standings


def standing_value(row: pd.Series, column: str) -> int:
	value = row.get(column, 0)
	return 0 if pd.isna(value) else int(value)


def pairwise_magic_number(
	team_row: pd.Series,
	boundary_row: pd.Series,
	season_games: int = KBO_SEASON_GAMES,
) -> int | None:
	team_remaining = max(0, season_games - standing_value(team_row, "games"))
	boundary_remaining = max(0, season_games - standing_value(boundary_row, "games"))
	team_decisions = season_games - standing_value(team_row, "draws")
	boundary_decisions = season_games - standing_value(boundary_row, "draws")
	team_wins = standing_value(team_row, "wins")
	boundary_wins = standing_value(boundary_row, "wins")

	for combined_results in range(team_remaining + boundary_remaining + 1):
		minimum_team_wins = max(0, combined_results - boundary_remaining)
		maximum_team_wins = min(team_remaining, combined_results)
		clinched_for_every_split = all(
			(team_wins + own_wins) * boundary_decisions
			> (boundary_wins + boundary_remaining - (combined_results - own_wins)) * team_decisions
			for own_wins in range(minimum_team_wins, maximum_team_wins + 1)
		)
		if clinched_for_every_split:
			return combined_results
	return None


def pairwise_tragic_number(
	team_row: pd.Series,
	boundary_row: pd.Series,
	season_games: int = KBO_SEASON_GAMES,
) -> int | None:
	team_remaining = max(0, season_games - standing_value(team_row, "games"))
	boundary_remaining = max(0, season_games - standing_value(boundary_row, "games"))
	team_decisions = season_games - standing_value(team_row, "draws")
	boundary_decisions = season_games - standing_value(boundary_row, "draws")
	team_wins = standing_value(team_row, "wins")
	boundary_wins = standing_value(boundary_row, "wins")

	for combined_results in range(team_remaining + boundary_remaining + 1):
		minimum_team_losses = max(0, combined_results - boundary_remaining)
		maximum_team_losses = min(team_remaining, combined_results)
		eliminated_for_every_split = all(
			(boundary_wins + (combined_results - own_losses)) * team_decisions
			> (team_wins + team_remaining - own_losses) * boundary_decisions
			for own_losses in range(minimum_team_losses, maximum_team_losses + 1)
		)
		if eliminated_for_every_split:
			return combined_results
	return None


def build_magic_number_table(
	team_frame: pd.DataFrame,
	season_games: int = KBO_SEASON_GAMES,
) -> pd.DataFrame:
	standings = build_standings(team_frame).reset_index(drop=True)
	if standings.empty:
		return standings

	standings.insert(0, "rank", range(1, len(standings) + 1))
	standings["remaining"] = (season_games - standings["games"]).clip(lower=0)
	for target_rank in RANK_TARGETS:
		kinds: list[str] = []
		numbers: list[int | None] = []
		for index, row in standings.iterrows():
			current_rank = index + 1
			if current_rank <= target_rank:
				boundary_index = target_rank
				kind = "magic"
				calculator = pairwise_magic_number
			else:
				boundary_index = target_rank - 1
				kind = "tragic"
				calculator = pairwise_tragic_number

			if boundary_index >= len(standings):
				number = 0 if kind == "magic" else None
			else:
				boundary = standings.iloc[boundary_index]
				number = calculator(row, boundary, season_games)
			kinds.append(kind)
			numbers.append(number)

		standings[f"target_{target_rank}_kind"] = kinds
		standings[f"target_{target_rank}_number"] = numbers
	return standings


def magic_number_cell_html(row: pd.Series, target_rank: int) -> str:
	kind = str(row.get(f"target_{target_rank}_kind") or "magic")
	number = row.get(f"target_{target_rank}_number")
	team = str(row.get("team") or "-")
	if pd.isna(number):
		value = "-"
	else:
		value = str(int(number))
	meaning = "매직넘버" if kind == "magic" else "트래직넘버"
	title = f"{team} {target_rank}위 {meaning}"
	return (
		f'<div class="number-cell {html.escape(kind)}" title="{html.escape(title)}">'
		f'<span class="number-value">{html.escape(value)}</span></div>'
	)


def magic_number_cells_html(row: pd.Series) -> list[str]:
	cells: list[str] = []
	index = 0
	while index < len(RANK_TARGETS):
		target_rank = RANK_TARGETS[index]
		kind = str(row.get(f"target_{target_rank}_kind") or "magic")
		number = row.get(f"target_{target_rank}_number")
		status = None
		if not pd.isna(number) and int(number) == 0:
			status = "secured" if kind == "magic" else "unavailable"

		if status is None:
			cells.append(f'<td class="col-target">{magic_number_cell_html(row, target_rank)}</td>')
			index += 1
			continue

		end = index + 1
		while end < len(RANK_TARGETS):
			next_rank = RANK_TARGETS[end]
			next_kind = str(row.get(f"target_{next_rank}_kind") or "magic")
			next_number = row.get(f"target_{next_rank}_number")
			next_status = None
			if not pd.isna(next_number) and int(next_number) == 0:
				next_status = "secured" if next_kind == "magic" else "unavailable"
			if next_status != status:
				break
			end += 1

		merged_ranks = RANK_TARGETS[index:end]
		label_rank = min(merged_ranks) if status == "secured" else max(merged_ranks)
		label = f"{label_rank}위 {'확보' if status == 'secured' else '불가'}"
		cells.append(
			f'<td class="col-target magic-status-cell" colspan="{len(merged_ranks)}">'
			f'<div class="magic-status {status}">{html.escape(label)}</div></td>'
		)
		index = end
	return cells


def render_magic_number_table(magic_table: pd.DataFrame) -> None:
	headers = [
		'<th class="col-current">현재</th>',
		'<th class="col-team">팀</th>',
		'<th class="col-record">전적</th>',
		'<th class="col-remaining">잔여</th>',
	]
	for target_rank in RANK_TARGETS:
		path_label, class_name = POSTSEASON_TARGETS.get(target_rank, ("", "regular"))
		path_html = f'<span class="target-path">{html.escape(path_label)}</span>' if path_label else ""
		headers.append(
			f'<th class="col-target target-{html.escape(class_name)}">'
			f'<span class="target-rank">{target_rank}위</span>'
			f'{path_html}</th>'
		)

	rows = []
	for _, row in magic_table.iterrows():
		rank = standing_value(row, "rank")
		team = str(row.get("team") or "-")
		if rank in POSTSEASON_TARGETS:
			_, class_name = POSTSEASON_TARGETS[rank]
			current_rank_html = f'<div class="seed-line"><span class="seed-badge seed-{html.escape(class_name)}">{rank}위</span></div>'
		else:
			current_rank_html = f'<div class="seed-line"><span class="seed-badge seed-outside">{rank}위</span></div>'
		cells = [
			f'<td class="col-current">{current_rank_html}</td>',
			f'<td class="col-team">{team_chip_html(team)}</td>',
			f'<td class="col-record">{standing_value(row, "wins")}-{standing_value(row, "losses")}-{standing_value(row, "draws")}</td>',
			f'<td class="col-remaining">{standing_value(row, "remaining")}</td>',
			*magic_number_cells_html(row),
		]
		rows.append(f"<tr>{''.join(cells)}</tr>")

	st.markdown(
		f'<div class="magic-table-wrap"><table class="magic-table"><thead><tr>{"".join(headers)}</tr></thead>'
		f'<tbody>{"".join(rows)}</tbody></table></div>',
		unsafe_allow_html=True,
	)


def render_magic_numbers(team: pd.DataFrame) -> None:
	if "season_year" not in team.columns:
		st.info("매직넘버를 계산할 시즌 데이터가 없습니다.")
		return
	season_years = pd.to_numeric(team["season_year"], errors="coerce").dropna()
	if season_years.empty:
		st.info("매직넘버를 계산할 시즌 데이터가 없습니다.")
		return
	latest_year = int(season_years.max())
	latest_team = team[pd.to_numeric(team["season_year"], errors="coerce").eq(latest_year)].copy()
	magic_table = build_magic_number_table(latest_team)
	if magic_table.empty:
		st.info("매직넘버를 계산할 종료 경기 데이터가 없습니다.")
		return

	st.markdown(magic_number_css(), unsafe_allow_html=True)
	completed_games = int(magic_table["games"].sum() / 2)
	metric_cols = st.columns(4)
	metric_cols[0].metric("기준 시즌", str(latest_year))
	metric_cols[1].metric("종료 경기", f"{completed_games} / {KBO_SEASON_GAMES * 5}")
	metric_cols[2].metric("잔여 경기", format_int(KBO_SEASON_GAMES * 5 - completed_games))
	with metric_cols[3]:
		render_league_leader_metric(magic_table.iloc[0])

	st.markdown(
		'<div class="magic-number-note"><span class="legend-mark legend-magic">매직넘버</span>'
		'<span>·</span><span class="legend-mark legend-tragic">트래직넘버</span>'
		'<span>·</span><span class="legend-mark legend-secured">확보</span>'
		'<span>·</span><span class="legend-mark legend-unavailable">불가</span>'
		'<span>· 향후 무승부 및 동률 결정 제외</span></div>',
		unsafe_allow_html=True,
	)
	render_magic_number_table(magic_table)


def display_standings_table(standings: pd.DataFrame) -> None:
	if standings.empty:
		st.info("선택한 조건에 완료 경기 데이터가 없습니다.")
		return
	render_standings_table(standings)


def render_league_leader_metric(row: pd.Series | None) -> None:
	if row is None or row.empty:
		st.metric("리그 1위", "-")
		return
	team = str(row.get("team") or "-")
	color = team_color(team)
	st.markdown(
		f"""
		<div class="league-leader-card">
			<div class="league-leader-label">리그 1위</div>
			<div class="league-leader-value">
				<span style="color:{html.escape(color)}">{html.escape(team)}</span>
				<span class="league-leader-pct">{html.escape(format_pct(row.get("win_pct")))}</span>
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


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


def filter_data(
	schedule: pd.DataFrame,
	team: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str], dict[str, list[str]]]:
	schedule = schedule[schedule["game_status"] == "final"].copy()
	team = team[team["is_final"]].copy()
	year_options = sorted(schedule["season_year_label"].dropna().unique().tolist(), reverse=True)
	default_years = year_options[:1]
	month_options = sorted(schedule["source_month_label"].dropna().unique().tolist())
	team_options = sorted(team["team"].dropna().astype(str).unique().tolist())

	with st.sidebar:
		st.header("필터")
		st.markdown(sidebar_filter_css(team_options), unsafe_allow_html=True)
		selected_years = st.pills(
			"연도", year_options, default=default_years, selection_mode="multi", width="stretch", key="filter_years"
		) or []
		selected_months = st.pills(
			"월", month_options, default=month_options, selection_mode="multi", width="stretch", key="filter_months"
		) or []
		selected_teams = st.pills(
			"팀", team_options, default=team_options, selection_mode="multi", width="stretch", key="filter_teams"
		) or []
		selected_home_away = st.pills(
			"홈/원정",
			HOME_AWAY_ORDER,
			default=HOME_AWAY_ORDER,
			selection_mode="multi",
			width="stretch",
			key="filter_home_away",
		) or []

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
		{
			"years": list(selected_years),
			"months": list(selected_months),
			"teams": list(selected_teams),
			"home_away": list(selected_home_away),
		},
	)


def render_overview(schedule: pd.DataFrame, team: pd.DataFrame) -> None:
	standings = build_standings(team)
	leader = standings.iloc[0] if not standings.empty else None

	metric_cols = st.columns(4)
	metric_cols[0].metric("경기 수", format_int(len(schedule)))
	with metric_cols[1]:
		render_league_leader_metric(leader)
	metric_cols[2].metric("총 관중 수", format_int(schedule["crowd"].sum()))
	metric_cols[3].metric("평균 관중", format_int(schedule["crowd"].mean()))

	st.subheader("팀 순위")
	display_standings_table(standings)

	left, right = st.columns(2)
	with left:
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
	with right:
		st.subheader("팀별 득실차")
		if standings.empty:
			plot_empty("득실차 데이터가 없습니다.")
		else:
			fig = team_metric_bar(
				standings,
				x="team",
				y="run_diff",
				labels={"team": "팀", "run_diff": "득실차"},
				sort_by="run_diff",
				texttemplate="%{text:,.0f}",
			)
			max_abs = max(10, standings["run_diff"].abs().max() * 1.18)
			fig.update_yaxes(range=[-max_abs, max_abs])
			st.plotly_chart(fig, width="stretch")

	st.subheader("최근 10경기")
	render_league_recent10_table(build_team_recent_summary(team, 10))


def render_team_detail(team: pd.DataFrame, rank_order: list[str]) -> None:
	teams = order_by_reference(team["team"].dropna().astype(str).unique().tolist(), rank_order)
	if not teams:
		st.info("선택한 조건에 팀 데이터가 없습니다.")
		return
	st.markdown(team_selector_css(teams), unsafe_allow_html=True)
	selected_team = st.pills(
		"팀",
		teams,
		default=teams[0],
		selection_mode="single",
		required=True,
		width="stretch",
		key="team_detail_selector",
	)
	selected_team = str(selected_team or teams[0])
	team_frame = team[team["team"] == selected_team].copy()
	final_frame = team_frame[team_frame["is_final"]].copy()

	wins = int(final_frame["win_flag"].sum()) if not final_frame.empty else 0
	losses = int(final_frame["loss_flag"].sum()) if not final_frame.empty else 0
	draws = int(final_frame["draw_flag"].sum()) if not final_frame.empty else 0
	win_pct = wins / (wins + losses) if wins + losses else pd.NA
	run_diff = final_frame["run_diff"].sum() if not final_frame.empty else pd.NA

	metric_cols = st.columns(7)
	metric_cols[0].metric("전적", f"{wins}-{losses}-{draws}")
	metric_cols[1].metric("승률", format_pct(win_pct))
	metric_cols[2].metric("득실차", format_int(run_diff))
	metric_cols[3].metric("평균 득점", format_float(final_frame["runs_for"].mean()))
	metric_cols[4].metric("평균 실점", format_float(final_frame["runs_against"].mean()))
	metric_cols[5].metric("평균 안타", format_float(final_frame["hits_for"].mean(), 2))
	metric_cols[6].metric("평균 실책", format_float(final_frame["errors_for"].mean(), 2))

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
		st.subheader("구장별 성적")
		stadium_categories = (
			final_frame.dropna(subset=["stadium"]).groupby("stadium").size().sort_values(ascending=False).index.astype(str).tolist()
			if not final_frame.empty
			else []
		)
		stadium = build_result_counts(final_frame.dropna(subset=["stadium"]), "stadium", stadium_categories) if stadium_categories else pd.DataFrame()
		if stadium.empty:
			plot_empty("구장별 성적 데이터가 없습니다.")
		else:
			st.plotly_chart(result_count_bar(stadium, "stadium", "구장"), width="stretch")
	with right:
		st.subheader("요일별 성적")
		weekday = build_result_counts(final_frame.dropna(subset=["weekday_label"]), "weekday_label", WEEKDAY_ORDER) if not final_frame.empty else pd.DataFrame()
		if weekday.empty:
			plot_empty("요일별 성적 데이터가 없습니다.")
		else:
			st.plotly_chart(result_count_bar(weekday, "weekday_label", "요일"), width="stretch")

	left, right = st.columns(2)
	with left:
		st.subheader("상대별 승률")
		if final_frame.empty:
			plot_empty("상대별 승률 데이터가 없습니다.")
		else:
			st.plotly_chart(opponent_win_pct_bar(final_frame), width="stretch")
	flow_summary = build_flow_summary(team_frame)
	with right:
		st.subheader("역전/끝내기")
		if flow_summary.empty:
			plot_empty("역전/끝내기 데이터가 없습니다.")
		else:
			st.plotly_chart(turnaround_walkoff_bar(flow_summary.iloc[0]), width="stretch")

	st.subheader("최근 10경기")
	recent = final_frame.sort_values(["game_date", "game_id"]).tail(10).copy()
	if recent.empty:
		plot_empty("최근 경기 데이터가 없습니다.")
		return

	recent_wins = int(recent["win_flag"].sum())
	recent_losses = int(recent["loss_flag"].sum())
	recent_draws = int(recent["draw_flag"].sum())
	recent_metric_cols = st.columns(7)
	recent_metric_cols[0].metric("최근 전적", f"{recent_wins}-{recent_losses}-{recent_draws}")
	recent_metric_cols[1].metric("최근 승률", format_pct(recent_wins / (recent_wins + recent_losses) if recent_wins + recent_losses else pd.NA))
	recent_metric_cols[2].metric("득실차", format_int(recent["run_diff"].sum()))
	recent_metric_cols[3].metric("평균 득점", format_float(recent["runs_for"].mean()))
	recent_metric_cols[4].metric("평균 실점", format_float(recent["runs_against"].mean()))
	recent_metric_cols[5].metric("평균 안타", format_float(recent["hits_for"].mean(), 2))
	recent_metric_cols[6].metric("평균 실책", format_float(recent["errors_for"].mean(), 2))

	recent = recent.sort_values(["game_date", "game_id"], ascending=[False, False]).reset_index(drop=True)
	render_recent_games_table(recent)


def aggregate_matchup_records(frame: pd.DataFrame, scope: str) -> pd.DataFrame:
	grouped = (
		frame.groupby(["team", "opponent"])
		.agg(
			**{
				f"{scope}_games": ("game_id", "count"),
				f"{scope}_wins": ("win_flag", "sum"),
				f"{scope}_losses": ("loss_flag", "sum"),
				f"{scope}_draws": ("draw_flag", "sum"),
			}
		)
		.reset_index()
	)
	decisions = grouped[f"{scope}_wins"] + grouped[f"{scope}_losses"]
	grouped[f"{scope}_win_pct"] = grouped[f"{scope}_wins"].div(decisions.where(decisions > 0))
	return grouped


def build_matchup_records(final_frame: pd.DataFrame) -> pd.DataFrame:
	matchups = aggregate_matchup_records(final_frame, "overall")
	for home_away, scope in (("home", "home"), ("away", "away")):
		split = aggregate_matchup_records(final_frame[final_frame["home_away"] == home_away], scope)
		matchups = matchups.merge(split, on=["team", "opponent"], how="left")

	count_columns = [
		f"{scope}_{metric}"
		for scope in ("overall", "home", "away")
		for metric in ("games", "wins", "losses", "draws")
	]
	matchups[count_columns] = matchups[count_columns].fillna(0).astype(int)
	return matchups


def matchup_rate_class(value: Any) -> str:
	if pd.isna(value):
		return "rate-empty"
	win_pct = float(value)
	if win_pct <= 0.25:
		return "rate-deep-red"
	if win_pct < 0.5:
		return "rate-red"
	if win_pct == 0.5:
		return "rate-neutral"
	if win_pct < 0.75:
		return "rate-green"
	return "rate-deep-green"


def matchup_record_text(row: pd.Series, scope: str) -> str:
	games = standing_value(row, f"{scope}_games")
	if games == 0:
		return "-"
	return (
		f"{standing_value(row, f'{scope}_wins')}-"
		f"{standing_value(row, f'{scope}_losses')}-"
		f"{standing_value(row, f'{scope}_draws')} "
		f"({format_pct(row.get(f'{scope}_win_pct'))})"
	)


def matchup_record_cell_html(row: pd.Series) -> str:
	rate_class = matchup_rate_class(row.get("overall_win_pct"))
	return (
		f'<td class="matchup-opponent-column {rate_class}"><div class="matchup-record">'
		f'<div class="matchup-record-line overall" title="전체">{html.escape(matchup_record_text(row, "overall"))}</div>'
		f'<div class="matchup-record-line split"><span class="matchup-scope" title="홈" aria-label="홈">🏠</span>{html.escape(matchup_record_text(row, "home"))}</div>'
		f'<div class="matchup-record-line split"><span class="matchup-scope" title="원정" aria-label="원정">✈️</span>{html.escape(matchup_record_text(row, "away"))}</div>'
		'</div></td>'
	)


def render_matchup_matrix(matchups: pd.DataFrame, rank_order: list[str]) -> None:
	row_teams = matchups["team"].dropna().astype(str).unique().tolist()
	opponent_teams = matchups["opponent"].dropna().astype(str).unique().tolist()
	row_order = [team for team in rank_order if team in row_teams]
	row_order += [team for team in row_teams if team not in row_order]
	column_order = [team for team in rank_order if team in opponent_teams]
	column_order += [team for team in opponent_teams if team not in column_order]
	lookup = matchups.set_index(["team", "opponent"])

	headers = ['<th class="matchup-team-column">팀 / 상대</th>']
	headers.extend(
		f'<th class="matchup-opponent-column">{team_chip_html(team)}</th>'
		for team in column_order
	)
	rows: list[str] = []
	for team in row_order:
		cells = [f'<th class="matchup-team-column" scope="row">{team_chip_html(team)}</th>']
		for opponent in column_order:
			if team == opponent:
				cells.append(
					'<td class="matchup-opponent-column matchup-diagonal"><span class="matchup-diagonal-mark">■</span></td>'
				)
			elif (team, opponent) in lookup.index:
				cells.append(matchup_record_cell_html(lookup.loc[(team, opponent)]))
			else:
				cells.append('<td class="matchup-opponent-column rate-empty">-</td>')
		rows.append(f"<tr>{''.join(cells)}</tr>")

	min_width = 74 + len(column_order) * 128
	st.markdown(
		f'<div class="matchup-table-wrap"><table class="matchup-table" style="min-width:{min_width}px">'
		f'<thead><tr>{"".join(headers)}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>',
		unsafe_allow_html=True,
	)


def render_matchups(team: pd.DataFrame, rank_order: list[str]) -> None:
	final_frame = team[team["is_final"]].copy()
	if final_frame.empty:
		st.info("선택한 조건에 상대전적 데이터가 없습니다.")
		return

	matchups = build_matchup_records(final_frame)
	st.markdown(matchup_matrix_css(), unsafe_allow_html=True)
	st.markdown(
		'<div class="matchup-legend">'
		'<span class="matchup-legend-item"><span class="matchup-legend-swatch rate-deep-red"></span>0.250 이하</span>'
		'<span class="matchup-legend-item"><span class="matchup-legend-swatch rate-red"></span>0.500 미만</span>'
		'<span class="matchup-legend-item"><span class="matchup-legend-swatch rate-neutral"></span>0.500</span>'
		'<span class="matchup-legend-item"><span class="matchup-legend-swatch rate-green"></span>0.750 미만</span>'
		'<span class="matchup-legend-item"><span class="matchup-legend-swatch rate-deep-green"></span>0.750 이상</span>'
		'</div>',
		unsafe_allow_html=True,
	)
	render_matchup_matrix(matchups, rank_order)


def phase_run_diff_bar(summary: pd.DataFrame) -> go.Figure:
	plot_frame = summary.sort_values(["after_5_run_diff", "first_5_run_diff"], ascending=[False, False]).copy()
	teams = plot_frame["team"].astype(str).tolist()
	colors = [team_color(team) for team in teams]
	fig = go.Figure()
	fig.add_bar(
		x=teams,
		y=plot_frame["first_5_run_diff"],
		name="5회까지",
		marker_color=colors,
		text=plot_frame["first_5_run_diff"],
		textposition="outside",
		cliponaxis=False,
	)
	fig.add_bar(
		x=teams,
		y=plot_frame["after_5_run_diff"],
		name="6회 이후",
		marker_color=colors,
		marker_pattern_shape="/",
		marker_pattern_solidity=0.25,
		text=plot_frame["after_5_run_diff"],
		textposition="outside",
		cliponaxis=False,
	)
	fig.update_traces(texttemplate="%{text:,.0f}")
	fig.update_layout(barmode="group", yaxis_title="득실", xaxis_title="팀")
	return apply_layout(fig)


def latest_selected_season(team: pd.DataFrame, selected_years: list[str]) -> int | None:
	if "season_year" not in team.columns:
		return None
	available = set(pd.to_numeric(team.get("season_year"), errors="coerce").dropna().astype(int).tolist())
	selected: list[int] = []
	for value in selected_years:
		try:
			selected.append(int(float(value)))
		except (TypeError, ValueError):
			continue
	candidates = available.intersection(selected)
	return max(candidates) if candidates else None


def build_daily_rank_trend(team: pd.DataFrame, season_year: int) -> pd.DataFrame:
	season = team[
		(team["is_final"])
		& pd.to_numeric(team["season_year"], errors="coerce").eq(season_year)
	].dropna(subset=["game_date", "team"]).copy()
	if season.empty:
		return pd.DataFrame()

	season["game_date"] = pd.to_datetime(season["game_date"], errors="coerce").dt.normalize()
	season = season.dropna(subset=["game_date"])
	daily = (
		season.groupby(["game_date", "team"], dropna=False)
		.agg(
			wins=("win_flag", "sum"),
			losses=("loss_flag", "sum"),
			draws=("draw_flag", "sum"),
			runs_for=("runs_for", "sum"),
			runs_against=("runs_against", "sum"),
		)
	)
	dates = sorted(season["game_date"].unique().tolist())
	teams = sorted(season["team"].dropna().astype(str).unique().tolist())
	full_index = pd.MultiIndex.from_product([dates, teams], names=["game_date", "team"])
	daily = daily.reindex(full_index, fill_value=0).reset_index().sort_values(["team", "game_date"])
	cumulative_columns = ["wins", "losses", "draws", "runs_for", "runs_against"]
	daily[cumulative_columns] = daily.groupby("team", sort=False)[cumulative_columns].cumsum()
	daily["run_diff"] = daily["runs_for"] - daily["runs_against"]
	decisions = daily["wins"] + daily["losses"]
	daily["win_pct"] = daily["wins"].div(decisions.where(decisions > 0))

	ranked_dates: list[pd.DataFrame] = []
	for _, snapshot in daily.groupby("game_date", sort=True):
		ranked = snapshot.sort_values(
			["win_pct", "wins", "run_diff", "team"],
			ascending=[False, False, False, True],
			na_position="last",
		).copy()
		ranked["rank"] = range(1, len(ranked) + 1)
		ranked_dates.append(ranked)

	trend = pd.concat(ranked_dates, ignore_index=True)
	trend["record"] = trend.apply(
		lambda row: f"{int(row['wins'])}-{int(row['losses'])}-{int(row['draws'])}",
		axis=1,
	)
	return trend.sort_values(["game_date", "rank"]).reset_index(drop=True)


def selected_month_numbers(selected_months: list[str]) -> list[int]:
	months: set[int] = set()
	for value in selected_months:
		try:
			month = int(float(value))
		except (TypeError, ValueError):
			continue
		if 1 <= month <= 12:
			months.add(month)
	return sorted(months)


def prepare_rank_trend_display(
	trend: pd.DataFrame,
	selected_months: list[str],
	selected_teams: list[str],
) -> pd.DataFrame:
	if trend.empty:
		return trend.copy()
	months = selected_month_numbers(selected_months)
	if not months:
		return pd.DataFrame(columns=[*trend.columns, "plot_rank"])

	selected_dates = trend.loc[trend["game_date"].dt.month.isin(months), "game_date"]
	if selected_dates.empty:
		return pd.DataFrame(columns=[*trend.columns, "plot_rank"])
	start_date = selected_dates.min()
	end_date = selected_dates.max()
	display = trend[trend["game_date"].between(start_date, end_date)].copy()
	if selected_teams:
		season_teams = set(display["team"].astype(str))
		team_selection = [team for team in selected_teams if team in season_teams]
		display = display[display["team"].isin(team_selection)].copy()
	display["plot_rank"] = display["rank"].where(display["game_date"].dt.month.isin(months))
	return display


def rank_trend_figure(display: pd.DataFrame, league_size: int) -> go.Figure:
	visible = display.dropna(subset=["plot_rank"]).copy()
	last_date = visible["game_date"].max()
	last_snapshot = visible[visible["game_date"].eq(last_date)].sort_values("plot_rank")
	team_order = last_snapshot["team"].astype(str).tolist()
	fig = go.Figure()
	for team in team_order:
		team_frame = display[display["team"].eq(team)].sort_values("game_date").copy()
		text = [""] * len(team_frame)
		last_visible_positions = team_frame.index[team_frame["plot_rank"].notna()].tolist()
		if last_visible_positions:
			last_position = team_frame.index.get_loc(last_visible_positions[-1])
			text[last_position] = team
		fig.add_scatter(
			x=team_frame["game_date"],
			y=team_frame["plot_rank"],
			mode="lines+markers+text",
			name=team,
			line=dict(color=team_color(team), width=2),
			marker=dict(color=team_color(team), size=4),
			text=text,
			textposition="middle right",
			customdata=team_frame[["record", "win_pct"]].to_numpy(),
			cliponaxis=False,
			hovertemplate=(
				f"<b>{html.escape(team)}</b><br>%{{x|%Y-%m-%d}}<br>"
				"%{y:.0f}위 · %{customdata[0]} · %{customdata[1]:.3f}<extra></extra>"
			),
			connectgaps=False,
		)

	start_date = visible["game_date"].min()
	end_date = visible["game_date"].max()
	height = max(470, min(640, 320 + league_size * 28))
	fig = apply_layout(fig, height=height)
	fig.update_layout(
		showlegend=False,
		hovermode="closest",
		margin=dict(l=52, r=70, t=20, b=52),
	)
	fig.update_xaxes(
		title_text="",
		range=[start_date - pd.Timedelta(days=1), end_date + pd.Timedelta(days=5)],
		tickmode="auto",
		nticks=6,
		tickformat="%m/%d",
		tickangle=0,
	)
	fig.update_yaxes(
		title_text="순위",
		range=[league_size + 0.5, 0.5],
		tickmode="array",
		tickvals=list(range(1, league_size + 1)),
		ticktext=[f"{rank}위" for rank in range(1, league_size + 1)],
		dtick=1,
	)
	return fig


def format_rank_date_range(start: pd.Timestamp, end: pd.Timestamp) -> str:
	return f"{start:%Y.%m.%d} - {end:%m.%d}"


def render_rank_trend(
	full_team: pd.DataFrame,
	filter_selections: dict[str, list[str]],
) -> None:
	st.subheader("순위 변동 추이")
	season_year = latest_selected_season(full_team, filter_selections.get("years", []))
	if season_year is None:
		plot_empty("선택한 연도에 순위 데이터가 없습니다.")
		return

	trend = build_daily_rank_trend(full_team, season_year)
	display = prepare_rank_trend_display(
		trend,
		filter_selections.get("months", []),
		filter_selections.get("teams", []),
	)
	visible = display.dropna(subset=["plot_rank"]) if "plot_rank" in display.columns else pd.DataFrame()
	if trend.empty or visible.empty:
		plot_empty("선택한 월에 완료된 경기의 순위 데이터가 없습니다.")
		return

	season_start = trend["game_date"].min()
	season_end = trend["game_date"].max()
	display_start = visible["game_date"].min()
	display_end = visible["game_date"].max()
	display_teams = visible["team"].nunique()
	league_size = trend["team"].nunique()
	metric_cols = st.columns(4)
	metric_cols[0].metric("기준 시즌", str(season_year))
	metric_cols[1].metric("전체 시즌 데이터", format_rank_date_range(season_start, season_end))
	metric_cols[2].metric("그래프 표시 기간", format_rank_date_range(display_start, display_end))
	metric_cols[3].metric("표시 팀", f"{display_teams}팀")

	months = selected_month_numbers(filter_selections.get("months", []))
	month_text = " · ".join(f"{month:02d}월" for month in months)
	year_note = " · 여러 연도 선택 시 최신 시즌" if len(filter_selections.get("years", [])) > 1 else ""
	st.caption(
		f"선택 월 {month_text}{year_note} · 순위는 시즌 개막일부터 해당 일자까지 리그 전체 경기 누적 기준"
		" · 선택하지 않은 중간 월은 선을 끊어 표시"
	)
	st.plotly_chart(rank_trend_figure(display, league_size), width="stretch")


FLOW_COLUMNS = [
	"first_5_runs_for",
	"first_5_runs_against",
	"after_5_runs_for",
	"after_5_runs_against",
	"comeback_win",
	"blown_loss",
	"walkoff_win",
	"walkoff_loss",
]


def build_flow_summary(team: pd.DataFrame) -> pd.DataFrame:
	final_team = team[team["is_final"]].copy()
	if any(column not in final_team.columns for column in FLOW_COLUMNS):
		return pd.DataFrame()
	if final_team.empty or not final_team[FLOW_COLUMNS].notna().any().any():
		return pd.DataFrame()

	for column in FLOW_COLUMNS:
		final_team[column] = final_team[column].fillna(0)

	summary = (
		final_team.groupby("team", dropna=False)
		.agg(
			games=("game_id", "count"),
			first_5_runs_for=("first_5_runs_for", "sum"),
			first_5_runs_against=("first_5_runs_against", "sum"),
			after_5_runs_for=("after_5_runs_for", "sum"),
			after_5_runs_against=("after_5_runs_against", "sum"),
			comeback_win=("comeback_win", "sum"),
			blown_loss=("blown_loss", "sum"),
			walkoff_win=("walkoff_win", "sum"),
			walkoff_loss=("walkoff_loss", "sum"),
		)
		.reset_index()
	)
	summary["first_5_run_diff"] = summary["first_5_runs_for"] - summary["first_5_runs_against"]
	summary["after_5_run_diff"] = summary["after_5_runs_for"] - summary["after_5_runs_against"]
	return summary


def render_flow_insights(
	schedule: pd.DataFrame,
	team: pd.DataFrame,
	full_team: pd.DataFrame,
	filter_selections: dict[str, list[str]],
) -> None:
	summary = build_flow_summary(team)
	if summary.empty:
		st.info("선택한 조건에 이닝 흐름 데이터가 없습니다. 전체 기간 재크롤링 후 표시됩니다.")
		render_rank_trend(full_team, filter_selections)
		return

	final_schedule = schedule[schedule["game_status"] == "final"].copy()
	extra_games = final_schedule[final_schedule["extra_inning_flag"].fillna(0) == 1].copy()
	streak_extremes = build_period_streak_extremes(team)
	metric_cols = st.columns(5)
	metric_cols[0].metric("연장 경기", format_int(len(extra_games)))
	metric_cols[1].metric("역전승", format_int(summary["comeback_win"].sum()))
	metric_cols[2].metric("역전패", format_int(summary["blown_loss"].sum()))
	metric_cols[3].metric("끝내기승", format_int(summary["walkoff_win"].sum()))
	metric_cols[4].metric("끝내기패", format_int(summary["walkoff_loss"].sum()))

	left, right = st.columns(2)
	with left:
		st.subheader("팀별 전반 / 후반 득실")
		st.plotly_chart(phase_run_diff_bar(summary), width="stretch")
	with right:
		st.subheader("역전승 / 역전패")
		fig = paired_team_bar(
			summary,
			team_column="team",
			first_column="comeback_win",
			second_column="blown_loss",
			first_name="역전승",
			second_name="역전패",
			title_y="경기",
		)
		st.plotly_chart(fig, width="stretch")

	left, right = st.columns([1, 1])
	with left:
		st.subheader("끝내기승 / 끝내기패")
		fig = paired_team_bar(
			summary,
			team_column="team",
			first_column="walkoff_win",
			second_column="walkoff_loss",
			first_name="끝내기승",
			second_name="끝내기패",
			title_y="경기",
		)
		st.plotly_chart(fig, width="stretch")
	with right:
		st.subheader("최다 연승 / 최다 연패")
		if streak_extremes.empty:
			plot_empty("연승/연패 데이터가 없습니다.")
		else:
			fig = paired_team_bar(
				streak_extremes,
				team_column="team",
				first_column="max_win_streak",
				second_column="max_loss_streak",
				first_name="최다 연승",
				second_name="최다 연패",
				title_y="경기",
			)
			st.plotly_chart(fig, width="stretch")

	render_rank_trend(full_team, filter_selections)


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


def render_games(schedule: pd.DataFrame, team: pd.DataFrame) -> None:
	final_team = team[team["is_final"]].copy()
	left, right = st.columns(2)
	with left:
		st.subheader("팀별 최다 득점 경기")
		top_scoring = build_team_extreme_games(final_team, "runs_for", ascending=False)
		render_team_extreme_table(top_scoring, "runs_for", "득점", "팀별 최다 득점 경기 데이터가 없습니다.")
	with right:
		st.subheader("팀별 최다 실점 경기")
		top_allowed = build_team_extreme_games(final_team, "runs_against", ascending=False)
		render_team_extreme_table(top_allowed, "runs_against", "실점", "팀별 최다 실점 경기 데이터가 없습니다.")

	left, right = st.columns(2)
	with left:
		st.subheader("팀별 최장 시간 경기")
		longest = build_team_extreme_games(final_team, "game_duration_min", ascending=False)
		render_team_extreme_table(longest, "game_duration_min", "시간(분)", "팀별 최장 시간 경기 데이터가 없습니다.")
	with right:
		st.subheader("팀별 최단 시간 경기")
		shortest = build_team_extreme_games(final_team, "game_duration_min", ascending=True)
		render_team_extreme_table(shortest, "game_duration_min", "시간(분)", "팀별 최단 시간 경기 데이터가 없습니다.", ascending=True)

	st.subheader("경기 목록")
	table = schedule.sort_values(
		["season_year", "game_date", "game_start_time", "game_id"],
		ascending=[False, False, False, False],
	)[
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
	st.set_page_config(page_title="KBO Dashboard", layout="wide")
	dark_mode = DEFAULT_DARK_MODE
	set_visual_mode(dark_mode)
	st.markdown(theme_css(dark_mode), unsafe_allow_html=True)
	st.title("KBO Dashboard")

	if not SCHEDULE_PATH.exists() or not TEAM_PATH.exists():
		st.error("data/output 폴더에 필요한 엑셀 파일이 없습니다.")
		return

	schedule_signature = file_signature(SCHEDULE_PATH)
	team_signature = file_signature(TEAM_PATH)
	schedule, team = load_data(str(SCHEDULE_PATH), str(TEAM_PATH), schedule_signature, team_signature)
	(
		filtered_schedule,
		filtered_team,
		attendance_schedule,
		attendance_team,
		rank_order,
		filter_selections,
	) = filter_data(schedule, team)

	if filtered_schedule.empty and filtered_team.empty:
		st.warning("선택한 조건에 데이터가 없습니다.")

	st.caption(
		f"종료 경기 기준 · Schedule {len(filtered_schedule):,} games · Team rows {len(filtered_team):,} · "
		f"{SCHEDULE_PATH.name} / {TEAM_PATH.name}"
	)

	overview_tab, team_tab, magic_tab, matchup_tab, flow_tab, attendance_tab, games_tab = st.tabs(
		["리그", "팀", "매직넘버", "상대전적", "흐름", "관중/구장", "경기"]
	)

	with overview_tab:
		render_overview(filtered_schedule, filtered_team)
	with team_tab:
		render_team_detail(filtered_team, rank_order)
	with magic_tab:
		render_magic_numbers(team)
	with matchup_tab:
		render_matchups(filtered_team, rank_order)
	with flow_tab:
		render_flow_insights(filtered_schedule, filtered_team, team, filter_selections)
	with attendance_tab:
		render_attendance(attendance_schedule, attendance_team, filtered_team)
	with games_tab:
		render_games(filtered_schedule, filtered_team)


if __name__ == "__main__":
	main()
