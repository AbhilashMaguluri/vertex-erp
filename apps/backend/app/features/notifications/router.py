from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.notifications.schemas import (
    NotificationResponse,
    NotificationSummaryResponse,
    NotificationUnreadCountResponse,
)
from app.features.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notification Center"])


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    category: Optional[str] = Query(None, description="ACADEMIC, COUNSELLING, ATTENDANCE, PARENT_COMMUNICATION, PLACEMENT, SYSTEM"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = NotificationService(db)
    notifs, _ = await service.list_user_notifications(
        str(current_user.id), unread_only, page, per_page, category
    )
    return notifs


@router.get("/summary", response_model=NotificationSummaryResponse)
async def get_notification_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Unread/total per category, for the notification centre's filter rail."""
    service = NotificationService(db)
    return await service.get_summary(str(current_user.id))


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = NotificationService(db)
    count = await service.get_unread_count(str(current_user.id))
    return NotificationUnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = NotificationService(db)
    return await service.mark_as_read(notification_id, str(current_user.id))


@router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = NotificationService(db)
    await service.mark_all_as_read(str(current_user.id))
    return None
