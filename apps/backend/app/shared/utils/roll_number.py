"""Centralized shared utility for roll number parsing, format validation, range expansion, and normalization."""
import re
from typing import List, Optional, Tuple


def normalise_roll_number(val: str) -> str:
    """Normalise roll number by stripping whitespace and converting to uppercase."""
    if not val:
        return ""
    return str(val).strip().upper()


def validate_roll_number_format(roll: str) -> Optional[str]:
    """Validate roll number format (e.g. 23BQ1A5401 or standard alphanumeric roll).

    Returns error message string if invalid, or None if valid.
    """
    if not roll:
        return "Roll number is empty."
    if len(roll) < 4 or len(roll) > 20:
        return f"Roll number length ({len(roll)}) must be between 4 and 20 characters."
    if not re.match(r"^[A-Z0-9\-_]+$", roll):
        return f"Roll number '{roll}' contains invalid characters."
    return None


def parse_and_expand_roll_range(
    start_roll: str,
    end_roll: Optional[str] = None,
) -> Tuple[List[str], Optional[str]]:
    """Expand a roll number range into individual roll numbers.

    Example:
        start_roll='23BQ1A5401', end_roll='23BQ1A5405'
        -> (['23BQ1A5401', '23BQ1A5402', '23BQ1A5403', '23BQ1A5404', '23BQ1A5405'], None)
    """
    start_norm = normalise_roll_number(start_roll)
    end_norm = normalise_roll_number(end_roll) if end_roll else None

    # Validate start roll
    start_err = validate_roll_number_format(start_norm)
    if start_err:
        return [], f"Start Roll Error: {start_err}"

    # Single roll case
    if not end_norm or end_norm == start_norm:
        return [start_norm], None

    # Validate end roll format
    end_err = validate_roll_number_format(end_norm)
    if end_err:
        return [], f"End Roll Error: {end_err}"

    # Extract alphanumeric prefix and numeric tail
    start_match = re.match(r"^(.*?)(0*(\d+))$", start_norm)
    end_match = re.match(r"^(.*?)(0*(\d+))$", end_norm)

    if not start_match or not end_match:
        return [], f"Cannot parse numeric sequence between '{start_norm}' and '{end_norm}'."

    start_prefix, start_num_str, start_num = start_match.group(1), start_match.group(2), int(start_match.group(3))
    end_prefix, end_num_str, end_num = end_match.group(1), end_match.group(2), int(end_match.group(3))

    if start_prefix != end_prefix:
        return [], f"Prefix mismatch between '{start_norm}' ({start_prefix}) and '{end_norm}' ({end_prefix})."

    if end_num < start_num:
        return [], f"End Roll '{end_norm}' ({end_num}) is smaller than Start Roll '{start_norm}' ({start_num})."

    diff = end_num - start_num + 1
    if diff > 1000:
        return [], f"Roll number range spans {diff} students, exceeding maximum limit of 1000 per range."

    padding = len(start_num_str)
    expanded: List[str] = []
    for num in range(start_num, end_num + 1):
        num_formatted = str(num).zfill(padding)
        expanded.append(f"{start_prefix}{num_formatted}")

    return expanded, None
