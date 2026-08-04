"""Preview builder for the Attendance Import feature.

Assembles top-level summary metrics and detail tables for display on the preview UI.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from app.features.admin.models import Subject
from app.features.attendance_import.schemas import (
    PreviewSummary,
    PreviewTables,
    ResolvedAttendanceEntry,
    StudentAttendancePreviewRow,
)


class AttendancePreviewBuilder:
    """Builds preview summary and detail tables."""

    def generate_summary(
        self,
        att_date: date,
        mode: str,
        subject: Optional[Subject],
        resolved_entries: List[ResolvedAttendanceEntry],
        warning_count: int,
        error_count: int,
    ) -> PreviewSummary:
        existing_students = sum(1 for e in resolved_entries if e.student_found)
        missing_students = sum(1 for e in resolved_entries if not e.student_found)
        new_records = sum(1 for e in resolved_entries if e.proposed_action == "CREATE")
        updates = sum(1 for e in resolved_entries if e.proposed_action == "UPDATE")
        skipped = sum(1 for e in resolved_entries if e.proposed_action == "SKIP")

        return PreviewSummary(
            attendance_date=att_date,
            mode=mode,
            subject_code=subject.code if subject else None,
            subject_name=subject.name if subject else None,
            total_students_in_file=len(resolved_entries),
            existing_students_found=existing_students,
            missing_students=missing_students,
            new_attendance_records=new_records,
            attendance_updates=updates,
            skipped_records=skipped,
            warnings=warning_count,
            errors=error_count,
        )

    def generate_preview_tables(
        self,
        resolved_entries: List[ResolvedAttendanceEntry],
    ) -> PreviewTables:
        rows = [
            StudentAttendancePreviewRow(
                roll_number=e.roll_number,
                student_name=e.student_name,
                status=_format_status_display(e.normalized_status),
                student_found="Yes" if e.student_found else "No",
                existing_attendance=(
                    f"Yes ({_format_status_display(e.existing_status)})"
                    if e.existing_attendance_id and e.existing_status
                    else "No"
                ),
                action=_format_action_display(e.proposed_action),
                error=e.error,
            )
            for e in resolved_entries
        ]
        return PreviewTables(records=rows)


def _format_status_display(status: Optional[str]) -> str:
    if not status:
        return "—"
    return {
        "PRESENT": "Present",
        "ABSENT": "Absent",
        "ON_DUTY": "On Duty",
        "MEDICAL_LEAVE": "Medical Leave",
    }.get(status, status)


def _format_action_display(action: str) -> str:
    return {
        "CREATE": "Create",
        "UPDATE": "Update",
        "SKIP": "Skip",
        "CANNOT_IMPORT": "Cannot Import",
    }.get(action, action)
