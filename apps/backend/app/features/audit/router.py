from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.permissions import require_permission
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.audit.schemas import (
    AuditLogResponse,
    SystemSettingResponse,
    SystemSettingUpdateRequest,
)
from app.features.audit.service import AuditService

router = APIRouter(tags=["Audit Logs & Settings"])


@router.get("/admin/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _: bool = Depends(require_permission("audit.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuditService(db)
    logs, _ = await service.list_audit_logs(action, entity_type, user_id, page, per_page)
    return logs


@router.get("/settings/{section}", response_model=List[SystemSettingResponse])
async def get_settings_section(
    section: str,
    _: bool = Depends(require_permission("settings.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuditService(db)
    return await service.get_settings_section(section)


@router.put("/settings/{section}/{key}", response_model=SystemSettingResponse)
async def update_setting(
    section: str,
    key: str,
    data: SystemSettingUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("settings.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuditService(db)
    return await service.update_setting_key(section, key, data.value, str(current_user.id))
