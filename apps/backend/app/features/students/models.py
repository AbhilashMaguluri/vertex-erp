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
    
    status: Mapped[str] = mapped_column(String(30), default=StudentStatus.ACTIVE.value, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(30), default=RiskLevel.NONE.value, nullable=False)

    department_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    current_semester_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("semesters.id", ondelete="SET NULL"), nullable=True)

    # Parent / Guardian Info
    father_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    father_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    father_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mother_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mother_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mother_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    guardian_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    guardian_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    guardian_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    guardian_relation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    enrollments: Mapped[List["StudentEnrollment"]] = relationship("StudentEnrollment", back_populates="student", cascade="all, delete-orphan")
    counsellor_assignments: Mapped[List["CounsellorAssignment"]] = relationship("CounsellorAssignment", back_populates="student", cascade="all, delete-orphan")


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
