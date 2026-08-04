"""Marks Import orchestration service.

Coordinates the complete workflow:
  parseExcel → validateRows → resolveStudents & ExistingMarks → buildPreview → executeImport
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit_log
from app.core.enums import AuditAction
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.database import AsyncSessionLocal
from app.features.admin.models import Subject
from app.features.imports.progress import progress_registry
from app.features.marks_import.executor import MarksImportExecutor
from app.features.marks_import.models import MarksImportBatch, MarksImportRecord
from app.features.marks_import.parser import parse_marks_excel
from app.features.marks_import.preview_builder import MarksPreviewBuilder
from app.features.marks_import.repository import MarksImportRepository
from app.features.marks_import.resolvers import ExistingMarksResolver, StudentResolver
from app.features.marks_import.schemas import (
    MarksImportConfiguration,
    MarksImportHistoryItem,
    MarksImportHistoryResponse,
    MarksImportPreviewResponse,
    MarksImportProgressResponse,
    MarksImportResultRecord,
    MarksImportSummaryResponse,
    ParsedMarksRow,
    ResolvedMarksEntry,
    ValidationErrorRow,
)
from app.features.marks_import.template_service import AssessmentTemplateService
from app.features.marks_import.validation_service import validate_rows

logger = logging.getLogger("app.marks_import")

_RUNNING_IMPORTS: set = set()


async def _run_import_task(batch_id: str, actor_id: str) -> None:
    async with AsyncSessionLocal() as session:
        service = MarksImportService(session)
        try:
            await service._execute(batch_id, actor_id)
        except Exception as exc:
            logger.exception("Marks import %s failed", batch_id)
            await session.rollback()
            progress_registry.update(batch_id, phase="FAILED", error=str(exc))
            await service._mark_failed(batch_id, str(exc))


class MarksImportService:
    """Main orchestrator for marks import workflow."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MarksImportRepository(db)

    async def analyze(
        self,
        filename: str,
        content: bytes,
        academic_year_id: Optional[str],
        semester_id: str,
        department_id: Optional[str],
        section_id: Optional[str],
        subject_id: str,
        assessment_code: str,
        actor: Any,
        request: Optional[Request] = None,
    ) -> MarksImportPreviewResponse:
        """Parse, validate, resolve, and generate preview response."""

        # Fetch subject & template
        subject = await self.repo.get_subject(subject_id)
        if not subject:
            raise ValidationError("Selected subject does not exist.")

        tmpl_service = AssessmentTemplateService(self.db)
        template = await tmpl_service.get_template_for_subject(subject_id, assessment_code)

        # Parse file against template schema
        parsed_rows, structural_errors = parse_marks_excel(filename, content, template)
        if structural_errors:
            raise ValidationError("File structure is invalid: " + "; ".join(structural_errors))

        # Validate rows
        validated_rows, validation_errors, warnings = validate_rows(parsed_rows, template)

        # Resolve students
        student_resolver = StudentResolver(self.repo)
        valid_rows = [r for r in validated_rows if r.is_valid]
        all_rolls = [r.student_roll for r in valid_rows]
        existing_students = await student_resolver.find_existing_students(all_rolls)

        # Resolve existing marks
        existing_marks_resolver = ExistingMarksResolver(self.repo)
        student_ids = [str(s.id) for s in existing_students.values()]
        existing_marks_map = await existing_marks_resolver.find_existing_marks(
            student_ids, subject_id, semester_id, assessment_code,
        )

        # Build resolved entries
        resolved_entries: List[ResolvedMarksEntry] = []
        for row in valid_rows:
            roll_upper = row.student_roll.upper()
            student = existing_students.get(roll_upper)

            if student:
                existing_mark = existing_marks_map.get(str(student.id))
                resolved_entries.append(ResolvedMarksEntry(
                    roll_number=row.student_roll,
                    source_row=row.row_number,
                    question_scores=row.question_scores,
                    total_marks=row.total_marks if row.total_marks is not None else 0.0,
                    max_marks=template.total_max_marks,
                    student_id=str(student.id),
                    student_name=student.user.full_name if student.user else row.student_roll,
                    student_found=True,
                    existing_mark_id=str(existing_mark.id) if existing_mark else None,
                    existing_total=existing_mark.marks_obtained if existing_mark else None,
                    resolution_status="EXISTING" if existing_mark else "NEW",
                    proposed_action="UPDATE" if existing_mark else "CREATE",
                ))
            else:
                resolved_entries.append(ResolvedMarksEntry(
                    roll_number=row.student_roll,
                    source_row=row.row_number,
                    question_scores=row.question_scores,
                    total_marks=row.total_marks if row.total_marks is not None else 0.0,
                    max_marks=template.total_max_marks,
                    student_found=False,
                    resolution_status="MISSING_STUDENT",
                    proposed_action="CANNOT_IMPORT",
                    error=f"Student roll '{row.student_roll}' not found in institution database.",
                ))

        # Build preview
        preview_builder = MarksPreviewBuilder()
        error_count = len(validation_errors) + sum(
            1 for e in resolved_entries if e.proposed_action == "CANNOT_IMPORT"
        )
        summary = preview_builder.generate_summary(
            subject, template, resolved_entries, len(warnings), error_count,
        )
        tables = preview_builder.generate_preview_tables(resolved_entries)

        # Store upload temp file
        stored_path = self._store_upload(filename, content)

        # Build detection JSON
        detection = {
            "academic_year_id": academic_year_id,
            "semester_id": semester_id,
            "department_id": department_id,
            "section_id": section_id,
            "subject_id": subject_id,
            "assessment_code": assessment_code,
            "resolved_entries": [e.model_dump() for e in resolved_entries],
            "validation_errors": [v.model_dump() for v in validation_errors],
            "warnings": warnings,
        }

        # Create batch DB record
        batch = MarksImportBatch(
            original_filename=filename,
            stored_path=stored_path,
            file_size_bytes=len(content),
            academic_year_id=academic_year_id,
            semester_id=semester_id,
            department_id=department_id,
            section_id=section_id,
            subject_id=subject_id,
            assessment_code=assessment_code.upper(),
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
            entity_type="MarksImportBatch",
            entity_id=str(batch.id),
            changes={"file": filename, "subject_id": subject_id, "assessment_code": assessment_code, "stage": "ANALYZED"},
            request=request,
        )
        await self.db.commit()

        return MarksImportPreviewResponse(
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
        stored = os.path.join(temp_dir, f"marks_import_{uuid.uuid4().hex}{ext}")
        with open(stored, "wb") as f:
            f.write(content)
        return stored

    async def get_preview(self, batch_id: str) -> MarksImportPreviewResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch or not batch.detection_json:
            raise NotFoundError("Marks import batch not found.")

        tmpl_service = AssessmentTemplateService(self.db)
        template = await tmpl_service.get_template_for_subject(batch.subject_id, batch.assessment_code)

        detection = batch.detection_json
        resolved_entries = [ResolvedMarksEntry(**e) for e in detection.get("resolved_entries", [])]
        validation_errors = [ValidationErrorRow(**v) for v in detection.get("validation_errors", [])]
        warnings = detection.get("warnings", [])

        preview_builder = MarksPreviewBuilder()
        error_count = len(validation_errors) + sum(
            1 for e in resolved_entries if e.proposed_action == "CANNOT_IMPORT"
        )
        summary = preview_builder.generate_summary(
            batch.subject, template, resolved_entries, len(warnings), error_count,
        )
        tables = preview_builder.generate_preview_tables(resolved_entries)

        return MarksImportPreviewResponse(
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
        config: MarksImportConfiguration,
        actor: Any,
        request: Optional[Request] = None,
    ) -> MarksImportProgressResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import batch not found.")
        if batch.status == "RUNNING":
            raise ConflictError("This import is already running.")
        if batch.status == "COMPLETED":
            raise ConflictError("This import has already been completed.")

        batch.status = "RUNNING"
        batch.configuration_json = config.model_dump(mode="json")
        batch.started_at = datetime.now(timezone.utc)
        batch.error_message = None
        await self.db.flush()

        await record_audit_log(
            self.db, user=actor,
            action=AuditAction.CREATE.value,
            entity_type="MarksImportBatch",
            entity_id=str(batch.id),
            changes={"stage": "STARTED", "file": batch.original_filename},
            request=request,
        )
        await self.db.commit()

        total = batch.students_detected
        progress_registry.start(str(batch.id), total)
        progress_registry.update(str(batch.id), phase="QUEUED", message="Preparing marks import…")

        task = asyncio.create_task(_run_import_task(str(batch.id), str(actor.id)))
        _RUNNING_IMPORTS.add(task)
        task.add_done_callback(_RUNNING_IMPORTS.discard)

        return MarksImportProgressResponse(
            batch_id=str(batch.id),
            status="RUNNING",
            phase="QUEUED",
            phase_label="Queued",
            percent=0,
            processed=0,
            total=total,
            message="Preparing marks import…",
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
            logger.exception("Could not record failure for marks import %s", batch_id)

    async def _execute(self, batch_id: str, actor_id: str) -> None:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import batch not found.")

        detection = batch.detection_json or {}
        config = MarksImportConfiguration(**(batch.configuration_json or {}))
        entries = [ResolvedMarksEntry(**e) for e in detection.get("resolved_entries", [])]

        progress_registry.update(batch_id, phase="EXECUTING", message="Saving mark records…")

        rolls = [e.roll_number for e in entries if e.student_found]
        student_map = await self.repo.get_students_by_rolls(rolls)

        executor = MarksImportExecutor(self.db, self.repo)
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
        progress_registry.update(batch_id, phase="COMPLETED", total=1, processed=1, message="Marks import complete.")

    async def get_progress(self, batch_id: str) -> MarksImportProgressResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import batch not found.")

        live = progress_registry.get(batch_id)
        if live and batch.status == "RUNNING":
            return MarksImportProgressResponse(
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
        return MarksImportProgressResponse(
            batch_id=batch_id, status=batch.status,
            phase=phase, phase_label=label, percent=percent,
            processed=batch.records_created + batch.records_updated + batch.records_skipped,
            total=batch.students_detected, error=batch.error_message,
        )

    async def get_summary(self, batch_id: str) -> MarksImportSummaryResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import batch not found.")
        records = await self.repo.list_records(batch_id)
        return MarksImportSummaryResponse(
            batch_id=str(batch.id),
            file_name=batch.original_filename,
            status=batch.status,
            subject_code=batch.subject.code if batch.subject else None,
            subject_name=batch.subject.name if batch.subject else None,
            assessment_code=batch.assessment_code,
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
            records=[MarksImportResultRecord.model_validate(r) for r in records],
        )

    async def get_history(self, limit: int = 20) -> MarksImportHistoryResponse:
        batches = await self.repo.list_batches(limit)
        stats = await self.repo.batch_statistics()
        return MarksImportHistoryResponse(
            items=[
                MarksImportHistoryItem(
                    batch_id=str(b.id),
                    file_name=b.original_filename,
                    subject_name=b.subject.name if b.subject else None,
                    assessment_code=b.assessment_code,
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
