"""Repository layer for Marks Import & Assessment Management."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.academics.models import Mark
from app.features.admin.models import Subject
from app.features.marks_import.models import MarksImportBatch, MarksImportRecord
from app.features.students.models import Student

logger = logging.getLogger("app.marks_import.repository")


class MarksImportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Batch management
    # ------------------------------------------------------------------
    async def create_batch(self, batch: MarksImportBatch) -> MarksImportBatch:
        self.db.add(batch)
        await self.db.flush()
        return batch

    async def get_batch(self, batch_id: str) -> Optional[MarksImportBatch]:
        query = (
            select(MarksImportBatch)
            .where(MarksImportBatch.id == batch_id)
            .options(
                selectinload(MarksImportBatch.imported_by),
                selectinload(MarksImportBatch.subject),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_batches(self, limit: int = 20) -> List[MarksImportBatch]:
        query = (
            select(MarksImportBatch)
            .options(
                selectinload(MarksImportBatch.imported_by),
                selectinload(MarksImportBatch.subject),
            )
            .order_by(MarksImportBatch.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def batch_statistics(self) -> dict:
        query = select(
            func.count(MarksImportBatch.id).label("total"),
            func.sum(case(
                (MarksImportBatch.status == "COMPLETED", 1), else_=0
            )).label("completed"),
            func.coalesce(func.sum(MarksImportBatch.records_created), 0).label("created"),
            func.coalesce(func.sum(MarksImportBatch.records_updated), 0).label("updated"),
            func.max(MarksImportBatch.created_at).label("last_at"),
        )
        row = (await self.db.execute(query)).first()
        total = int(row.total or 0)
        completed = int(row.completed or 0)
        return {
            "total": total,
            "completed": completed,
            "created": int(row.created or 0),
            "updated": int(row.updated or 0),
            "last_at": row.last_at,
            "success_rate": round((completed / total) * 100, 1) if total else 0.0,
        }

    async def add_records(self, records: Sequence[MarksImportRecord]) -> None:
        if not records:
            return
        self.db.add_all(list(records))
        await self.db.flush()

    async def list_records(self, batch_id: str, limit: int = 500) -> List[MarksImportRecord]:
        query = (
            select(MarksImportRecord)
            .where(MarksImportRecord.batch_id == batch_id)
            .order_by(
                MarksImportRecord.source_row_number,
                MarksImportRecord.identifier,
            )
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Student lookups (batched)
    # ------------------------------------------------------------------
    async def get_students_by_rolls(self, roll_numbers: Sequence[str]) -> Dict[str, Student]:
        if not roll_numbers:
            return {}
        found: Dict[str, Student] = {}
        rolls = [r.upper() for r in roll_numbers]
        for start in range(0, len(rolls), 500):
            chunk = rolls[start: start + 500]
            query = (
                select(Student)
                .where(Student.roll_number.in_(chunk), Student.deleted_at.is_(None))
                .options(selectinload(Student.user))
            )
            result = await self.db.execute(query)
            for student in result.scalars().all():
                found[student.roll_number.upper()] = student
        return found

    # ------------------------------------------------------------------
    # Mark lookups (batched)
    # ------------------------------------------------------------------
    async def get_existing_marks(
        self,
        student_ids: Sequence[str],
        subject_id: str,
        semester_id: str,
        assessment_code: str,
    ) -> Dict[str, Mark]:
        """Find existing Mark records for student_ids, subject_id, semester_id, and assessment_code.

        Returns {student_id_str: Mark}.
        """
        if not student_ids or not subject_id or not semester_id:
            return {}
        found: Dict[str, Mark] = {}
        for start in range(0, len(student_ids), 500):
            chunk = list(student_ids[start: start + 500])
            query = select(Mark).where(
                Mark.student_id.in_(chunk),
                Mark.subject_id == subject_id,
                Mark.semester_id == semester_id,
                Mark.assessment_type == assessment_code.upper(),
            )
            result = await self.db.execute(query)
            for mark in result.scalars().all():
                found[str(mark.student_id)] = mark
        return found

    async def get_subject(self, subject_id: str) -> Optional[Subject]:
        result = await self.db.execute(
            select(Subject).where(Subject.id == subject_id, Subject.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
