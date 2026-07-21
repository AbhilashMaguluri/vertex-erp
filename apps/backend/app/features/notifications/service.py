from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.features.notifications.models import Notification
from app.features.notifications.repository import NotificationRepository
from app.features.notifications.schemas import NotificationResponse


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationRepository(db)

    async def list_user_notifications(
        self, user_id: str, unread_only: bool = False, page: int = 1, per_page: int = 20
    ) -> Tuple[List[NotificationResponse], int]:
        notifs, total = await self.repo.list_user_notifications(user_id, unread_only, page, per_page)
        return [NotificationResponse.model_validate(n) for n in notifs], total

    async def get_unread_count(self, user_id: str) -> int:
        return await self.repo.get_unread_count(user_id)

    async def mark_as_read(self, notification_id: str, user_id: str) -> NotificationResponse:
        notif = await self.repo.mark_as_read(notification_id, user_id)
        if not notif:
            raise NotFoundError("Notification not found")
        await self.db.commit()
        return NotificationResponse.model_validate(notif)

    async def mark_all_as_read(self, user_id: str):
        await self.repo.mark_all_as_read(user_id)
        await self.db.commit()
