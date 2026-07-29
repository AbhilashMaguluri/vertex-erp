from datetime import date
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.attendance.models import AttendanceRecord, AttendanceCorrection


class AttendanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_attendance_record(self, record: AttendanceRecord) -> AttendanceRecord:
        # Check if record exists
        query = select(AttendanceRecord).where(
            AttendanceRecord.student_id == record.student_id,
            AttendanceRecord.subject_id == record.subject_id,
            AttendanceRecord.date == record.date,
        )
        res = await self.db.execute(query)
        existing = res.scalar_one_or_none()
        if existing:
            existing.status = record.status
            existing.recorded_by_user_id = record.recorded_by_user_id
            await self.db.flush()
            return existing
        else:
            self.db.add(record)
            await self.db.flush()
            return record

    async def get_record_by_id(self, record_id: str) -> Optional[AttendanceRecord]:
        query = select(AttendanceRecord).where(AttendanceRecord.id == record_id)
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def list_all_records(self) -> List[AttendanceRecord]:
        res = await self.db.execute(select(AttendanceRecord))
        return list(res.scalars().all())

    async def get_student_attendance_records(self, student_id: str) -> List[AttendanceRecord]:
        query = (
            select(AttendanceRecord)
            .where(AttendanceRecord.student_id == student_id)
            .order_by(AttendanceRecord.date.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_subject_attendance_records(
        self, subject_id: str, attendance_date: Optional[date] = None
    ) -> List[AttendanceRecord]:
        query = select(AttendanceRecord).where(AttendanceRecord.subject_id == subject_id)
        if attendance_date:
            query = query.where(AttendanceRecord.date == attendance_date)
        query = query.order_by(AttendanceRecord.date.desc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create_correction(self, correction: AttendanceCorrection) -> AttendanceCorrection:
        self.db.add(correction)
        await self.db.flush()
        return correction

    async def get_correction_by_id(self, correction_id: str) -> Optional[AttendanceCorrection]:
        query = select(AttendanceCorrection).where(AttendanceCorrection.id == correction_id)
        res = await self.db.execute(query)
        return res.scalar_one_or_none()
