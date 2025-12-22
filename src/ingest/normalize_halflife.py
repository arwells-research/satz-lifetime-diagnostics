from __future__ import annotations
import re
from typing import Optional

_UNIT_TO_SECONDS = {
    "s": 1.0,
    "sec": 1.0,
    "ms": 1e-3,
    "us": 1e-6,
    "ns": 1e-9,
    "ps": 1e-12,
    "m": 60.0,
    "min": 60.0,
    "h": 3600.0,
    "hr": 3600.0,
    "d": 86400.0,
    "day": 86400.0,
    "y": 365.25 * 86400.0,
    "yr": 365.25 * 86400.0,
}

def parse_halflife_to_seconds(value: str | float | int, unit: Optional[str] = None) -> Optional[float]:
    """
    Normalize a half-life to seconds.
    Accepts:
      - numeric seconds directly (if unit None)
      - strings like "12.3 s", "5.2 ms", "3.1 h"
      - value + unit columns

    Returns float seconds or None if not parseable.
    """
    if value is None:
        return None

    # Already numeric and unit provided
    if isinstance(value, (int, float)) and unit:
        u = unit.strip().lower()
        u = u.replace("seconds", "s").replace("second", "s")
        u = u.replace("minutes", "min").replace("minute", "min")
        u = u.replace("hours", "h").replace("hour", "h")
        u = u.replace("years", "y").replace("year", "y")
        if u in _UNIT_TO_SECONDS:
            return float(value) * _UNIT_TO_SECONDS[u]
        return None

    # Numeric without unit -> assume seconds
    if isinstance(value, (int, float)) and not unit:
        return float(value)

    s = str(value).strip()
    if s == "":
        return None

    # If unit supplied separately, just parse number part
    if unit:
        m = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", s)
        if not m:
            return None
        return parse_halflife_to_seconds(float(m.group(0)), unit)

    # Parse "num unit" in one string
    m = re.match(r"^\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*([A-Za-z]+)\s*$", s)
    if m:
        num = float(m.group(1))
        u = m.group(2).lower()
        u = u.replace("sec", "s").replace("min", "min").replace("hr", "h").replace("yr", "y")
        if u in _UNIT_TO_SECONDS:
            return num * _UNIT_TO_SECONDS[u]
        return None

    # As a last resort, if it looks numeric, assume seconds
    try:
        return float(s)
    except Exception:
        return None