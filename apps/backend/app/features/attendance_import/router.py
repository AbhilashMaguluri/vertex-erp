"""FastAPI router for the Enterprise Attendance Import feature."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit_log
from app.core.enums import AuditAction
from app.core.permissions import require_permission
from app.database import get_async_db
from app.features.attendance_import import exports
from app.features.attendance_import.schemas import (
    AttendanceImportConfiguration,
    AttendanceImportHistoryResponse,
    AttendanceImportPreviewResponse,
    AttendanceImportProgressResponse,
    AttendanceImportSummaryResponse,
    ValidationErrorRow,
)
from app.features.attendance_import.service import AttendanceImportService
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User

router = APIRouter(prefix="/admin/attendance-imports", tags=["Attendance Import"])

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _attachment(content: bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- History & Template (static parameter paths first) ----------------------
@router.get("", response_model=AttendanceImportHistoryResponse)
async def list_attendance_import_history(
    limit: int = Query(20, ge=1, le=100),
    _: bool = Depends(require_permission("attendance.create")),
    db: AsyncSession = Depends(get_async_db),
):
    """Recent attendance imports and aggregate statistics."""
    return await AttendanceImportService(db).get_history(limit)


@router.get("/sample-template.xlsx")
async def download_attendance_sample_template(
    _: bool = Depends(require_permission("attendance.create")),
):
    """Download two-column sample template (Student Roll Number, Attendance Status)."""
    return _attachment(
        exports.build_sample_template(),
        "Attendance_Import_Template.xlsx",
        XLSX_MEDIA_TYPE,
    )


# --- Upload & Analyze ------------------------------------------------------
@router.post("/analyze", response_model=AttendanceImportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def analyze_attendance_file(
    request: Request,
    file: UploadFile = File(..., description="Two-column Excel or CSV file"),
    mode: str = Form("TODAY", description="TODAY or PAST"),
    attendance_date: Optional[date] = Form(None, description="Attendance date (defaults to today if missing)"),
    subject_id: Optional[str] = Form(None, description="Subject UUID"),
    department_id: Optional[str] = Form(None),
    section_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("attendance.create")),
    db: AsyncSession = Depends(get_async_db),
):
    """Upload and analyze an attendance file. Mode TODAY defaults date to today."""
    effective_date = attendance_date or date.today()
    if mode.upper() == "TODAY":
        effective_date = date.today()

    service = AttendanceImportService(db)
    content = await file.read()
    return await service.analyze(
        file.filename or "attendance_upload.xlsx",
        content,
        mode.upper(),
        effective_date,
        subject_id,
        department_id,
        section_id,
        current_user,
        request,
    )


# --- Preview ----------------------------------------------------------------
@router.get("/{batch_id}/preview", response_model=AttendanceImportPreviewResponse)
async def get_attendance_preview(
    batch_id: str,
    _: bool = Depends(require_permission("attendance.create")),
    db: AsyncSession = Depends(get_async_db),
):
    return await AttendanceImportService(db).get_preview(batch_id)


# --- Execute ----------------------------------------------------------------
@router.post(
    "/{batch_id}/execute",
    response_model=AttendanceImportProgressResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_attendance_import(
    batch_id: str,
    config: AttendanceImportConfiguration,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("attendance.create")),
    db: AsyncSession = Depends(get_async_db),
):
    """Start attendance import execution inside a database transaction."""
    service = AttendanceImportService(db)
    return await service.start_import(batch_id, config, current_user, request)


# --- Progress ---------------------------------------------------------------
@router.get("/{batch_id}/progress", response_model=AttendanceImportProgressResponse)
async def get_attendance_progress(
    batch_id: str,
    _: bool = Depends(require_permission("attendance.create")),
    db: AsyncSession = Depends(get_async_db),
):
    return await AttendanceImportService(db).get_progress(batch_id)


# --- Summary ----------------------------------------------------------------
@router.get("/{batch_id}", response_model=AttendanceImportSummaryResponse)
async def get_attendance_summary(
    batch_id: str,
    _: bool = Depends(require_permission("attendance.create")),
    db: AsyncSession = Depends(get_async_db),
):
    return await AttendanceImportService(db).get_summary(batch_id)


# --- Error Report Download --------------------------------------------------
@router.get("/{batch_id}/errors.xlsx")
async def download_attendance_error_report(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("attendance.create")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AttendanceImportService(db)
    batch = await service.repo.get_batch(batch_id)
    if not batch or not batch.detection_json:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Attendance import batch not found.")

    validation_errors = [
        ValidationErrorRow(**v)
        for v in batch.detection_json.get("validation_errors", [])
    ]
    content = exports.build_error_report(validation_errors)

    await record_audit_log(
        db, user=current_user, action=AuditAction.EXPORT.value,
        entity_type="AttendanceImportBatch", entity_id=batch_id,
        changes={"artifact": "error_report"}, request=request,
    )
    await db.commit()
    return _attachment(content, "Attendance_Import_Errors.xlsx", XLSX_MEDIA_TYPE)


# --- Summary Report Download ------------------------------------------------
@router.get("/{batch_id}/report.xlsx")
async def download_attendance_report(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("attendance.create")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AttendanceImportService(db)
    summary = await service.get_summary(batch_id)
    batch = await service.repo.get_batch(batch_id)
    detection = (batch.detection_json or {}) if batch else {}
    content = exports.build_report_workbook(
        batch, summary.records,
        detection.get("warnings", []),
        detection.get("errors", []),
    )
    await record_audit_log(
        db, user=current_user, action=AuditAction.EXPORT.value,
        entity_type="AttendanceImportBatch", entity_id=batch_id,
        changes={"artifact": "report.xlsx"}, request=request,
    )
    await db.commit()
    return _attachment(
        content,
        exports.download_filename("attendance_import_report", batch, "xlsx"),
        XLSX_MEDIA_TYPE,
    )
