"""Roll number range generator and spreadsheet cell expansion service."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.core.exceptions import ValidationError
from app.services.roll_number.base import default_resolver
from app.services.roll_number.validators import MAX_ROLLS_PER_RANGE, MAX_ROLLS_PER_FILE

_DASH_CHARS = "‐‑‒–—―−˗－~→➡⇒"
_CONNECTOR_RE = re.compile(
    r"\s*\b(?:up\s*to|upto|through|thru|till|until|to)\b\s*", re.IGNORECASE
)
_DOTDOT_RE = re.compile(r"\.{2,}")
_SEPARATOR_RE = re.compile(r"[,;&/+\n\r\t]+|\band\b", re.IGNORECASE)


@dataclass
class ExpansionResult:
    roll_numbers: List[str] = field(default_factory=list)
    segments: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.roll_numbers) and not self.errors


def normalise_cell(value: str) -> str:
    """Uppercase, collapse whitespace and reduce connectors to a single '-'."""
    text = (value or "").strip().upper()
    if not text:
        return ""
    # Normalize arrows and multi-char dash representations
    text = text.replace("->", "-").replace("=>", "-")
    for ch in _DASH_CHARS:
        text = text.replace(ch, "-")
    text = _DOTDOT_RE.sub("-", text)
    text = _CONNECTOR_RE.sub("-", text)
    text = re.sub(r"\s*-\s*", "-", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def generate_roll_number_range(
    start_roll: str,
    raw_end: str,
    institution_code: Optional[str] = None,
    max_count: int = MAX_ROLLS_PER_RANGE,
) -> List[str]:
    """Generate consecutive roll numbers from start_roll to raw_end."""
    cleaned_start = re.sub(r"[^A-Z0-9]", "", (start_roll or "").upper())
    strategy = default_resolver.resolve(cleaned_start, institution_code=institution_code)
    return strategy.generate_range(cleaned_start, raw_end, max_count=max_count)


def _expand_segment(
    segment: str,
    institution_code: Optional[str] = None,
) -> ExpansionResult:
    result = ExpansionResult()
    cleaned_seg = segment.strip()
    if not cleaned_seg:
        return result

    if "-" not in cleaned_seg:
        cleaned_roll = re.sub(r"[^A-Z0-9]", "", cleaned_seg.upper())
        try:
            strategy = default_resolver.resolve(cleaned_roll, institution_code=institution_code)
            parts = strategy.parse(cleaned_roll)
            if parts is None:
                result.errors.append(f"'{segment}' is not a recognisable roll number")
                return result
            result.roll_numbers.append(parts.cleaned)
            result.segments.append(parts.cleaned)
        except Exception:
            result.errors.append(f"'{segment}' is not a recognisable roll number")
        return result

    left_raw, _, right_raw = cleaned_seg.partition("-")
    cleaned_left = re.sub(r"[^A-Z0-9]", "", left_raw.upper())
    if not cleaned_left:
        result.errors.append(f"could not read '{left_raw}' as the start of a range")
        return result

    try:
        rolls = generate_roll_number_range(
            cleaned_left,
            right_raw,
            institution_code=institution_code,
            max_count=MAX_ROLLS_PER_RANGE,
        )
        count = len(rolls)
        result.roll_numbers.extend(rolls)
        result.segments.append(
            f"{rolls[0]} → {rolls[-1]} ({count} student{'s' if count != 1 else ''})"
            if count > 1
            else rolls[0]
        )
    except ValidationError as exc:
        result.errors.append(f"in '{segment}': {exc.detail if hasattr(exc, 'detail') else str(exc)}")
    except Exception as exc:
        result.errors.append(f"in '{segment}': {str(exc)}")

    return result


def expand_roll_cell(
    value: str,
    institution_code: Optional[str] = None,
) -> ExpansionResult:
    """Expand one spreadsheet cell into every roll number it denotes."""
    result = ExpansionResult()
    text = normalise_cell(value)
    if not text:
        result.errors.append("no roll number in this row")
        return result

    segments = [s.strip() for s in _SEPARATOR_RE.split(text) if s and s.strip()]
    if not segments:
        result.errors.append(f"'{value}' contains no roll numbers")
        return result

    seen: set[str] = set()
    for segment in segments:
        for part in segment.split(" "):
            part = part.strip()
            if not part:
                continue
            part_result = _expand_segment(part, institution_code=institution_code)
            result.errors.extend(part_result.errors)
            result.warnings.extend(part_result.warnings)
            result.segments.extend(part_result.segments)
            for roll in part_result.roll_numbers:
                if roll in seen:
                    result.warnings.append(f"{roll} appears more than once in this cell")
                    continue
                seen.add(roll)
                result.roll_numbers.append(roll)

    if not result.roll_numbers and not result.errors:
        result.errors.append(f"'{value}' contains no roll numbers")
    return result
