from typing import Dict, List, Optional, Sequence

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.admin.models import AcademicYear, Department, Section, Semester
from app.features.auth.models import Role, User
from app.features.imports.models import ImportBatch, ImportBatchRecord
from app.features.students.models import CounsellorAssignment, Student


class ImportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Batches ---------------------------------------------------------
    async def create_batch(self, batch: ImportBatch) -> ImportBatch:
        self.db.add(batch)
        await self.db.flush()
        return batch

    async def get_batch(self, batch_id: str) -> Optional[ImportBatch]:
        query = (
            select(ImportBatch)
            .where(ImportBatch.id == batch_id)
            .options(selectinload(ImportBatch.imported_by))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_batches(self, limit: int = 20) -> List[ImportBatch]:
        query = (
            select(ImportBatch)
            .options(selectinload(ImportBatch.imported_by))
            .order_by(ImportBatch.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def batch_statistics(self) -> dict:
        """History-page rollups. One scan rather than a query per tile."""
        query = select(
            func.count(ImportBatch.id).label("total"),
            func.sum(case((ImportBatch.status == "COMPLETED", 1), else_=0)).label("completed"),
            func.coalesce(func.sum(ImportBatch.students_created), 0).label("students"),
            func.coalesce(func.sum(ImportBatch.counsellors_created), 0).label("counsellors"),
            func.max(ImportBatch.created_at).label("last_at"),
        )
        row = (await self.db.execute(query)).first()
        total = int(row.total or 0)
        completed = int(row.completed or 0)
        return {
            "total": total,
            "completed": completed,
            "students": int(row.students or 0),
            "counsellors": int(row.counsellors or 0),
            "last_at": row.last_at,
            "success_rate": round((completed / total) * 100, 1) if total else 0.0,
        }

    async def add_records(self, records: Sequence[ImportBatchRecord]) -> None:
        if not records:
            return
        self.db.add_all(list(records))
        await self.db.flush()

    async def list_records(self, batch_id: str, limit: int = 500) -> List[ImportBatchRecord]:
        query = (
            select(ImportBatchRecord)
            .where(ImportBatchRecord.batch_id == batch_id)
            # Failures and skips first: the reason an import needs looking at
            # is never the several hundred rows that worked.
            .order_by(
                ImportBatchRecord.status.in_(("CREATED", "REUSED")),
                ImportBatchRecord.source_row_number,
                ImportBatchRecord.identifier,
            )
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Lookups used during analysis & execution -------------------------
    async def get_students_by_rolls(self, roll_numbers: Sequence[str]) -> Dict[str, Student]:
        """Existing students keyed by roll number — the duplicate check."""
        if not roll_numbers:
            return {}
        found: Dict[str, Student] = {}
        rolls = [r.upper() for r in roll_numbers]
        # Chunked: a single IN () list of several thousand parameters is slower
        # than a handful of round trips and risks the driver's parameter cap.
        for start in range(0, len(rolls), 500):
            chunk = rolls[start : start + 500]
            query = (
                select(Student)
                .where(Student.roll_number.in_(chunk), Student.deleted_at.is_(None))
                .options(selectinload(Student.user))
            )
            result = await self.db.execute(query)
            for student in result.scalars().all():
                found[student.roll_number.upper()] = student
        return found

    async def list_counsellor_users(self) -> List[User]:
        """Every account that can hold a caseload, for name/phone matching."""
        query = (
            select(User)
            .join(User.roles)
            .where(
                Role.name.in_(("COUNSELLOR", "FACULTY", "HOD")),
                User.deleted_at.is_(None),
            )
            .options(selectinload(User.roles))
        )
        result = await self.db.execute(query)
        return list(result.unique().scalars().all())

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

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        query = (
            select(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .options(selectinload(User.roles))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email_or_username(self, value: str) -> Optional[User]:
        lowered = (value or "").strip().lower()
        if not lowered:
            return None
        query = (
            select(User)
            .where(
                or_(func.lower(User.email) == lowered, func.lower(User.username) == lowered),
                User.deleted_at.is_(None),
            )
            .options(selectinload(User.roles))
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    # --- Academic catalog -------------------------------------------------
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

    async def find_section(
        self, department_id: str, year: Optional[int], name: str, batch_year: int
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

    async def get_semester(self, semester_id: str) -> Optional[Semester]:
        result = await self.db.execute(
            select(Semester).where(Semester.id == semester_id, Semester.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_department(self, department_id: str) -> Optional[Department]:
        result = await self.db.execute(
            select(Department).where(Department.id == department_id, Department.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_role(self, name: str) -> Optional[Role]:
        result = await self.db.execute(select(Role).where(Role.name == name.upper()))
        return result.scalar_one_or_none()

    async def close_open_assignments(self, student_ids: Sequence[str]) -> None:
        from datetime import datetime, timezone

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

    async def students_with_open_assignment(self, student_ids: Sequence[str]) -> set:
        if not student_ids:
            return set()
        query = select(CounsellorAssignment.student_id).where(
            CounsellorAssignment.student_id.in_(list(student_ids)),
            CounsellorAssignment.effective_to.is_(None),
        )
        result = await self.db.execute(query)
        return {str(row[0]) for row in result.all()}
