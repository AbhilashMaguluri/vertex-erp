from typing import Any, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.academics.models import Mark, SGPAHistory, Backlog
from app.features.admin.models import Semester, Subject


class AcademicsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_mark(self, mark: Mark) -> Mark:
        query = select(Mark).where(
            Mark.student_id == mark.student_id,
            Mark.subject_id == mark.subject_id,
            Mark.semester_id == mark.semester_id,
            Mark.assessment_type == mark.assessment_type,
        )
        res = await self.db.execute(query)
        existing = res.scalar_one_or_none()
        if existing:
            existing.marks_obtained = mark.marks_obtained
            existing.max_marks = mark.max_marks
            existing.recorded_by_user_id = mark.recorded_by_user_id
            return existing
        else:
            self.db.add(mark)
            return mark

    async def get_student_marks(self, student_id: str, semester_id: Optional[str] = None) -> List[Mark]:
        query = select(Mark).where(Mark.student_id == student_id)
        if semester_id:
            query = query.where(Mark.semester_id == semester_id)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_student_marks_detailed(self, student_id: str) -> List[Any]:
        """Every recorded mark for a student, already joined to its subject and
        semester so the transcript can be assembled without a per-row lookup."""
        query = (
            select(
                Mark.assessment_type,
                Mark.marks_obtained,
                Mark.max_marks,
                Subject.id.label("subject_id"),
                Subject.code.label("subject_code"),
                Subject.name.label("subject_name"),
                Subject.credits,
                Semester.id.label("semester_id"),
                Semester.name.label("semester_name"),
                Semester.number.label("semester_number"),
            )
            .join(Subject, Subject.id == Mark.subject_id)
            .join(Semester, Semester.id == Mark.semester_id)
            .where(Mark.student_id == student_id)
            .order_by(Semester.number, Subject.code)
        )
        res = await self.db.execute(query)
        return list(res.all())

    async def save_sgpa_history(self, sgpa_entry: SGPAHistory) -> SGPAHistory:
        query = select(SGPAHistory).where(
            SGPAHistory.student_id == sgpa_entry.student_id,
            SGPAHistory.semester_id == sgpa_entry.semester_id,
        )
        res = await self.db.execute(query)
        existing = res.scalar_one_or_none()
        if existing:
            existing.sgpa = sgpa_entry.sgpa
            existing.cgpa = sgpa_entry.cgpa
            existing.total_credits = sgpa_entry.total_credits
            existing.earned_credits = sgpa_entry.earned_credits
            return existing
        else:
            self.db.add(sgpa_entry)
            return sgpa_entry

    async def get_student_sgpa_history(self, student_id: str) -> List[SGPAHistory]:
        query = select(SGPAHistory).where(SGPAHistory.student_id == student_id).order_by(SGPAHistory.created_at.asc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_student_backlogs(self, student_id: str) -> List[Backlog]:
        query = select(Backlog).where(Backlog.student_id == student_id)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create_backlog(self, backlog: Backlog) -> Backlog:
        self.db.add(backlog)
        await self.db.flush()
        return backlog

    async def list_all_sgpa_histories(self) -> List[SGPAHistory]:
        res = await self.db.execute(select(SGPAHistory))
        return list(res.scalars().all())

    async def list_all_active_backlogs(self) -> List[Backlog]:
        query = select(Backlog).where(Backlog.status == "ACTIVE")
        res = await self.db.execute(query)
        return list(res.scalars().all())
