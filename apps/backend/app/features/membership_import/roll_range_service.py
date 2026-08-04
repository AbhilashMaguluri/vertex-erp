"""Roll number range expansion — isolated, reusable utility.

Delegates to the existing ``app.services.roll_number`` package for pattern
recognition and generation.  This module exposes a single, testable
``expand_range`` function that the import service calls.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from app.core.exceptions import ValidationError
from app.services.roll_number.generator import generate_roll_number_range, normalise_cell


def expand_range(
    start_roll: str,
    end_roll: str,
    *,
    institution_code: Optional[str] = None,
    max_count: int = 500,
) -> List[str]:
    """Expand a start/end roll-number pair into every roll in between.

    Returns a sorted list of normalised roll-number strings, e.g.::

        expand_range("23BQ1A5401", "23BQ1A5410")
        # -> ["23BQ1A5401", "23BQ1A5402", ..., "23BQ1A5410"]

    Raises ``ValidationError`` if the range is unparseable or too large.
    """
    cleaned_start = normalise_cell(start_roll)
    cleaned_end = normalise_cell(end_roll)

    if not cleaned_start:
        raise ValidationError(f"Start roll number is empty or unreadable: '{start_roll}'")
    if not cleaned_end:
        raise ValidationError(f"End roll number is empty or unreadable: '{end_roll}'")

    try:
        rolls = generate_roll_number_range(
            cleaned_start,
            cleaned_end,
            institution_code=institution_code,
            max_count=max_count,
        )
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(
            f"Could not expand range {start_roll} → {end_roll}: {exc}"
        ) from exc

    if not rolls:
        raise ValidationError(
            f"Range {start_roll} → {end_roll} produced zero roll numbers."
        )

    return rolls


def validate_roll_number_format(roll: str) -> Optional[str]:
    """Return an error message if the roll number format is invalid, else None."""
    cleaned = re.sub(r"[^A-Z0-9]", "", roll.upper())
    if len(cleaned) < 6:
        return f"Roll number '{roll}' is too short (minimum 6 characters)."
    if not re.search(r"\d", cleaned):
        return f"Roll number '{roll}' contains no digits."
    return None


def compare_roll_numbers(start: str, end: str) -> bool:
    """Return True if start <= end in roll-number order.

    Compares the numeric tail; if both share the same prefix the start's
    tail must not exceed the end's tail.
    """
    cleaned_start = re.sub(r"[^A-Z0-9]", "", start.upper())
    cleaned_end = re.sub(r"[^A-Z0-9]", "", end.upper())

    # Extract numeric tails
    start_match = re.search(r"(\d+)$", cleaned_start)
    end_match = re.search(r"(\d+)$", cleaned_end)

    if not start_match or not end_match:
        return True  # Can't compare; let the generator decide

    start_num = int(start_match.group(1))
    end_num = int(end_match.group(1))

    # Extract prefixes
    start_prefix = cleaned_start[: start_match.start()]
    end_prefix = cleaned_end[: end_match.start()]

    # If end is just a suffix (shorter), it inherits the start prefix
    if len(cleaned_end) < len(cleaned_start) and not end_prefix:
        return start_num <= end_num

    if start_prefix == end_prefix:
        return start_num <= end_num

    return True  # Different prefixes — let the generator decide
