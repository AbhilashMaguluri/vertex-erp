from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.academics.models import Mark, SGPAHistory, Backlog


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
            existing.recorded_by = mark.recorded_by
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
        query = select(Backlog).where(Backlog.student_id == student_id, Backlog.deleted_at.is_(None))
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create_backlog(self, backlog: Backlog) -> Backlog:
        self.db.add(backlog)
        await self.db.flush()
        return backlog
