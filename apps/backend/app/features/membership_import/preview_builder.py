"""Preview builder — assembles the preview summary and detail tables.

Reads from resolved data structures, writes nothing to the database.
"""
from __future__ import annotations

from typing import Dict, List

from app.features.membership_import.schemas import (
    CounselorEntry,
    CounselorPreviewRow,
    ExpandedStudentEntry,
    MembershipEntry,
    MembershipPreviewRow,
    PreviewSummary,
    PreviewTables,
    StudentPreviewRow,
)
from app.features.students.models import CounsellorAssignment


class ImportPreviewBuilder:
    """Builds the preview the administrator reviews before confirming."""

    def generate_summary(
        self,
        students: List[ExpandedStudentEntry],
        counselors: Dict[str, CounselorEntry],
        memberships: List[MembershipEntry],
        warning_count: int,
        error_count: int,
    ) -> PreviewSummary:
        existing_students = sum(1 for s in students if s.student_status == "EXISTING")
        new_students = sum(1 for s in students if s.student_status == "MISSING")
        existing_counselors = sum(1 for c in counselors.values() if c.status == "FOUND")
        missing_counselors = sum(1 for c in counselors.values() if c.status == "MISSING")
        existing_memberships = sum(1 for m in memberships if m.membership_status == "EXISTING")
        new_memberships = sum(1 for m in memberships if m.membership_action == "CREATE")

        return PreviewSummary(
            total_students=len(students),
            existing_student_accounts=existing_students,
            new_student_accounts=new_students,
            existing_counselor_accounts=existing_counselors,
            missing_counselors=missing_counselors,
            existing_memberships=existing_memberships,
            new_memberships=new_memberships,
            warnings=warning_count,
            errors=error_count,
        )

    def generate_preview_tables(
        self,
        students: List[ExpandedStudentEntry],
        counselors: Dict[str, CounselorEntry],
        memberships: List[MembershipEntry],
    ) -> PreviewTables:
        student_rows = self._build_student_table(students)
        counselor_rows = self._build_counselor_table(counselors)
        membership_rows = self._build_membership_table(memberships)

        return PreviewTables(
            students=student_rows,
            counselors=counselor_rows,
            memberships=membership_rows,
        )

    def _build_student_table(
        self, students: List[ExpandedStudentEntry],
    ) -> List[StudentPreviewRow]:
        # Deduplicate by roll number
        seen = set()
        rows: List[StudentPreviewRow] = []
        for s in students:
            if s.roll_number in seen:
                continue
            seen.add(s.roll_number)
            rows.append(StudentPreviewRow(
                roll_number=s.roll_number,
                email_used=s.student_email,
                name=s.student_name,
                status="Existing" if s.student_status == "EXISTING" else "Missing",
                action="Reuse" if s.student_action == "REUSE" else "Create Account",
            ))
        return rows

    def _build_counselor_table(
        self, counselors: Dict[str, CounselorEntry],
    ) -> List[CounselorPreviewRow]:
        return [
            CounselorPreviewRow(
                email=c.email,
                name=c.display_name,
                status="Found" if c.status == "FOUND" else "Missing",
                action="Reuse" if c.action == "REUSE" else "Cannot Import",
                student_count=c.student_count,
            )
            for c in sorted(counselors.values(), key=lambda c: (-c.student_count, c.email))
        ]

    def _build_membership_table(
        self, memberships: List[MembershipEntry],
    ) -> List[MembershipPreviewRow]:
        return [
            MembershipPreviewRow(
                student_roll=m.roll_number,
                student_name=m.student_name,
                counselor_email=m.counselor_email,
                counselor_name=m.counselor_name,
                status=_membership_display_status(m.membership_status),
                action=_membership_display_action(m.membership_action),
                error=m.error,
            )
            for m in memberships
        ]


def _membership_display_status(status: str) -> str:
    return {
        "NEW": "New",
        "EXISTING": "Existing",
        "SKIP": "Skip",
    }.get(status, status)


def _membership_display_action(action: str) -> str:
    return {
        "CREATE": "Create",
        "UPDATE": "Update",
        "SKIP": "Skip",
        "ERROR": "Error",
    }.get(action, action)
