from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.exceptions import ForbiddenError
from app.core.pagination import PaginatedResponse
from app.core.permissions import require_permission
from app.core.scoping import (
    ensure_student_assigned_to_counsellor,
    is_assignment_scoped_counsellor,
)
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.students.schemas import (
    StudentProfileResponse,
    Student360Response,
    RosterStudentResponse,
    RiskFlagUpdateRequest,
    CaseloadStudentResponse,
    CaseloadFacets,
    SessionContextResponse,
    AcademicCorrectionCreate,
    AcademicCorrectionReview,
    AcademicCorrectionClarification,
    AcademicCorrectionResponse,
)

from app.features.students.repository import CASELOAD_SORT_FIELDS, StudentRepository
from app.features.students.service import StudentService

router = APIRouter(prefix="/students", tags=["Student Workspace"])


def _resolve_caseload_scope(current_user: User, counsellor_id: Optional[str]) -> Optional[str]:
    """A counsellor's caseload is always their own — any counsellor_id they
    pass is ignored rather than honoured, so the filter can't be used to read
    another counsellor's students. ADMIN/SUPER_ADMIN/HOD are institution-wide
    and may scope to a specific counsellor, or omit it to see everyone."""
    # Defence in depth. student.caseload.read is never granted to STUDENT, so
    # this should be unreachable — but an unscoped caseload is an institution
    # roster, and that must fail closed if the grant is ever mis-edited.
    if "STUDENT" in {r.name for r in current_user.roles}:
        raise ForbiddenError("Students cannot browse other student records.")
    if is_assignment_scoped_counsellor(current_user):
        return str(current_user.id)
    return counsellor_id


@router.get("/caseload", response_model=PaginatedResponse[CaseloadStudentResponse])
async def list_caseload(
    search: Optional[str] = Query(
        None,
        description="Roll number, registration number, name, email, phone, branch or section",
    ),
    year: Optional[int] = Query(None, ge=1, le=4),
    section_id: Optional[str] = Query(None),
    semester_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    batch_year: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_attendance: Optional[float] = Query(None, ge=0, le=100),
    max_attendance: Optional[float] = Query(None, ge=0, le=100),
    min_cgpa: Optional[float] = Query(None, ge=0, le=10),
    max_cgpa: Optional[float] = Query(None, ge=0, le=10),
    has_backlogs: Optional[bool] = Query(None),
    counsellor_id: Optional[str] = Query(None, description="Admin/HOD only; ignored for counsellors"),
    sort_by: str = Query("roll_number"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.caseload.read")),
    db: AsyncSession = Depends(get_async_db),
):
    """The counsellor portal's primary listing: assigned students with the
    metrics that drive intervention, filterable and paginated server-side."""
    if sort_by not in CASELOAD_SORT_FIELDS:
        sort_by = "roll_number"
    service = StudentService(db)
    return await service.list_caseload(
        page=page,
        per_page=per_page,
        counsellor_id=_resolve_caseload_scope(current_user, counsellor_id),
        search=search,
        year=year,
        section_id=section_id,
        semester_id=semester_id,
        department_id=department_id,
        batch_year=batch_year,
        risk_level=risk_level,
        status=status,
        min_attendance=min_attendance,
        max_attendance=max_attendance,
        min_cgpa=min_cgpa,
        max_cgpa=max_cgpa,
        has_backlogs=has_backlogs,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get("/caseload/facets", response_model=CaseloadFacets)
async def get_caseload_facets(
    counsellor_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.caseload.read")),
    db: AsyncSession = Depends(get_async_db),
):
    """Filter options drawn from the caller's own caseload. Same permission as
    the list itself — the distinct sections/batches of a caseload the caller
    cannot read would still leak its shape."""
    service = StudentService(db)
    return await service.get_caseload_facets(_resolve_caseload_scope(current_user, counsellor_id))


@router.get("/{student_id}/session-context", response_model=SessionContextResponse)
async def get_session_context(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("counselling.create")),
    db: AsyncSession = Depends(get_async_db),
):
    """Prefill for the session recorder. Gated on counselling.create (not
    student.read) because it exists solely to open a session — students hold
    student.read and must never reach it."""
    await ensure_student_assigned_to_counsellor(current_user, student_id, StudentRepository(db))
    service = StudentService(db)
    return await service.get_session_context(student_id)


@router.get("/roster", response_model=List[RosterStudentResponse])
async def get_section_roster(
    section_id: str = Query(...),
    semester_id: str = Query(...),
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    return await service.get_section_roster(section_id, semester_id)


@router.get("/me/workspace", response_model=Student360Response)
async def get_my_workspace(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    student_id = await service.get_my_student_id(str(current_user.id))
    return await service.get_student_360_workspace(student_id)


@router.get("/{student_id}/workspace", response_model=Student360Response)
async def get_student_360_workspace(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    await ensure_student_assigned_to_counsellor(current_user, student_id, StudentRepository(db))
    return await service.get_student_360_workspace(student_id)


@router.get("/{student_id}", response_model=StudentProfileResponse)
async def get_student_profile(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    await ensure_student_assigned_to_counsellor(current_user, student_id, StudentRepository(db))
    return await service.get_student_profile(student_id)


@router.get("/{student_id}/360/personal")
async def get_student_360_personal(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Retrieve Student 360 Personal Details section (Identity, Contact, Parent, Emergency, Residence, Links, Staff)."""
    service = StudentService(db)
    p_service = StudentProfileService(db)
    target_id = student_id
    if student_id == "me":
        target_id = await service.get_my_student_id(str(current_user.id))
    return await p_service.get_self_profile(target_id)


@router.get("/{student_id}/360/academic")
async def get_student_360_academic(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Retrieve Student 360 Academic Details section (Enrollment, CGPA/GPA History, Credits, Backlogs)."""
    service = StudentService(db)
    target_id = student_id
    if student_id == "me":
        target_id = await service.get_my_student_id(str(current_user.id))
    return await service.get_student_360_workspace(target_id)


@router.patch("/{student_id}/risk", response_model=StudentProfileResponse)
async def update_student_risk_flag(
    student_id: str,
    data: RiskFlagUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.risk.update")),
    db: AsyncSession = Depends(get_async_db),
):
    await ensure_student_assigned_to_counsellor(current_user, student_id, StudentRepository(db))
    service = StudentService(db)
    return await service.update_risk_flag(student_id, data, str(current_user.id))


# ------------------------------------------------------------------
# Academic Record Correction Request & CRM Workflow Endpoints
# ------------------------------------------------------------------

@router.post("/me/academic-corrections", response_model=AcademicCorrectionResponse, status_code=status.HTTP_201_CREATED)
async def create_my_academic_correction_request(
    data: AcademicCorrectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    return await service.create_academic_correction_request(str(current_user.id), data)


@router.get("/me/academic-corrections", response_model=List[AcademicCorrectionResponse])
async def list_my_academic_corrections(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    return await service.list_my_academic_corrections(str(current_user.id))


@router.get("/academic-corrections/caseload", response_model=List[AcademicCorrectionResponse])
async def list_caseload_academic_corrections(
    counsellor_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.caseload.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    target_counsellor = _resolve_caseload_scope(current_user, counsellor_id)
    return await service.list_counsellor_academic_corrections(target_counsellor)


@router.get("/academic-corrections/{request_id}", response_model=AcademicCorrectionResponse)
async def get_academic_correction_request(
    request_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    return await service.get_academic_correction(request_id)


@router.patch("/academic-corrections/{request_id}/review", response_model=AcademicCorrectionResponse)
async def review_academic_correction_request(
    request_id: str,
    data: AcademicCorrectionReview,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.caseload.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    return await service.review_academic_correction(request_id, str(current_user.id), data)


@router.post("/academic-corrections/{request_id}/clarification", response_model=AcademicCorrectionResponse)
async def submit_academic_correction_clarification(
    request_id: str,
    data: AcademicCorrectionClarification,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    return await service.submit_clarification(request_id, str(current_user.id), data)

