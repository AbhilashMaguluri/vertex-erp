"""Preview builder for Marks Import.

Assembles top-level summary metrics and detail tables for display on the preview UI.
"""
from __future__ import annotations

from typing import List, Optional

from app.features.admin.models import Subject
from app.features.marks_import.models import AssessmentTemplate
from app.features.marks_import.schemas import (
    PreviewSummary,
    PreviewTables,
    ResolvedMarksEntry,
    StudentMarksPreviewRow,
)


class MarksPreviewBuilder:
    """Builds preview summary and detail tables."""

    def generate_summary(
        self,
        subject: Optional[Subject],
        template: AssessmentTemplate,
        resolved_entries: List[ResolvedMarksEntry],
        warning_count: int,
        error_count: int,
    ) -> PreviewSummary:
        existing_students = sum(1 for e in resolved_entries if e.student_found)
        missing_students = sum(1 for e in resolved_entries if not e.student_found)
        new_records = sum(1 for e in resolved_entries if e.proposed_action == "CREATE")
        updates = sum(1 for e in resolved_entries if e.proposed_action == "UPDATE")
        skipped = sum(1 for e in resolved_entries if e.proposed_action == "SKIP")

        return PreviewSummary(
            subject_code=subject.code if subject else None,
            subject_name=subject.name if subject else None,
            assessment_code=template.assessment_code,
            assessment_name=template.assessment_name,
            total_max_marks=template.total_max_marks,
            total_students_in_file=len(resolved_entries),
            existing_students_found=existing_students,
            missing_students=missing_students,
            new_records=new_records,
            updates=updates,
            skipped_records=skipped,
            warnings=warning_count,
            errors=error_count,
        )

    def generate_preview_tables(
        self,
        resolved_entries: List[ResolvedMarksEntry],
    ) -> PreviewTables:
        rows = [
            StudentMarksPreviewRow(
                roll_number=e.roll_number,
                student_name=e.student_name,
                question_breakdown=_format_breakdown_display(e.question_scores, e.total_marks, e.max_marks),
                total_marks=e.total_marks,
                max_marks=e.max_marks,
                student_found="Yes" if e.student_found else "No",
                existing_marks=(
                    f"Yes ({e.existing_total}/{e.max_marks})"
                    if e.existing_mark_id and e.existing_total is not None
                    else "No"
                ),
                action=_format_action_display(e.proposed_action),
                error=e.error,
            )
            for e in resolved_entries
        ]
        return PreviewTables(records=rows)


def _format_breakdown_display(scores: dict, total: float, max_m: float) -> str:
    if scores:
        parts = [f"{k}:{v}" for k, v in scores.items()]
        return f"{', '.join(parts)} = {total}/{max_m}"
    return f"{total}/{max_m}"


def _format_action_display(action: str) -> str:
    return {
        "CREATE": "Create",
        "UPDATE": "Update",
        "SKIP": "Skip",
        "CANNOT_IMPORT": "Cannot Import",
    }.get(action, action)
