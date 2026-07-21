from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.audit.models import AuditLog, SystemSetting


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(self, log_entry: AuditLog) -> AuditLog:
        self.db.add(log_entry)
        await self.db.flush()
        return log_entry

    async def list_audit_logs(
        self,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        user_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[AuditLog], int]:
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))

        if action:
            query = query.where(AuditLog.action == action.upper())
            count_query = count_query.where(AuditLog.action == action.upper())

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
            count_query = count_query.where(AuditLog.entity_type == entity_type)

        if user_id:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)

        query = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * per_page).limit(per_page)

        logs_res = await self.db.execute(query)
        count_res = await self.db.execute(count_query)

        return list(logs_res.scalars().all()), count_res.scalar_one()

    # Settings
    async def get_settings_by_section(self, section: str) -> List[SystemSetting]:
        query = select(SystemSetting).where(SystemSetting.section == section)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def upsert_setting(self, setting: SystemSetting) -> SystemSetting:
        query = select(SystemSetting).where(SystemSetting.key == setting.key)
        res = await self.db.execute(query)
        existing = res.scalar_one_or_none()
        if existing:
            existing.value_json = setting.value_json
            existing.updated_by = setting.updated_by
            return existing
        else:
            self.db.add(setting)
            return setting
