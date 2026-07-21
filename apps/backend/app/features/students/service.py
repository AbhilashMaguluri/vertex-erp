from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.core.events import event_bus, DomainEvent
from app.features.students.repository import StudentRepository
from app.features.students.schemas import (
    StudentProfileResponse,
    Student360Response,
    OverviewStat,
    RiskFlagUpdateRequest,
)
from app.features.admin.repository import AdminRepository
from app.core.enums import TimelineEventType


class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StudentRepository(db)
        self.admin_repo = AdminRepository(db)

    async def get_student_profile(self, student_id: str) -> StudentProfileResponse:
        student = await self.repo.get_student_by_id(student_id)
        if not student:
            raise NotFoundError("Student not found")

        dept_name = None
        if student.department_id:
            dept = await self.admin_repo.get_department_by_id(str(student.department_id))
            if dept:
                dept_name = dept.name

        counsellor_name = None
        if student.counsellor_assignments:
            active_assign = next(
                (a for a in student.counsellor_assignments if a.effective_to is None), None
            )
            if active_assign and active_assign.counsellor:
                counsellor_name = active_assign.counsellor.full_name

        return StudentProfileResponse(
            id=str(student.id),
            user_id=str(student.user_id),
            roll_number=student.roll_number,
            registration_number=student.registration_number,
            full_name=student.user.full_name if student.user else "Unknown",
            email=student.user.email if student.user else "",
            phone=student.user.phone if student.user else None,
            date_of_birth=student.date_of_birth,
            batch_year=student.batch_year,
            status=student.status,
            risk_level=student.risk_level,
            department_id=str(student.department_id),
            department_name=dept_name,
            current_semester_id=str(student.current_semester_id) if student.current_semester_id else None,
            counsellor_name=counsellor_name,
            father_name=student.father_name,
            father_phone=student.father_phone,
            mother_name=student.mother_name,
            mother_phone=student.mother_phone,
            guardian_name=student.guardian_name,
            guardian_phone=student.guardian_phone,
            created_at=student.created_at,
            updated_at=student.updated_at,
        )

    async def get_student_360_workspace(self, student_id: str) -> Student360Response:
        profile = await self.get_student_profile(student_id)

        stats = [
            OverviewStat(
                title="Overall Attendance",
                value="82.4%",
                change="+1.2%",
                trend="up",
                description="Above 75% threshold",
            ),
            OverviewStat(
                title="Current SGPA",
                value="8.4",
                change="+0.3",
                trend="up",
                description="Semester 4 SGPA",
            ),
            OverviewStat(
                title="Active Backlogs",
                value="0",
                trend="neutral",
                description="All subjects cleared",
            ),
            OverviewStat(
                title="Risk Level",
                value=profile.risk_level,
                trend="neutral",
                description=f"Current Status: {profile.status}",
            ),
        ]

        attention_items = []
        if profile.risk_level in ["HIGH", "CRITICAL"]:
            attention_items.append(f"Student is flagged as {profile.risk_level} risk level.")

        return Student360Response(
            profile=profile,
            stats=stats,
            attention_items=attention_items,
            recent_events=[],
        )

    async def update_risk_flag(
        self, student_id: str, data: RiskFlagUpdateRequest, actor_id: str
    ) -> StudentProfileResponse:
        student = await self.repo.get_student_by_id(student_id)
        if not student:
            raise NotFoundError("Student not found")

        old_risk = student.risk_level
        student.risk_level = data.risk_level.upper()
        student.updated_by = actor_id
        await self.db.commit()

        # Emit domain event for Universal Timeline & Notification subscribers
        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.RISK_FLAG_CHANGED.value,
                student_id=str(student.id),
                actor_id=actor_id,
                metadata={
                    "previous_risk_level": old_risk,
                    "new_risk_level": student.risk_level,
                    "reason": data.reason,
                },
            )
        )

        return await self.get_student_profile(student_id)
