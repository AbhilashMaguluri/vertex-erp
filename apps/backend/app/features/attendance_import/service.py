"""Attendance Import orchestration service.

Coordinates the complete workflow:
  parseExcel → validateRows → resolveStudents & ExistingAttendance → buildPreview → executeImport
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit_log
from app.core.enums import AuditAction
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.database import AsyncSessionLocal
from app.features.admin.models import Subject
from app.features.attendance_import.executor import AttendanceImportExecutor
from app.features.attendance_import.models import AttendanceImportBatch, AttendanceImportRecord
from app.features.attendance_import.parser import parse_attendance_excel
from app.features.attendance_import.preview_builder import AttendancePreviewBuilder
from app.features.attendance_import.repository import AttendanceImportRepository
from app.features.attendance_import.resolvers import ExistingAttendanceResolver, StudentResolver
from app.features.attendance_import.schemas import (
    AttendanceImportConfiguration,
    AttendanceImportHistoryItem,
    AttendanceImportHistoryResponse,
    AttendanceImportPreviewResponse,
    AttendanceImportProgressResponse,
    AttendanceImportResultRecord,
    AttendanceImportSummaryResponse,
    NormalizedAttendanceEntry,
    ParsedAttendanceRow,
    ResolvedAttendanceEntry,
    ValidationErrorRow,
)
from app.features.attendance_import.validation_service import validate_rows
from app.features.imports.progress import progress_registry

logger = logging.getLogger("app.attendance_import")

_RUNNING_IMPORTS: set = set()


async def _run_import_task(batch_id: str, actor_id: str) -> None:
    async with AsyncSessionLocal() as session:
        service = AttendanceImportService(session)
        try:
            await service._execute(batch_id, actor_id)
        except Exception as exc:
            logger.exception("Attendance import %s failed", batch_id)
            await session.rollback()
            progress_registry.update(batch_id, phase="FAILED", error=str(exc))
            await service._mark_failed(batch_id, str(exc))


class AttendanceImportService:
    """Main orchestrator for attendance import workflow."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AttendanceImportRepository(db)

    async def analyze(
        self,
        filename: str,
        content: bytes,
        mode: str,
        attendance_date: date,
        subject_id: Optional[str],
        department_id: Optional[str],
        section_id: Optional[str],
        actor: Any,
        request: Optional[Request] = None,
    ) -> AttendanceImportPreviewResponse:
        """Parse, validate, resolve, and generate preview response."""

        # Parse file
        parsed_rows, structural_errors = parse_attendance_excel(filename, content)
        if structural_errors:
            raise ValidationError("File structure is invalid: " + "; ".join(structural_errors))

        # Validate rows
        normalized_entries, validation_errors, warnings = validate_rows(parsed_rows)

        # Resolve subject metadata if provided
        subject: Optional[Subject] = None
        if subject_id:
            subject = await self.repo.get_subject(subject_id)

        # Resolve students
        student_resolver = StudentResolver(self.repo)
        all_rolls = [e.roll_number for e in normalized_entries]
        existing_students = await student_resolver.find_existing_students(all_rolls)

        # Resolve existing attendance records if date and subject are available
        existing_attendance_resolver = ExistingAttendanceResolver(self.repo)
        student_ids = [str(s.id) for s in existing_students.values()]
        existing_att_map: Dict[str, Any] = {}
        if subject_id and attendance_date:
            existing_att_map = await existing_attendance_resolver.find_existing_attendance(
                student_ids, subject_id, attendance_date,
            )

        # Build resolved entries
        resolved_entries: List[ResolvedAttendanceEntry] = []
        for entry in normalized_entries:
            roll_upper = entry.roll_number.upper()
            student = existing_students.get(roll_upper)

            if student:
                att_record = existing_att_map.get(str(student.id))
                resolved_entries.append(ResolvedAttendanceEntry(
                    roll_number=entry.roll_number,
                    source_row=entry.source_row,
                    normalized_status=entry.normalized_status,
                    student_id=str(student.id),
                    student_name=student.user.full_name if student.user else entry.roll_number,
                    student_found=True,
                    existing_attendance_id=str(att_record.id) if att_record else None,
                    existing_status=att_record.status if att_record else None,
                    resolution_status="EXISTING" if att_record else "NEW",
                    proposed_action="UPDATE" if att_record else "CREATE",
                ))
            else:
                resolved_entries.append(ResolvedAttendanceEntry(
                    roll_number=entry.roll_number,
                    source_row=entry.source_row,
                    normalized_status=entry.normalized_status,
                    student_found=False,
                    resolution_status="MISSING_STUDENT",
                    proposed_action="CANNOT_IMPORT",
                    error=f"Student roll '{entry.roll_number}' not found in institution database.",
                ))

        # Build preview
        preview_builder = AttendancePreviewBuilder()
        error_count = len(validation_errors) + sum(
            1 for e in resolved_entries if e.proposed_action == "CANNOT_IMPORT"
        )
        summary = preview_builder.generate_summary(
            attendance_date, mode, subject, resolved_entries, len(warnings), error_count,
        )
        tables = preview_builder.generate_preview_tables(resolved_entries)

        # Store upload temp file
        stored_path = self._store_upload(filename, content)

        # Build detection JSON
        detection = {
            "mode": mode,
            "attendance_date": attendance_date.isoformat(),
            "subject_id": subject_id,
            "department_id": department_id,
            "section_id": section_id,
            "resolved_entries": [e.model_dump() for e in resolved_entries],
            "validation_errors": [v.model_dump() for v in validation_errors],
            "warnings": warnings,
        }

        # Create batch DB record
        batch = AttendanceImportBatch(
            original_filename=filename,
            stored_path=stored_path,
            file_size_bytes=len(content),
            mode=mode,
            attendance_date=attendance_date,
            subject_id=subject_id,
            department_id=department_id,
            section_id=section_id,
            status="ANALYZED",
            imported_by_user_id=actor.id,
            detection_json=detection,
            total_rows=len(parsed_rows),
            students_detected=len(resolved_entries),
        )
        await self.repo.create_batch(batch)

        await record_audit_log(
            self.db, user=actor,
            action=AuditAction.CREATE.value,
            entity_type="AttendanceImportBatch",
            entity_id=str(batch.id),
            changes={"file": filename, "date": str(attendance_date), "mode": mode, "stage": "ANALYZED"},
            request=request,
        )
        await self.db.commit()

        return AttendanceImportPreviewResponse(
            batch_id=str(batch.id),
            file_name=filename,
            status=batch.status,
            summary=summary,
            tables=tables,
            validation_errors=validation_errors,
            warnings=warnings,
            parsed_row_count=len(parsed_rows),
        )

    def _store_upload(self, filename: str, content: bytes) -> str:
        import tempfile
        temp_dir = tempfile.gettempdir()
        ext = os.path.splitext(filename)[1].lower() or ".xlsx"
        stored = os.path.join(temp_dir, f"attendance_import_{uuid.uuid4().hex}{ext}")
        with open(stored, "wb") as f:
            f.write(content)
        return stored

    async def get_preview(self, batch_id: str) -> AttendanceImportPreviewResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch or not batch.detection_json:
            raise NotFoundError("Attendance import batch not found.")

        detection = batch.detection_json
        resolved_entries = [ResolvedAttendanceEntry(**e) for e in detection.get("resolved_entries", [])]
        validation_errors = [ValidationErrorRow(**v) for v in detection.get("validation_errors", [])]
        warnings = detection.get("warnings", [])

        preview_builder = AttendancePreviewBuilder()
        error_count = len(validation_errors) + sum(
            1 for e in resolved_entries if e.proposed_action == "CANNOT_IMPORT"
        )
        summary = preview_builder.generate_summary(
            batch.attendance_date, batch.mode, batch.subject,
            resolved_entries, len(warnings), error_count,
        )
        tables = preview_builder.generate_preview_tables(resolved_entries)

        return AttendanceImportPreviewResponse(
            batch_id=str(batch.id),
            file_name=batch.original_filename,
            status=batch.status,
            summary=summary,
            tables=tables,
            validation_errors=validation_errors,
            warnings=warnings,
            parsed_row_count=batch.total_rows,
        )

    async def start_import(
        self,
        batch_id: str,
        config: AttendanceImportConfiguration,
        actor: Any,
        request: Optional[Request] = None,
    ) -> AttendanceImportProgressResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import batch not found.")
        if batch.status == "RUNNING":
            raise ConflictError("This import is already running.")
        if batch.status == "COMPLETED":
            raise ConflictError("This import has already been completed.")

        if not await self.repo.get_subject(config.subject_id):
            raise ValidationError("Selected subject does not exist.")

        batch.status = "RUNNING"
        batch.configuration_json = config.model_dump(mode="json")
        batch.started_at = datetime.now(timezone.utc)
        batch.error_message = None
        await self.db.flush()

        await record_audit_log(
            self.db, user=actor,
            action=AuditAction.CREATE.value,
            entity_type="AttendanceImportBatch",
            entity_id=str(batch.id),
            changes={"stage": "STARTED", "file": batch.original_filename},
            request=request,
        )
        await self.db.commit()

        total = batch.students_detected
        progress_registry.start(str(batch.id), total)
        progress_registry.update(str(batch.id), phase="QUEUED", message="Preparing attendance import…")

        task = asyncio.create_task(_run_import_task(str(batch.id), str(actor.id)))
        _RUNNING_IMPORTS.add(task)
        task.add_done_callback(_RUNNING_IMPORTS.discard)

        return AttendanceImportProgressResponse(
            batch_id=str(batch.id),
            status="RUNNING",
            phase="QUEUED",
            phase_label="Queued",
            percent=0,
            processed=0,
            total=total,
            message="Preparing attendance import…",
        )

    async def _mark_failed(self, batch_id: str, message: str) -> None:
        try:
            batch = await self.repo.get_batch(batch_id)
            if batch:
                batch.status = "FAILED"
                batch.error_message = message[:2000]
                batch.completed_at = datetime.now(timezone.utc)
                await self.db.commit()
        except Exception:
            logger.exception("Could not record failure for attendance import %s", batch_id)

    async def _execute(self, batch_id: str, actor_id: str) -> None:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import batch not found.")

        detection = batch.detection_json or {}
        config = AttendanceImportConfiguration(**(batch.configuration_json or {}))
        entries = [ResolvedAttendanceEntry(**e) for e in detection.get("resolved_entries", [])]

        progress_registry.update(batch_id, phase="EXECUTING", message="Saving attendance records…")

        # Resolve students map
        rolls = [e.roll_number for e in entries if e.student_found]
        student_map = await self.repo.get_students_by_rolls(rolls)

        executor = AttendanceImportExecutor(self.db, self.repo)
        records, created_count, updated_count, skipped_count, failed_count = (
            await executor.execute_import(entries, config, student_map, actor_id)
        )

        for r in records:
            r.batch_id = batch.id

        batch.students_found = len(student_map)
        batch.missing_students = len(entries) - len(student_map)
        batch.records_created = created_count
        batch.records_updated = updated_count
        batch.records_skipped = skipped_count
        batch.failed_records = failed_count
        batch.warning_count = len(detection.get("warnings", []))
        batch.summary_json = {
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "failed": failed_count,
        }
        batch.status = "COMPLETED"
        batch.completed_at = datetime.now(timezone.utc)

        await self.repo.add_records(records)
        await self.db.commit()
        progress_registry.update(batch_id, phase="COMPLETED", total=1, processed=1, message="Attendance import complete.")

    async def get_progress(self, batch_id: str) -> AttendanceImportProgressResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import batch not found.")

        live = progress_registry.get(batch_id)
        if live and batch.status == "RUNNING":
            return AttendanceImportProgressResponse(
                batch_id=batch_id, status=batch.status,
                phase=live.phase, phase_label=live.phase_label,
                percent=live.percent, processed=live.processed,
                total=live.total, message=live.message, error=live.error,
            )

        terminal = {
            "COMPLETED": ("COMPLETED", "Completed", 100),
            "FAILED": ("FAILED", "Failed", 100),
            "ANALYZED": ("QUEUED", "Ready to import", 0),
            "RUNNING": ("EXECUTING", "Import in progress", 50),
        }
        phase, label, percent = terminal.get(batch.status, ("QUEUED", "Queued", 0))
        return AttendanceImportProgressResponse(
            batch_id=batch_id, status=batch.status,
            phase=phase, phase_label=label, percent=percent,
            processed=batch.records_created + batch.records_updated + batch.records_skipped,
            total=batch.students_detected, error=batch.error_message,
        )

    async def get_summary(self, batch_id: str) -> AttendanceImportSummaryResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import batch not found.")
        records = await self.repo.list_records(batch_id)
        return AttendanceImportSummaryResponse(
            batch_id=str(batch.id),
            file_name=batch.original_filename,
            status=batch.status,
            mode=batch.mode,
            attendance_date=batch.attendance_date,
            subject_code=batch.subject.code if batch.subject else None,
            subject_name=batch.subject.name if batch.subject else None,
            imported_by=batch.imported_by.full_name if batch.imported_by else None,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
            total_rows=batch.total_rows,
            students_detected=batch.students_detected,
            students_found=batch.students_found,
            missing_students=batch.missing_students,
            records_created=batch.records_created,
            records_updated=batch.records_updated,
            records_skipped=batch.records_skipped,
            failed_records=batch.failed_records,
            warning_count=batch.warning_count,
            error_message=batch.error_message,
            records=[AttendanceImportResultRecord.model_validate(r) for r in records],
        )

    async def get_history(self, limit: int = 20) -> AttendanceImportHistoryResponse:
        batches = await self.repo.list_batches(limit)
        stats = await self.repo.batch_statistics()
        return AttendanceImportHistoryResponse(
            items=[
                AttendanceImportHistoryItem(
                    batch_id=str(b.id),
                    file_name=b.original_filename,
                    mode=b.mode,
                    attendance_date=b.attendance_date,
                    subject_name=b.subject.name if b.subject else None,
                    status=b.status,
                    imported_by=b.imported_by.full_name if b.imported_by else None,
                    created_at=b.created_at,
                    completed_at=b.completed_at,
                    records_created=b.records_created,
                    records_updated=b.records_updated,
                    failed_records=b.failed_records,
                )
                for b in batches
            ],
            total_imports=stats["total"],
            completed_imports=stats["completed"],
            total_records_created=stats["created"],
            total_records_updated=stats["updated"],
            success_rate=stats["success_rate"],
            last_import_at=stats["last_at"],
        )
