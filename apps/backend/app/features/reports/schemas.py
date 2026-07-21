from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    report_type: str = Field(..., description="STUDENT, SEMESTER, DEPARTMENT, COUNSELLOR, ATTENDANCE, PERFORMANCE, BACKLOG")
    file_format: str = Field("PDF", description="PDF, EXCEL, CSV")
    scope_metadata: Optional[Dict[str, Any]] = None


class ReportRecordResponse(BaseModel):
    id: str
    report_type: str
    generated_by_user_id: str
    file_path: str
    file_format: str
    created_at: datetime

    class Config:
        from_attributes = True
