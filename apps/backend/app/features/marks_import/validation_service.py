"""Validation service for dynamic marks import format."""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from app.shared.utils.roll_number import (
    normalise_roll_number,
    validate_roll_number_format,
)
from app.features.marks_import.models import AssessmentTemplate
from app.features.marks_import.schemas import ParsedMarksRow, ValidationErrorRow


def validate_structure(
    headers: List[str], template: AssessmentTemplate,
) -> Tuple[Dict[str, int], List[str]]:
    """Validate header row against active AssessmentTemplate."""
    normalised = [h.strip().lower() for h in headers]
    column_map: Dict[str, int] = {}
    errors: List[str] = []

    # Locate roll number column
    roll_aliases = {
        "student roll number", "roll number", "roll no", "rollno",
        "student roll", "registration number", "regd no", "roll", "ht no",
    }
    roll_col = -1
    for idx, h in enumerate(normalised):
        if h in roll_aliases:
            roll_col = idx
            break
    if roll_col < 0:
        errors.append("Required column 'Student Roll Number' is missing from header row.")
    else:
        column_map["student_roll"] = roll_col

    # Map question components
    components = template.components_json or []
    if components:
        for comp in components:
            key = str(comp.get("key") or comp.get("label") or "").strip().lower()
            found = False
            for idx, h in enumerate(normalised):
                if h == key or h == f"q_{key}" or h == f"question {key}":
                    column_map[comp["key"]] = idx
                    found = True
                    break
            if not found:
                errors.append(f"Required question column '{comp['key']}' is missing from header row.")
    else:
        # Single marks column
        marks_aliases = {"marks", "marks obtained", "score", "total marks", "total"}
        marks_col = -1
        for idx, h in enumerate(normalised):
            if h in marks_aliases:
                marks_col = idx
                break
        if marks_col < 0:
            errors.append("Required column 'Marks' is missing from header row.")
        else:
            column_map["marks"] = marks_col

    return column_map, errors


def validate_rows(
    rows: List[ParsedMarksRow],
    template: AssessmentTemplate,
) -> Tuple[List[ParsedMarksRow], List[ValidationErrorRow], List[str]]:
    """Validate every row against template max marks boundaries and numeric constraints."""
    components = {c["key"]: float(c["max_marks"]) for c in (template.components_json or [])}
    total_max = float(template.total_max_marks or 30.0)

    validation_errors: List[ValidationErrorRow] = []
    warnings: List[str] = []
    seen_rolls: Set[str] = set()

    for row in rows:
        if not row.student_roll.strip():
            _add_error(row, validation_errors, "", "Student roll number is empty.",
                       "Enter a valid roll number like 23BQ1A5401.")
            continue

        roll = normalise_roll_number(row.student_roll)

        # Roll format
        roll_err = validate_roll_number_format(roll)
        if roll_err:
            _add_error(row, validation_errors, roll, roll_err,
                       "Check roll number format (e.g. 23BQ1A5401).")
            continue

        # Check duplicate roll in file
        if roll in seen_rolls:
            warnings.append(f"Row {row.row_number}: Duplicate roll number '{roll}' in file — imported once.")
            continue
        seen_rolls.add(roll)

        # Question score boundary checks
        if components:
            calculated_total = 0.0
            for q_key, q_max in components.items():
                score = row.question_scores.get(q_key)
                if score is None:
                    _add_error(row, validation_errors, roll,
                               f"Score for Question '{q_key}' is missing or empty.",
                               f"Enter a numeric score between 0 and {q_max}.")
                elif score < 0:
                    _add_error(row, validation_errors, roll,
                               f"Score for Question '{q_key}' ({score}) cannot be negative.",
                               "Enter a non-negative number.")
                elif score > q_max:
                    _add_error(row, validation_errors, roll,
                               f"Score for Question '{q_key}' ({score}) exceeds maximum marks ({q_max}).",
                               f"Enter a score <= {q_max}.")
                else:
                    calculated_total += score

            row.total_marks = round(calculated_total, 2)
            if row.total_marks > total_max:
                _add_error(row, validation_errors, roll,
                           f"Calculated total marks ({row.total_marks}) exceeds exam maximum ({total_max}).",
                           f"Adjust question scores so sum <= {total_max}.")
        else:
            # Single marks score check
            score = row.total_marks
            if score is None:
                _add_error(row, validation_errors, roll, "Marks cell is empty.",
                           f"Enter a numeric score between 0 and {total_max}.")
            elif score < 0:
                _add_error(row, validation_errors, roll, f"Marks ({score}) cannot be negative.",
                           "Enter a non-negative number.")
            elif score > total_max:
                _add_error(row, validation_errors, roll,
                           f"Marks ({score}) exceeds maximum allowed ({total_max}).",
                           f"Enter a score <= {total_max}.")

    return rows, validation_errors, warnings


def _add_error(
    row: ParsedMarksRow,
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
