"""Pydantic schemas for the Membership Import feature.

Every DTO used by the router, services, and preview builder is defined
here.  Nothing leaks implementation details.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Parsed row — what the Excel parser produces
# --------------------------------------------------------------------------

class ParsedMembershipRow(BaseModel):
    """One row from the uploaded Excel, before expansion."""

    row_number: int
    start_roll: str
    end_roll: str
    counselor_email: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


# --------------------------------------------------------------------------
# Expanded student entry
# --------------------------------------------------------------------------

class ExpandedStudentEntry(BaseModel):
    """One student produced after range expansion."""

    roll_number: str
    source_row: int
    counselor_email: str
    student_email: Optional[str] = None
    student_user_id: Optional[str] = None
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    student_status: str = "MISSING"  # EXISTING | MISSING
    student_action: str = "CREATE_ACCOUNT"  # REUSE | CREATE_ACCOUNT


# --------------------------------------------------------------------------
# Counselor resolution
# --------------------------------------------------------------------------

class CounselorEntry(BaseModel):
    """Resolved counselor status."""

    email: str
    user_id: Optional[str] = None
    display_name: Optional[str] = None
    status: str = "MISSING"  # FOUND | MISSING
    action: str = "CANNOT_IMPORT"  # REUSE | CANNOT_IMPORT
    student_count: int = 0
    source_rows: List[int] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Membership resolution
# --------------------------------------------------------------------------

class MembershipEntry(BaseModel):
    """One student-counselor membership after all lookups."""

    roll_number: str
    student_email: Optional[str] = None
    student_name: Optional[str] = None
    student_user_id: Optional[str] = None
    student_id: Optional[str] = None
    student_status: str  # EXISTING | MISSING
    student_action: str  # REUSE | CREATE_ACCOUNT
    counselor_email: str
    counselor_user_id: Optional[str] = None
    counselor_name: Optional[str] = None
    counselor_status: str  # FOUND | MISSING
    membership_status: str  # NEW | EXISTING | SKIP
    membership_action: str  # CREATE | UPDATE | SKIP | ERROR
    source_row: int
    error: Optional[str] = None


# --------------------------------------------------------------------------
# Preview / Summary
# --------------------------------------------------------------------------

class PreviewSummary(BaseModel):
    """Top-level import statistics for the confirmation dialog."""

    total_students: int = 0
    existing_student_accounts: int = 0
    new_student_accounts: int = 0
    existing_counselor_accounts: int = 0
    missing_counselors: int = 0
    existing_memberships: int = 0
    new_memberships: int = 0
    warnings: int = 0
    errors: int = 0


class StudentPreviewRow(BaseModel):
    """One row of the student preview table."""

    roll_number: str
    email_used: Optional[str] = None
    name: Optional[str] = None
    status: str  # Existing | Missing
    action: str  # Reuse | Create Account


class CounselorPreviewRow(BaseModel):
    """One row of the counselor preview table."""

    email: str
    name: Optional[str] = None
    status: str  # Found | Missing
    action: str  # Reuse | Cannot Import
    student_count: int = 0


class MembershipPreviewRow(BaseModel):
    """One row of the membership preview table."""

    student_roll: str
    student_name: Optional[str] = None
    counselor_email: str
    counselor_name: Optional[str] = None
    status: str  # New | Existing
    action: str  # Create | Update | Skip | Error
    error: Optional[str] = None


class PreviewTables(BaseModel):
    """All three detail tables on the preview screen."""

    students: List[StudentPreviewRow] = Field(default_factory=list)
    counselors: List[CounselorPreviewRow] = Field(default_factory=list)
    memberships: List[MembershipPreviewRow] = Field(default_factory=list)


class ValidationErrorRow(BaseModel):
    """One error for the downloadable error report."""

    row: int
    error: str
    description: str
    suggested_fix: str


# --------------------------------------------------------------------------
# API responses
# --------------------------------------------------------------------------

class MembershipImportPreviewResponse(BaseModel):
    """Full preview returned to the frontend before confirmation."""

    batch_id: str
    file_name: str
    status: str

    summary: PreviewSummary
    tables: PreviewTables

    validation_errors: List[ValidationErrorRow] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    # Raw row-level data for deep inspection
    parsed_row_count: int = 0
    expanded_student_count: int = 0


class MembershipImportProgressResponse(BaseModel):
    """Progress polling response during import execution."""

    batch_id: str
    status: str
    phase: str
    phase_label: str
    percent: int
    processed: int
    total: int
    message: Optional[str] = None
    error: Optional[str] = None


class MembershipImportResultRecord(BaseModel):
    """One record in the import result."""

    record_type: str  # STUDENT | COUNSELOR | MEMBERSHIP
    identifier: str
    display_name: Optional[str] = None
    status: str  # CREATED | REUSED | SKIPPED | FAILED | UPDATED
    message: Optional[str] = None
    source_row_number: Optional[int] = None

    class Config:
        from_attributes = True


class GeneratedStudentCredential(BaseModel):
    """Credential for a newly created student account."""

    roll_number: str
    full_name: str
    username: str
    email: str
    temporary_password: str
    counselor_email: str
    status: str = "Active"


class MembershipImportSummaryResponse(BaseModel):
    """Post-import summary."""

    batch_id: str
    file_name: str
    status: str
    imported_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    total_rows: int = 0
    students_detected: int = 0
    students_created: int = 0
    students_reused: int = 0
    students_skipped: int = 0
    counselors_found: int = 0
    counselors_missing: int = 0
    memberships_created: int = 0
    memberships_updated: int = 0
    memberships_skipped: int = 0
    failed_records: int = 0
    warning_count: int = 0
    error_message: Optional[str] = None

    credentials_available: bool = False
    credential_count: int = 0
    records: List[MembershipImportResultRecord] = Field(default_factory=list)


class MembershipImportHistoryItem(BaseModel):
    """One item in the import history list."""

    batch_id: str
    file_name: str
    status: str
    imported_by: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    students_created: int = 0
    students_reused: int = 0
    memberships_created: int = 0
    failed_records: int = 0
    credentials_available: bool = False


class MembershipImportHistoryResponse(BaseModel):
    """Import history list with summary stats."""

    items: List[MembershipImportHistoryItem]
    total_imports: int = 0
    completed_imports: int = 0
    total_memberships_created: int = 0
    total_students_created: int = 0
    success_rate: float = 0.0
    last_import_at: Optional[datetime] = None


class MembershipImportConfiguration(BaseModel):
    """Configuration submitted with the import confirmation.

    The new membership import requires fewer manual selections — the Excel
    carries the counselor email directly.  Department / semester are still
    needed for student account creation and assignment records.
    """

    department_id: str = Field(..., description="Department for new student accounts")
    semester_id: str = Field(..., description="Semester for the counsellor assignment")
    section_name: str = Field(..., min_length=1, max_length=20, description="Section, e.g. A")
    batch_year: int = Field(..., ge=2000, le=2100)
    academic_year_id: Optional[str] = None
    study_year: Optional[int] = Field(None, ge=1, le=4)
    reassign_existing_students: bool = False
