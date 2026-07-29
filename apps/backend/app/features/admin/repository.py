from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.admin.models import Department, Section, AcademicYear, Semester, Subject, SubjectFaculty
from app.features.students.models import CounsellorAssignment


class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Department
    async def create_department(self, dept: Department) -> Department:
        self.db.add(dept)
        await self.db.flush()
        return dept

    async def get_department_by_id(self, dept_id: str) -> Optional[Department]:
        query = select(Department).where(Department.id == dept_id, Department.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_department_by_code(self, code: str, exclude_id: Optional[str] = None) -> Optional[Department]:
        query = select(Department).where(Department.code == code, Department.deleted_at.is_(None))
        if exclude_id:
            query = query.where(Department.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_departments(self) -> List[Department]:
        query = select(Department).where(Department.deleted_at.is_(None)).order_by(Department.code)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # Section
    async def create_section(self, section: Section) -> Section:
        self.db.add(section)
        await self.db.flush()
        return section

    async def list_sections(self, department_id: Optional[str] = None) -> List[Section]:
        query = select(Section).where(Section.deleted_at.is_(None))
        if department_id:
            query = query.where(Section.department_id == department_id)
        query = query.order_by(Section.year, Section.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_section_by_name(
        self, department_id: str, year: Optional[int], name: str, exclude_id: Optional[str] = None
    ) -> Optional[Section]:
        query = select(Section).where(
            Section.department_id == department_id,
            Section.year == year,
            Section.name == name,
            Section.deleted_at.is_(None),
        )
        if exclude_id:
            query = query.where(Section.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def count_active_enrollments_for_section(self, section_id: str) -> int:
        from sqlalchemy import func
        from app.features.students.models import StudentEnrollment

        query = select(func.count()).select_from(StudentEnrollment).where(StudentEnrollment.section_id == section_id)
        result = await self.db.execute(query)
        return int(result.scalar_one())

    # Academic Year
    async def create_academic_year(self, ay: AcademicYear) -> AcademicYear:
        self.db.add(ay)
        await self.db.flush()
        return ay

    async def list_academic_years(self) -> List[AcademicYear]:
        query = select(AcademicYear).where(AcademicYear.deleted_at.is_(None)).order_by(AcademicYear.start_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_academic_year_by_id(self, ay_id: str) -> Optional[AcademicYear]:
        query = select(AcademicYear).where(AcademicYear.id == ay_id, AcademicYear.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_academic_year_by_name(self, name: str, exclude_id: Optional[str] = None) -> Optional[AcademicYear]:
        query = select(AcademicYear).where(AcademicYear.name == name, AcademicYear.deleted_at.is_(None))
        if exclude_id:
            query = query.where(AcademicYear.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # Semester — fixed institutional catalog, seeded once (see app/scripts/seed.py)
    async def create_semester(self, sem: Semester) -> Semester:
        self.db.add(sem)
        await self.db.flush()
        return sem

    async def list_semesters(self) -> List[Semester]:
        query = select(Semester).where(Semester.deleted_at.is_(None)).order_by(Semester.number)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # Subject
    async def create_subject(self, sub: Subject) -> Subject:
        self.db.add(sub)
        await self.db.flush()
        return sub

    async def list_subjects(self, department_id: Optional[str] = None) -> List[Subject]:
        query = select(Subject).where(Subject.deleted_at.is_(None))
        if department_id:
            query = query.where(Subject.department_id == department_id)
        query = query.order_by(Subject.code)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_subject_by_id(self, subject_id: str) -> Optional[Subject]:
        query = select(Subject).where(Subject.id == subject_id, Subject.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_subject_by_code(self, code: str, exclude_id: Optional[str] = None) -> Optional[Subject]:
        query = select(Subject).where(Subject.code == code, Subject.deleted_at.is_(None))
        if exclude_id:
            query = query.where(Subject.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_subjects_by_ids(self, subject_ids: List[str]) -> List[Subject]:
        if not subject_ids:
            return []
        query = select(Subject).where(Subject.id.in_(subject_ids), Subject.deleted_at.is_(None))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # Semester lookup (used when provisioning student accounts)
    async def get_semester_by_id(self, semester_id: str) -> Optional[Semester]:
        query = select(Semester).where(Semester.id == semester_id, Semester.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_section_by_id(self, section_id: str) -> Optional[Section]:
        query = select(Section).where(Section.id == section_id, Section.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # Counsellor assignment
    async def close_open_counsellor_assignments(self, student_id: str) -> None:
        query = select(CounsellorAssignment).where(
            CounsellorAssignment.student_id == student_id,
            CounsellorAssignment.effective_to.is_(None),
        )
        result = await self.db.execute(query)
        now = datetime.now(timezone.utc)
        for assignment in result.scalars().all():
            assignment.effective_to = now
        await self.db.flush()

    async def create_counsellor_assignment(self, assignment: CounsellorAssignment) -> CounsellorAssignment:
        self.db.add(assignment)
        await self.db.flush()
        return assignment
