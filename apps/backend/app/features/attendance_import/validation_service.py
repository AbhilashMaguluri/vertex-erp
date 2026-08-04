"""Validation service for the two-column attendance import format.

Validates structure (header columns) and individual rows for:
- Required cells
- Attendance status normalization (Present/Absent/OD/ML -> PRESENT/ABSENT/ON_DUTY/MEDICAL_LEAVE)
- Roll number format
- Duplicate roll numbers in file
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from app.features.attendance_import.roll_range_service import (
    normalise_roll_number,
    validate_roll_number_format,
)
from app.features.attendance_import.schemas import (
    NormalizedAttendanceEntry,
    ParsedAttendanceRow,
    ValidationErrorRow,
)


EXPECTED_COLUMN_ALIASES = {
    "student_roll": {
        "student roll number", "roll number", "roll no", "rollno",
        "student roll", "registration number", "regd no", "roll_number",
        "student_roll_number", "roll", "ht no", "hall ticket number",
    },
    "attendance_status": {
        "attendance status", "status", "attendance", "attendence status",
        "attendence", "present/absent", "p/a", "attendance_status",
    },
}

STATUS_NORMALIZATION_MAP = {
    "PRESENT": "PRESENT",
    "P": "PRESENT",
    "1": "PRESENT",
    "TRUE": "PRESENT",
    "YES": "PRESENT",
    "Y": "PRESENT",

    "ABSENT": "ABSENT",
    "A": "ABSENT",
    "0": "ABSENT",
    "FALSE": "ABSENT",
    "NO": "ABSENT",
    "N": "ABSENT",

    "ON DUTY": "ON_DUTY",
    "ON_DUTY": "ON_DUTY",
    "OD": "ON_DUTY",
    "DUTY": "ON_DUTY",

    "MEDICAL LEAVE": "MEDICAL_LEAVE",
    "MEDICAL_LEAVE": "MEDICAL_LEAVE",
    "ML": "MEDICAL_LEAVE",
    "MEDICAL": "MEDICAL_LEAVE",
    "LEAVE": "MEDICAL_LEAVE",
}


def validate_structure(headers: List[str]) -> Tuple[Dict[str, int], List[str]]:
    """Validate that the Excel contains the expected columns."""
    normalised = [h.strip().lower() for h in headers]
    column_map: Dict[str, int] = {}
    errors: List[str] = []

    for canonical, aliases in EXPECTED_COLUMN_ALIASES.items():
        found = False
        for idx, header in enumerate(normalised):
            if header in aliases:
                column_map[canonical] = idx
                found = True
                break
        if not found:
            errors.append(f"Required column '{canonical.replace('_', ' ').title()}' is missing from header row.")

    return column_map, errors


def normalize_status(raw: str) -> Optional[str]:
    """Normalize raw attendance status string to standard status enum value."""
    if not raw or not raw.strip():
        return None
    cleaned = raw.strip().upper()
    return STATUS_NORMALIZATION_MAP.get(cleaned)


def validate_rows(
    rows: List[ParsedAttendanceRow],
) -> Tuple[List[NormalizedAttendanceEntry], List[ValidationErrorRow], List[str]]:
    """Validate every row and return (normalized_entries, validation_errors, warnings)."""
    normalized_entries: List[NormalizedAttendanceEntry] = []
    validation_errors: List[ValidationErrorRow] = []
    warnings: List[str] = []
    seen_rolls: Set[str] = set()

    for row in rows:
        # Check empty roll
        if not row.student_roll.strip():
            _add_error(row, validation_errors, "", "Student roll number is empty.",
                       "Enter a valid roll number like 23BQ1A5401.")
            continue

        roll = normalise_roll_number(row.student_roll)

        # Check empty status
        if not row.raw_status.strip():
            _add_error(row, validation_errors, roll, "Attendance status is empty.",
                       "Enter Present, Absent, P, A, OD, or ML.")
            continue

        # Check roll format
        roll_err = validate_roll_number_format(roll)
        if roll_err:
            _add_error(row, validation_errors, roll, roll_err,
                       "Check roll number format (e.g. 23BQ1A5401).")
            continue

        # Check status normalization
        norm_status = normalize_status(row.raw_status)
        if not norm_status:
            _add_error(
                row, validation_errors, roll,
                f"Invalid attendance status '{row.raw_status}'.",
                "Use 'Present', 'Absent', 'P', 'A', 'On Duty', 'OD', 'Medical Leave', or 'ML'."
            )
            continue

        # Check duplicate roll in file
        if roll in seen_rolls:
            warnings.append(f"Row {row.row_number}: Duplicate roll number '{roll}' in file — imported once.")
            continue
        seen_rolls.add(roll)

        normalized_entries.append(NormalizedAttendanceEntry(
            roll_number=roll,
            source_row=row.row_number,
            normalized_status=norm_status,
        ))

    return normalized_entries, validation_errors, warnings


def _add_error(
    row: ParsedAttendanceRow,
    errors: List[ValidationErrorRow],
    roll: str,
    error: str,
    suggested_fix: str,
) -> None:
    row.errors.append(error)
    errors.append(ValidationErrorRow(
        row=row.row_number,
        roll_number=roll,
        error=error,
        suggested_fix=suggested_fix,
    ))
