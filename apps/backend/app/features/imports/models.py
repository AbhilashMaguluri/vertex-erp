import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.shared.models.base import TimestampMixin


class ImportBatch(Base, TimestampMixin):
    """One upload of an office file, from analysis through to completion.

    The row is created the moment a file is analysed — before anything is
    written to the rest of the system — so an abandoned upload still leaves an
    honest trace of who uploaded what, and a completed one carries the full
    summary the Import History page reports against.
    """

    __tablename__ = "import_batches"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ANALYZED -> RUNNING -> COMPLETED | FAILED. A batch is never re-run once
    # COMPLETED; the administrator uploads the file again instead, which is
    # what makes duplicate-skipping the safe default.
    status: Mapped[str] = mapped_column(String(30), default="ANALYZED", nullable=False, index=True)

    imported_by_user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # What the parser understood: detected columns, expanded rows, counsellors,
    # duplicates and warnings. Re-read at execute time so the plan the
    # administrator approved on the Preview step is the plan that runs.
    detection_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # The choices made on the Configure step (department, semester, section …).
    configuration_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    summary_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Issued credentials, including the one-time temporary passwords.
    #
    # These are plaintext by necessity: an administrator has to be able to hand
    # a student their first password, and a hash cannot be read back. They are
    # only useful until first login (every account is created with
    # force_password_change=True), the download is permission-gated and
    # audit-logged, and the Completed screen offers a one-click purge which
    # clears this column. Purge after distributing the sheet.
    credentials_json: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    credentials_purged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_detected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    counsellors_detected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    students_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    counsellors_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    counsellors_reused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assignments_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    records: Mapped[List["ImportBatchRecord"]] = relationship(
        "ImportBatchRecord", back_populates="batch", cascade="all, delete-orphan"
    )
    imported_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[imported_by_user_id])


class ImportBatchRecord(Base, TimestampMixin):
    """The outcome of one student or one counsellor within a batch.

    Written for every entity the import touched, whichever way it went, so the
    downloadable report can account for the difference between the roll numbers
    on the sheet and the accounts that now exist.
    """

    __tablename__ = "import_batch_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # STUDENT | COUNSELLOR
    record_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # Roll number for a student, the name as written on the sheet for a counsellor.
    identifier: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # CREATED | REUSED | SKIPPED | FAILED
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    batch: Mapped[ImportBatch] = relationship("ImportBatch", back_populates="records")
