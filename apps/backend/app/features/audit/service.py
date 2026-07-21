from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.audit.models import AuditLog, SystemSetting
from app.features.audit.repository import AuditRepository
from app.features.audit.schemas import AuditLogResponse, SystemSettingResponse


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuditRepository(db)

    async def list_audit_logs(
        self,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        user_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[AuditLogResponse], int]:
        logs, total = await self.repo.list_audit_logs(action, entity_type, user_id, page, per_page)
        return [AuditLogResponse.model_validate(l) for l in logs], total

    async def get_settings_section(self, section: str) -> List[SystemSettingResponse]:
        settings = await self.repo.get_settings_by_section(section)
        return [
            SystemSettingResponse(
                section=s.section,
                key=s.key,
                value=s.value_json,
                updated_at=s.updated_at,
            )
            for s in settings
        ]

    async def update_setting_key(self, section: str, key: str, value: dict, user_id: str) -> SystemSettingResponse:
        setting = SystemSetting(
            section=section,
            key=key,
            value_json=value,
            updated_by=user_id,
        )
        saved = await self.repo.upsert_setting(setting)
        await self.db.commit()
        return SystemSettingResponse(
            section=saved.section,
            key=saved.key,
            value=saved.value_json,
            updated_at=saved.updated_at,
        )
