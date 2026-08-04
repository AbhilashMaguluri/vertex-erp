"""Resolver services for student accounts, counselor accounts, and memberships.

Each resolver has a single responsibility:
- StudentAccountResolver: find/prepare student accounts
- CounselorResolver: find counselor accounts by email
- MembershipResolver: check existing assignments
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence, Set

from app.features.auth.models import User
from app.features.membership_import.repository import MembershipImportRepository
from app.features.membership_import.schemas import (
    CounselorEntry,
    ExpandedStudentEntry,
)
from app.features.students.models import CounsellorAssignment, Student

logger = logging.getLogger("app.membership_import.resolvers")

# Supported email domains for student lookups
STUDENT_EMAIL_DOMAINS = ["vvit.net", "vvitu.ac.in"]


class StudentAccountResolver:
    """Resolve existing student accounts and prepare missing ones."""

    def __init__(self, repo: MembershipImportRepository):
        self.repo = repo

    async def find_existing_students(
        self, roll_numbers: List[str],
    ) -> Dict[str, Student]:
        """Batch-lookup existing student accounts by roll number."""
        return await self.repo.get_students_by_rolls(roll_numbers)

    async def resolve_students(
        self,
        entries: List[ExpandedStudentEntry],
        existing_students: Dict[str, Student],
    ) -> List[ExpandedStudentEntry]:
        """Update each entry with student account status.

        Also tries email-based lookup for students whose roll number
        didn't match but whose email might exist.
        """
        # Collect emails to try for students not found by roll
        missing_roll_numbers = [
            e.roll_number for e in entries
            if e.roll_number.upper() not in existing_students
        ]

        # Build candidate emails for missing students
        candidate_emails: List[str] = []
        for roll in missing_roll_numbers:
            for domain in STUDENT_EMAIL_DOMAINS:
                candidate_emails.append(f"{roll.lower()}@{domain}")

        # Batch lookup by email
        email_users: Dict[str, User] = {}
        if candidate_emails:
            email_users = await self.repo.get_users_by_emails(candidate_emails)

        for entry in entries:
            roll_upper = entry.roll_number.upper()

            if roll_upper in existing_students:
                student = existing_students[roll_upper]
                entry.student_status = "EXISTING"
                entry.student_action = "REUSE"
                entry.student_user_id = str(student.user_id)
                entry.student_id = str(student.id)
                entry.student_name = student.user.full_name if student.user else None
                entry.student_email = student.user.email if student.user else None
            else:
                # Try email-based lookup
                found_user: Optional[User] = None
                found_email: Optional[str] = None
                for domain in STUDENT_EMAIL_DOMAINS:
                    email = f"{entry.roll_number.lower()}@{domain}"
                    user = email_users.get(email)
                    if user:
                        found_user = user
                        found_email = email
                        break

                if found_user:
                    # User exists but no student record — still mark as existing
                    entry.student_status = "EXISTING"
                    entry.student_action = "REUSE"
                    entry.student_user_id = str(found_user.id)
                    entry.student_email = found_email
                    entry.student_name = found_user.full_name
                else:
                    entry.student_status = "MISSING"
                    entry.student_action = "CREATE_ACCOUNT"
                    # Assign the first supported domain for new accounts
                    entry.student_email = f"{entry.roll_number.lower()}@{STUDENT_EMAIL_DOMAINS[0]}"

        return entries


class CounselorResolver:
    """Resolve counselor accounts by email."""

    def __init__(self, repo: MembershipImportRepository):
        self.repo = repo

    async def find_counselors_by_emails(
        self, emails: List[str],
    ) -> Dict[str, CounselorEntry]:
        """Batch-lookup counselor accounts.

        Returns a dict keyed by lowercase email.
        """
        unique_emails = list(set(e.lower() for e in emails if e))
        existing_users = await self.repo.get_counselors_by_emails(unique_emails)

        entries: Dict[str, CounselorEntry] = {}
        for email in unique_emails:
            user = existing_users.get(email)
            if user:
                entries[email] = CounselorEntry(
                    email=email,
                    user_id=str(user.id),
                    display_name=user.full_name,
                    status="FOUND",
                    action="REUSE",
                )
            else:
                entries[email] = CounselorEntry(
                    email=email,
                    status="MISSING",
                    action="CANNOT_IMPORT",
                )

        return entries


class MembershipResolver:
    """Check for existing counselor assignments (memberships)."""

    def __init__(self, repo: MembershipImportRepository):
        self.repo = repo

    async def check_existing_memberships(
        self, student_ids: List[str],
    ) -> Dict[str, CounsellorAssignment]:
        """Return existing open assignments keyed by student_id."""
        return await self.repo.get_existing_assignments(student_ids)
