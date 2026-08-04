"""Membership Import orchestration service.

Coordinates the full import lifecycle:
  parseExcel → validateRows → expandRollRanges → buildPreview → executeImport

All business logic flows through this service.  The router is thin —
it calls methods here, never constructs its own logic.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.audit import record_audit_log
from app.core.enums import AuditAction, TimelineEventType
from app.core.events import DomainEvent, event_bus
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.database import AsyncSessionLocal
from app.features.admin.models import Section
from app.features.auth.models import User
from app.features.imports import naming
from app.features.imports.progress import progress_registry
from app.features.membership_import.executor import ImportExecutor
from app.features.membership_import.models import MembershipImportBatch, MembershipImportRecord
from app.features.membership_import.parser import parse_membership_excel
from app.features.membership_import.preview_builder import ImportPreviewBuilder
from app.features.membership_import.repository import MembershipImportRepository
from app.features.membership_import.resolvers import (
    CounselorResolver,
    MembershipResolver,
    StudentAccountResolver,
)
from app.features.membership_import.roll_range_service import expand_range
from app.features.membership_import.schemas import (
    CounselorEntry,
    ExpandedStudentEntry,
    GeneratedStudentCredential,
    MembershipEntry,
    MembershipImportConfiguration,
    MembershipImportHistoryItem,
    MembershipImportHistoryResponse,
    MembershipImportPreviewResponse,
    MembershipImportProgressResponse,
    MembershipImportResultRecord,
    MembershipImportSummaryResponse,
    ParsedMembershipRow,
    ValidationErrorRow,
)
from app.features.membership_import.validation_service import validate_rows

logger = logging.getLogger("app.membership_import")

DEFAULT_EMAIL_DOMAIN = "vvit.net"

# Strong references to in-flight imports.
_RUNNING_IMPORTS: set = set()


async def _run_import_task(batch_id: str, actor_id: str) -> None:
    """Run one import on its own session, detached from the request."""
    async with AsyncSessionLocal() as session:
        service = MembershipImportService(session)
        try:
            await service._execute(batch_id, actor_id)
        except Exception as exc:
            logger.exception("Membership import %s failed", batch_id)
            await session.rollback()
            progress_registry.update(batch_id, phase="FAILED", error=str(exc))
            await service._mark_failed(batch_id, str(exc))


def _email_domain() -> str:
    configured = (settings.EMAILS_FROM_EMAIL or "").strip()
    if "@" in configured:
        domain = configured.rsplit("@", 1)[1].strip().lower()
        if domain:
            return domain
    return DEFAULT_EMAIL_DOMAIN


class MembershipImportService:
    """Main orchestrator for the membership import workflow."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MembershipImportRepository(db)

    # ------------------------------------------------------------------
    # Stage 1 — Upload & Parse & Validate & Preview
    # ------------------------------------------------------------------
    async def analyze(
        self,
        filename: str,
        content: bytes,
        actor: User,
        request: Optional[Request] = None,
    ) -> MembershipImportPreviewResponse:
        """Parse, validate, expand, resolve, and build preview.
        Nothing is written to the database except the batch record itself."""

        # Parse Excel
        parsed_rows, structural_errors = parse_membership_excel(filename, content)
        if structural_errors:
            raise ValidationError(
                "File structure is invalid: " + "; ".join(structural_errors)
            )

        # Validate rows
        validated_rows, validation_errors = validate_rows(parsed_rows)

        # Separate valid from invalid rows
        valid_rows = [r for r in validated_rows if r.is_valid]
        invalid_rows = [r for r in validated_rows if not r.is_valid]

        # Expand roll number ranges
        expanded_entries = self._expand_roll_ranges(valid_rows)

        # Resolve students
        student_resolver = StudentAccountResolver(self.repo)
        all_rolls = [e.roll_number for e in expanded_entries]
        existing_students = await student_resolver.find_existing_students(all_rolls)
        expanded_entries = await student_resolver.resolve_students(
            expanded_entries, existing_students,
        )

        # Resolve counselors
        counselor_resolver = CounselorResolver(self.repo)
        counselor_emails = list(set(e.counselor_email for e in expanded_entries))
        counselor_entries = await counselor_resolver.find_counselors_by_emails(counselor_emails)

        # Update counselor student counts
        for entry in expanded_entries:
            email_lower = entry.counselor_email.lower()
            if email_lower in counselor_entries:
                counselor_entries[email_lower].student_count += 1
                if entry.source_row not in counselor_entries[email_lower].source_rows:
                    counselor_entries[email_lower].source_rows.append(entry.source_row)

        # Resolve memberships
        membership_resolver = MembershipResolver(self.repo)
        student_ids = [
            e.student_id for e in expanded_entries
            if e.student_id is not None
        ]
        existing_assignments = await membership_resolver.check_existing_memberships(student_ids)

        # Build membership entries
        memberships = self._build_memberships(
            expanded_entries, counselor_entries, existing_assignments,
        )

        # Build preview
        preview_builder = ImportPreviewBuilder()
        warning_count = sum(len(r.warnings) for r in validated_rows)
        error_count = len(validation_errors) + sum(
            1 for m in memberships if m.membership_action == "ERROR"
        )

        summary = preview_builder.generate_summary(
            expanded_entries, counselor_entries, memberships,
            warning_count, error_count,
        )
        tables = preview_builder.generate_preview_tables(
            expanded_entries, counselor_entries, memberships,
        )

        # Collect warnings
        warnings: List[str] = []
        for row in validated_rows:
            for w in row.warnings:
                warnings.append(f"Row {row.row_number}: {w}")

        errors: List[str] = []
        for row in invalid_rows:
            for e in row.errors:
                errors.append(f"Row {row.row_number}: {e}")

        # Store the file
        stored_path = self._store_upload(filename, content)

        # Build detection JSON for later execution
        detection = {
            "parsed_rows": [r.model_dump() for r in validated_rows],
            "expanded_entries": [e.model_dump() for e in expanded_entries],
            "counselor_entries": {k: v.model_dump() for k, v in counselor_entries.items()},
            "memberships": [m.model_dump() for m in memberships],
            "validation_errors": [v.model_dump() for v in validation_errors],
            "email_domain": _email_domain(),
            "warnings": warnings,
            "errors": errors,
        }

        # Create batch record
        batch = MembershipImportBatch(
            original_filename=filename,
            stored_path=stored_path,
            file_size_bytes=len(content),
            status="ANALYZED",
            imported_by_user_id=actor.id,
            detection_json=detection,
            total_rows=len(parsed_rows),
            students_detected=len(expanded_entries),
        )
        await self.repo.create_batch(batch)

        await record_audit_log(
            self.db, user=actor,
            action=AuditAction.CREATE.value,
            entity_type="MembershipImportBatch",
            entity_id=str(batch.id),
            changes={"file": filename, "students_detected": len(expanded_entries), "stage": "ANALYZED"},
            request=request,
        )
        await self.db.commit()

        return MembershipImportPreviewResponse(
            batch_id=str(batch.id),
            file_name=filename,
            status=batch.status,
            summary=summary,
            tables=tables,
            validation_errors=validation_errors,
            warnings=warnings,
            errors=errors,
            parsed_row_count=len(parsed_rows),
            expanded_student_count=len(expanded_entries),
        )

    def _expand_roll_ranges(
        self, rows: List[ParsedMembershipRow],
    ) -> List[ExpandedStudentEntry]:
        """Expand every valid row's start-end range into individual students."""
        entries: List[ExpandedStudentEntry] = []
        seen_rolls: set = set()

        for row in rows:
            try:
                rolls = expand_range(row.start_roll, row.end_roll)
            except ValidationError as exc:
                row.errors.append(str(exc.message if hasattr(exc, 'message') else exc))
                continue

            for roll in rolls:
                if roll in seen_rolls:
                    row.warnings.append(f"Duplicate roll number '{roll}' — imported once.")
                    continue
                seen_rolls.add(roll)
                entries.append(ExpandedStudentEntry(
                    roll_number=roll,
                    source_row=row.row_number,
                    counselor_email=row.counselor_email.strip().lower(),
                ))

        return entries

    def _build_memberships(
        self,
        students: List[ExpandedStudentEntry],
        counselors: Dict[str, CounselorEntry],
        existing_assignments: Dict[str, Any],
    ) -> List[MembershipEntry]:
        """Build the membership plan from resolved students and counselors."""
        memberships: List[MembershipEntry] = []

        for s in students:
            email_lower = s.counselor_email.lower()
            counselor = counselors.get(email_lower)

            m = MembershipEntry(
                roll_number=s.roll_number,
                student_email=s.student_email,
                student_name=s.student_name,
                student_user_id=s.student_user_id,
                student_id=s.student_id,
                student_status=s.student_status,
                student_action=s.student_action,
                counselor_email=s.counselor_email,
                source_row=s.source_row,
                counselor_user_id=counselor.user_id if counselor else None,
                counselor_name=counselor.display_name if counselor else None,
                counselor_status=counselor.status if counselor else "MISSING",
                membership_status="NEW",
                membership_action="CREATE",
            )

            # Counselor missing → error
            if not counselor or counselor.status == "MISSING":
                m.membership_action = "ERROR"
                m.error = f"Counselor '{s.counselor_email}' not found. Cannot import."
                memberships.append(m)
                continue

            # Check existing assignment
            if s.student_id and s.student_id in existing_assignments:
                existing = existing_assignments[s.student_id]
                if str(existing.counsellor_id) == counselor.user_id:
                    m.membership_status = "EXISTING"
                    m.membership_action = "SKIP"
                    m.error = "Already assigned to this counselor."
                else:
                    m.membership_status = "EXISTING"
                    m.membership_action = "UPDATE"

            memberships.append(m)

        return memberships

    def _store_upload(self, filename: str, content: bytes) -> str:
        import tempfile
        temp_dir = tempfile.gettempdir()
        extension = os.path.splitext(filename)[1].lower() or ".xlsx"
        stored = os.path.join(temp_dir, f"membership_import_{uuid.uuid4().hex}{extension}")
        with open(stored, "wb") as f:
            f.write(content)
        return stored

    # ------------------------------------------------------------------
    # Preview retrieval
    # ------------------------------------------------------------------
    async def get_preview(self, batch_id: str) -> MembershipImportPreviewResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch or not batch.detection_json:
            raise NotFoundError("Import not found.")

        detection = batch.detection_json

        # Rebuild schemas from stored JSON
        expanded = [ExpandedStudentEntry(**e) for e in detection.get("expanded_entries", [])]
        counselors = {k: CounselorEntry(**v) for k, v in detection.get("counselor_entries", {}).items()}
        memberships = [MembershipEntry(**m) for m in detection.get("memberships", [])]
        validation_errors = [ValidationErrorRow(**v) for v in detection.get("validation_errors", [])]

        preview_builder = ImportPreviewBuilder()
        warning_count = len(detection.get("warnings", []))
        error_count = len(validation_errors) + sum(
            1 for m in memberships if m.membership_action == "ERROR"
        )
        summary = preview_builder.generate_summary(
            expanded, counselors, memberships, warning_count, error_count,
        )
        tables = preview_builder.generate_preview_tables(expanded, counselors, memberships)

        return MembershipImportPreviewResponse(
            batch_id=str(batch.id),
            file_name=batch.original_filename,
            status=batch.status,
            summary=summary,
            tables=tables,
            validation_errors=validation_errors,
            warnings=detection.get("warnings", []),
            errors=detection.get("errors", []),
            parsed_row_count=batch.total_rows,
            expanded_student_count=batch.students_detected,
        )

    # ------------------------------------------------------------------
    # Stage 7 — Execute Import
    # ------------------------------------------------------------------
    async def start_import(
        self,
        batch_id: str,
        config: MembershipImportConfiguration,
        actor: User,
        request: Optional[Request] = None,
    ) -> MembershipImportProgressResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found.")
        if batch.status == "RUNNING":
            raise ConflictError("This import is already running.")
        if batch.status == "COMPLETED":
            raise ConflictError("This import has already been applied.")
        if not batch.detection_json:
            raise ValidationError("No analysis attached — upload the file again.")

        await self._validate_config(config)

        batch.status = "RUNNING"
        batch.configuration_json = config.model_dump()
        batch.started_at = datetime.now(timezone.utc)
        batch.error_message = None
        await self.db.flush()

        await record_audit_log(
            self.db, user=actor,
            action=AuditAction.CREATE.value,
            entity_type="MembershipImportBatch",
            entity_id=str(batch.id),
            changes={"stage": "STARTED", "file": batch.original_filename},
            request=request,
        )
        await self.db.commit()

        total = len(batch.detection_json.get("memberships", []))
        progress_registry.start(str(batch.id), total)
        progress_registry.update(str(batch.id), phase="QUEUED", message="Preparing the import…")

        task = asyncio.create_task(_run_import_task(str(batch.id), str(actor.id)))
        _RUNNING_IMPORTS.add(task)
        task.add_done_callback(_RUNNING_IMPORTS.discard)

        return MembershipImportProgressResponse(
            batch_id=str(batch.id),
            status="RUNNING",
            phase="QUEUED",
            phase_label="Queued",
            percent=0,
            processed=0,
            total=total,
            message="Preparing the import…",
        )

    async def _validate_config(self, config: MembershipImportConfiguration) -> None:
        if not await self.repo.get_department(config.department_id):
            raise ValidationError("The selected department does not exist.")
        if not await self.repo.get_semester(config.semester_id):
            raise ValidationError("The selected semester does not exist.")

    async def _mark_failed(self, batch_id: str, message: str) -> None:
        try:
            batch = await self.repo.get_batch(batch_id)
            if batch:
                batch.status = "FAILED"
                batch.error_message = message[:2000]
                batch.completed_at = datetime.now(timezone.utc)
                await self.db.commit()
        except Exception:
            logger.exception("Could not record failure of membership import %s", batch_id)

    async def _execute(self, batch_id: str, actor_id: str) -> None:
        """Execute the import inside a transaction."""
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found.")

        detection = batch.detection_json or {}
        config = MembershipImportConfiguration(**(batch.configuration_json or {}))
        memberships = [MembershipEntry(**m) for m in detection.get("memberships", [])]
        domain = detection.get("email_domain") or _email_domain()

        actor = await self.repo.get_user_by_id(actor_id)
        semester = await self.repo.get_semester(config.semester_id)
        section = await self._ensure_section(config, actor_id)
        student_role = await self.repo.get_role("STUDENT")
        if not student_role:
            raise ValidationError("STUDENT role is missing. Run seed first.")

        taken_usernames, taken_emails = await self.repo.get_taken_usernames_and_emails()

        # Resolve counselor users for execution
        counselor_emails = list(set(m.counselor_email for m in memberships))
        counselor_users = await self.repo.get_counselors_by_emails(counselor_emails)

        executor = ImportExecutor(self.db, self.repo)

        # Phase 1: Create student accounts
        progress_registry.update(batch_id, phase="STUDENTS", message="Creating student accounts…")
        student_map, credentials, student_records, students_created, students_reused = (
            await executor.create_student_accounts(
                memberships, config, semester, section, student_role,
                domain, taken_usernames, taken_emails, actor_id,
            )
        )

        # Phase 2: Create memberships
        progress_registry.update(batch_id, phase="MEMBERSHIPS", message="Creating memberships…")
        membership_records, memberships_created, memberships_updated, memberships_skipped = (
            await executor.create_memberships(
                memberships, student_map, counselor_users, config,
            )
        )

        # Finalise
        all_records = student_records + membership_records
        failed = sum(1 for r in all_records if r.status == "FAILED")

        batch.students_created = students_created
        batch.students_reused = students_reused
        batch.counselors_found = sum(1 for c in counselor_users.values())
        batch.counselors_missing = len(set(counselor_emails)) - len(counselor_users)
        batch.memberships_created = memberships_created
        batch.memberships_updated = memberships_updated
        batch.memberships_skipped = memberships_skipped
        batch.failed_records = failed
        batch.warning_count = len(detection.get("warnings", []))
        batch.credentials_json = [c.model_dump() for c in credentials]
        batch.summary_json = {
            "students_created": students_created,
            "students_reused": students_reused,
            "memberships_created": memberships_created,
            "memberships_updated": memberships_updated,
            "memberships_skipped": memberships_skipped,
            "failed_records": failed,
            "section": section.name,
        }
        batch.status = "COMPLETED"
        batch.completed_at = datetime.now(timezone.utc)

        # Assign batch_id to records
        for r in all_records:
            r.batch_id = batch.id

        # Publish domain event for counsellor assignments
        if memberships_created > 0 or memberships_updated > 0:
            try:
                await event_bus.publish(
                    DomainEvent(
                        type=TimelineEventType.COUNSELLOR_ASSIGNED.value,
                        actor_id=actor_id,
                        metadata={
                            "section_id": config.section_id,
                            "semester_id": config.semester_id,
                            "count": memberships_created + memberships_updated,
                        },
                    )
                )
            except Exception as exc:
                logger.warning("Failed to publish counsellor assigned event: %s", exc)

        await self.repo.add_records(all_records)
        await record_audit_log(
            self.db, user=actor,
            action=AuditAction.CREATE.value,
            entity_type="MembershipImportBatch",
            entity_id=str(batch.id),
            changes={"stage": "COMPLETED", "file": batch.original_filename, **batch.summary_json},
        )
        await self.db.commit()
        progress_registry.update(batch_id, phase="COMPLETED", total=1, processed=1, message="Import complete.")

    async def _ensure_section(self, config: MembershipImportConfiguration, actor_id: str) -> Section:
        study_year = config.study_year
        section = await self.repo.find_section(
            config.department_id, study_year, config.section_name, config.batch_year,
        )
        if section:
            return section

        section = Section(
            department_id=config.department_id,
            name=config.section_name.strip().upper(),
            year=study_year,
            batch_year=config.batch_year,
            created_by=actor_id,
        )
        self.db.add(section)
        await self.db.flush()
        return section

    # ------------------------------------------------------------------
    # Progress, Summary, History
    # ------------------------------------------------------------------
    async def get_progress(self, batch_id: str) -> MembershipImportProgressResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found.")

        live = progress_registry.get(batch_id)
        if live and batch.status == "RUNNING":
            return MembershipImportProgressResponse(
                batch_id=batch_id, status=batch.status,
                phase=live.phase, phase_label=live.phase_label,
                percent=live.percent, processed=live.processed,
                total=live.total, message=live.message, error=live.error,
            )

        terminal = {
            "COMPLETED": ("COMPLETED", "Completed", 100),
            "FAILED": ("FAILED", "Failed", 100),
            "ANALYZED": ("QUEUED", "Ready to import", 0),
            "RUNNING": ("MEMBERSHIPS", "Import in progress", 50),
        }
        phase, label, percent = terminal.get(batch.status, ("QUEUED", "Queued", 0))
        return MembershipImportProgressResponse(
            batch_id=batch_id, status=batch.status,
            phase=phase, phase_label=label, percent=percent,
            processed=batch.memberships_created + batch.memberships_skipped,
            total=batch.students_detected, error=batch.error_message,
        )

    async def get_summary(self, batch_id: str) -> MembershipImportSummaryResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found.")
        records = await self.repo.list_records(batch_id)
        return MembershipImportSummaryResponse(
            batch_id=str(batch.id),
            file_name=batch.original_filename,
            status=batch.status,
            imported_by=batch.imported_by.full_name if batch.imported_by else None,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
            total_rows=batch.total_rows,
            students_detected=batch.students_detected,
            students_created=batch.students_created,
            students_reused=batch.students_reused,
            counselors_found=batch.counselors_found,
            counselors_missing=batch.counselors_missing,
            memberships_created=batch.memberships_created,
            memberships_updated=batch.memberships_updated,
            memberships_skipped=batch.memberships_skipped,
            failed_records=batch.failed_records,
            warning_count=batch.warning_count,
            error_message=batch.error_message,
            credentials_available=bool(batch.credentials_json),
            credential_count=len(batch.credentials_json or []),
            records=[MembershipImportResultRecord.model_validate(r) for r in records],
        )

    async def get_history(self, limit: int = 20) -> MembershipImportHistoryResponse:
        batches = await self.repo.list_batches(limit)
        stats = await self.repo.batch_statistics()
        return MembershipImportHistoryResponse(
            items=[
                MembershipImportHistoryItem(
                    batch_id=str(b.id),
                    file_name=b.original_filename,
                    status=b.status,
                    imported_by=b.imported_by.full_name if b.imported_by else None,
                    created_at=b.created_at,
                    completed_at=b.completed_at,
                    students_created=b.students_created,
                    students_reused=b.students_reused,
                    memberships_created=b.memberships_created,
                    failed_records=b.failed_records,
                    credentials_available=bool(b.credentials_json),
                )
                for b in batches
            ],
            total_imports=stats["total"],
            completed_imports=stats["completed"],
            total_memberships_created=stats["memberships"],
            total_students_created=stats["students"],
            success_rate=stats["success_rate"],
            last_import_at=stats["last_at"],
        )

    async def get_credentials(
        self, batch_id: str,
    ) -> Tuple[MembershipImportBatch, List[GeneratedStudentCredential]]:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found.")
        if not batch.credentials_json:
            raise NotFoundError("No credentials stored for this import.")
        return batch, [GeneratedStudentCredential(**c) for c in batch.credentials_json]

    async def purge_credentials(
        self, batch_id: str, actor: User, request: Optional[Request] = None,
    ) -> None:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found.")
        batch.credentials_json = None
        batch.credentials_purged_at = datetime.now(timezone.utc)
        await record_audit_log(
            self.db, user=actor,
            action=AuditAction.DELETE.value,
            entity_type="MembershipImportBatch",
            entity_id=str(batch.id),
            changes={"credentials": "purged"},
            request=request,
        )
        await self.db.commit()
