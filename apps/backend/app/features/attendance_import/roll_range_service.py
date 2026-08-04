"""Roll number normalization and format validation for attendance import."""
from __future__ import annotations

import re
from typing import Optional


def normalise_roll_number(roll: str) -> str:
    """Clean and uppercase a roll number cell string."""
    return re.sub(r"\s+", "", (roll or "").strip().upper())


def validate_roll_number_format(roll: str) -> Optional[str]:
    """Return an error message if roll number format is invalid, else None."""
    cleaned = normalise_roll_number(roll)
    if not cleaned:
        return "Roll number is empty."
    if len(cleaned) < 5:
        return f"Roll number '{roll}' is too short (minimum 5 characters)."
    if not re.search(r"\d", cleaned):
        return f"Roll number '{roll}' contains no digits."
    if not re.search(r"[A-Z]", cleaned):
        return f"Roll number '{roll}' contains no letters."
    return None
