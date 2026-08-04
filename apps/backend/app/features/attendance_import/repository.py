"""Repository layer for the Attendance Import feature.

Handles database queries for batches, student lookups, existing attendance
records, and subject metadata.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.admin.models import Department, Section, Subject
from app.features.attendance.models import AttendanceRecord
from app.features.attendance_import.models import AttendanceImportBatch, AttendanceImportRecord
from app.features.students.models import Student

logger = logging.getLogger("app.attendance_import.repository")


class AttendanceImportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Batch management
    # ------------------------------------------------------------------
    async def create_batch(self, batch: AttendanceImportBatch) -> AttendanceImportBatch:
        self.db.add(batch)
        await self.db.flush()
        return batch

    async def get_batch(self, batch_id: str) -> Optional[AttendanceImportBatch]:
        query = (
            select(AttendanceImportBatch)
            .where(AttendanceImportBatch.id == batch_id)
            .options(
                selectinload(AttendanceImportBatch.imported_by),
                selectinload(AttendanceImportBatch.subject),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_batches(self, limit: int = 20) -> List[AttendanceImportBatch]:
        query = (
            select(AttendanceImportBatch)
            .options(
                selectinload(AttendanceImportBatch.imported_by),
                selectinload(AttendanceImportBatch.subject),
            )
            .order_by(AttendanceImportBatch.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def batch_statistics(self) -> dict:
        query = select(
            func.count(AttendanceImportBatch.id).label("total"),
            func.sum(case(
                (AttendanceImportBatch.status == "COMPLETED", 1), else_=0
            )).label("completed"),
            func.coalesce(func.sum(AttendanceImportBatch.records_created), 0).label("created"),
            func.coalesce(func.sum(AttendanceImportBatch.records_updated), 0).label("updated"),
            func.max(AttendanceImportBatch.created_at).label("last_at"),
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

    async def add_records(self, records: Sequence[AttendanceImportRecord]) -> None:
        if not records:
            return
        self.db.add_all(list(records))
        await self.db.flush()

    async def list_records(self, batch_id: str, limit: int = 500) -> List[AttendanceImportRecord]:
        query = (
            select(AttendanceImportRecord)
            .where(AttendanceImportRecord.batch_id == batch_id)
            .order_by(
                AttendanceImportRecord.source_row_number,
                AttendanceImportRecord.identifier,
            )
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Student lookups (batched)
    # ------------------------------------------------------------------
    async def get_students_by_rolls(self, roll_numbers: Sequence[str]) -> Dict[str, Student]:
        """Find existing students by roll number. Returns {roll_upper: Student}."""
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
    # Attendance Record lookups (batched)
    # ------------------------------------------------------------------
    async def get_existing_attendance(
        self,
        student_ids: Sequence[str],
        subject_id: str,
        att_date: date,
    ) -> Dict[str, AttendanceRecord]:
        """Find existing attendance records for given student_ids, subject_id, and date.

        Returns {student_id_str: AttendanceRecord}.
        """
        if not student_ids or not subject_id or not att_date:
            return {}
        found: Dict[str, AttendanceRecord] = {}
        for start in range(0, len(student_ids), 500):
            chunk = list(student_ids[start: start + 500])
            query = select(AttendanceRecord).where(
                AttendanceRecord.student_id.in_(chunk),
                AttendanceRecord.subject_id == subject_id,
                AttendanceRecord.date == att_date,
            )
            result = await self.db.execute(query)
            for att in result.scalars().all():
                found[str(att.student_id)] = att
        return found

    # ------------------------------------------------------------------
    # Academic catalog helpers
    # ------------------------------------------------------------------
    async def get_subject(self, subject_id: str) -> Optional[Subject]:
        result = await self.db.execute(
            select(Subject).where(Subject.id == subject_id, Subject.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_subjects(self, department_id: Optional[str] = None) -> List[Subject]:
        query = select(Subject).where(Subject.deleted_at.is_(None))
        if department_id:
            query = query.where(Subject.department_id == department_id)
        query = query.order_by(Subject.code)
        result = await self.db.execute(query)
        return list(result.scalars().all())
