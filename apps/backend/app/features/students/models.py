import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.shared.models.base import AuditMixin, TimestampMixin
from app.core.enums import StudentStatus, RiskLevel


class Student(Base, AuditMixin):
    __tablename__ = "students"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    roll_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    registration_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    batch_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # MALE / FEMALE / OTHER. Nullable: existing rows predate the column and
    # the value is student-maintained, so it is legitimately unknown until
    # they fill in their personal information.
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    status: Mapped[str] = mapped_column(String(30), default=StudentStatus.ACTIVE.value, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(30), default=RiskLevel.NONE.value, nullable=False)

    department_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    current_semester_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("semesters.id", ondelete="SET NULL"), nullable=True)

    # Family, contact and address details are NOT here — they are
    # student-maintained and live on student_profiles (see profile_models.py).
    # Keeping them off this table is what makes "a student may not write
    # anything on `students`" a structural rule rather than a per-endpoint
    # convention. The two exceptions above (gender, photo_url) stay because
    # institution-wide rosters and dashboards aggregate them.

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    enrollments: Mapped[List["StudentEnrollment"]] = relationship("StudentEnrollment", back_populates="student", cascade="all, delete-orphan")
    counsellor_assignments: Mapped[List["CounsellorAssignment"]] = relationship("CounsellorAssignment", back_populates="student", cascade="all, delete-orphan")
    profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile", uselist=False, cascade="all, delete-orphan"
    )


class StudentEnrollment(Base, TimestampMixin):
    __tablename__ = "student_enrollments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="RESTRICT"), nullable=False, index=True)
    semester_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("semesters.id", ondelete="RESTRICT"), nullable=False, index=True)

    student: Mapped[Student] = relationship("Student", back_populates="enrollments")


class CounsellorAssignment(Base, TimestampMixin):
    __tablename__ = "counsellor_assignments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    counsellor_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("semesters.id", ondelete="RESTRICT"), nullable=False, index=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped[Student] = relationship("Student", back_populates="counsellor_assignments")
    counsellor: Mapped["User"] = relationship("User", foreign_keys=[counsellor_id])


class AcademicCorrectionRequest(Base, TimestampMixin):
    __tablename__ = "academic_correction_requests"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    counsellor_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    section_name: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    current_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    proposed_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    document_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("student_documents.id", ondelete="SET NULL"), nullable=True)

    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED", nullable=False, index=True)
    counsellor_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped[Student] = relationship("Student", foreign_keys=[student_id])
    counsellor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[counsellor_id])
    document: Mapped[Optional["StudentDocument"]] = relationship("StudentDocument", foreign_keys=[document_id])
    logs: Mapped[List["AcademicCorrectionLog"]] = relationship("AcademicCorrectionLog", back_populates="request", cascade="all, delete-orphan", order_by="AcademicCorrectionLog.created_at.asc()")


class AcademicCorrectionLog(Base):
    __tablename__ = "academic_correction_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_correction_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    from_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("student_documents.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    request: Mapped[AcademicCorrectionRequest] = relationship("AcademicCorrectionRequest", back_populates="logs")
    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])
    document: Mapped[Optional["StudentDocument"]] = relationship("StudentDocument", foreign_keys=[document_id])

