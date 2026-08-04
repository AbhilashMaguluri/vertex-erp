"""Database models for the Membership Import feature.

Tracks batches and individual records, separate from the existing Office
Import tables so the two import domains don't conflate.
"""
import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.shared.models.base import TimestampMixin


class MembershipImportBatch(Base, TimestampMixin):
    """One upload of a membership import file, from analysis through completion."""

    __tablename__ = "membership_import_batches"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ANALYZED -> RUNNING -> COMPLETED | FAILED
    status: Mapped[str] = mapped_column(String(30), default="ANALYZED", nullable=False, index=True)

    imported_by_user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # JSON snapshots of the analysis and configuration
    detection_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    configuration_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    summary_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Issued credentials (temporary passwords for newly created students)
    credentials_json: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    credentials_purged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Counters
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_detected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_reused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    counselors_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    counselors_missing: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    memberships_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    memberships_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    memberships_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    records: Mapped[List["MembershipImportRecord"]] = relationship(
        "MembershipImportRecord", back_populates="batch", cascade="all, delete-orphan"
    )
    imported_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[imported_by_user_id])


class MembershipImportRecord(Base, TimestampMixin):
    """One record outcome within a membership import batch."""

    __tablename__ = "membership_import_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("membership_import_batches.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # STUDENT | COUNSELOR | MEMBERSHIP
    record_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    identifier: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # CREATED | REUSED | SKIPPED | FAILED | UPDATED
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    batch: Mapped[MembershipImportBatch] = relationship("MembershipImportBatch", back_populates="records")
