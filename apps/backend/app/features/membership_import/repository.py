"""Repository for the Membership Import feature.

All database queries live here — the service layer never constructs
SQLAlchemy queries directly.  Queries are batched where possible to
avoid N+1 patterns.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Set

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.admin.models import AcademicYear, Department, Section, Semester
from app.features.auth.models import Role, User
from app.features.membership_import.models import MembershipImportBatch, MembershipImportRecord
from app.features.students.models import CounsellorAssignment, Student, StudentEnrollment

logger = logging.getLogger("app.membership_import.repository")


class MembershipImportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Batch management
    # ------------------------------------------------------------------
    async def create_batch(self, batch: MembershipImportBatch) -> MembershipImportBatch:
        self.db.add(batch)
        await self.db.flush()
        return batch

    async def get_batch(self, batch_id: str) -> Optional[MembershipImportBatch]:
        query = (
            select(MembershipImportBatch)
            .where(MembershipImportBatch.id == batch_id)
            .options(selectinload(MembershipImportBatch.imported_by))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_batches(self, limit: int = 20) -> List[MembershipImportBatch]:
        query = (
            select(MembershipImportBatch)
            .options(selectinload(MembershipImportBatch.imported_by))
            .order_by(MembershipImportBatch.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def batch_statistics(self) -> dict:
        query = select(
            func.count(MembershipImportBatch.id).label("total"),
            func.sum(case(
                (MembershipImportBatch.status == "COMPLETED", 1), else_=0
            )).label("completed"),
            func.coalesce(func.sum(MembershipImportBatch.memberships_created), 0).label("memberships"),
            func.coalesce(func.sum(MembershipImportBatch.students_created), 0).label("students"),
            func.max(MembershipImportBatch.created_at).label("last_at"),
        )
        row = (await self.db.execute(query)).first()
        total = int(row.total or 0)
        completed = int(row.completed or 0)
        return {
            "total": total,
            "completed": completed,
            "memberships": int(row.memberships or 0),
            "students": int(row.students or 0),
            "last_at": row.last_at,
            "success_rate": round((completed / total) * 100, 1) if total else 0.0,
        }

    async def add_records(self, records: Sequence[MembershipImportRecord]) -> None:
        if not records:
            return
        self.db.add_all(list(records))
        await self.db.flush()

    async def list_records(self, batch_id: str, limit: int = 500) -> List[MembershipImportRecord]:
        query = (
            select(MembershipImportRecord)
            .where(MembershipImportRecord.batch_id == batch_id)
            .order_by(
                MembershipImportRecord.status.in_(("CREATED", "REUSED")),
                MembershipImportRecord.source_row_number,
                MembershipImportRecord.identifier,
            )
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Student lookups — batched
    # ------------------------------------------------------------------
    async def get_students_by_rolls(self, roll_numbers: Sequence[str]) -> Dict[str, Student]:
        """Find existing students by roll number.  Returns {roll_upper: Student}."""
        if not roll_numbers:
            return {}
        found: Dict[str, Student] = {}
        rolls = [r.upper() for r in roll_numbers]
        for start in range(0, len(rolls), 500):
            chunk = rolls[start: start + 500]
            query = (
                select(Student)
                .where(Student.roll_number.in_(chunk), Student.deleted_at.is_(None))
                .options(selectinload(Student.user))
            )
            result = await self.db.execute(query)
            for student in result.scalars().all():
                found[student.roll_number.upper()] = student
        return found

    async def get_users_by_emails(self, emails: Sequence[str]) -> Dict[str, User]:
        """Find existing users by email.  Returns {email_lower: User}."""
        if not emails:
            return {}
        found: Dict[str, User] = {}
        lowered = [e.lower() for e in emails]
        for start in range(0, len(lowered), 500):
            chunk = lowered[start: start + 500]
            query = (
                select(User)
                .where(
                    func.lower(User.email).in_(chunk),
                    User.deleted_at.is_(None),
                )
                .options(selectinload(User.roles))
            )
            result = await self.db.execute(query)
            for user in result.scalars().all():
                found[user.email.lower()] = user
        return found

    # ------------------------------------------------------------------
    # Counselor lookups
    # ------------------------------------------------------------------
    async def get_counselors_by_emails(self, emails: Sequence[str]) -> Dict[str, User]:
        """Find counselor/faculty/HOD accounts by email.  Returns {email_lower: User}."""
        if not emails:
            return {}
        found: Dict[str, User] = {}
        lowered = [e.lower() for e in emails]
        for start in range(0, len(lowered), 500):
            chunk = lowered[start: start + 500]
            query = (
                select(User)
                .join(User.roles)
                .where(
                    func.lower(User.email).in_(chunk),
                    Role.name.in_(("COUNSELLOR", "FACULTY", "HOD")),
                    User.deleted_at.is_(None),
                )
                .options(selectinload(User.roles))
            )
            result = await self.db.execute(query)
            for user in result.unique().scalars().all():
                found[user.email.lower()] = user
        return found

    # ------------------------------------------------------------------
    # Membership / assignment lookups
    # ------------------------------------------------------------------
    async def get_existing_assignments(
        self, student_ids: Sequence[str],
    ) -> Dict[str, CounsellorAssignment]:
        """Active (open) assignments keyed by student_id string."""
        if not student_ids:
            return {}
        found: Dict[str, CounsellorAssignment] = {}
        for start in range(0, len(student_ids), 500):
            chunk = list(student_ids[start: start + 500])
            query = (
                select(CounsellorAssignment)
                .where(
                    CounsellorAssignment.student_id.in_(chunk),
                    CounsellorAssignment.effective_to.is_(None),
                )
                .options(selectinload(CounsellorAssignment.counsellor))
            )
            result = await self.db.execute(query)
            for assignment in result.scalars().all():
                found[str(assignment.student_id)] = assignment
        return found

    async def close_open_assignments(self, student_ids: Sequence[str]) -> None:
        if not student_ids:
            return
        query = select(CounsellorAssignment).where(
            CounsellorAssignment.student_id.in_(list(student_ids)),
            CounsellorAssignment.effective_to.is_(None),
        )
        result = await self.db.execute(query)
        now = datetime.now(timezone.utc)
        for assignment in result.scalars().all():
            assignment.effective_to = now
        await self.db.flush()

    # ------------------------------------------------------------------
    # Academic catalog
    # ------------------------------------------------------------------
    async def get_department(self, department_id: str) -> Optional[Department]:
        result = await self.db.execute(
            select(Department).where(Department.id == department_id, Department.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_semester(self, semester_id: str) -> Optional[Semester]:
        result = await self.db.execute(
            select(Semester).where(Semester.id == semester_id, Semester.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_role(self, name: str) -> Optional[Role]:
        result = await self.db.execute(select(Role).where(Role.name == name.upper()))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        query = (
            select(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .options(selectinload(User.roles))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_taken_usernames_and_emails(self) -> tuple[set, set]:
        result = await self.db.execute(
            select(User.username, User.email).where(User.deleted_at.is_(None))
        )
        usernames, emails = set(), set()
        for username, email in result.all():
            if username:
                usernames.add(username.lower())
            if email:
                emails.add(email.lower())
        return usernames, emails

    async def find_section(
        self, department_id: str, year: Optional[int], name: str, batch_year: int,
    ) -> Optional[Section]:
        query = select(Section).where(
            Section.department_id == department_id,
            func.upper(Section.name) == name.upper(),
            Section.batch_year == batch_year,
            Section.deleted_at.is_(None),
        )
        if year is not None:
            query = query.where(or_(Section.year == year, Section.year.is_(None)))
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_departments(self) -> List[Department]:
        result = await self.db.execute(
            select(Department).where(Department.deleted_at.is_(None)).order_by(Department.code)
        )
        return list(result.scalars().all())

    async def list_semesters(self) -> List[Semester]:
        result = await self.db.execute(
            select(Semester).where(Semester.deleted_at.is_(None)).order_by(Semester.number)
        )
        return list(result.scalars().all())

    async def list_academic_years(self) -> List[AcademicYear]:
        result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.deleted_at.is_(None)).order_by(AcademicYear.start_date.desc())
        )
        return list(result.scalars().all())
