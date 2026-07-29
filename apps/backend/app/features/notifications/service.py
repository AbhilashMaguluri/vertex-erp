from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enums import NotificationCategory
from app.core.exceptions import NotFoundError
from app.features.notifications.models import Notification
from app.features.notifications.repository import NotificationRepository
from app.features.notifications.schemas import (
    CategoryCount,
    NotificationResponse,
    NotificationSummaryResponse,
)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationRepository(db)

    async def list_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        page: int = 1,
        per_page: int = 20,
        category: Optional[str] = None,
    ) -> Tuple[List[NotificationResponse], int]:
        notifs, total = await self.repo.list_user_notifications(
            user_id, unread_only, page, per_page, category
        )
        return [NotificationResponse.model_validate(n) for n in notifs], total

    async def get_unread_count(self, user_id: str) -> int:
        return await self.repo.get_unread_count(user_id)

    async def get_summary(self, user_id: str) -> NotificationSummaryResponse:
        counts = await self.repo.category_counts(user_id)
        # Every category is emitted, including empty ones, so the filter rail
        # has a stable shape instead of tabs appearing and vanishing as
        # notifications arrive and get read.
        by_category = {c: (total, unread) for c, total, unread in counts}
        categories = [
            CategoryCount(
                category=cat.value,
                total=by_category.get(cat.value, (0, 0))[0],
                unread=by_category.get(cat.value, (0, 0))[1],
            )
            for cat in NotificationCategory
        ]
        return NotificationSummaryResponse(
            unread_count=sum(c.unread for c in categories),
            total_count=sum(c.total for c in categories),
            categories=categories,
        )

    async def mark_as_read(self, notification_id: str, user_id: str) -> NotificationResponse:
        notif = await self.repo.mark_as_read(notification_id, user_id)
        if not notif:
            raise NotFoundError("Notification not found")
        await self.db.commit()
        return NotificationResponse.model_validate(notif)

    async def mark_all_as_read(self, user_id: str):
        await self.repo.mark_all_as_read(user_id)
        await self.db.commit()
