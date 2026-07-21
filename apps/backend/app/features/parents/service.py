from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.core.events import event_bus, DomainEvent
from app.features.parents.models import ParentCommunication
from app.features.parents.repository import ParentRepository
from app.features.parents.schemas import (
    ParentCommunicationCreateRequest,
    ParentCommunicationResponse,
)
from app.features.students.repository import StudentRepository
from app.core.enums import TimelineEventType


class ParentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ParentRepository(db)
        self.student_repo = StudentRepository(db)

    async def log_communication(
        self, data: ParentCommunicationCreateRequest, counsellor_id: str
    ) -> ParentCommunicationResponse:
        student = await self.student_repo.get_student_by_id(data.student_id)
        if not student:
            raise NotFoundError("Student not found")

        comm = ParentCommunication(
            student_id=data.student_id,
            counsellor_id=counsellor_id,
            communication_date=data.communication_date,
            communication_time=data.communication_time,
            mode=data.mode.upper(),
            parent_name=data.parent_name,
            relation=data.relation,
            contact_number=data.contact_number,
            summary=data.summary,
            concerns=data.concerns,
            action_items=data.action_items,
            outcome=data.outcome.upper(),
            follow_up_date=data.follow_up_date,
            created_by=counsellor_id,
        )

        created = await self.repo.create_communication(comm)
        await self.db.commit()

        # Emit domain event
        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.PARENT_COMMUNICATION.value,
                student_id=data.student_id,
                actor_id=counsellor_id,
                metadata={
                    "parent_name": data.parent_name,
                    "relation": data.relation,
                    "mode": data.mode,
                    "outcome": data.outcome,
                },
            )
        )

        return ParentCommunicationResponse.model_validate(created)

    async def get_student_communications(
        self, student_id: str
    ) -> List[ParentCommunicationResponse]:
        comms = await self.repo.get_student_communications(student_id)
        return [ParentCommunicationResponse.model_validate(c) for c in comms]
