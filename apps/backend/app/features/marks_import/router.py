"""FastAPI router for Enterprise Marks Import & Assessment Management."""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit_log
from app.core.enums import AuditAction
from app.core.permissions import require_permission
from app.database import get_async_db
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.marks_import import exports
from app.features.marks_import.excel_generator import build_dynamic_marks_template
from app.features.marks_import.schemas import (
    AssessmentTemplateCreate,
    AssessmentTemplateResponse,
    AssessmentTemplateUpdate,
    MarksImportConfiguration,
    MarksImportHistoryResponse,
    MarksImportPreviewResponse,
    MarksImportProgressResponse,
    MarksImportSummaryResponse,
    ValidationErrorRow,
)
from app.features.marks_import.service import MarksImportService
from app.features.marks_import.template_service import AssessmentTemplateService

router = APIRouter(prefix="/admin", tags=["Marks Import & Assessment Management"])

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _attachment(content: bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --------------------------------------------------------------------------
# Assessment Template Endpoints
# --------------------------------------------------------------------------

@router.get("/assessment-templates", response_model=List[AssessmentTemplateResponse])
async def list_assessment_templates(
    subject_id: Optional[str] = Query(None),
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    """List available assessment templates."""
    return await AssessmentTemplateService(db).list_templates(subject_id)


@router.post("/assessment-templates", response_model=AssessmentTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment_template(
    data: AssessmentTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new configurable assessment structure."""
    return await AssessmentTemplateService(db).create_template(data)


@router.put("/assessment-templates/{template_id}", response_model=AssessmentTemplateResponse)
async def update_assessment_template(
    template_id: str,
    data: AssessmentTemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Update an existing assessment structure."""
    return await AssessmentTemplateService(db).update_template(template_id, data)


# --------------------------------------------------------------------------
# Dynamic Template Download
# --------------------------------------------------------------------------

@router.get("/marks-imports/sample-template.xlsx")
async def download_dynamic_marks_template(
    assessment_code: str = Query("MID_WRITTEN"),
    subject_id: Optional[str] = Query(None),
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    """Download custom Excel template generated for the active AssessmentTemplate."""
    tmpl_service = AssessmentTemplateService(db)
    template = await tmpl_service.get_template_for_subject(subject_id, assessment_code)
    content = build_dynamic_marks_template(template)
    filename = f"Marks_Template_{template.assessment_code}.xlsx"
    return _attachment(content, filename, XLSX_MEDIA_TYPE)


# --------------------------------------------------------------------------
# Marks Import Endpoints
# --------------------------------------------------------------------------

@router.get("/marks-imports", response_model=MarksImportHistoryResponse)
async def list_marks_import_history(
    limit: int = Query(20, ge=1, le=100),
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    return await MarksImportService(db).get_history(limit)


@router.post("/marks-imports/analyze", response_model=MarksImportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def analyze_marks_file(
    request: Request,
    file: UploadFile = File(..., description="Excel or CSV marks file"),
    semester_id: str = Form(...),
    subject_id: str = Form(...),
    assessment_code: str = Form("MID_WRITTEN"),
    academic_year_id: Optional[str] = Form(None),
    department_id: Optional[str] = Form(None),
    section_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    """Upload and analyze a marks spreadsheet against assessment structure."""
    service = MarksImportService(db)
    content = await file.read()
    return await service.analyze(
        file.filename or "marks_upload.xlsx",
        content,
        academic_year_id,
        semester_id,
        department_id,
        section_id,
        subject_id,
        assessment_code,
        current_user,
        request,
    )


@router.get("/marks-imports/{batch_id}/preview", response_model=MarksImportPreviewResponse)
async def get_marks_preview(
    batch_id: str,
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    return await MarksImportService(db).get_preview(batch_id)


@router.post(
    "/marks-imports/{batch_id}/execute",
    response_model=MarksImportProgressResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_marks_import(
    batch_id: str,
    config: MarksImportConfiguration,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    """Execute marks import within a database transaction."""
    service = MarksImportService(db)
    return await service.start_import(batch_id, config, current_user, request)


@router.get("/marks-imports/{batch_id}/progress", response_model=MarksImportProgressResponse)
async def get_marks_progress(
    batch_id: str,
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    return await MarksImportService(db).get_progress(batch_id)


@router.get("/marks-imports/{batch_id}", response_model=MarksImportSummaryResponse)
async def get_marks_summary(
    batch_id: str,
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    return await MarksImportService(db).get_summary(batch_id)


@router.get("/marks-imports/{batch_id}/errors.xlsx")
async def download_marks_error_report(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    service = MarksImportService(db)
    batch = await service.repo.get_batch(batch_id)
    if not batch or not batch.detection_json:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Marks import batch not found.")

    validation_errors = [
        ValidationErrorRow(**v)
        for v in batch.detection_json.get("validation_errors", [])
    ]
    content = exports.build_error_report(validation_errors)

    await record_audit_log(
        db, user=current_user, action=AuditAction.EXPORT.value,
        entity_type="MarksImportBatch", entity_id=batch_id,
        changes={"artifact": "error_report"}, request=request,
    )
    await db.commit()
    return _attachment(content, "Marks_Import_Errors.xlsx", XLSX_MEDIA_TYPE)


@router.get("/marks-imports/{batch_id}/report.xlsx")
async def download_marks_report(
    batch_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    service = MarksImportService(db)
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
        entity_type="MarksImportBatch", entity_id=batch_id,
        changes={"artifact": "report.xlsx"}, request=request,
    )
    await db.commit()
    return _attachment(
        content,
        exports.download_filename("marks_import_report", batch, "xlsx"),
        XLSX_MEDIA_TYPE,
    )
