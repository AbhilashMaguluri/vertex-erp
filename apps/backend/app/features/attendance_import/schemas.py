"""Pydantic schemas for the Enterprise Attendance Import feature."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Raw parsed row
# --------------------------------------------------------------------------

class ParsedAttendanceRow(BaseModel):
    """One row from the uploaded Excel before normalization."""

    row_number: int
    student_roll: str
    raw_status: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


# --------------------------------------------------------------------------
# Normalized entry
# --------------------------------------------------------------------------

class NormalizedAttendanceEntry(BaseModel):
    """One attendance entry after status normalization."""

    roll_number: str
    source_row: int
    normalized_status: str  # PRESENT | ABSENT | ON_DUTY | MEDICAL_LEAVE


# --------------------------------------------------------------------------
# Resolved entry
# --------------------------------------------------------------------------

class ResolvedAttendanceEntry(BaseModel):
    """Entry resolved against student database and existing attendance."""

    roll_number: str
    source_row: int
    normalized_status: str
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    student_found: bool = False
    section_matched: bool = True
    existing_attendance_id: Optional[str] = None
    existing_status: Optional[str] = None
    resolution_status: str  # NEW | EXISTING | MISSING_STUDENT
    proposed_action: str  # CREATE | UPDATE | SKIP | CANNOT_IMPORT
    error: Optional[str] = None


# --------------------------------------------------------------------------
# Preview Data Structures
# --------------------------------------------------------------------------

class PreviewSummary(BaseModel):
    """Top-level metrics for preview and confirmation modal."""

    attendance_date: date
    mode: str  # TODAY | PAST
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    total_students_in_file: int = 0
    existing_students_found: int = 0
    missing_students: int = 0
    new_attendance_records: int = 0
    attendance_updates: int = 0
    skipped_records: int = 0
    warnings: int = 0
    errors: int = 0


class StudentAttendancePreviewRow(BaseModel):
    """One row of the detailed preview table."""

    roll_number: str
    student_name: Optional[str] = None
    status: str  # Present | Absent | On Duty | Medical Leave
    student_found: str  # Yes | No
    existing_attendance: str  # Yes (Status) | No
    action: str  # Create | Update | Skip | Cannot Import
    error: Optional[str] = None


class PreviewTables(BaseModel):
    """Detail tables for preview display."""

    records: List[StudentAttendancePreviewRow] = Field(default_factory=list)


class ValidationErrorRow(BaseModel):
    """Row error entry for downloadable error report."""

    row: int
    roll_number: str
    error: str
    suggested_fix: str


# --------------------------------------------------------------------------
# Configuration & API DTOs
# --------------------------------------------------------------------------

class AttendanceImportConfiguration(BaseModel):
    """Configuration submitted when executing the import."""

    mode: str = Field("TODAY", description="TODAY or PAST")
    attendance_date: date
    subject_id: str = Field(..., description="Subject UUID for attendance records")
    department_id: Optional[str] = None
    section_id: Optional[str] = None
    allow_overwrite: bool = Field(True, description="Whether to update existing attendance records")


class AttendanceImportPreviewResponse(BaseModel):
    """Response returned after file analysis."""

    batch_id: str
    file_name: str
    status: str
    summary: PreviewSummary
    tables: PreviewTables
    validation_errors: List[ValidationErrorRow] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    parsed_row_count: int = 0


class AttendanceImportProgressResponse(BaseModel):
    """Progress response during import execution."""

    batch_id: str
    status: str
    phase: str
    phase_label: str
    percent: int
    processed: int
    total: int
    message: Optional[str] = None
    error: Optional[str] = None


class AttendanceImportResultRecord(BaseModel):
    """Record outcome for audit log and completion summary."""

    record_type: str = "ATTENDANCE"
    identifier: str
    display_name: Optional[str] = None
    status: str  # CREATED | UPDATED | SKIPPED | FAILED
    message: Optional[str] = None
    source_row_number: Optional[int] = None

    class Config:
        from_attributes = True


class AttendanceImportSummaryResponse(BaseModel):
    """Post-import summary response."""

    batch_id: str
    file_name: str
    status: str
    mode: str
    attendance_date: date
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    imported_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    total_rows: int = 0
    students_detected: int = 0
    students_found: int = 0
    missing_students: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    failed_records: int = 0
    warning_count: int = 0
    error_message: Optional[str] = None

    records: List[AttendanceImportResultRecord] = Field(default_factory=list)


class AttendanceImportHistoryItem(BaseModel):
    """Item in history list."""

    batch_id: str
    file_name: str
    mode: str
    attendance_date: date
    subject_name: Optional[str] = None
    status: str
    imported_by: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    records_created: int = 0
    records_updated: int = 0
    failed_records: int = 0


class AttendanceImportHistoryResponse(BaseModel):
    """History list with aggregated statistics."""

    items: List[AttendanceImportHistoryItem]
    total_imports: int = 0
    completed_imports: int = 0
    total_records_created: int = 0
    total_records_updated: int = 0
    success_rate: float = 0.0
    last_import_at: Optional[datetime] = None
