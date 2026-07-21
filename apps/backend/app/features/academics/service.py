from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ValidationError
from app.core.events import event_bus, DomainEvent
from app.features.academics.models import Mark, SGPAHistory, Backlog
from app.features.academics.repository import AcademicsRepository
from app.features.academics.schemas import (
    BulkMarksCreate,
    MarksResponse,
    SGPACalculationResponse,
    BacklogResponse,
)
from app.core.enums import TimelineEventType, BacklogStatus


class AcademicsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AcademicsRepository(db)

    async def record_bulk_marks(
        self, data: BulkMarksCreate, faculty_id: str
    ) -> List[MarksResponse]:
        created_list = []
        for item in data.records:
            if item.marks_obtained > item.max_marks:
                raise ValidationError(f"Marks obtained ({item.marks_obtained}) cannot exceed max marks ({item.max_marks}).")

            mark = Mark(
                student_id=item.student_id,
                subject_id=data.subject_id,
                semester_id=data.semester_id,
                assessment_type=data.assessment_type.upper(),
                marks_obtained=item.marks_obtained,
                max_marks=item.max_marks,
                recorded_by_user_id=faculty_id,
            )
            created = await self.repo.create_mark(mark)
            created_list.append(created)

            # Auto-flag backlog if external grade < 40%
            if data.assessment_type.upper() == "EXTERNAL" and (item.marks_obtained / item.max_marks) < 0.40:
                backlog = Backlog(
                    student_id=item.student_id,
                    subject_id=data.subject_id,
                    semester_id=data.semester_id,
                    status=BacklogStatus.ACTIVE.value,
                )
                await self.repo.create_backlog(backlog)

                await event_bus.publish(
                    DomainEvent(
                        type=TimelineEventType.BACKLOG_ADDED.value,
                        student_id=item.student_id,
                        actor_id=faculty_id,
                        metadata={"subject_id": data.subject_id},
                    )
                )

        await self.db.commit()

        # Emit Marks Updated Event
        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.MARKS_UPDATED.value,
                actor_id=faculty_id,
                metadata={"subject_id": data.subject_id, "assessment_type": data.assessment_type},
            )
        )

        return [MarksResponse.model_validate(m) for m in created_list]

    async def calculate_sgpa(self, student_id: str, semester_id: str) -> SGPACalculationResponse:
        marks = await self.repo.get_student_semester_marks(student_id, semester_id)
        if not marks:
            sgpa_val = 0.0
        else:
            percentages = [(m.marks_obtained / m.max_marks) * 10 for m in marks]
            sgpa_val = round(sum(percentages) / len(percentages), 2)

        history = SGPAHistory(
            student_id=student_id,
            semester_id=semester_id,
            sgpa=sgpa_val,
            cgpa=sgpa_val,
            total_credits=20,
        )
        await self.repo.save_sgpa(history)
        await self.db.commit()

        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.SGPA_CALCULATED.value,
                student_id=student_id,
                metadata={"semester_id": semester_id, "sgpa": sgpa_val},
            )
        )

        return SGPACalculationResponse(
            student_id=student_id,
            semester_id=semester_id,
            sgpa=sgpa_val,
            cgpa=sgpa_val,
            total_credits=20,
        )

    async def get_student_backlogs(self, student_id: str) -> List[BacklogResponse]:
        backlogs = await self.repo.get_student_backlogs(student_id)
        return [BacklogResponse.model_validate(b) for b in backlogs]
