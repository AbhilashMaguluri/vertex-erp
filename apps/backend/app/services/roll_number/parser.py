"""Roll number parsing and metadata extraction service."""
from __future__ import annotations

import re
from typing import Optional

from app.services.roll_number.base import default_resolver
from app.services.roll_number.strategies.base import RollMetadata, RollParts


def parse_roll(
    roll_number: str,
    institution_code: Optional[str] = None,
    strategy_name: Optional[str] = None,
) -> Optional[RollParts]:
    """Parse a roll number into structured RollParts using the resolved strategy."""
    cleaned = re.sub(r"[^A-Z0-9]", "", (roll_number or "").upper())
    if not cleaned:
        return None

    strategy = default_resolver.resolve(
        cleaned,
        institution_code=institution_code,
        strategy_name=strategy_name,
    )
    return strategy.parse(cleaned)


def describe_roll(
    roll_number: str,
    institution_code: Optional[str] = None,
) -> RollMetadata:
    """Extract academic metadata from a roll number string."""
    cleaned = re.sub(r"[^A-Z0-9]", "", (roll_number or "").upper())
    if not cleaned:
        return RollMetadata()

    try:
        strategy = default_resolver.resolve(
            cleaned,
            institution_code=institution_code,
        )
        meta = strategy.describe(cleaned)
        if meta.batch_year is not None:
            return meta
    except Exception:
        pass

    # Generic fallback for off-pattern roll numbers (e.g., 21XYZ999)
    meta = RollMetadata()
    if len(cleaned) >= 2 and cleaned[:2].isdigit():
        meta.batch_year = 2000 + int(cleaned[:2])
    return meta
