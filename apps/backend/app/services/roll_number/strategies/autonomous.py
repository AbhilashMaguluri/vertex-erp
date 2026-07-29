"""VVIT Autonomous Roll Number Strategy."""
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

_AUTONOMOUS_ROLL_RE = re.compile(
    r"^(\d{2})([A-Z]{2})(\d[A-Z])(\d{2})([A-Z0-9]{2})$"
)

_TENS_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_UNITS_CHARS = "0123456789"


class VVITAutonomousStrategy(RollNumberStrategy):
    """Strategy for VVIT Autonomous roll numbers with alphanumeric serial progression."""

    @property
    def name(self) -> str:
        return "vvit_autonomous"

    def matches(self, roll_number: str) -> bool:
        cleaned = re.sub(r"[^A-Z0-9]", "", (roll_number or "").upper())
        match = _AUTONOMOUS_ROLL_RE.match(cleaned)
        if not match:
            return False
        program = match.group(3)
        return program in ("1A", "5A", "1E", "1D", "1F")

    def parse(self, roll_number: str) -> Optional[RollParts]:
        cleaned = re.sub(r"[^A-Z0-9]", "", (roll_number or "").upper())
        match = _AUTONOMOUS_ROLL_RE.match(cleaned)
        if not match:
            return None

        year, college, program, branch, serial_tail = match.groups()
        academic_prefix = f"{year}{college}{program}"
        full_serial = f"{branch}{serial_tail}"

        return RollParts(
            raw=roll_number,
            cleaned=cleaned,
            academic_prefix=academic_prefix,
            batch_year_prefix=year,
            college_code=college,
            program_code=program,
            branch_code=branch,
            serial_tail=serial_tail,
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
            institution_type="VVIT Autonomous",
        )

    def tail_to_index(self, tail: str) -> int:
        if len(tail) != 2:
            raise ValidationError(f"Invalid serial tail length: '{tail}'")
        t_char, u_char = tail[0].upper(), tail[1].upper()
        if t_char not in _TENS_CHARS or u_char not in _UNITS_CHARS:
            raise ValidationError(f"Invalid serial tail characters in '{tail}'")

        tens_idx = _TENS_CHARS.index(t_char)
        units_idx = _UNITS_CHARS.index(u_char)
        return tens_idx * 10 + units_idx

    def index_to_tail(self, index: int) -> str:
        tens_idx = index // 10
        units_idx = index % 10
        if tens_idx >= len(_TENS_CHARS):
            raise ValidationError(f"Serial index {index} exceeds maximum supported capacity")
        return f"{_TENS_CHARS[tens_idx]}{_UNITS_CHARS[units_idx]}"

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

        # For alphanumeric serials (containing letters like A0, B6), branch codes must match.
        # For purely numeric 4-digit serials (e.g. 5498 to 5502), numeric range expansion is permitted.
        is_alphanumeric_range = not (start_parts.full_serial.isdigit() and end_parts.full_serial.isdigit())
        if not allow_cross_dept and is_alphanumeric_range:
            if start_parts.branch_code != end_parts.branch_code:
                raise ValidationError(
                    f"Department mismatch in range endpoints: '{start_parts.branch_code}' vs '{end_parts.branch_code}'"
                )

    def generate_range(
        self,
        start_roll: str,
        raw_end: str,
        max_count: int = 500,
    ) -> List[str]:
        start_parts = self.parse(start_roll)
        if not start_parts:
            raise ValidationError(f"'{start_roll}' is not a valid VVIT Autonomous roll number")

        cleaned_end = re.sub(r"[^A-Z0-9]", "", (raw_end or "").upper())
        if not cleaned_end:
            raise ValidationError(f"Could not read '{raw_end}' as the end of a range")

        # 1. Full roll end endpoint (e.g., 23BQ1A54A7 or 23BQ1A5502 or 23BQ1A9999)
        if _AUTONOMOUS_ROLL_RE.match(cleaned_end):
            end_parts = self.parse(cleaned_end)
            if end_parts is None:
                raise ValidationError(f"could not read '{raw_end}' as the end of a range")

            self.validate_endpoints(start_parts, end_parts)

            # Check if both start and end serials are purely numeric 4-digit numbers (e.g. 5498 to 5502 or 5401 to 9999)
            if start_parts.full_serial.isdigit() and end_parts.full_serial.isdigit():
                start_num = int(start_parts.full_serial)
                end_num = int(end_parts.full_serial)
                if end_num < start_num:
                    raise ValidationError(
                        f"the range ends ({end_num}) before it starts ({start_num})"
                    )
                count = end_num - start_num + 1
                if count > max_count:
                    raise ValidationError(
                        f"'{start_roll}' expands to {count} roll numbers, above the {max_count} per-range limit — split it across rows if this is intentional"
                    )
                width = len(start_parts.full_serial)
                return [f"{start_parts.academic_prefix}{n:0{width}d}" for n in range(start_num, end_num + 1)]

            # Otherwise, use Autonomous alphanumeric progression on 2-char tail
            start_idx = self.tail_to_index(start_parts.serial_tail)
            end_idx = self.tail_to_index(end_parts.serial_tail)

            if end_idx < start_idx:
                raise ValidationError(
                    f"the range ends ({end_idx}) before it starts ({start_idx})"
                )

            count = end_idx - start_idx + 1
            if count > max_count:
                raise ValidationError(
                    f"'{start_roll}' expands to {count} roll numbers, above the {max_count} per-range limit — split it across rows if this is intentional"
                )

            return [
                f"{start_parts.academic_prefix}{start_parts.branch_code}{self.index_to_tail(idx)}"
                for idx in range(start_idx, end_idx + 1)
            ]

        # 2. Branch + Serial match (e.g. 54A7 or 5410 or 5502)
        if re.match(r"^\d{2}[A-Z0-9]{2}$", cleaned_end):
            full_end = f"{start_parts.academic_prefix}{cleaned_end}"
            return self.generate_range(start_roll, full_end, max_count=max_count)

        # 3. Numeric shorthand (e.g. 10 or 5410 or 9999)
        if cleaned_end.isdigit():
            width = len(cleaned_end)
            if width < len(start_parts.full_serial):
                start_digits = start_parts.full_serial
                merged = start_digits[: len(start_digits) - width] + cleaned_end
                full_end = f"{start_parts.academic_prefix}{merged}"
            elif width == len(start_parts.full_serial):
                full_end = f"{start_parts.academic_prefix}{cleaned_end}"
            else:
                raise ValidationError(f"Could not read '{raw_end}' as the end of range starting with '{start_parts.cleaned}'")
            return self.generate_range(start_roll, full_end, max_count=max_count)

        # 4. Alphanumeric tail match (e.g. A7 or B6)
        if re.match(r"^[A-Z0-9]{1,2}$", cleaned_end):
            padded_tail = cleaned_end.zfill(2)
            full_end = f"{start_parts.academic_prefix}{start_parts.branch_code}{padded_tail}"
            return self.generate_range(start_roll, full_end, max_count=max_count)

        raise ValidationError(f"could not read '{raw_end}' as the end of a range")
