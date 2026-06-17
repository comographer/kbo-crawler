from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path


def timestamped_path(path: Path) -> Path:
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	return path.with_name(f"{path.stem}_{timestamp}{path.suffix}")


def write_with_permission_fallback(path: Path, writer: Callable[[Path], None]) -> Path:
	try:
		writer(path)
		return path
	except PermissionError:
		fallback_path = timestamped_path(path)
		writer(fallback_path)
		return fallback_path
