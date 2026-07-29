from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.core.permissions import require_permission
from app.core.pagination import PaginatedResponse, PaginationParams
from app.features.admin.schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    AcademicYearCreate,
    AcademicYearUpdate,
    AcademicYearResponse,
    SemesterResponse,
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
)
from app.features.auth.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserProfileResponse,
    UserListItemResponse,
    AdminCreateUserResponse,
    AdminResetPasswordResponse,
    AssignCounsellorRequest,
    SessionResponse,
)
from app.features.admin.service import AdminService

router = APIRouter(prefix="/admin", tags=["Administration & Academic Config"])


# Departments
@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("department.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.create_department(data, str(current_user.id))


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    _: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_departments()


@router.patch("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: str,
    data: DepartmentUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("department.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.update_department(department_id, data, current_user, request)


# Sections
@router.post("/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    data: SectionCreate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("section.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.create_section(data, str(current_user.id))


@router.get("/sections", response_model=List[SectionResponse])
async def list_sections(
    department_id: Optional[str] = Query(None),
    _: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_sections(department_id)


@router.patch("/sections/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: str,
    data: SectionUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("section.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.update_section(section_id, data, current_user, request)


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("section.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    await service.delete_section(section_id, current_user, request)


# Academic Years
@router.post("/academic-years", response_model=AcademicYearResponse, status_code=status.HTTP_201_CREATED)
async def create_academic_year(
    data: AcademicYearCreate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("academic.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.create_academic_year(data, str(current_user.id))


@router.get("/academic-years", response_model=List[AcademicYearResponse])
async def list_academic_years(
    _: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_academic_years()


@router.patch("/academic-years/{academic_year_id}", response_model=AcademicYearResponse)
async def update_academic_year(
    academic_year_id: str,
    data: AcademicYearUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("academic.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.update_academic_year(academic_year_id, data, current_user, request)


# Semesters — fixed institutional catalog (1-1 .. 4-2), seeded once; read-only API.
@router.get("/semesters", response_model=List[SemesterResponse])
async def list_semesters(
    _: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_semesters()


# Subjects
@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    data: SubjectCreate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("subject.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.create_subject(data, str(current_user.id))


@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    department_id: Optional[str] = Query(None),
    _: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_subjects(department_id)


@router.patch("/subjects/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: str,
    data: SubjectUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("subject.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.update_subject(subject_id, data, current_user, request)


# --- User Management ----------------------------------------------------
@router.post("/users", response_model=AdminCreateUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.create_user_by_admin(data, str(current_user.id), current_user, request)


@router.get("/users", response_model=PaginatedResponse[UserListItemResponse])
async def list_users(
    role: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_users(role, department_id, is_active, search, PaginationParams(page=page, per_page=per_page))


@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user(
    user_id: str,
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.get_user(user_id)


@router.patch("/users/{user_id}", response_model=UserProfileResponse)
async def update_user(
    user_id: str,
    data: UserUpdateRequest,
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.update_user(user_id, data)


@router.post("/users/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    await service.deactivate_user(user_id, current_user, request)


@router.post("/users/{user_id}/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    await service.activate_user(user_id, current_user, request)


@router.post("/users/{user_id}/reset-password", response_model=AdminResetPasswordResponse)
async def admin_reset_password(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.admin_reset_password(user_id, current_user, request)


@router.get("/users/{user_id}/sessions", response_model=List[SessionResponse])
async def list_user_sessions(
    user_id: str,
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    return await service.list_user_sessions(user_id)


@router.post("/users/{user_id}/force-logout", status_code=status.HTTP_204_NO_CONTENT)
async def force_logout_user(
    user_id: str,
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    await service.force_logout_user(user_id)


@router.post("/users/assign-counsellor", status_code=status.HTTP_204_NO_CONTENT)
async def assign_counsellor(
    data: AssignCounsellorRequest,
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AdminService(db)
    await service.assign_counsellor(data)


# Bulk provisioning is served by the Office Import module — see
# app/features/imports/router.py, mounted at /admin/imports.
