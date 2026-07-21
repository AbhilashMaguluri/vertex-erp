from typing import List, Optional, Tuple
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.admin.models import Department, Section, AcademicYear, Semester, Subject, SubjectFaculty
from app.features.auth.models import User, Role


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
        query = query.order_by(Section.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # Academic Year
    async def create_academic_year(self, ay: AcademicYear) -> AcademicYear:
        self.db.add(ay)
        await self.db.flush()
        return ay

    async def list_academic_years(self) -> List[AcademicYear]:
        query = select(AcademicYear).where(AcademicYear.deleted_at.is_(None)).order_by(AcademicYear.start_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # Semester
    async def create_semester(self, sem: Semester) -> Semester:
        self.db.add(sem)
        await self.db.flush()
        return sem

    async def list_semesters(self, academic_year_id: Optional[str] = None) -> List[Semester]:
        query = select(Semester).where(Semester.deleted_at.is_(None))
        if academic_year_id:
            query = query.where(Semester.academic_year_id == academic_year_id)
        query = query.order_by(Semester.number)
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

    # User Admin List
    async def list_users(self, page: int = 1, per_page: int = 20, role: Optional[str] = None) -> Tuple[List[User], int]:
        query = select(User).where(User.deleted_at.is_(None))
        count_query = select(func.count(User.id)).where(User.deleted_at.is_(None))
        
        if role:
            query = query.join(User.roles).where(Role.name == role.upper())
            count_query = count_query.join(User.roles).where(Role.name == role.upper())

        query = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        
        users_result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        
        return list(users_result.scalars().all()), count_result.scalar_one()
