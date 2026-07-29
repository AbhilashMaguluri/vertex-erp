"""Office Import orchestration.

Analysis is read-only: it parses the file, resolves what it can against the
database, and writes nothing but the batch row itself. Execution is the
opposite — one transaction that either provisions the whole sheet or leaves the
system exactly as it found it.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.audit import record_audit_log
from app.core.enums import AuditAction, StudentStatus
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.security import generate_readable_password, get_password_hash
from app.database import AsyncSessionLocal
from app.features.admin.models import Section
from app.features.auth.models import User
from app.features.imports import naming
from app.features.imports.models import ImportBatch, ImportBatchRecord
from app.features.imports.parser import ParsedFile, parse_office_file
from app.features.imports.progress import progress_registry
from app.features.imports.repository import ImportRepository
from app.services.roll_number import describe_roll
from app.features.imports.schemas import (
    DetectedColumn,
    DetectedCounsellor,
    DetectedRange,
    DuplicateStudent,
    FieldSuggestion,
    GeneratedCredential,
    ImportConfiguration,
    ImportHistoryItem,
    ImportHistoryResponse,
    ImportPreviewResponse,
    ImportProgressResponse,
    ImportRecordResult,
    ImportSummaryResponse,
)
from app.features.students.models import CounsellorAssignment, Student, StudentEnrollment
from app.features.students.profile_models import StudentProfile

logger = logging.getLogger("app.imports")

MAX_UPLOAD_BYTES = 12 * 1024 * 1024

# Login addresses are minted on the institution's domain: a student's is
# <rollnumber>@<domain>, matching the default student password convention
# already in app/core/security.py.
DEFAULT_EMAIL_DOMAIN = "vvit.net"

# Friendly names for the columns the parser recognises, used on the Preview step.
FIELD_LABELS: Dict[str, str] = {
    "roll_range": "Student Roll Numbers",
    "counsellor_name": "Counsellor Name",
    "counsellor_phone": "Counsellor Phone",
    "counsellor_email": "Counsellor Email",
    "student_name": "Student Name",
    "department": "Department",
    "branch_code": "Branch Code",
    "academic_year": "Academic Year",
    "semester": "Semester",
    "section": "Section",
    "batch": "Batch",
    "gender": "Gender",
    "student_email": "Student Email",
    "student_phone": "Student Phone",
    "parent_phone": "Parent Phone",
    "date_of_birth": "Date of Birth",
}

_GENDERS = {"M": "MALE", "MALE": "MALE", "F": "FEMALE", "FEMALE": "FEMALE", "O": "OTHER", "OTHER": "OTHER"}

# A student record needs a date of birth and the office sheet does not carry
# one. Rather than invent a plausible birthday, every imported student gets
# this sentinel; the student replaces it from their own profile page, and it is
# obviously-not-real so nobody mistakes it for data.
UNKNOWN_DATE_OF_BIRTH = date(1900, 1, 1)


# Strong references to in-flight imports. asyncio only holds a weak reference
# to a running task, so without this a garbage collection pass can cancel an
# import mid-transaction.
_RUNNING_IMPORTS: set = set()


async def _run_import_task(batch_id: str, actor_id: str) -> None:
    """Run one import on its own session, detached from the request.

    Deliberately a module-level function rather than a method: the service that
    scheduled it belongs to a request whose session closes as soon as the 202
    is returned, and nothing in here may touch it.
    """
    async with AsyncSessionLocal() as session:
        service = ImportService(session)
        try:
            await service._execute(batch_id, actor_id)
        except Exception as exc:  # noqa: BLE001 — the batch must record any failure
            logger.exception("Office import %s failed", batch_id)
            await session.rollback()
            progress_registry.update(batch_id, phase="FAILED", error=str(exc))
            await service._mark_failed(batch_id, str(exc))


def _email_domain() -> str:
    """The institution's mail domain, taken from the configured sender address
    when there is one so a deployment elsewhere does not mint vvit.net logins."""
    configured = (settings.EMAILS_FROM_EMAIL or "").strip()
    if "@" in configured:
        domain = configured.rsplit("@", 1)[1].strip().lower()
        if domain:
            return domain
    return DEFAULT_EMAIL_DOMAIN


class ImportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ImportRepository(db)

    # ------------------------------------------------------------------
    # Step 1 & 2 — upload and analyse
    # ------------------------------------------------------------------
    async def analyze(
        self, filename: str, content: bytes, actor: User, request: Optional[Request] = None
    ) -> ImportPreviewResponse:
        if not content:
            raise ValidationError("The uploaded file is empty.")
        if len(content) > MAX_UPLOAD_BYTES:
            raise ValidationError(
                f"This file is {len(content) / 1_048_576:.1f} MB, above the "
                f"{MAX_UPLOAD_BYTES // 1_048_576} MB upload limit."
            )

        parsed = parse_office_file(filename, content)
        stored_path = self._store_upload(filename, content)

        detection = await self._build_detection(parsed)

        batch = ImportBatch(
            original_filename=filename,
            stored_path=stored_path,
            file_size_bytes=len(content),
            status="ANALYZED",
            imported_by_user_id=actor.id,
            detection_json=detection,
            total_rows=detection["total_rows"],
            students_detected=detection["students_detected"],
            counsellors_detected=detection["counsellors_detected"],
        )
        await self.repo.create_batch(batch)
        await record_audit_log(
            self.db,
            user=actor,
            action=AuditAction.CREATE.value,
            entity_type="ImportBatch",
            entity_id=str(batch.id),
            changes={"file": filename, "students_detected": detection["students_detected"], "stage": "ANALYZED"},
            request=request,
        )
        await self.db.commit()

        return self._preview_response(batch, detection)

    def _store_upload(self, filename: str, content: bytes) -> str:
        import tempfile
        temp_dir = tempfile.gettempdir()
        extension = os.path.splitext(filename)[1].lower() or ".xlsx"
        stored = os.path.join(temp_dir, f"import_{uuid.uuid4().hex}{extension}")
        with open(stored, "wb") as handle:
            handle.write(content)
        return stored

    async def _build_detection(self, parsed: ParsedFile) -> Dict[str, Any]:
        """Turn the parsed sheet into the plan the Preview step renders and the
        Import step replays. Every database lookup the plan needs happens here,
        once, rather than per row."""
        domain = _email_domain()

        all_rolls: List[str] = []
        roll_first_row: Dict[str, int] = {}
        intra_file_duplicates: Dict[str, List[int]] = {}
        ranges: List[Dict[str, Any]] = []

        for row in parsed.rows:
            for roll in row.roll_numbers:
                if roll in roll_first_row:
                    intra_file_duplicates.setdefault(roll, [roll_first_row[roll]]).append(row.row_number)
                    continue
                roll_first_row[roll] = row.row_number
                all_rolls.append(roll)

            ranges.append(
                {
                    "row_number": row.row_number,
                    "raw_text": row.raw_roll_text,
                    "description": " + ".join(row.range_segments) or row.raw_roll_text,
                    "student_count": len(row.roll_numbers),
                    "counsellor_name": row.counsellor_name,
                    "counsellor_phone": row.counsellor_phone,
                    "first_roll": row.roll_numbers[0] if row.roll_numbers else None,
                    "last_roll": row.roll_numbers[-1] if row.roll_numbers else None,
                    "warnings": row.warnings,
                    "errors": row.errors,
                }
            )

        existing_students = await self.repo.get_students_by_rolls(all_rolls)
        counsellors = await self._resolve_counsellors(parsed, domain)

        duplicates: List[Dict[str, Any]] = []
        for roll, student in existing_students.items():
            duplicates.append(
                {
                    "roll_number": roll,
                    "reason": "A student account with this roll number already exists — it will be skipped.",
                    "existing_name": student.user.full_name if student.user else None,
                    "row_numbers": [roll_first_row.get(roll)] if roll_first_row.get(roll) else [],
                }
            )
        for roll, rows in intra_file_duplicates.items():
            duplicates.append(
                {
                    "roll_number": roll,
                    "reason": f"Listed more than once in this file (rows {', '.join(str(r) for r in rows)}) — imported once.",
                    "existing_name": None,
                    "row_numbers": rows,
                }
            )

        importable = [r for r in all_rolls if r not in existing_students]
        suggestions = await self._build_suggestions(parsed, all_rolls)

        errors = [f"Row {row.row_number}: {e}" for row in parsed.rows for e in row.errors]
        warnings = list(parsed.warnings) + [
            f"Row {row.row_number}: {w}" for row in parsed.rows for w in row.warnings
        ]

        return {
            "sheet_name": parsed.sheet_name,
            "header_row_number": parsed.header_row_number,
            "detected_columns": [
                {"field": f, "source_header": h, "label": FIELD_LABELS.get(f, f.replace("_", " ").title())}
                for f, h in parsed.detected_columns.items()
            ],
            "ignored_columns": parsed.ignored_columns,
            "total_rows": len(parsed.rows),
            "valid_rows": sum(1 for r in parsed.rows if r.ok),
            "students_detected": len(all_rolls),
            "counsellors_detected": len(counsellors),
            "duplicate_students": len(duplicates),
            "importable_students": len(importable),
            "ranges": ranges,
            "counsellors": counsellors,
            "duplicates": duplicates,
            "suggestions": suggestions,
            "warnings": warnings,
            "errors": errors,
            "email_domain": domain,
            # The executable plan: roll -> counsellor key, plus per-student
            # optional attributes read off the sheet.
            "plan": self._build_plan(parsed, roll_first_row),
        }

    def _build_plan(self, parsed: ParsedFile, roll_first_row: Dict[str, int]) -> List[Dict[str, Any]]:
        """One entry per student to create, in sheet order."""
        plan: List[Dict[str, Any]] = []
        emitted: set = set()
        for row in parsed.rows:
            counsellor_key = (
                naming.normalise_person_key(row.counsellor_name) if row.counsellor_name else None
            )
            # Per-student columns (name, gender, email …) only describe a
            # student when the row names exactly one; on a range row they would
            # be the same value stamped onto forty different people.
            single = len(row.roll_numbers) == 1
            for roll in row.roll_numbers:
                if roll in emitted:
                    continue
                emitted.add(roll)
                plan.append(
                    {
                        "roll_number": roll,
                        "row_number": roll_first_row.get(roll, row.row_number),
                        "counsellor_key": counsellor_key,
                        "student_name": row.student_name if single else None,
                        "gender": row.gender if single else None,
                        "email": row.student_email if single else None,
                        "phone": row.student_phone if single else None,
                        "date_of_birth": row.date_of_birth if single else None,
                    }
                )
        return plan

    async def _resolve_counsellors(self, parsed: ParsedFile, domain: str) -> List[Dict[str, Any]]:
        """Group the sheet's counsellors and decide, for each, whether an
        account already exists.

        Matching is by phone number first — the one identifier an office sheet
        gets right and a person cannot spell two ways — then by a normalised
        name key, which collapses "Dr. S. Ravindra" and "Ravindra S." together.
        """
        existing_users = await self.repo.list_counsellor_users()
        by_phone: Dict[str, User] = {}
        by_name: Dict[str, User] = {}
        for user in existing_users:
            if user.phone:
                by_phone.setdefault("".join(ch for ch in user.phone if ch.isdigit())[-10:], user)
            by_name.setdefault(naming.normalise_person_key(user.full_name), user)

        taken_usernames, taken_emails = await self.repo.get_taken_usernames_and_emails()

        grouped: Dict[str, Dict[str, Any]] = {}
        for row in parsed.rows:
            if not row.counsellor_name:
                continue
            key = naming.normalise_person_key(row.counsellor_name)
            if not key:
                continue
            entry = grouped.setdefault(
                key,
                {
                    "key": key,
                    "name_as_written": row.counsellor_name,
                    "phone": row.counsellor_phone,
                    "email": row.counsellor_email,
                    "student_count": 0,
                    "rows": [],
                },
            )
            entry["student_count"] += len(row.roll_numbers)
            entry["rows"].append(row.row_number)
            entry["phone"] = entry["phone"] or row.counsellor_phone
            entry["email"] = entry["email"] or row.counsellor_email

        resolved: List[Dict[str, Any]] = []
        for key, entry in grouped.items():
            person = naming.split_person_name(entry["name_as_written"])
            digits = "".join(ch for ch in (entry["phone"] or "") if ch.isdigit())[-10:]

            match = by_phone.get(digits) if digits else None
            matched_on = "phone number" if match else None
            if not match:
                match = by_name.get(key)
                matched_on = "name" if match else None

            record = {
                **entry,
                "display_name": person.display_name,
                "first_name": person.first_name,
                "last_name": person.last_name,
            }
            if match:
                record.update(
                    {
                        "status": "EXISTING",
                        "existing_user_id": str(match.id),
                        "matched_on": matched_on,
                        "proposed_username": match.username or match.email,
                        "email": match.email,
                    }
                )
            else:
                username, email = naming.allocate_counsellor_identity(
                    person, domain, taken_usernames, taken_emails
                )
                taken_usernames.add(username)
                taken_emails.add(email)
                record.update(
                    {
                        "status": "NEW",
                        "existing_user_id": None,
                        "matched_on": None,
                        "proposed_username": username,
                        "proposed_email": email,
                    }
                )
            resolved.append(record)

        resolved.sort(key=lambda c: (-c["student_count"], c["display_name"]))
        return resolved

    async def _build_suggestions(self, parsed: ParsedFile, rolls: List[str]) -> List[Dict[str, Any]]:
        """What the Configure step should pre-fill, and where each value came from.

        Nothing here is applied automatically. A suggestion carries its
        provenance (the file, the roll number's own structure, or the current
        academic calendar) so the administrator can see why a box is filled in.
        """
        departments = await self.repo.list_departments()
        semesters = await self.repo.list_semesters()
        academic_years = await self.repo.list_academic_years()

        first_values: Dict[str, Optional[str]] = {}
        for field_name in ("department", "branch_code", "section", "semester", "academic_year", "batch"):
            first_values[field_name] = next(
                (getattr(row, field_name) for row in parsed.rows if getattr(row, field_name)), None
            )

        meta = describe_roll(rolls[0]) if rolls else None
        suggestions: List[Dict[str, Any]] = []

        # --- Department ---------------------------------------------------
        dept_id, dept_label, dept_source, dept_confidence, dept_note = None, None, "NONE", "NONE", None
        written = first_values["department"] or first_values["branch_code"]
        if written:
            match = self._match_department(departments, written)
            if match:
                dept_id, dept_label, dept_source, dept_confidence = str(match.id), match.name, "FILE", "HIGH"
        if not dept_id and meta and meta.branch_hint:
            match = self._match_department(departments, meta.branch_hint)
            if match:
                dept_id, dept_label, dept_source, dept_confidence = str(match.id), match.name, "DERIVED", "MEDIUM"
                dept_note = (
                    f"Read from the roll number: branch code {meta.branch_code} in "
                    f"{rolls[0]} maps to {meta.branch_hint}."
                )
        suggestions.append(
            {
                "field": "department_id",
                "label": "Department",
                "required": True,
                "source": dept_source,
                "detected_value": dept_label or written,
                "detected_id": dept_id,
                "confidence": dept_confidence,
                "note": dept_note,
            }
        )

        # --- Batch year ---------------------------------------------------
        batch_year: Optional[int] = None
        batch_source, batch_note = "NONE", None
        if first_values["batch"]:
            digits = "".join(ch for ch in first_values["batch"] if ch.isdigit())[:4]
            if len(digits) == 4:
                batch_year, batch_source = int(digits), "FILE"
        if batch_year is None and meta and meta.batch_year:
            batch_year, batch_source = meta.batch_year, "DERIVED"
            batch_note = f"Read from the roll number: {rolls[0]} begins with {str(meta.batch_year)[-2:]}."
        suggestions.append(
            {
                "field": "batch_year",
                "label": "Batch",
                "required": True,
                "source": batch_source,
                "detected_value": str(batch_year) if batch_year else None,
                "detected_id": None,
                "confidence": "HIGH" if batch_source == "FILE" else ("MEDIUM" if batch_year else "NONE"),
                "note": batch_note,
            }
        )

        # --- Semester -----------------------------------------------------
        semester_id, semester_label, sem_source, sem_note = None, None, "NONE", None
        if first_values["semester"]:
            match = self._match_semester(semesters, first_values["semester"])
            if match:
                semester_id, semester_label, sem_source = str(match.id), match.name, "FILE"
        if not semester_id:
            current = next((s for s in semesters if s.is_current), None)
            if current:
                semester_id, semester_label, sem_source = str(current.id), current.name, "CURRENT"
                sem_note = "The semester currently marked as active in Academic Configuration."
            elif batch_year:
                derived = self._derive_semester_name(batch_year)
                match = self._match_semester(semesters, derived)
                if match:
                    semester_id, semester_label, sem_source = str(match.id), match.name, "DERIVED"
                    sem_note = f"Worked out from the {batch_year} batch and today's date."
        suggestions.append(
            {
                "field": "semester_id",
                "label": "Semester",
                "required": True,
                "source": sem_source,
                "detected_value": semester_label,
                "detected_id": semester_id,
                "confidence": "HIGH" if sem_source == "FILE" else ("MEDIUM" if semester_id else "NONE"),
                "note": sem_note,
            }
        )

        # --- Section ------------------------------------------------------
        section = (first_values["section"] or "").strip().upper() or None
        suggestions.append(
            {
                "field": "section_name",
                "label": "Section",
                "required": True,
                "source": "FILE" if section else "NONE",
                "detected_value": section,
                "detected_id": None,
                "confidence": "HIGH" if section else "NONE",
                "note": None if section else "Not present in the file — choose the section these students belong to.",
            }
        )

        # --- Academic year -------------------------------------------------
        ay_id, ay_label, ay_source, ay_note = None, None, "NONE", None
        if first_values["academic_year"]:
            match = next(
                (a for a in academic_years if a.name.replace(" ", "") == first_values["academic_year"].replace(" ", "")),
                None,
            )
            if match:
                ay_id, ay_label, ay_source = str(match.id), match.name, "FILE"
        if not ay_id:
            current = next((a for a in academic_years if a.is_current), None)
            if current:
                ay_id, ay_label, ay_source = str(current.id), current.name, "CURRENT"
                ay_note = "The academic year currently marked as active."
        suggestions.append(
            {
                "field": "academic_year_id",
                "label": "Academic Year",
                "required": False,
                "source": ay_source,
                "detected_value": ay_label,
                "detected_id": ay_id,
                "confidence": "HIGH" if ay_source == "FILE" else ("MEDIUM" if ay_id else "NONE"),
                "note": ay_note,
            }
        )
        return suggestions

    @staticmethod
    def _match_department(departments: List[Any], written: str) -> Optional[Any]:
        needle = "".join(ch for ch in written.lower() if ch.isalnum())
        if not needle:
            return None
        for dept in departments:
            code = "".join(ch for ch in dept.code.lower() if ch.isalnum())
            name = "".join(ch for ch in dept.name.lower() if ch.isalnum())
            if needle in (code, name) or needle == code:
                return dept
        for dept in departments:
            name = "".join(ch for ch in dept.name.lower() if ch.isalnum())
            if needle and (needle in name or name in needle):
                return dept
        return None

    @staticmethod
    def _match_semester(semesters: List[Any], written: str) -> Optional[Any]:
        cleaned = written.strip().upper().replace(" ", "")
        roman = {"I": "1", "II": "2", "III": "3", "IV": "4"}
        for semester in semesters:
            if cleaned == semester.name.upper().replace(" ", ""):
                return semester
        # "IV-I" is how a college writes "4-1".
        parts = cleaned.replace("–", "-").split("-")
        if len(parts) == 2:
            converted = f"{roman.get(parts[0], parts[0])}-{roman.get(parts[1], parts[1])}"
            for semester in semesters:
                if converted == semester.name.upper().replace(" ", ""):
                    return semester
        if cleaned.isdigit():
            for semester in semesters:
                if semester.number == int(cleaned):
                    return semester
        return None

    @staticmethod
    def _derive_semester_name(batch_year: int) -> str:
        """Where a batch should be today. The academic year turns over in July,
        odd semesters run Jul–Dec and even ones Jan–Jun."""
        today = date.today()
        study_year = today.year - batch_year + (1 if today.month >= 7 else 0)
        study_year = max(1, min(4, study_year))
        half = 1 if today.month >= 7 else 2
        return f"{study_year}-{half}"

    # ------------------------------------------------------------------
    # Preview / summary serialisation
    # ------------------------------------------------------------------
    def _preview_response(self, batch: ImportBatch, detection: Dict[str, Any]) -> ImportPreviewResponse:
        counsellors = detection.get("counsellors", [])
        return ImportPreviewResponse(
            batch_id=str(batch.id),
            file_name=batch.original_filename,
            sheet_name=detection["sheet_name"],
            header_row_number=detection["header_row_number"],
            status=batch.status,
            detected_columns=[DetectedColumn(**c) for c in detection["detected_columns"]],
            ignored_columns=detection["ignored_columns"],
            total_rows=detection["total_rows"],
            valid_rows=detection["valid_rows"],
            students_detected=detection["students_detected"],
            counsellors_detected=detection["counsellors_detected"],
            new_counsellors=sum(1 for c in counsellors if c["status"] == "NEW"),
            existing_counsellors=sum(1 for c in counsellors if c["status"] == "EXISTING"),
            duplicate_students=detection["duplicate_students"],
            importable_students=detection["importable_students"],
            ranges=[DetectedRange(**r) for r in detection["ranges"]],
            counsellors=[
                DetectedCounsellor(
                    key=c["key"],
                    name_as_written=c["name_as_written"],
                    display_name=c["display_name"],
                    phone=c.get("phone"),
                    email=c.get("email") or c.get("proposed_email"),
                    proposed_username=c.get("proposed_username"),
                    student_count=c["student_count"],
                    status=c["status"],
                    existing_user_id=c.get("existing_user_id"),
                    matched_on=c.get("matched_on"),
                    rows=c.get("rows", []),
                )
                for c in counsellors
            ],
            duplicates=[DuplicateStudent(**d) for d in detection["duplicates"]],
            suggestions=[FieldSuggestion(**s) for s in detection["suggestions"]],
            warnings=detection["warnings"],
            errors=detection["errors"],
            sample_roll_numbers=[p["roll_number"] for p in detection["plan"][:12]],
        )

    async def get_preview(self, batch_id: str) -> ImportPreviewResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch or not batch.detection_json:
            raise NotFoundError("Import not found")
        return self._preview_response(batch, batch.detection_json)

    # ------------------------------------------------------------------
    # Step 4 — execute
    # ------------------------------------------------------------------
    async def start_import(
        self, batch_id: str, config: ImportConfiguration, actor: User, request: Optional[Request] = None
    ) -> ImportProgressResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found")
        if batch.status == "RUNNING":
            raise ConflictError("This import is already running.")
        if batch.status == "COMPLETED":
            raise ConflictError(
                "This import has already been applied. Upload the file again to import any remaining students."
            )
        if not batch.detection_json:
            raise ValidationError("This upload has no analysis attached — upload the file again.")

        await self._validate_configuration(config)

        batch.status = "RUNNING"
        batch.configuration_json = config.model_dump()
        batch.started_at = datetime.now(timezone.utc)
        batch.error_message = None
        await self.db.flush()
        await record_audit_log(
            self.db,
            user=actor,
            action=AuditAction.CREATE.value,
            entity_type="ImportBatch",
            entity_id=str(batch.id),
            changes={"stage": "STARTED", "file": batch.original_filename, "configuration": config.model_dump()},
            request=request,
        )
        await self.db.commit()

        total = len(batch.detection_json.get("plan", []))
        progress_registry.start(str(batch.id), total)
        progress_registry.update(str(batch.id), phase="QUEUED", message="Preparing the import…")

        # Detached from the request: the import owns its own session and
        # transaction, so the browser closing mid-run cannot leave it half done.
        # The reference is held until the task finishes — asyncio keeps only a
        # weak reference, and a task nothing else points at can be collected
        # mid-flight.
        task = asyncio.create_task(_run_import_task(str(batch.id), str(actor.id)))
        _RUNNING_IMPORTS.add(task)
        task.add_done_callback(_RUNNING_IMPORTS.discard)

        return ImportProgressResponse(
            batch_id=str(batch.id),
            status="RUNNING",
            phase="QUEUED",
            phase_label="Queued",
            percent=0,
            processed=0,
            total=total,
            message="Preparing the import…",
        )

    async def _validate_configuration(self, config: ImportConfiguration) -> None:
        if not await self.repo.get_department(config.department_id):
            raise ValidationError("The selected department no longer exists in Academic Configuration.")
        if not await self.repo.get_semester(config.semester_id):
            raise ValidationError("The selected semester no longer exists in Academic Configuration.")

    async def _mark_failed(self, batch_id: str, message: str) -> None:
        try:
            batch = await self.repo.get_batch(batch_id)
            if batch:
                batch.status = "FAILED"
                batch.error_message = message[:2000]
                batch.completed_at = datetime.now(timezone.utc)
                await self.db.commit()
        except Exception:  # noqa: BLE001 — nothing useful is left to do here
            logger.exception("Could not record the failure of import %s", batch_id)

    async def _execute(self, batch_id: str, actor_id: str) -> None:
        """Provision the whole sheet in one transaction.

        Individual rows that cannot be created are recorded as FAILED inside a
        savepoint and the run continues — one malformed roll number must not
        cost the other four hundred. A failure outside a savepoint aborts
        everything, which is the point of the single transaction.
        """
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found")

        detection = batch.detection_json or {}
        config = ImportConfiguration(**(batch.configuration_json or {}))
        plan: List[Dict[str, Any]] = detection.get("plan", [])
        domain = detection.get("email_domain") or _email_domain()

        actor = await self.repo.get_user_by_id(actor_id)

        records: List[ImportBatchRecord] = []
        credentials: List[Dict[str, Any]] = []

        semester = await self.repo.get_semester(config.semester_id)
        section = await self._ensure_section(config, actor_id)
        student_role = await self.repo.get_role("STUDENT")
        counsellor_role = await self.repo.get_role("COUNSELLOR")
        if not student_role or not counsellor_role:
            raise ValidationError(
                "The STUDENT and COUNSELLOR roles are missing. Run `python -m app.scripts.seed` first."
            )

        taken_usernames, taken_emails = await self.repo.get_taken_usernames_and_emails()

        # ---- Counsellors ------------------------------------------------
        progress_registry.update(
            batch_id, phase="COUNSELLORS", total=len(detection.get("counsellors", [])),
            message="Creating counsellor accounts…",
        )
        counsellor_users: Dict[str, User] = {}
        counsellors_created = counsellors_reused = 0

        for entry in detection.get("counsellors", []):
            key = entry["key"]
            try:
                if entry.get("existing_user_id"):
                    existing = await self.repo.get_user_by_id(entry["existing_user_id"])
                    if existing:
                        counsellor_users[key] = existing
                        counsellors_reused += 1
                        records.append(
                            ImportBatchRecord(
                                batch_id=batch.id, record_type="COUNSELLOR", identifier=entry["name_as_written"],
                                display_name=existing.full_name, status="REUSED", user_id=existing.id,
                                message=f"Existing account reused (matched on {entry.get('matched_on') or 'name'}).",
                                source_row_number=(entry.get("rows") or [None])[0],
                            )
                        )
                        progress_registry.advance(batch_id, f"Reused {existing.full_name}")
                        continue

                async with self.db.begin_nested():
                    username = entry.get("proposed_username") or naming.slugify(entry["display_name"])
                    email = entry.get("proposed_email") or f"{username}@{domain}"
                    # The analysis may be minutes old; re-check against what is
                    # actually taken now rather than trusting the stored plan.
                    while username.lower() in taken_usernames or email.lower() in taken_emails:
                        username, email = naming.allocate_counsellor_identity(
                            naming.split_person_name(entry["name_as_written"]),
                            domain, taken_usernames, taken_emails,
                        )
                    password = generate_readable_password()
                    user = User(
                        email=email.lower(),
                        username=username,
                        hashed_password=get_password_hash(password),
                        first_name=entry.get("first_name") or entry["display_name"],
                        last_name=entry.get("last_name") or "",
                        phone=entry.get("phone"),
                        department_id=config.department_id,
                        is_active=True,
                        force_password_change=True,
                        created_by=actor_id,
                    )
                    user.roles.append(counsellor_role)
                    self.db.add(user)
                    await self.db.flush()

                taken_usernames.add(username.lower())
                taken_emails.add(email.lower())
                counsellor_users[key] = user
                counsellors_created += 1
                credentials.append(
                    {
                        "record_type": "COUNSELLOR",
                        "identifier": entry["name_as_written"],
                        "full_name": user.full_name,
                        "username": username,
                        "email": user.email,
                        "temporary_password": password,
                        "counsellor": None,
                        "status": "Active",
                    }
                )
                records.append(
                    ImportBatchRecord(
                        batch_id=batch.id, record_type="COUNSELLOR", identifier=entry["name_as_written"],
                        display_name=user.full_name, status="CREATED", user_id=user.id,
                        message=f"Counsellor account created ({username}).",
                        source_row_number=(entry.get("rows") or [None])[0],
                    )
                )
                progress_registry.advance(batch_id, f"Created {user.full_name}")
            except Exception as exc:  # noqa: BLE001 — one counsellor must not abort the batch
                records.append(
                    ImportBatchRecord(
                        batch_id=batch.id, record_type="COUNSELLOR", identifier=entry["name_as_written"],
                        display_name=entry.get("display_name"), status="FAILED",
                        message=self._message_of(exc),
                        source_row_number=(entry.get("rows") or [None])[0],
                    )
                )
                progress_registry.advance(batch_id)

        # ---- Students ----------------------------------------------------
        progress_registry.update(
            batch_id, phase="STUDENTS", total=len(plan), message="Creating student accounts…"
        )
        existing_students = await self.repo.get_students_by_rolls([p["roll_number"] for p in plan])
        created_students: List[Tuple[Student, Optional[str]]] = []
        students_created = students_skipped = 0

        for item in plan:
            roll = item["roll_number"].upper()
            counsellor = counsellor_users.get(item.get("counsellor_key") or "")
            counsellor_name = counsellor.full_name if counsellor else None

            if roll in existing_students:
                students_skipped += 1
                existing = existing_students[roll]
                records.append(
                    ImportBatchRecord(
                        batch_id=batch.id, record_type="STUDENT", identifier=roll,
                        display_name=existing.user.full_name if existing.user else None,
                        status="SKIPPED", message="A student with this roll number already exists.",
                        source_row_number=item.get("row_number"),
                        user_id=existing.user_id,
                    )
                )
                if config.reassign_existing_students and counsellor:
                    created_students.append((existing, item.get("counsellor_key")))
                progress_registry.advance(batch_id, f"Skipped {roll} (already exists)")
                continue

            try:
                async with self.db.begin_nested():
                    student, password, username = await self._create_student(
                        item, roll, config, semester, section, student_role, domain,
                        taken_usernames, taken_emails, actor_id,
                    )
                taken_usernames.add(username.lower())
                taken_emails.add(f"{username.lower()}@{domain}")
                students_created += 1
                created_students.append((student, item.get("counsellor_key")))
                credentials.append(
                    {
                        "record_type": "STUDENT",
                        "identifier": roll,
                        "full_name": student.user.full_name if student.user else roll,
                        "username": username,
                        "email": f"{username.lower()}@{domain}",
                        "temporary_password": password,
                        "counsellor": counsellor_name,
                        "status": "Active",
                    }
                )
                records.append(
                    ImportBatchRecord(
                        batch_id=batch.id, record_type="STUDENT", identifier=roll,
                        display_name=student.user.full_name if student.user else roll,
                        status="CREATED", user_id=student.user_id,
                        message="Student account, academic record and profile created.",
                        source_row_number=item.get("row_number"),
                    )
                )
                progress_registry.advance(batch_id, f"Created {roll}")
            except Exception as exc:  # noqa: BLE001 — record and carry on
                records.append(
                    ImportBatchRecord(
                        batch_id=batch.id, record_type="STUDENT", identifier=roll,
                        status="FAILED", message=self._message_of(exc),
                        source_row_number=item.get("row_number"),
                    )
                )
                progress_registry.advance(batch_id)

        # ---- Counsellor assignments ---------------------------------------
        progress_registry.update(
            batch_id, phase="ASSIGNMENTS", total=len(created_students),
            message="Assigning students to their counsellors…",
        )
        assignments_created = 0
        already_assigned = await self.repo.students_with_open_assignment(
            [str(s.id) for s, _ in created_students]
        )
        for student, counsellor_key in created_students:
            counsellor = counsellor_users.get(counsellor_key or "")
            # Both skip conditions are settled before the savepoint opens: a
            # student who needs no assignment should not cost a SAVEPOINT/RELEASE
            # round trip, and branching out of an open `async with` is the kind
            # of thing that reads as a bug even when it isn't.
            if not counsellor:
                progress_registry.advance(batch_id)
                continue
            is_reassignment = str(student.id) in already_assigned
            if is_reassignment and not config.reassign_existing_students:
                progress_registry.advance(batch_id)
                continue

            try:
                async with self.db.begin_nested():
                    if is_reassignment:
                        await self.repo.close_open_assignments([str(student.id)])
                    self.db.add(
                        CounsellorAssignment(
                            student_id=student.id,
                            counsellor_id=counsellor.id,
                            semester_id=config.semester_id,
                            effective_from=datetime.now(timezone.utc),
                        )
                    )
                    await self.db.flush()
                assignments_created += 1
                progress_registry.advance(batch_id, f"Assigned {student.roll_number}")
            except Exception as exc:  # noqa: BLE001
                records.append(
                    ImportBatchRecord(
                        batch_id=batch.id, record_type="STUDENT", identifier=student.roll_number,
                        status="FAILED", message=f"Counsellor assignment failed: {self._message_of(exc)}",
                    )
                )
                progress_registry.advance(batch_id)

        # ---- Finalise ------------------------------------------------------
        progress_registry.update(batch_id, phase="CREDENTIALS", total=1, message="Generating credentials…")
        failed = sum(1 for r in records if r.status == "FAILED")
        batch.students_created = students_created
        batch.students_skipped = students_skipped
        batch.counsellors_created = counsellors_created
        batch.counsellors_reused = counsellors_reused
        batch.assignments_created = assignments_created
        batch.failed_records = failed
        batch.warning_count = len(detection.get("warnings", []))
        batch.credentials_json = credentials
        batch.summary_json = {
            "students_created": students_created,
            "students_skipped": students_skipped,
            "counsellors_created": counsellors_created,
            "counsellors_reused": counsellors_reused,
            "assignments_created": assignments_created,
            "failed_records": failed,
            "section": section.name,
            "section_id": str(section.id),
        }
        batch.status = "COMPLETED"
        batch.completed_at = datetime.now(timezone.utc)

        progress_registry.update(batch_id, phase="FINALISING", total=1, message="Committing the import…")
        await self.repo.add_records(records)
        await record_audit_log(
            self.db,
            user=actor,
            action=AuditAction.CREATE.value,
            entity_type="ImportBatch",
            entity_id=str(batch.id),
            changes={
                "stage": "COMPLETED",
                "file": batch.original_filename,
                **batch.summary_json,
            },
        )
        await self.db.commit()

        progress_registry.update(batch_id, phase="COMPLETED", total=1, processed=1, message="Import complete.")

    async def _create_student(
        self,
        item: Dict[str, Any],
        roll: str,
        config: ImportConfiguration,
        semester: Any,
        section: Section,
        student_role: Any,
        domain: str,
        taken_usernames: set,
        taken_emails: set,
        actor_id: str,
    ) -> Tuple[Student, str, str]:
        username = naming.student_username(roll)
        email = naming.student_email(roll, domain)
        if username.lower() in taken_usernames or email.lower() in taken_emails:
            raise ValidationError(f"The login '{username}' is already in use by another account.")

        first_name, last_name = self._student_name(item, roll)
        password = generate_readable_password()

        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone=item.get("phone"),
            department_id=config.department_id,
            is_active=True,
            force_password_change=True,
            created_by=actor_id,
        )
        user.roles.append(student_role)
        self.db.add(user)
        await self.db.flush()

        student = Student(
            user_id=user.id,
            roll_number=roll,
            # The office sheet has no separate registration number; the roll
            # number is what the institution registers a student under, and the
            # column is unique + NOT NULL.
            registration_number=roll,
            date_of_birth=self._parse_date(item.get("date_of_birth")) or UNKNOWN_DATE_OF_BIRTH,
            batch_year=config.batch_year,
            gender=_GENDERS.get((item.get("gender") or "").strip().upper()),
            status=StudentStatus.ACTIVE.value,
            department_id=config.department_id,
            current_semester_id=semester.id if semester else None,
            created_by=actor_id,
        )
        self.db.add(student)
        await self.db.flush()

        # The academic record and an empty profile shell, so the student's own
        # profile page and every roster query work from the first login rather
        # than 404-ing until someone edits them.
        self.db.add(
            StudentEnrollment(student_id=student.id, section_id=section.id, semester_id=config.semester_id)
        )
        self.db.add(StudentProfile(student_id=student.id))
        await self.db.flush()

        student.user = user
        return student, password, username

    @staticmethod
    def _student_name(item: Dict[str, Any], roll: str) -> Tuple[str, str]:
        """The office range sheet carries no student names. Rather than invent
        one, the account is named after the roll number until the student fills
        their profile in — obviously a placeholder, never mistaken for data."""
        written = (item.get("student_name") or "").strip()
        if written:
            person = naming.split_person_name(written)
            return person.first_name, person.last_name
        return roll, ""

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[date]:
        if not value:
            return None
        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    async def _ensure_section(self, config: ImportConfiguration, actor_id: str) -> Section:
        """Find the section, or create it. Sections for a new intake usually do
        not exist yet, and making the administrator go and create one by hand is
        exactly the manual mapping this module exists to remove."""
        study_year = config.study_year
        section = await self.repo.find_section(
            config.department_id, study_year, config.section_name, config.batch_year
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

    @staticmethod
    def _message_of(exc: Exception) -> str:
        message = getattr(exc, "message", None) or str(exc)
        return message[:500]

    # ------------------------------------------------------------------
    # Progress, summary and history
    # ------------------------------------------------------------------
    async def get_progress(self, batch_id: str) -> ImportProgressResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found")

        live = progress_registry.get(batch_id)
        if live and batch.status == "RUNNING":
            return ImportProgressResponse(
                batch_id=batch_id, status=batch.status, phase=live.phase, phase_label=live.phase_label,
                percent=live.percent, processed=live.processed, total=live.total,
                message=live.message, error=live.error,
            )

        terminal = {
            "COMPLETED": ("COMPLETED", "Completed", 100),
            "FAILED": ("FAILED", "Failed", 100),
            "ANALYZED": ("QUEUED", "Ready to import", 0),
            "RUNNING": ("STUDENTS", "Import in progress", 50),
        }
        phase, label, percent = terminal.get(batch.status, ("QUEUED", "Queued", 0))
        processed = batch.students_created + batch.students_skipped
        return ImportProgressResponse(
            batch_id=batch_id, status=batch.status, phase=phase, phase_label=label, percent=percent,
            processed=processed, total=batch.students_detected, error=batch.error_message,
        )

    async def get_summary(self, batch_id: str) -> ImportSummaryResponse:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found")
        records = await self.repo.list_records(batch_id)
        return ImportSummaryResponse(
            batch_id=str(batch.id),
            file_name=batch.original_filename,
            status=batch.status,
            imported_by=batch.imported_by.full_name if batch.imported_by else None,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
            total_rows=batch.total_rows,
            students_detected=batch.students_detected,
            counsellors_detected=batch.counsellors_detected,
            students_created=batch.students_created,
            students_skipped=batch.students_skipped,
            counsellors_created=batch.counsellors_created,
            counsellors_reused=batch.counsellors_reused,
            assignments_created=batch.assignments_created,
            failed_records=batch.failed_records,
            warning_count=batch.warning_count,
            error_message=batch.error_message,
            configuration=batch.configuration_json,
            credentials_available=bool(batch.credentials_json),
            credential_count=len(batch.credentials_json or []),
            records=[ImportRecordResult.model_validate(r) for r in records],
        )

    async def get_history(self, limit: int = 20) -> ImportHistoryResponse:
        batches = await self.repo.list_batches(limit)
        stats = await self.repo.batch_statistics()
        return ImportHistoryResponse(
            items=[
                ImportHistoryItem(
                    batch_id=str(b.id),
                    file_name=b.original_filename,
                    status=b.status,
                    imported_by=b.imported_by.full_name if b.imported_by else None,
                    created_at=b.created_at,
                    completed_at=b.completed_at,
                    students_created=b.students_created,
                    counsellors_created=b.counsellors_created,
                    students_skipped=b.students_skipped,
                    failed_records=b.failed_records,
                    credentials_available=bool(b.credentials_json),
                )
                for b in batches
            ],
            total_imports=stats["total"],
            completed_imports=stats["completed"],
            total_students_created=stats["students"],
            total_counsellors_created=stats["counsellors"],
            success_rate=stats["success_rate"],
            last_import_at=stats["last_at"],
        )

    async def get_credentials(self, batch_id: str) -> Tuple[ImportBatch, List[GeneratedCredential]]:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found")
        if not batch.credentials_json:
            raise NotFoundError(
                "No credentials are stored for this import — they have been purged, or the import "
                "created no new accounts."
            )
        return batch, [GeneratedCredential(**c) for c in batch.credentials_json]

    async def purge_credentials(self, batch_id: str, actor: User, request: Optional[Request] = None) -> None:
        batch = await self.repo.get_batch(batch_id)
        if not batch:
            raise NotFoundError("Import not found")
        batch.credentials_json = None
        batch.credentials_purged_at = datetime.now(timezone.utc)
        await record_audit_log(
            self.db,
            user=actor,
            action=AuditAction.DELETE.value,
            entity_type="ImportBatch",
            entity_id=str(batch.id),
            changes={"credentials": "purged"},
            request=request,
        )
        await self.db.commit()
