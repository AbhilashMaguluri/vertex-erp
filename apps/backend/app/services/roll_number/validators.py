"""Validation functions for roll numbers and roll number range endpoints."""
from __future__ import annotations

import re
from typing import Optional

from app.core.exceptions import ValidationError
from app.services.roll_number.base import default_resolver
from app.services.roll_number.strategies.base import RollParts

MAX_ROLLS_PER_RANGE = 500
MAX_ROLLS_PER_FILE = 5000


def validate_single_roll(
    roll_number: str,
    institution_code: Optional[str] = None,
) -> RollParts:
    """Validate that a single string is a valid roll number."""
    cleaned = re.sub(r"[^A-Z0-9]", "", (roll_number or "").upper())
    if not cleaned:
        raise ValidationError("Roll number cannot be empty")

    strategy = default_resolver.resolve(cleaned, institution_code=institution_code)
    parts = strategy.parse(cleaned)
    if parts is None:
        raise ValidationError(f"'{roll_number}' is not a valid roll number format")
    return parts


def validate_range_endpoints(
    start_roll: str,
    end_roll_raw: str,
    institution_code: Optional[str] = None,
    allow_cross_batch: bool = False,
    allow_cross_dept: bool = False,
) -> None:
    """Validate range endpoints for compatibility and correct sequence ordering."""
    cleaned_start = re.sub(r"[^A-Z0-9]", "", (start_roll or "").upper())
    if not cleaned_start:
        raise ValidationError("Start roll number cannot be empty")

    strategy = default_resolver.resolve(cleaned_start, institution_code=institution_code)
    start_parts = strategy.parse(cleaned_start)
    if start_parts is None:
        raise ValidationError(f"'{start_roll}' is not a valid start roll number")

    # Delegate endpoint validation to strategy
    if hasattr(strategy, "resolve_end"):
        end_parts = strategy.resolve_end(start_parts, end_roll_raw)
        if isinstance(end_parts, RollParts):
            strategy.validate_endpoints(
                start_parts,
                end_parts,
                allow_cross_batch=allow_cross_batch,
                allow_cross_dept=allow_cross_dept,
            )
