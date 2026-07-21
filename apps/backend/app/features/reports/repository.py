from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.reports.models import ReportRecord


class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_report_record(self, report: ReportRecord) -> ReportRecord:
        self.db.add(report)
        await self.db.flush()
        return report

    async def list_user_reports(self, user_id: str) -> List[ReportRecord]:
        query = (
            select(ReportRecord)
            .where(ReportRecord.generated_by_user_id == user_id)
            .order_by(ReportRecord.created_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())
