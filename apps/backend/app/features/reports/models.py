import uuid
from typing import Any, Dict, Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.shared.models.base import TimestampMixin


class ReportRecord(Base, TimestampMixin):
    __tablename__ = "report_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # STUDENT, SEMESTER, DEPARTMENT, COUNSELLOR, ATTENDANCE, PERFORMANCE, BACKLOG
    generated_by_user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), default="PDF", nullable=False)  # PDF, EXCEL, CSV
    scope_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
