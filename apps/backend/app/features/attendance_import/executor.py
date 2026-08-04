"""Attendance Import Executor — executes attendance record writes inside a transaction."""
from __future__ import annotations

import logging
from datetime import date
from typing import Dict, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import TimelineEventType
from app.core.events import DomainEvent, event_bus
from app.features.attendance.models import AttendanceRecord
from app.features.attendance_import.models import AttendanceImportRecord
from app.features.attendance_import.repository import AttendanceImportRepository
from app.features.attendance_import.schemas import (
    AttendanceImportConfiguration,
    ResolvedAttendanceEntry,
)
from app.features.students.models import Student

logger = logging.getLogger("app.attendance_import.executor")


class AttendanceImportExecutor:
    """Executes attendance imports within a database transaction."""

    def __init__(self, db: AsyncSession, repo: AttendanceImportRepository):
        self.db = db
        self.repo = repo

    async def execute_import(
        self,
        entries: List[ResolvedAttendanceEntry],
        config: AttendanceImportConfiguration,
        student_map: Dict[str, Student],
        actor_id: str,
    ) -> Tuple[List[AttendanceImportRecord], int, int, int, int]:
        """Execute attendance record writes inside a transaction.

        Returns (records, created_count, updated_count, skipped_count, failed_count).
        """
        records: List[AttendanceImportRecord] = []
        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0

        # Load existing attendance records for the target date and subject
        student_ids = [str(s.id) for s in student_map.values()]
        existing_att_map = await self.repo.get_existing_attendance(
            student_ids, config.subject_id, config.attendance_date,
        )

        for entry in entries:
            roll_upper = entry.roll_number.upper()
            student = student_map.get(roll_upper)

            if not student:
                failed_count += 1
                records.append(AttendanceImportRecord(
                    record_type="ATTENDANCE",
                    identifier=entry.roll_number,
                    status="FAILED",
                    message="Student record not found.",
                    source_row_number=entry.source_row,
                ))
                continue

            existing_att = existing_att_map.get(str(student.id))

            if existing_att:
                if not config.allow_overwrite:
                    skipped_count += 1
                    records.append(AttendanceImportRecord(
                        record_type="ATTENDANCE",
                        identifier=entry.roll_number,
                        display_name=student.user.full_name if student.user else entry.roll_number,
                        status="SKIPPED",
                        message=f"Attendance already recorded on {config.attendance_date} ({existing_att.status}). Overwrite disabled.",
                        source_row_number=entry.source_row,
                        student_id=student.id,
                        attendance_record_id=existing_att.id,
                    ))
                    continue

                if existing_att.status == entry.normalized_status:
                    skipped_count += 1
                    records.append(AttendanceImportRecord(
                        record_type="ATTENDANCE",
                        identifier=entry.roll_number,
                        display_name=student.user.full_name if student.user else entry.roll_number,
                        status="SKIPPED",
                        message=f"Status is already '{entry.normalized_status}'. No change needed.",
                        source_row_number=entry.source_row,
                        student_id=student.id,
                        attendance_record_id=existing_att.id,
                    ))
                    continue

                try:
                    async with self.db.begin_nested():
                        old_status = existing_att.status
                        existing_att.status = entry.normalized_status
                        existing_att.recorded_by_user_id = actor_id
                        await self.db.flush()

                    updated_count += 1
                    records.append(AttendanceImportRecord(
                        record_type="ATTENDANCE",
                        identifier=entry.roll_number,
                        display_name=student.user.full_name if student.user else entry.roll_number,
                        status="UPDATED",
                        message=f"Updated status from {old_status} to {entry.normalized_status}.",
                        source_row_number=entry.source_row,
                        student_id=student.id,
                        attendance_record_id=existing_att.id,
                    ))
                except Exception as exc:
                    logger.warning("Failed to update attendance for %s: %s", entry.roll_number, exc)
                    failed_count += 1
                    records.append(AttendanceImportRecord(
                        record_type="ATTENDANCE",
                        identifier=entry.roll_number,
                        status="FAILED",
                        message=_safe_message(exc),
                        source_row_number=entry.source_row,
                        student_id=student.id,
                    ))
            else:
                try:
                    async with self.db.begin_nested():
                        att = AttendanceRecord(
                            student_id=student.id,
                            subject_id=config.subject_id,
                            date=config.attendance_date,
                            status=entry.normalized_status,
                            recorded_by_user_id=actor_id,
                        )
                        self.db.add(att)
                        await self.db.flush()

                    created_count += 1
                    records.append(AttendanceImportRecord(
                        record_type="ATTENDANCE",
                        identifier=entry.roll_number,
                        display_name=student.user.full_name if student.user else entry.roll_number,
                        status="CREATED",
                        message=f"Recorded attendance status: {entry.normalized_status}.",
                        source_row_number=entry.source_row,
                        student_id=student.id,
                        attendance_record_id=att.id,
                    ))
                except Exception as exc:
                    logger.warning("Failed to create attendance for %s: %s", entry.roll_number, exc)
                    failed_count += 1
                    records.append(AttendanceImportRecord(
                        record_type="ATTENDANCE",
                        identifier=entry.roll_number,
                        status="FAILED",
                        message=_safe_message(exc),
                        source_row_number=entry.source_row,
                        student_id=student.id,
                    ))

        # Publish event
        if created_count > 0 or updated_count > 0:
            try:
                await event_bus.publish(
                    DomainEvent(
                        type=TimelineEventType.ATTENDANCE_UPDATED.value,
                        actor_id=actor_id,
                        metadata={
                            "subject_id": config.subject_id,
                            "date": str(config.attendance_date),
                            "count": created_count + updated_count,
                            "mode": config.mode,
                        },
                    )
                )
            except Exception as exc:
                logger.warning("Failed to publish attendance event: %s", exc)

        return records, created_count, updated_count, skipped_count, failed_count


def _safe_message(exc: Exception) -> str:
    message = getattr(exc, "message", None) or str(exc)
    return message[:500]
