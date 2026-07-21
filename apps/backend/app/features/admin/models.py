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
    name: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. CSE-A
    batch_year: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g. 2024

    department: Mapped[Department] = relationship("Department", back_populates="sections")


class AcademicYear(Base, AuditMixin):
    __tablename__ = "academic_years"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g. 2026-2027
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    semesters: Mapped[List["Semester"]] = relationship("Semester", back_populates="academic_year", cascade="all, delete-orphan")


class Semester(Base, AuditMixin):
    __tablename__ = "semesters"

    academic_year_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)  # Semester 1 to 8
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. Fall 2026 / Semester 5
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    academic_year: Mapped[AcademicYear] = relationship("AcademicYear", back_populates="semesters")


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
