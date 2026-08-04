"""Marks Import Executor — executes mark record writes inside a transaction."""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import TimelineEventType
from app.core.events import DomainEvent, event_bus
from app.features.academics.models import Mark
from app.features.marks_import.models import MarksImportRecord
from app.features.marks_import.repository import MarksImportRepository
from app.features.marks_import.schemas import (
    MarksImportConfiguration,
    ResolvedMarksEntry,
)
from app.features.students.models import Student

logger = logging.getLogger("app.marks_import.executor")


class MarksImportExecutor:
    """Executes marks imports within a database transaction."""

    def __init__(self, db: AsyncSession, repo: MarksImportRepository):
        self.db = db
        self.repo = repo

    async def execute_import(
        self,
        entries: List[ResolvedMarksEntry],
        config: MarksImportConfiguration,
        student_map: Dict[str, Student],
        actor_id: str,
    ) -> Tuple[List[MarksImportRecord], int, int, int, int]:
        """Execute mark record writes inside a transaction.

        Returns (records, created_count, updated_count, skipped_count, failed_count).
        """
        records: List[MarksImportRecord] = []
        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0

        # Load existing marks
        student_ids = [str(s.id) for s in student_map.values()]
        existing_marks_map = await self.repo.get_existing_marks(
            student_ids, config.subject_id, config.semester_id, config.assessment_code,
        )

        for entry in entries:
            roll_upper = entry.roll_number.upper()
            student = student_map.get(roll_upper)

            if not student:
                failed_count += 1
                records.append(MarksImportRecord(
                    record_type="MARKS",
                    identifier=entry.roll_number,
                    status="FAILED",
                    message="Student record not found.",
                    source_row_number=entry.source_row,
                ))
                continue

            existing_mark = existing_marks_map.get(str(student.id))

            if existing_mark:
                if not config.allow_overwrite:
                    skipped_count += 1
                    records.append(MarksImportRecord(
                        record_type="MARKS",
                        identifier=entry.roll_number,
                        display_name=student.user.full_name if student.user else entry.roll_number,
                        status="SKIPPED",
                        message=f"Marks already recorded ({existing_mark.marks_obtained}/{existing_mark.max_marks}). Overwrite disabled.",
                        source_row_number=entry.source_row,
                        student_id=student.id,
                        mark_id=existing_mark.id,
                    ))
                    continue

                try:
                    async with self.db.begin_nested():
                        old_marks = existing_mark.marks_obtained
                        existing_mark.marks_obtained = entry.total_marks
                        existing_mark.max_marks = entry.max_marks
                        existing_mark.recorded_by_user_id = actor_id
                        existing_mark.breakdown_json = entry.question_scores
                        await self.db.flush()

                    updated_count += 1
                    records.append(MarksImportRecord(
                        record_type="MARKS",
                        identifier=entry.roll_number,
                        display_name=student.user.full_name if student.user else entry.roll_number,
                        status="UPDATED",
                        message=f"Updated marks from {old_marks} to {entry.total_marks}/{entry.max_marks}.",
                        source_row_number=entry.source_row,
                        student_id=student.id,
                        mark_id=existing_mark.id,
                    ))
                except Exception as exc:
                    logger.warning("Failed to update marks for %s: %s", entry.roll_number, exc)
                    failed_count += 1
                    records.append(MarksImportRecord(
                        record_type="MARKS",
                        identifier=entry.roll_number,
                        status="FAILED",
                        message=_safe_message(exc),
                        source_row_number=entry.source_row,
                        student_id=student.id,
                    ))
            else:
                try:
                    async with self.db.begin_nested():
                        mark = Mark(
                            student_id=student.id,
                            subject_id=config.subject_id,
                            semester_id=config.semester_id,
                            assessment_type=config.assessment_code.upper(),
                            marks_obtained=entry.total_marks,
                            max_marks=entry.max_marks,
                            recorded_by_user_id=actor_id,
                            breakdown_json=entry.question_scores,
                        )
                        self.db.add(mark)
                        await self.db.flush()

                    created_count += 1
                    records.append(MarksImportRecord(
                        record_type="MARKS",
                        identifier=entry.roll_number,
                        display_name=student.user.full_name if student.user else entry.roll_number,
                        status="CREATED",
                        message=f"Recorded marks: {entry.total_marks}/{entry.max_marks}.",
                        source_row_number=entry.source_row,
                        student_id=student.id,
                        mark_id=mark.id,
                    ))
                except Exception as exc:
                    logger.warning("Failed to create marks for %s: %s", entry.roll_number, exc)
                    failed_count += 1
                    records.append(MarksImportRecord(
                        record_type="MARKS",
                        identifier=entry.roll_number,
                        status="FAILED",
                        message=_safe_message(exc),
                        source_row_number=entry.source_row,
                        student_id=student.id,
                    ))

        # Publish domain event
        if created_count > 0 or updated_count > 0:
            try:
                await event_bus.publish(
                    DomainEvent(
                        type=TimelineEventType.MARKS_UPDATED.value,
                        actor_id=actor_id,
                        metadata={
                            "subject_id": config.subject_id,
                            "semester_id": config.semester_id,
                            "assessment_code": config.assessment_code,
                            "count": created_count + updated_count,
                        },
                    )
                )
            except Exception as exc:
                logger.warning("Failed to publish marks event: %s", exc)

        return records, created_count, updated_count, skipped_count, failed_count


def _safe_message(exc: Exception) -> str:
    message = getattr(exc, "message", None) or str(exc)
    return message[:500]
