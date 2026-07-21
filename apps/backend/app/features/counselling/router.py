from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.permissions import require_permission
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.counselling.schemas import (
    SessionCreateRequest,
    SessionResponse,
    ActionItemResponse,
    FollowUpStatusUpdateRequest,
)
from app.features.counselling.service import CounsellingService

router = APIRouter(prefix="/counselling", tags=["Counselling Sessions"])


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("counselling.create")),
    db: AsyncSession = Depends(get_async_db),
):
    service = CounsellingService(db)
    return await service.create_session(data, str(current_user.id))


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    student_id: Optional[str] = Query(None),
    counsellor_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _: bool = Depends(require_permission("counselling.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = CounsellingService(db)
    sessions, _ = await service.list_sessions(student_id, counsellor_id, page, per_page)
    return sessions


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    _: bool = Depends(require_permission("counselling.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = CounsellingService(db)
    return await service.get_session_by_id(session_id)


@router.get("/follow-ups", response_model=List[ActionItemResponse])
async def list_follow_ups(
    counsellor_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    _: bool = Depends(require_permission("counselling.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = CounsellingService(db)
    return await service.list_follow_ups(counsellor_id, status)


@router.patch("/follow-ups/{action_item_id}/status", response_model=ActionItemResponse)
async def update_follow_up_status(
    action_item_id: str,
    data: FollowUpStatusUpdateRequest,
    _: bool = Depends(require_permission("counselling.update")),
    db: AsyncSession = Depends(get_async_db),
):
    service = CounsellingService(db)
    return await service.update_follow_up_status(action_item_id, data.status)


@router.post("/sessions/{session_id}/acknowledge", response_model=SessionResponse)
async def acknowledge_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("counselling.acknowledge")),
    db: AsyncSession = Depends(get_async_db),
):
    service = CounsellingService(db)
    return await service.acknowledge_session(session_id, str(current_user.id))
