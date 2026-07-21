from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, NotFoundError
from app.features.admin.models import Department, Section, AcademicYear, Semester, Subject
from app.features.admin.repository import AdminRepository
from app.features.admin.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    SectionCreate,
    SectionResponse,
    AcademicYearCreate,
    AcademicYearResponse,
    SemesterCreate,
    SemesterResponse,
    SubjectCreate,
    SubjectResponse,
)
from app.features.auth.schemas import UserCreateRequest, UserProfileResponse
from app.features.auth.service import AuthService
from app.features.auth.models import User
from app.core.security import get_password_hash


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminRepository(db)

    # Department Services
    async def create_department(self, data: DepartmentCreate, creator_id: str) -> DepartmentResponse:
        dept = Department(
            code=data.code.upper(),
            name=data.name,
            description=data.description,
            hod_user_id=data.hod_user_id,
            created_by=creator_id,
        )
        await self.repo.create_department(dept)
        await self.db.commit()
        return DepartmentResponse.model_validate(dept)

    async def list_departments(self) -> List[DepartmentResponse]:
        depts = await self.repo.list_departments()
        return [DepartmentResponse.model_validate(d) for d in depts]

    # Section Services
    async def create_section(self, data: SectionCreate, creator_id: str) -> SectionResponse:
        section = Section(
            department_id=data.department_id,
            name=data.name,
            batch_year=data.batch_year,
            created_by=creator_id,
        )
        await self.repo.create_section(section)
        await self.db.commit()
        return SectionResponse.model_validate(section)

    async def list_sections(self, department_id: Optional[str] = None) -> List[SectionResponse]:
        sections = await self.repo.list_sections(department_id)
        return [SectionResponse.model_validate(s) for s in sections]

    # Academic Year Services
    async def create_academic_year(self, data: AcademicYearCreate, creator_id: str) -> AcademicYearResponse:
        ay = AcademicYear(
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            is_current=data.is_current,
            created_by=creator_id,
        )
        await self.repo.create_academic_year(ay)
        await self.db.commit()
        return AcademicYearResponse.model_validate(ay)

    async def list_academic_years(self) -> List[AcademicYearResponse]:
        ays = await self.repo.list_academic_years()
        return [AcademicYearResponse.model_validate(a) for a in ays]

    # Semester Services
    async def create_semester(self, data: SemesterCreate, creator_id: str) -> SemesterResponse:
        sem = Semester(
            academic_year_id=data.academic_year_id,
            number=data.number,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            is_current=data.is_current,
            created_by=creator_id,
        )
        await self.repo.create_semester(sem)
        await self.db.commit()
        return SemesterResponse.model_validate(sem)

    async def list_semesters(self, academic_year_id: Optional[str] = None) -> List[SemesterResponse]:
        sems = await self.repo.list_semesters(academic_year_id)
        return [SemesterResponse.model_validate(s) for s in sems]

    # Subject Services
    async def create_subject(self, data: SubjectCreate, creator_id: str) -> SubjectResponse:
        subject = Subject(
            department_id=data.department_id,
            code=data.code.upper(),
            name=data.name,
            credits=data.credits,
            max_mid_marks=data.max_mid_marks,
            max_internal_marks=data.max_internal_marks,
            max_external_marks=data.max_external_marks,
            created_by=creator_id,
        )
        await self.repo.create_subject(subject)
        await self.db.commit()
        return SubjectResponse.model_validate(subject)

    async def list_subjects(self, department_id: Optional[str] = None) -> List[SubjectResponse]:
        subs = await self.repo.list_subjects(department_id)
        return [SubjectResponse.model_validate(s) for s in subs]

    # User Admin Services
    async def create_user_by_admin(self, data: UserCreateRequest, creator_id: str) -> UserProfileResponse:
        auth_service = AuthService(self.db)
        existing = await auth_service.repo.get_user_by_email(data.email)
        if existing:
            raise ConflictError(f"User with email '{data.email}' already exists")

        user = User(
            email=data.email.lower(),
            hashed_password=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            department_id=data.department_id,
            created_by=creator_id,
        )

        for role_name in data.roles:
            role = await auth_service.repo.get_role_by_name(role_name)
            if role:
                user.roles.append(role)

        await auth_service.repo.create_user(user)
        await self.db.commit()

        return await auth_service.get_user_profile(str(user.id))
