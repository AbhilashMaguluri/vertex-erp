"""Database models for the Attendance Import feature."""
import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.shared.models.base import TimestampMixin


class AttendanceImportBatch(Base, TimestampMixin):
    """One upload batch of attendance records."""

    __tablename__ = "attendance_import_batches"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # TODAY | PAST
    mode: Mapped[str] = mapped_column(String(20), default="TODAY", nullable=False)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    subject_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    department_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id", ondelete="SET NULL"), nullable=True
    )

    # ANALYZED | RUNNING | COMPLETED | FAILED
    status: Mapped[str] = mapped_column(String(30), default="ANALYZED", nullable=False, index=True)

    imported_by_user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    detection_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    configuration_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    summary_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Counters
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_detected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_students: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    records: Mapped[List["AttendanceImportRecord"]] = relationship(
        "AttendanceImportRecord", back_populates="batch", cascade="all, delete-orphan"
    )
    imported_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[imported_by_user_id])
    subject: Mapped[Optional["Subject"]] = relationship("Subject", foreign_keys=[subject_id])


class AttendanceImportRecord(Base, TimestampMixin):
    """One record outcome within an attendance import batch."""

    __tablename__ = "attendance_import_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance_import_batches.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    record_type: Mapped[str] = mapped_column(String(20), default="ATTENDANCE", nullable=False)
    identifier: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # CREATED | UPDATED | SKIPPED | FAILED
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    student_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="SET NULL"), nullable=True
    )
    attendance_record_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance_records.id", ondelete="SET NULL"), nullable=True
    )

    batch: Mapped[AttendanceImportBatch] = relationship("AttendanceImportBatch", back_populates="records")
