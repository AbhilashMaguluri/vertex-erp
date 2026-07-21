from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.notifications.models import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(self, notification: Notification) -> Notification:
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def list_user_notifications(
        self, user_id: str, unread_only: bool = False, page: int = 1, per_page: int = 20
    ) -> Tuple[List[Notification], int]:
        query = select(Notification).where(Notification.user_id == user_id)
        count_query = select(func.count(Notification.id)).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read.is_(False))
            count_query = count_query.where(Notification.is_read.is_(False))

        query = query.order_by(Notification.created_at.desc()).offset((page - 1) * per_page).limit(per_page)

        notifs_res = await self.db.execute(query)
        count_res = await self.db.execute(count_query)

        return list(notifs_res.scalars().all()), count_res.scalar_one()

    async def get_unread_count(self, user_id: str) -> int:
        query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        )
        res = await self.db.execute(query)
        return res.scalar_one()

    async def mark_as_read(self, notification_id: str, user_id: str) -> Optional[Notification]:
        query = select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        res = await self.db.execute(query)
        notif = res.scalar_one_or_none()
        if notif:
            notif.is_read = True
            notif.read_at = datetime.now(timezone.utc)
            await self.db.flush()
        return notif

    async def mark_all_as_read(self, user_id: str):
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
