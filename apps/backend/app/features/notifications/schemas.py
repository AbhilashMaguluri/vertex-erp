from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: UUID | str
    user_id: UUID | str
    type: str
    category: str
    priority: str
    title: str
    message: str
    action_url: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class CategoryCount(BaseModel):
    category: str
    total: int
    unread: int


class NotificationSummaryResponse(BaseModel):
    """Per-category counts for the notification centre's filter rail."""

    unread_count: int
    total_count: int
    categories: List[CategoryCount] = []
