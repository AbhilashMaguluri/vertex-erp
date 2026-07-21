from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.core.permissions import require_permission
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
from app.features.admin.service import AdminService

router = APIRouter(prefix="/admin", tags=["Administration & Academic Config"])


# Departments
@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("department.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.create_department(data, str(current_user.id))


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_departments()


# Sections
@router.post("/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    data: SectionCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("section.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.create_section(data, str(current_user.id))


@router.get("/sections", response_model=List[SectionResponse])
async def list_sections(
    department_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_sections(department_id)


# Academic Years
@router.post("/academic-years", response_model=AcademicYearResponse, status_code=status.HTTP_201_CREATED)
async def create_academic_year(
    data: AcademicYearCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("academic.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.create_academic_year(data, str(current_user.id))


@router.get("/academic-years", response_model=List[AcademicYearResponse])
async def list_academic_years(
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_academic_years()


# Semesters
@router.post("/semesters", response_model=SemesterResponse, status_code=status.HTTP_201_CREATED)
async def create_semester(
    data: SemesterCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("academic.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.create_semester(data, str(current_user.id))


@router.get("/semesters", response_model=List[SemesterResponse])
async def list_semesters(
    academic_year_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_semesters(academic_year_id)


# Subjects
@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    data: SubjectCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("subject.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.create_subject(data, str(current_user.id))


@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    department_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_subjects(department_id)


# User Management
@router.post("/users", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreateRequest,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.create_user_by_admin(data, str(current_user.id))
