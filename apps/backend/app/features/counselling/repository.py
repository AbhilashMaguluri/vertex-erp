from typing import List, Optional, Tuple
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.features.counselling.models import CounsellingSession, SessionActionItem
from app.core.enums import FollowUpStatus


class CounsellingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, session: CounsellingSession) -> CounsellingSession:
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session_by_id(self, session_id: str) -> Optional[CounsellingSession]:
        query = (
            select(CounsellingSession)
            .options(selectinload(CounsellingSession.action_items))
            .where(CounsellingSession.id == session_id, CounsellingSession.deleted_at.is_(None))
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def list_sessions(
        self, student_id: Optional[str] = None, counsellor_id: Optional[str] = None, page: int = 1, per_page: int = 20
    ) -> Tuple[List[CounsellingSession], int]:
        query = select(CounsellingSession).where(CounsellingSession.deleted_at.is_(None))
        count_query = select(func.count(CounsellingSession.id)).where(CounsellingSession.deleted_at.is_(None))

        if student_id:
            query = query.where(CounsellingSession.student_id == student_id)
            count_query = count_query.where(CounsellingSession.student_id == student_id)

        if counsellor_id:
            query = query.where(CounsellingSession.counsellor_id == counsellor_id)
            count_query = count_query.where(CounsellingSession.counsellor_id == counsellor_id)

        query = (
            query.options(selectinload(CounsellingSession.action_items))
            .order_by(CounsellingSession.session_date.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )

        sessions_res = await self.db.execute(query)
        count_res = await self.db.execute(count_query)

        return list(sessions_res.scalars().all()), count_res.scalar_one()

    async def list_follow_ups(
        self, counsellor_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[SessionActionItem]:
        query = select(SessionActionItem).join(CounsellingSession)

        if status:
            query = query.where(SessionActionItem.status == status.upper())
        else:
            query = query.where(SessionActionItem.status == FollowUpStatus.PENDING.value)

        if counsellor_id:
            query = query.where(CounsellingSession.counsellor_id == counsellor_id)

        query = query.order_by(SessionActionItem.due_date.asc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def update_action_item_status(self, action_item_id: str, new_status: str) -> Optional[SessionActionItem]:
        query = select(SessionActionItem).where(SessionActionItem.id == action_item_id)
        res = await self.db.execute(query)
        item = res.scalar_one_or_none()

        if item:
            item.status = new_status.upper()
            await self.db.flush()

        return item
