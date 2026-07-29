from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.permissions import require_permission
from app.core.scoping import ensure_student_assigned_to_counsellor, is_assignment_scoped_counsellor
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.students.repository import StudentRepository
from app.features.counselling.schemas import (
    SessionCreateRequest,
    SessionResponse,
    ActionItemResponse,
    FollowUpStatusUpdateRequest,
    FollowUpUpdateRequest,
    CounsellorDashboardResponse,
)
from app.features.counselling.service import CounsellingService

router = APIRouter(prefix="/counselling", tags=["Counselling Sessions"])


@router.get("/dashboard", response_model=CounsellorDashboardResponse)
async def get_counsellor_dashboard(
    counsellor_id: Optional[str] = Query(None, description="Admin/HOD only; ignored for counsellors"),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("counselling.read")),
    db: AsyncSession = Depends(get_async_db),
):
    """Counsellor landing page. A counsellor always gets their own caseload —
    any counsellor_id they pass is discarded, not honoured."""
    if is_assignment_scoped_counsellor(current_user):
        counsellor_id = str(current_user.id)
    service = CounsellingService(db)
    return await service.get_counsellor_dashboard(counsellor_id)


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreateRequest,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("counselling.create")),
    db: AsyncSession = Depends(get_async_db),
):
    await ensure_student_assigned_to_counsellor(current_user, data.student_id, StudentRepository(db))
    service = CounsellingService(db)
    return await service.create_session(data, str(current_user.id))


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    student_id: Optional[str] = Query(None),
    counsellor_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("counselling.read")),
    db: AsyncSession = Depends(get_async_db),
):
    # A counsellor (not also ADMIN/SUPER_ADMIN/HOD) only ever sees their own
    # caseload — ignore any other counsellor_id they might pass.
    if is_assignment_scoped_counsellor(current_user):
        counsellor_id = str(current_user.id)
    service = CounsellingService(db)
    sessions, _ = await service.list_sessions(
        student_id, counsellor_id, page, per_page, viewer=current_user
    )
    return sessions


@router.get("/my-sessions", response_model=List[SessionResponse])
async def list_my_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("counselling.acknowledge")),
    db: AsyncSession = Depends(get_async_db),
):
    """A student's own counselling history. The student id is resolved from
    the session token, never accepted as a parameter, and confidential notes
    are stripped on the way out."""
    service = CounsellingService(db)
    return await service.list_my_sessions(str(current_user.id), page, per_page, current_user)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("counselling.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = CounsellingService(db)
    return await service.get_session_by_id(session_id, current_user)


@router.get("/follow-ups", response_model=List[ActionItemResponse])
async def list_follow_ups(
    counsellor_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("counselling.read")),
    db: AsyncSession = Depends(get_async_db),
):
    if is_assignment_scoped_counsellor(current_user):
        counsellor_id = str(current_user.id)
    service = CounsellingService(db)
    return await service.list_follow_ups(counsellor_id, status)


@router.patch("/follow-ups/{action_item_id}/status", response_model=ActionItemResponse)
async def update_follow_up_status(
    action_item_id: str,
    data: FollowUpStatusUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("counselling.update")),
    db: AsyncSession = Depends(get_async_db),
):
    """Mark a follow-up complete. The caller is passed through so the service
    can verify the item belongs to one of their own sessions — the permission
    alone does not say WHICH items a counsellor may close."""
    service = CounsellingService(db)
    return await service.update_follow_up_status(action_item_id, data.status, current_user)


@router.patch("/follow-ups/{action_item_id}", response_model=ActionItemResponse)
async def update_follow_up(
    action_item_id: str,
    data: FollowUpUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("counselling.update")),
    db: AsyncSession = Depends(get_async_db),
):
    """Complete and/or reschedule a follow-up in one call — what the
    workspace's one-click follow-up tracker posts. Same ownership rule as
    the status-only route."""
    service = CounsellingService(db)
    return await service.update_follow_up(
        action_item_id,
        current_user=current_user,
        new_status=data.status,
        new_due_date=data.due_date,
    )


@router.post("/sessions/{session_id}/acknowledge", response_model=SessionResponse)
async def acknowledge_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("counselling.acknowledge")),
    db: AsyncSession = Depends(get_async_db),
):
    service = CounsellingService(db)
    return await service.acknowledge_session(session_id, str(current_user.id), current_user)
