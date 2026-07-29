import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.shared.models.base import AuditMixin


class Department(Base, AuditMixin):
    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hod_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    sections: Mapped[List["Section"]] = relationship("Section", back_populates="department", cascade="all, delete-orphan")
    subjects: Mapped[List["Subject"]] = relationship("Subject", back_populates="department", cascade="all, delete-orphan")


class Section(Base, AuditMixin):
    __tablename__ = "sections"

    department_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. A
    # Study year within the department's 4-year program (1st..4th) — the
    # level the Academic Configuration hierarchy groups sections under.
    # Nullable so pre-existing rows created before this column don't need a
    # backfill; new sections always set it (see SectionCreate).
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    batch_year: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g. 2024 — admission/intake batch

    department: Mapped[Department] = relationship("Department", back_populates="sections")


class AcademicYear(Base, AuditMixin):
    __tablename__ = "academic_years"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g. 2026-2027
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Semester(Base, AuditMixin):
    """A fixed, institution-wide catalog of program semesters (1-1 .. 4-2).

    Not scoped to a particular AcademicYear — the same 8 rows are seeded once
    (see app/scripts/seed.py) and reused every year, so there is no
    create/update API for this entity.
    """

    __tablename__ = "semesters"

    academic_year_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True, index=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # 1 to 8
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. 1-1, 4-2
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Subject(Base, AuditMixin):
    __tablename__ = "subjects"

    department_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)  # e.g. CS501
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    max_mid_marks: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_internal_marks: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    max_external_marks: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    department: Mapped[Department] = relationship("Department", back_populates="subjects")


class SubjectFaculty(Base):
    __tablename__ = "subject_faculty"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
