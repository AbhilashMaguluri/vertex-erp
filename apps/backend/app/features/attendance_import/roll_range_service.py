"""Roll range expansion and validation service for Attendance Import.

Delegates to shared roll number utility.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from app.shared.utils.roll_number import (
    normalise_roll_number,
    parse_and_expand_roll_range,
    validate_roll_number_format,
)

# Alias for backwards compatibility with feature service
expand_range = parse_and_expand_roll_range

__all__ = [
    "normalise_roll_number",
    "validate_roll_number_format",
    "parse_and_expand_roll_range",
    "expand_range",
]
