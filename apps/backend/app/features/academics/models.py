import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.shared.models.base import TimestampMixin
from app.core.enums import BacklogStatus


class Mark(Base, TimestampMixin):
    __tablename__ = "marks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False, index=True)
    semester_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("semesters.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    assessment_type: Mapped[str] = mapped_column(String(50), nullable=False)  # MID_TERM_1, MID_TERM_2, INTERNAL, EXTERNAL
    marks_obtained: Mapped[float] = mapped_column(Float, nullable=False)
    max_marks: Mapped[float] = mapped_column(Float, nullable=False)
    
    recorded_by_user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    breakdown_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class SGPAHistory(Base, TimestampMixin):
    __tablename__ = "sgpa_histories"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("semesters.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    sgpa: Mapped[float] = mapped_column(Float, nullable=False)
    cgpa: Mapped[float] = mapped_column(Float, nullable=False)
    total_credits: Mapped[int] = mapped_column(Integer, nullable=False)


class Backlog(Base, TimestampMixin):
    __tablename__ = "backlogs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False, index=True)
    semester_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("semesters.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    status: Mapped[str] = mapped_column(String(30), default=BacklogStatus.ACTIVE.value, nullable=False, index=True)
    cleared_at_semester_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("semesters.id", ondelete="SET NULL"), nullable=True)
    cleared_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
