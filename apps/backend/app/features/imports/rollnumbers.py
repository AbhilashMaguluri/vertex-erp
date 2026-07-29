"""Roll-number range parsing compatibility layer.

Delegates all parsing, range generation, and validation to the central
`app.services.roll_number` service while maintaining backwards compatibility
for existing import paths.
"""
from __future__ import annotations

import re
from typing import Optional

from app.services.roll_number import (
    MAX_ROLLS_PER_FILE,
    MAX_ROLLS_PER_RANGE,
    ExpansionResult,
    RollMetadata,
    describe_roll,
    expand_roll_cell,
    normalise_cell,
    parse_roll,
)
from app.services.roll_number.strategies.base import RollParts


class RollToken:
    """Backwards-compatible wrapper for token decomposition."""

    def __init__(self, prefix: str, number: int, width: int):
        self.prefix = prefix
        self.number = number
        self.width = width

    @property
    def text(self) -> str:
        return f"{self.prefix}{self.number:0{self.width}d}"


def parse_token(raw: str) -> Optional[RollToken]:
    """Legacy token parser wrapper."""
    parts = parse_roll(raw)
    if parts is None:
        return None
    # For legacy token compatibility:
    prefix = f"{parts.academic_prefix}{parts.branch_code}"
    # Try converting tail to int if numeric
    if parts.serial_tail.isdigit():
        num = int(parts.serial_tail)
        width = len(parts.serial_tail)
    else:
        num = 0
        width = len(parts.serial_tail)
    return RollToken(prefix=prefix, number=num, width=width)


__all__ = [
    "MAX_ROLLS_PER_RANGE",
    "MAX_ROLLS_PER_FILE",
    "RollMetadata",
    "ExpansionResult",
    "RollToken",
    "normalise_cell",
    "describe_roll",
    "expand_roll_cell",
    "parse_token",
]
