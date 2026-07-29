"""VVIT University Roll Number Strategy."""
from __future__ import annotations

import re
from typing import List, Optional

from app.core.exceptions import ValidationError
from app.services.roll_number.strategies.base import (
    RollMetadata,
    RollNumberStrategy,
    RollParts,
)

JNTUK_BRANCH_CODES = {
    "01": "CE",
    "02": "EEE",
    "03": "ME",
    "04": "ECE",
    "05": "CSE",
    "12": "IT",
    "54": "AI&DS",
}

_UNIVERSITY_ROLL_RE = re.compile(
    r"^(\d{2})([A-Z]{2})(\d[A-Z])(\d{2})(\d+)$"
)


class VVITUniversityStrategy(RollNumberStrategy):
    """Strategy for VVIT University roll numbers using standard decimal numeric progression."""

    @property
    def name(self) -> str:
        return "vvit_university"

    def matches(self, roll_number: str) -> bool:
        cleaned = re.sub(r"[^A-Z0-9]", "", (roll_number or "").upper())
        match = _UNIVERSITY_ROLL_RE.match(cleaned)
        return bool(match)

    def parse(self, roll_number: str) -> Optional[RollParts]:
        cleaned = re.sub(r"[^A-Z0-9]", "", (roll_number or "").upper())
        match = _UNIVERSITY_ROLL_RE.match(cleaned)
        if not match:
            return None

        year, college, program, branch, digits = match.groups()
        academic_prefix = f"{year}{college}{program}"
        full_serial = f"{branch}{digits}"

        return RollParts(
            raw=roll_number,
            cleaned=cleaned,
            academic_prefix=academic_prefix,
            batch_year_prefix=year,
            college_code=college,
            program_code=program,
            branch_code=branch,
            serial_tail=digits,
            full_serial=full_serial,
            strategy_name=self.name,
        )

    def describe(self, roll_number: str) -> RollMetadata:
        parts = self.parse(roll_number)
        if not parts:
            return RollMetadata()

        batch_year = 2000 + int(parts.batch_year_prefix)
        is_lateral = parts.program_code == "5A"
        branch_hint = JNTUK_BRANCH_CODES.get(parts.branch_code)

        return RollMetadata(
            batch_year=batch_year,
            branch_code=parts.branch_code,
            branch_hint=branch_hint,
            college_code=parts.college_code,
            program_code=parts.program_code,
            is_lateral_entry=is_lateral,
            institution_type="VVIT University",
        )

    def validate_endpoints(
        self,
        start_parts: RollParts,
        end_parts: RollParts,
        allow_cross_batch: bool = False,
        allow_cross_dept: bool = False,
    ) -> None:
        if not allow_cross_batch:
            if start_parts.academic_prefix != end_parts.academic_prefix:
                raise ValidationError(
                    f"range endpoints belong to different series "
                    f"('{start_parts.academic_prefix}…' and '{end_parts.academic_prefix}…')"
                )

        if start_parts.college_code != end_parts.college_code:
            raise ValidationError(
                f"range endpoints belong to different series "
                f"('{start_parts.college_code}' and '{end_parts.college_code}')"
            )

    def generate_range(
        self,
        start_roll: str,
        raw_end: str,
        max_count: int = 500,
    ) -> List[str]:
        start_parts = self.parse(start_roll)
        if not start_parts:
            raise ValidationError(f"'{start_roll}' is not a valid VVIT University roll number")

        cleaned_end = re.sub(r"[^A-Z0-9]", "", (raw_end or "").upper())

        # Full roll end
        if _UNIVERSITY_ROLL_RE.match(cleaned_end):
            end_parts = self.parse(cleaned_end)
            if end_parts is None:
                raise ValidationError(f"could not read '{raw_end}' as the end of a range")
            self.validate_endpoints(start_parts, end_parts)

            start_val = int(start_parts.full_serial)
            end_val = int(end_parts.full_serial)
            if end_val < start_val:
                raise ValidationError(
                    f"the range ends ({end_val}) before it starts ({start_val})"
                )
            count = end_val - start_val + 1
            if count > max_count:
                raise ValidationError(
                    f"expands to {count} roll numbers, above the {max_count} per-range limit — split it across rows if this is intentional"
                )
            width = len(start_parts.full_serial)
            return [f"{start_parts.academic_prefix}{n:0{width}d}" for n in range(start_val, end_val + 1)]

        # Branch + Serial (e.g., 5412) or numeric tail (e.g., 12 or 5412)
        if cleaned_end.isdigit():
            width = len(cleaned_end)
            if width < len(start_parts.full_serial):
                start_digits = start_parts.full_serial
                merged = start_digits[: len(start_digits) - width] + cleaned_end
                full_end = f"{start_parts.academic_prefix}{merged}"
            elif width == len(start_parts.full_serial):
                full_end = f"{start_parts.academic_prefix}{cleaned_end}"
            else:
                raise ValidationError(f"could not read '{raw_end}' as the end of a range")
            return self.generate_range(start_roll, full_end, max_count=max_count)

        raise ValidationError(f"could not read '{raw_end}' as the end of a range")
