from typing import List

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit_log
from app.core.enums import AuditAction
from app.core.permissions import require_permission
from app.database import get_async_db
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.imports import exports
from app.features.imports.schemas import (
    GeneratedCredential,
    ImportConfiguration,
    ImportHistoryResponse,
    ImportPreviewResponse,
    ImportProgressResponse,
    ImportSummaryResponse,
)
from app.features.imports.service import ImportService

router = APIRouter(prefix="/admin/imports", tags=["Office Import"])

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _attachment(content: bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# Literal paths are declared before "/{batch_id}" — FastAPI resolves routes in
# declaration order, so a parameterised single-segment route registered first
# would swallow "/sample-template.xlsx" as an import id.
@router.get("", response_model=ImportHistoryResponse)
async def list_import_history(
    limit: int = Query(20, ge=1, le=100),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Recent imports plus the success-rate rollups on the dashboard."""
    return await ImportService(db).get_history(limit)


@router.get("/sample-template.xlsx")
async def download_sample_template(
    _: bool = Depends(require_permission("user.manage")),
):
    """The sample office template — the format the office already uses."""
    return _attachment(exports.build_sample_template(), "SCMS_Office_Import_Template.xlsx", XLSX_MEDIA_TYPE)


# --- Step 1 & 2 — upload, analyse, preview --------------------------------
@router.post("/analyze", response_model=ImportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def analyze_office_file(
    request: Request,
    file: UploadFile = File(..., description="The office Excel/CSV file, uploaded as received"),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Read an office file and report what would be created. Writes nothing
    outside the import's own audit trail."""
    service = ImportService(db)
    content = await file.read()
    return await service.analyze(file.filename or "upload.xlsx", content, current_user, request)


@router.get("/{batch_id}/preview", response_model=ImportPreviewResponse)
async def get_import_preview(
    batch_id: str,
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    return await ImportService(db).get_preview(batch_id)


# --- Steps 3 & 4 — configure and run --------------------------------------
@router.post("/{batch_id}/execute", response_model=ImportProgressResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_import(
    batch_id: str,
    config: ImportConfiguration,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Start the import. Returns immediately; poll `/progress` for the bar."""
    service = ImportService(db)
    return await service.start_import(batch_id, config, current_user, request)


@router.get("/{batch_id}/progress", response_model=ImportProgressResponse)
async def get_import_progress(
    batch_id: str,
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    return await ImportService(db).get_progress(batch_id)


# --- Step 5 — results ------------------------------------------------------
@router.get("/{batch_id}", response_model=ImportSummaryResponse)
async def get_import_summary(
    batch_id: str,
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    return await ImportService(db).get_summary(batch_id)


@router.get("/{batch_id}/credentials", response_model=List[GeneratedCredential])
async def list_generated_credentials(
    batch_id: str,
    limit: int = Query(50, ge=1, le=500),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Preview of the issued logins, for the Completed screen."""
    _batch, credentials = await ImportService(db).get_credentials(batch_id)
    return credentials[:limit]


@router.get("/{batch_id}/credentials.xlsx")
async def download_generated_credentials(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Download the credentials workbook. Every download is audit-logged —
    this file contains one-time passwords in plaintext."""
    service = ImportService(db)
    batch, credentials = await service.get_credentials(batch_id)
    content = exports.build_credentials_workbook(batch, credentials)
    await record_audit_log(
        db, user=current_user, action=AuditAction.EXPORT.value,
        entity_type="ImportBatch", entity_id=batch_id,
        changes={"artifact": "credentials", "records": len(credentials)}, request=request,
    )
    await db.commit()
    return _attachment(content, exports.download_filename("scms_credentials", batch, "xlsx"), XLSX_MEDIA_TYPE)


@router.delete("/{batch_id}/credentials", status_code=status.HTTP_204_NO_CONTENT)
async def purge_generated_credentials(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Clear the stored temporary passwords once the sheet has been handed out."""
    await ImportService(db).purge_credentials(batch_id, current_user, request)


@router.get("/{batch_id}/report.xlsx")
async def download_import_report_excel(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = ImportService(db)
    batch, records, warnings, errors = await _report_inputs(service, batch_id)
    content = exports.build_report_workbook(batch, records, warnings, errors)
    await record_audit_log(
        db, user=current_user, action=AuditAction.EXPORT.value,
        entity_type="ImportBatch", entity_id=batch_id,
        changes={"artifact": "report.xlsx"}, request=request,
    )
    await db.commit()
    return _attachment(content, exports.download_filename("scms_import_report", batch, "xlsx"), XLSX_MEDIA_TYPE)


@router.get("/{batch_id}/report.pdf")
async def download_import_report_pdf(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = ImportService(db)
    batch, records, warnings, errors = await _report_inputs(service, batch_id)
    content = exports.build_report_pdf(batch, records, warnings, errors)
    await record_audit_log(
        db, user=current_user, action=AuditAction.EXPORT.value,
        entity_type="ImportBatch", entity_id=batch_id,
        changes={"artifact": "report.pdf"}, request=request,
    )
    await db.commit()
    return _attachment(content, exports.download_filename("scms_import_report", batch, "pdf"), "application/pdf")


async def _report_inputs(service: ImportService, batch_id: str):
    summary = await service.get_summary(batch_id)
    batch = await service.repo.get_batch(batch_id)
    detection = (batch.detection_json or {}) if batch else {}
    return batch, summary.records, detection.get("warnings", []), detection.get("errors", [])


