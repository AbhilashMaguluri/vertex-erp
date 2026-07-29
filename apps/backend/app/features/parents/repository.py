from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.parents.models import ParentCommunication


class ParentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_communication(self, comm: ParentCommunication) -> ParentCommunication:
        self.db.add(comm)
        await self.db.flush()
        return comm

    async def get_student_communications(self, student_id: str) -> List[ParentCommunication]:
        query = (
            select(ParentCommunication)
            .where(ParentCommunication.student_id == student_id)
            .order_by(ParentCommunication.communication_date.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())
