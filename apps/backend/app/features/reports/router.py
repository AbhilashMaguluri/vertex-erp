import os
from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.permissions import require_permission
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.reports.schemas import ReportGenerateRequest, ReportRecordResponse
from app.features.reports.service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports Management"])

_MEDIA_TYPES = {
    "PDF": "application/pdf",
    "EXCEL": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "CSV": "text/csv",
}


@router.post("/generate", response_model=ReportRecordResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    data: ReportGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("report.generate")),
    db: AsyncSession = Depends(get_async_db),
):
    service = ReportService(db)
    return await service.generate_report(data, str(current_user.id))


@router.get("/history", response_model=List[ReportRecordResponse])
async def list_report_history(
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("report.download")),
    db: AsyncSession = Depends(get_async_db),
):
    service = ReportService(db)
    return await service.list_reports(str(current_user.id))


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("report.download")),
    db: AsyncSession = Depends(get_async_db),
):
    service = ReportService(db)
    record = await service.get_report_for_download(report_id, str(current_user.id))
    if record.file_path.startswith("http://") or record.file_path.startswith("https://"):
        return RedirectResponse(url=record.file_path, status_code=302)
    filename = os.path.basename(record.file_path)
    media_type = _MEDIA_TYPES.get(record.file_format, "application/octet-stream")
    return FileResponse(record.file_path, media_type=media_type, filename=filename)
