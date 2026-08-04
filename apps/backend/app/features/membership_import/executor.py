"""Import executor — writes to the database inside a transaction.

Separated from the orchestrator so the transaction boundary is explicit
and testable.  Creates student accounts, memberships, and assignment
records.  Rolls back everything on fatal error.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import StudentStatus
from app.core.security import generate_readable_password, get_password_hash
from app.features.admin.models import Section
from app.features.auth.models import User
from app.features.imports import naming
from app.features.membership_import.models import MembershipImportRecord
from app.features.membership_import.repository import MembershipImportRepository
from app.features.membership_import.schemas import (
    GeneratedStudentCredential,
    MembershipEntry,
    MembershipImportConfiguration,
)
from app.features.students.models import CounsellorAssignment, Student, StudentEnrollment
from app.features.students.profile_models import StudentProfile

logger = logging.getLogger("app.membership_import.executor")

UNKNOWN_DATE_OF_BIRTH = date(1900, 1, 1)
DEFAULT_EMAIL_DOMAIN = "vvit.net"


class ImportExecutor:
    """Executes the import inside a database transaction."""

    def __init__(self, db: AsyncSession, repo: MembershipImportRepository):
        self.db = db
        self.repo = repo

    async def create_student_accounts(
        self,
        memberships: List[MembershipEntry],
        config: MembershipImportConfiguration,
        semester: Any,
        section: Section,
        student_role: Any,
        domain: str,
        taken_usernames: set,
        taken_emails: set,
        actor_id: str,
    ) -> Tuple[
        Dict[str, Student],
        List[GeneratedStudentCredential],
        List[MembershipImportRecord],
        int, int,
    ]:
        """Create missing student accounts.  Returns the student map,
        credentials, records, and counts."""
        students_created = 0
        students_reused = 0
        created_map: Dict[str, Student] = {}
        credentials: List[GeneratedStudentCredential] = []
        records: List[MembershipImportRecord] = []

        # Batch-load existing students for reuse
        existing_rolls = [m.roll_number for m in memberships if m.student_action == "REUSE" and m.student_id]
        existing_students = await self.repo.get_students_by_rolls(existing_rolls)

        for m in memberships:
            if m.membership_action == "ERROR":
                continue

            roll = m.roll_number.upper()

            if m.student_action == "REUSE":
                student = existing_students.get(roll)
                if student:
                    created_map[roll] = student
                    students_reused += 1
                    records.append(MembershipImportRecord(
                        record_type="STUDENT", identifier=roll,
                        display_name=student.user.full_name if student.user else None,
                        status="REUSED", user_id=student.user_id,
                        message="Existing student account reused.",
                        source_row_number=m.source_row,
                    ))
                elif m.student_user_id:
                    # User exists but no Student record — look up by user_id
                    user = await self.repo.get_user_by_id(m.student_user_id)
                    if user:
                        students_reused += 1
                        records.append(MembershipImportRecord(
                            record_type="STUDENT", identifier=roll,
                            display_name=user.full_name,
                            status="REUSED", user_id=user.id,
                            message="Existing user account reused (no student record).",
                            source_row_number=m.source_row,
                        ))
                continue

            # CREATE_ACCOUNT
            try:
                async with self.db.begin_nested():
                    student, password, username = await self._create_student(
                        roll, config, semester, section, student_role,
                        domain, taken_usernames, taken_emails, actor_id,
                    )
                taken_usernames.add(username.lower())
                taken_emails.add(f"{username.lower()}@{domain}")
                created_map[roll] = student
                students_created += 1
                credentials.append(GeneratedStudentCredential(
                    roll_number=roll,
                    full_name=student.user.full_name if student.user else roll,
                    username=username,
                    email=f"{username.lower()}@{domain}",
                    temporary_password=password,
                    counselor_email=m.counselor_email,
                ))
                records.append(MembershipImportRecord(
                    record_type="STUDENT", identifier=roll,
                    display_name=student.user.full_name if student.user else roll,
                    status="CREATED", user_id=student.user_id,
                    message="Student account and profile created.",
                    source_row_number=m.source_row,
                ))
            except Exception as exc:
                logger.warning("Failed to create student %s: %s", roll, exc)
                records.append(MembershipImportRecord(
                    record_type="STUDENT", identifier=roll,
                    status="FAILED",
                    message=_safe_message(exc),
                    source_row_number=m.source_row,
                ))

        return created_map, credentials, records, students_created, students_reused

    async def create_memberships(
        self,
        memberships: List[MembershipEntry],
        student_map: Dict[str, Student],
        counselor_users: Dict[str, User],
        config: MembershipImportConfiguration,
    ) -> Tuple[List[MembershipImportRecord], int, int, int]:
        """Create/update counsellor assignments.  Returns records and counts."""
        records: List[MembershipImportRecord] = []
        created = updated = skipped = 0

        # Pre-fetch existing assignments
        student_ids = [str(s.id) for s in student_map.values()]
        existing_assignments = await self.repo.get_existing_assignments(student_ids)

        for m in memberships:
            if m.membership_action == "ERROR" or m.membership_action == "SKIP":
                skipped += 1
                records.append(MembershipImportRecord(
                    record_type="MEMBERSHIP",
                    identifier=f"{m.roll_number} → {m.counselor_email}",
                    status="SKIPPED",
                    message=m.error or "Skipped.",
                    source_row_number=m.source_row,
                ))
                continue

            roll_upper = m.roll_number.upper()
            student = student_map.get(roll_upper)
            counselor = counselor_users.get(m.counselor_email.lower())

            if not student or not counselor:
                skipped += 1
                reason = "Student not found." if not student else "Counselor not found."
                records.append(MembershipImportRecord(
                    record_type="MEMBERSHIP",
                    identifier=f"{m.roll_number} → {m.counselor_email}",
                    status="SKIPPED",
                    message=reason,
                    source_row_number=m.source_row,
                ))
                continue

            try:
                existing = existing_assignments.get(str(student.id))

                if existing and str(existing.counsellor_id) == str(counselor.id):
                    # Already assigned to same counselor
                    skipped += 1
                    records.append(MembershipImportRecord(
                        record_type="MEMBERSHIP",
                        identifier=f"{m.roll_number} → {m.counselor_email}",
                        status="SKIPPED",
                        message="Already assigned to this counselor.",
                        source_row_number=m.source_row,
                    ))
                    continue

                async with self.db.begin_nested():
                    if existing and config.reassign_existing_students:
                        # Close old assignment
                        await self.repo.close_open_assignments([str(student.id)])
                        updated += 1
                        action_label = "UPDATED"
                        message = (
                            f"Reassigned from {existing.counsellor.full_name if existing.counsellor else 'unknown'} "
                            f"to {counselor.full_name}."
                        )
                    elif existing:
                        skipped += 1
                        records.append(MembershipImportRecord(
                            record_type="MEMBERSHIP",
                            identifier=f"{m.roll_number} → {m.counselor_email}",
                            status="SKIPPED",
                            message=f"Already assigned to {existing.counsellor.full_name if existing.counsellor else 'another counselor'}. Enable reassignment to override.",
                            source_row_number=m.source_row,
                        ))
                        continue
                    else:
                        created += 1
                        action_label = "CREATED"
                        message = f"Assigned to {counselor.full_name}."

                    self.db.add(CounsellorAssignment(
                        student_id=student.id,
                        counsellor_id=counselor.id,
                        semester_id=config.semester_id,
                        effective_from=datetime.now(timezone.utc),
                    ))
                    await self.db.flush()

                records.append(MembershipImportRecord(
                    record_type="MEMBERSHIP",
                    identifier=f"{m.roll_number} → {m.counselor_email}",
                    display_name=f"{m.roll_number} → {counselor.full_name}",
                    status=action_label,
                    message=message,
                    source_row_number=m.source_row,
                ))
            except Exception as exc:
                logger.warning("Failed membership %s → %s: %s", m.roll_number, m.counselor_email, exc)
                records.append(MembershipImportRecord(
                    record_type="MEMBERSHIP",
                    identifier=f"{m.roll_number} → {m.counselor_email}",
                    status="FAILED",
                    message=_safe_message(exc),
                    source_row_number=m.source_row,
                ))

        return records, created, updated, skipped

    async def _create_student(
        self,
        roll: str,
        config: MembershipImportConfiguration,
        semester: Any,
        section: Section,
        student_role: Any,
        domain: str,
        taken_usernames: set,
        taken_emails: set,
        actor_id: str,
    ) -> Tuple[Student, str, str]:
        """Create a single student account with all related records."""
        username = naming.student_username(roll)
        email = naming.student_email(roll, domain)

        if username.lower() in taken_usernames or email.lower() in taken_emails:
            from app.core.exceptions import ValidationError
            raise ValidationError(f"Login '{username}' is already in use.")

        password = generate_readable_password()

        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            first_name=roll,
            last_name="",
            department_id=config.department_id,
            is_active=True,
            force_password_change=True,
            created_by=actor_id,
        )
        user.roles.append(student_role)
        self.db.add(user)
        await self.db.flush()

        student = Student(
            user_id=user.id,
            roll_number=roll,
            registration_number=roll,
            date_of_birth=UNKNOWN_DATE_OF_BIRTH,
            batch_year=config.batch_year,
            status=StudentStatus.ACTIVE.value,
            department_id=config.department_id,
            current_semester_id=semester.id if semester else None,
            created_by=actor_id,
        )
        self.db.add(student)
        await self.db.flush()

        self.db.add(StudentEnrollment(
            student_id=student.id,
            section_id=section.id,
            semester_id=config.semester_id,
        ))
        self.db.add(StudentProfile(student_id=student.id))
        await self.db.flush()

        student.user = user
        return student, password, username


def _safe_message(exc: Exception) -> str:
    """Extract a safe message from an exception."""
    message = getattr(exc, "message", None) or str(exc)
    return message[:500]
