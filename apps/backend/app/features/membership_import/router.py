"""FastAPI router for the Membership Import feature.

Thin layer — all business logic lives in the service.
"""
from typing import List

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit_log
from app.core.enums import AuditAction
from app.core.permissions import require_permission
from app.database import get_async_db
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.membership_import import exports
from app.features.membership_import.schemas import (
    GeneratedStudentCredential,
    MembershipImportConfiguration,
    MembershipImportHistoryResponse,
    MembershipImportPreviewResponse,
    MembershipImportProgressResponse,
    MembershipImportSummaryResponse,
    ValidationErrorRow,
)
from app.features.membership_import.service import MembershipImportService

router = APIRouter(prefix="/admin/membership-imports", tags=["Membership Import"])

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _attachment(content: bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- History & Template (before parameterised routes) ----------------------
@router.get("", response_model=MembershipImportHistoryResponse)
async def list_membership_import_history(
    limit: int = Query(20, ge=1, le=100),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Recent membership imports and summary statistics."""
    return await MembershipImportService(db).get_history(limit)


@router.get("/sample-template.xlsx")
async def download_membership_sample_template(
    _: bool = Depends(require_permission("user.manage")),
):
    """Download the three-column sample template."""
    return _attachment(
        exports.build_sample_template(),
        "Membership_Import_Template.xlsx",
        XLSX_MEDIA_TYPE,
    )


# --- Upload & Analyze ------------------------------------------------------
@router.post("/analyze", response_model=MembershipImportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def analyze_membership_file(
    request: Request,
    file: UploadFile = File(..., description="Three-column Excel file"),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Upload and analyze a membership import file.  Returns a full preview
    without writing anything to the system."""
    service = MembershipImportService(db)
    content = await file.read()
    return await service.analyze(
        file.filename or "upload.xlsx", content, current_user, request,
    )


# --- Preview ----------------------------------------------------------------
@router.get("/{batch_id}/preview", response_model=MembershipImportPreviewResponse)
async def get_membership_preview(
    batch_id: str,
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    return await MembershipImportService(db).get_preview(batch_id)


# --- Execute ----------------------------------------------------------------
@router.post(
    "/{batch_id}/execute",
    response_model=MembershipImportProgressResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_membership_import(
    batch_id: str,
    config: MembershipImportConfiguration,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Start the membership import.  Returns immediately; poll /progress."""
    service = MembershipImportService(db)
    return await service.start_import(batch_id, config, current_user, request)


# --- Progress ---------------------------------------------------------------
@router.get("/{batch_id}/progress", response_model=MembershipImportProgressResponse)
async def get_membership_progress(
    batch_id: str,
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    return await MembershipImportService(db).get_progress(batch_id)


# --- Summary ----------------------------------------------------------------
@router.get("/{batch_id}", response_model=MembershipImportSummaryResponse)
async def get_membership_summary(
    batch_id: str,
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    return await MembershipImportService(db).get_summary(batch_id)


# --- Credentials ------------------------------------------------------------
@router.get("/{batch_id}/credentials", response_model=List[GeneratedStudentCredential])
async def list_membership_credentials(
    batch_id: str,
    limit: int = Query(50, ge=1, le=500),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    _batch, credentials = await MembershipImportService(db).get_credentials(batch_id)
    return credentials[:limit]


@router.get("/{batch_id}/credentials.xlsx")
async def download_membership_credentials(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = MembershipImportService(db)
    batch, credentials = await service.get_credentials(batch_id)
    content = exports.build_credentials_workbook(batch, credentials)
    await record_audit_log(
        db, user=current_user, action=AuditAction.EXPORT.value,
        entity_type="MembershipImportBatch", entity_id=batch_id,
        changes={"artifact": "credentials", "records": len(credentials)},
        request=request,
    )
    await db.commit()
    return _attachment(
        content,
        exports.download_filename("membership_credentials", batch, "xlsx"),
        XLSX_MEDIA_TYPE,
    )


@router.delete("/{batch_id}/credentials", status_code=status.HTTP_204_NO_CONTENT)
async def purge_membership_credentials(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    await MembershipImportService(db).purge_credentials(batch_id, current_user, request)


# --- Error Report -----------------------------------------------------------
@router.get("/{batch_id}/errors.xlsx")
async def download_error_report(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Download validation errors as Import_Errors.xlsx."""
    service = MembershipImportService(db)
    batch = await service.repo.get_batch(batch_id)
    if not batch or not batch.detection_json:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Import not found.")

    validation_errors = [
        ValidationErrorRow(**v)
        for v in batch.detection_json.get("validation_errors", [])
    ]
    content = exports.build_error_report(validation_errors)

    await record_audit_log(
        db, user=current_user, action=AuditAction.EXPORT.value,
        entity_type="MembershipImportBatch", entity_id=batch_id,
        changes={"artifact": "error_report"}, request=request,
    )
    await db.commit()
    return _attachment(content, "Import_Errors.xlsx", XLSX_MEDIA_TYPE)


# --- Import Report ----------------------------------------------------------
@router.get("/{batch_id}/report.xlsx")
async def download_membership_report(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = MembershipImportService(db)
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
        entity_type="MembershipImportBatch", entity_id=batch_id,
        changes={"artifact": "report.xlsx"}, request=request,
    )
    await db.commit()
    return _attachment(
        content,
        exports.download_filename("membership_import_report", batch, "xlsx"),
        XLSX_MEDIA_TYPE,
    )
