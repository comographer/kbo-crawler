from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from zipfile import BadZipFile

import pandas as pd


def timestamped_path(path: Path) -> Path:
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	return path.with_name(f"{path.stem}_{timestamp}{path.suffix}")


def excel_frame_matches(
	path: Path,
	expected_frame: pd.DataFrame,
	sheet_name: str | int = 0,
	expected_sheet_names: Sequence[str] | None = None,
) -> bool:
	if not path.exists():
		return False
	try:
		with pd.ExcelFile(path) as workbook:
			if expected_sheet_names is not None and workbook.sheet_names != list(expected_sheet_names):
				return False
			current_frame = pd.read_excel(workbook, sheet_name=sheet_name)
	except (BadZipFile, OSError, ValueError):
		return False

	try:
		pd.testing.assert_frame_equal(
			current_frame,
			expected_frame,
			check_dtype=False,
			check_exact=False,
			rtol=0,
			atol=0,
		)
	except AssertionError:
		return False
	return True


def write_with_permission_fallback(path: Path, writer: Callable[[Path], None]) -> Path:
	try:
		writer(path)
		return path
	except PermissionError:
		fallback_path = timestamped_path(path)
		writer(fallback_path)
		return fallback_path
