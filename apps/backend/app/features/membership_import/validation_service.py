"""Validation service for the three-column membership import format.

Validates structure (column presence) and every individual row for:
- Required cell presence
- Roll number format
- Email format
- Start > End roll number
- Duplicate rows
- Invalid ranges
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from app.features.membership_import.schemas import (
    ParsedMembershipRow,
    ValidationErrorRow,
)


# Expected column headers (case-insensitive, normalised)
EXPECTED_COLUMNS = {"start roll number", "end roll number", "counselor email"}
EXPECTED_COLUMN_ALIASES = {
    "start roll number": {"start roll number", "start roll no", "start rollno", "from roll",
                          "from roll number", "start roll", "start_roll_number"},
    "end roll number": {"end roll number", "end roll no", "end rollno", "to roll",
                        "to roll number", "end roll", "end_roll_number"},
    "counselor email": {"counselor email", "counsellor email", "counselor mail",
                        "counsellor mail", "faculty email", "mentor email",
                        "counselor_email", "counsellor_email"},
}

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)

SUPPORTED_DOMAINS = {"vvit.net", "vvitu.ac.in"}


def validate_structure(headers: List[str]) -> Tuple[Dict[str, int], List[str]]:
    """Validate that the Excel has the expected columns.

    Returns (column_map, errors) where column_map maps canonical field
    name → column index.
    """
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
            errors.append(f"Required column '{canonical}' is missing from the header row.")

    return column_map, errors


def validate_email_format(email: str) -> Optional[str]:
    """Return an error if the email is not valid."""
    if not email or not email.strip():
        return "Counselor email is empty."
    cleaned = email.strip().lower()
    if not _EMAIL_RE.match(cleaned):
        return f"'{email}' is not a valid email address."
    return None


def validate_email_domain(email: str) -> Optional[str]:
    """Check the email domain is one of the supported institution domains."""
    cleaned = email.strip().lower()
    domain = cleaned.split("@")[-1] if "@" in cleaned else ""
    if domain not in SUPPORTED_DOMAINS:
        return f"Email domain '@{domain}' is not supported. Use @vvit.net or @vvitu.ac.in."
    return None


def validate_rows(
    rows: List[ParsedMembershipRow],
) -> Tuple[List[ParsedMembershipRow], List[ValidationErrorRow]]:
    """Validate every row and return (validated_rows, error_report_rows).

    Errors are attached to rows in-place AND collected in a flat error
    report suitable for Excel export.
    """
    validation_errors: List[ValidationErrorRow] = []
    seen_ranges: Set[Tuple[str, str, str]] = set()
    seen_counselor_ranges: Dict[str, List[int]] = {}

    for row in rows:
        # --- Empty cells --------------------------------------------------
        if not row.start_roll.strip():
            _add_error(row, validation_errors, "Start roll number is empty.",
                       "The start roll number cell is blank.",
                       "Enter a valid start roll number like 23BQ1A5401.")
        if not row.end_roll.strip():
            _add_error(row, validation_errors, "End roll number is empty.",
                       "The end roll number cell is blank.",
                       "Enter a valid end roll number like 23BQ1A5410.")
        if not row.counselor_email.strip():
            _add_error(row, validation_errors, "Counselor email is empty.",
                       "The counselor email cell is blank.",
                       "Enter a valid counselor email like name@vvit.net.")

        if row.errors:
            continue  # Skip further checks if basics are missing

        # --- Roll number format -------------------------------------------
        start_err = _validate_roll_format(row.start_roll)
        if start_err:
            _add_error(row, validation_errors, f"Invalid start roll: {start_err}",
                       f"'{row.start_roll}' does not match expected roll number format.",
                       "Use format like 23BQ1A5401.")

        end_err = _validate_roll_format(row.end_roll)
        if end_err:
            _add_error(row, validation_errors, f"Invalid end roll: {end_err}",
                       f"'{row.end_roll}' does not match expected roll number format.",
                       "Use format like 23BQ1A5410.")

        # --- Email format -------------------------------------------------
        email_err = validate_email_format(row.counselor_email)
        if email_err:
            _add_error(row, validation_errors, email_err,
                       f"'{row.counselor_email}' is not a valid email.",
                       "Use format like name@vvit.net.")
            continue

        domain_err = validate_email_domain(row.counselor_email)
        if domain_err:
            _add_error(row, validation_errors, domain_err,
                       f"Email domain is not supported.",
                       "Use @vvit.net or @vvitu.ac.in.")

        # --- Start > End -------------------------------------------------
        if not row.errors:
            from app.features.membership_import.roll_range_service import compare_roll_numbers
            if not compare_roll_numbers(row.start_roll, row.end_roll):
                _add_error(row, validation_errors,
                           f"Start roll '{row.start_roll}' is greater than end roll '{row.end_roll}'.",
                           "The start roll number comes after the end roll number in sequence.",
                           "Swap the start and end roll numbers.")

        # --- Duplicate rows -----------------------------------------------
        key = (
            row.start_roll.strip().upper(),
            row.end_roll.strip().upper(),
            row.counselor_email.strip().lower(),
        )
        if key in seen_ranges:
            _add_error(row, validation_errors,
                       f"Duplicate row: {row.start_roll}–{row.end_roll} for {row.counselor_email}.",
                       "This exact range and counselor combination appears more than once.",
                       "Remove the duplicate row.")
        seen_ranges.add(key)

        # Track counselor email occurrences for info
        email_lower = row.counselor_email.strip().lower()
        seen_counselor_ranges.setdefault(email_lower, []).append(row.row_number)

    return rows, validation_errors


def _validate_roll_format(roll: str) -> Optional[str]:
    """Basic format check for a roll number."""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", roll.strip())
    if len(cleaned) < 6:
        return f"Too short ({len(cleaned)} chars, minimum 6)."
    if not re.search(r"\d", cleaned):
        return "Contains no digits."
    if not re.search(r"[A-Za-z]", cleaned):
        return "Contains no letters."
    return None


def _add_error(
    row: ParsedMembershipRow,
    errors: List[ValidationErrorRow],
    error: str,
    description: str,
    suggested_fix: str,
) -> None:
    """Append an error to both the row and the flat error list."""
    row.errors.append(error)
    errors.append(ValidationErrorRow(
        row=row.row_number,
        error=error,
        description=description,
        suggested_fix=suggested_fix,
    ))
