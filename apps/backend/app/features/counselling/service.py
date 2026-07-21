from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.events import event_bus, DomainEvent
from app.features.counselling.models import CounsellingSession, SessionActionItem
from app.features.counselling.repository import CounsellingRepository
from app.features.counselling.schemas import (
    SessionCreateRequest,
    SessionResponse,
    ActionItemResponse,
    ComplianceResponse,
)
from app.core.enums import TimelineEventType, FollowUpStatus


class CounsellingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CounsellingRepository(db)

    async def create_session(self, data: SessionCreateRequest, counsellor_id: str) -> SessionResponse:
        if len(data.observations.strip()) < 50:
            raise ValidationError("Observations must contain at least 50 characters (PRD §23.1 requirement)")

        session = CounsellingSession(
            student_id=data.student_id,
            counsellor_id=counsellor_id,
            session_date=data.session_date,
            session_type=data.session_type.upper(),
            mode=data.mode.upper(),
            observations=data.observations,
            follow_up_required=data.follow_up_required,
            follow_up_date=data.follow_up_date,
            risk_assessment=data.risk_assessment.upper() if data.risk_assessment else "NONE",
            confidential=data.confidential,
        )

        if data.action_items:
            for item in data.action_items:
                action = SessionActionItem(
                    description=item.description,
                    due_date=item.due_date,
                    status=FollowUpStatus.PENDING.value,
                    assigned_to_user_id=item.assigned_to_user_id,
                )
                session.action_items.append(action)

        created_session = await self.repo.create_session(session)
        await self.db.commit()

        # Emit Domain Events
        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.SESSION_CONDUCTED.value,
                student_id=data.student_id,
                actor_id=counsellor_id,
                metadata={
                    "session_id": str(created_session.id),
                    "session_type": created_session.session_type,
                    "mode": created_session.mode,
                    "follow_up_required": created_session.follow_up_required,
                },
            )
        )

        if created_session.action_items:
            for item in created_session.action_items:
                await event_bus.publish(
                    DomainEvent(
                        type=TimelineEventType.FOLLOW_UP_CREATED.value,
                        student_id=data.student_id,
                        actor_id=counsellor_id,
                        metadata={
                            "action_item_id": str(item.id),
                            "description": item.description,
                            "due_date": str(item.due_date),
                        },
                    )
                )

        return SessionResponse.model_validate(created_session)

    async def get_session_by_id(self, session_id: str) -> SessionResponse:
        session = await self.repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundError("Counselling session not found")
        return SessionResponse.model_validate(session)

    async def list_sessions(
        self, student_id: Optional[str] = None, counsellor_id: Optional[str] = None, page: int = 1, per_page: int = 20
    ) -> Tuple[List[SessionResponse], int]:
        sessions, total = await self.repo.list_sessions(student_id, counsellor_id, page, per_page)
        return [SessionResponse.model_validate(s) for s in sessions], total

    async def list_follow_ups(
        self, counsellor_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[ActionItemResponse]:
        items = await self.repo.list_follow_ups(counsellor_id, status)
        return [ActionItemResponse.model_validate(i) for i in items]

    async def update_follow_up_status(self, action_item_id: str, new_status: str) -> ActionItemResponse:
        updated = await self.repo.update_action_item_status(action_item_id, new_status)
        if not updated:
            raise NotFoundError("Follow-up action item not found")
        await self.db.commit()
        return ActionItemResponse.model_validate(updated)

    async def acknowledge_session(self, session_id: str, student_user_id: str) -> SessionResponse:
        session = await self.repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundError("Counselling session not found")

        session.student_acknowledged = True
        session.acknowledged_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Emit acknowledgment event
        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.SESSION_ACKNOWLEDGED.value,
                student_id=str(session.student_id),
                actor_id=student_user_id,
                metadata={"session_id": session_id},
            )
        )

        return SessionResponse.model_validate(session)
