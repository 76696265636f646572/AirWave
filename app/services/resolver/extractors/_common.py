from __future__ import annotations

from typing import Any


def duration_seconds_parse(value: Any) -> int | None:
    """Shared duration parsing for all extractors."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, str):
        try:
            return max(0, int(float(value.strip())))
        except ValueError:
            return None
    return None
