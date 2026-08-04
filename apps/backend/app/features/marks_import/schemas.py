"""Pydantic schemas for the Enterprise Marks Import & Assessment Management feature."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Assessment Component & Template schemas
# --------------------------------------------------------------------------

class AssessmentComponentSchema(BaseModel):
    """Question component (e.g. Question A with max marks 6.0)."""

    key: str = Field(..., description="Component identifier, e.g. A, B, Q1")
    label: str = Field(..., description="Display label, e.g. Question A")
    max_marks: float = Field(..., ge=0, description="Maximum marks allowed for this question")


class AssessmentTemplateCreate(BaseModel):
    """Schema for creating a new assessment template."""

    subject_id: Optional[str] = Field(None, description="Subject UUID (null for global template)")
    assessment_code: str = Field(..., min_length=2, max_length=50)
    assessment_name: str = Field(..., min_length=2, max_length=100)
    total_max_marks: float = Field(..., ge=0)
    components: List[AssessmentComponentSchema] = Field(default_factory=list)
    description: Optional[str] = None


class AssessmentTemplateUpdate(BaseModel):
    """Schema for updating an existing assessment template."""

    assessment_name: Optional[str] = None
    total_max_marks: Optional[float] = None
    components: Optional[List[AssessmentComponentSchema]] = None
    description: Optional[str] = None


class AssessmentTemplateResponse(BaseModel):
    """Assessment template response."""

    id: str
    subject_id: Optional[str] = None
    assessment_code: str
    assessment_name: str
    total_max_marks: float
    components: List[AssessmentComponentSchema]
    description: Optional[str] = None

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# Import Data DTOs
# --------------------------------------------------------------------------

class ParsedMarksRow(BaseModel):
    """Parsed row from Excel before validation."""

    row_number: int
    student_roll: str
    question_scores: Dict[str, float] = Field(default_factory=dict)
    total_marks: Optional[float] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


class ResolvedMarksEntry(BaseModel):
    """Marks entry resolved against student database and existing marks."""

    roll_number: str
    source_row: int
    question_scores: Dict[str, float] = Field(default_factory=dict)
    total_marks: float
    max_marks: float
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    student_found: bool = False
    existing_mark_id: Optional[str] = None
    existing_total: Optional[float] = None
    resolution_status: str  # NEW | EXISTING | MISSING_STUDENT
    proposed_action: str  # CREATE | UPDATE | SKIP | CANNOT_IMPORT
    error: Optional[str] = None


# --------------------------------------------------------------------------
# Preview & Validation DTOs
# --------------------------------------------------------------------------

class PreviewSummary(BaseModel):
    """Top-level metrics for preview UI."""

    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    assessment_code: str
    assessment_name: str
    total_max_marks: float
    total_students_in_file: int = 0
    existing_students_found: int = 0
    missing_students: int = 0
    new_records: int = 0
    updates: int = 0
    skipped_records: int = 0
    warnings: int = 0
    errors: int = 0


class StudentMarksPreviewRow(BaseModel):
    """Row in detailed marks preview table."""

    roll_number: str
    student_name: Optional[str] = None
    question_breakdown: str  # e.g. "A:6, B:5.5, C:4" or "20/20"
    total_marks: float
    max_marks: float
    student_found: str  # Yes | No
    existing_marks: str  # Yes (24.5/30) | No
    action: str  # Create | Update | Skip | Cannot Import
    error: Optional[str] = None


class PreviewTables(BaseModel):
    records: List[StudentMarksPreviewRow] = Field(default_factory=list)


class ValidationErrorRow(BaseModel):
    row: int
    roll_number: str
    error: str
    suggested_fix: str


# --------------------------------------------------------------------------
# Configuration & Response DTOs
# --------------------------------------------------------------------------

class MarksImportConfiguration(BaseModel):
    academic_year_id: Optional[str] = None
    semester_id: str = Field(..., description="Semester UUID")
    department_id: Optional[str] = None
    section_id: Optional[str] = None
    subject_id: str = Field(..., description="Subject UUID")
    assessment_code: str = Field(..., description="Assessment Code")
    allow_overwrite: bool = Field(True, description="Whether to update existing marks")


class MarksImportPreviewResponse(BaseModel):
    batch_id: str
    file_name: str
    status: str
    summary: PreviewSummary
    tables: PreviewTables
    validation_errors: List[ValidationErrorRow] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    parsed_row_count: int = 0


class MarksImportProgressResponse(BaseModel):
    batch_id: str
    status: str
    phase: str
    phase_label: str
    percent: int
    processed: int
    total: int
    message: Optional[str] = None
    error: Optional[str] = None


class MarksImportResultRecord(BaseModel):
    record_type: str = "MARKS"
    identifier: str
    display_name: Optional[str] = None
    status: str  # CREATED | UPDATED | SKIPPED | FAILED
    message: Optional[str] = None
    source_row_number: Optional[int] = None

    class Config:
        from_attributes = True


class MarksImportSummaryResponse(BaseModel):
    batch_id: str
    file_name: str
    status: str
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    assessment_code: str
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

    records: List[MarksImportResultRecord] = Field(default_factory=list)


class MarksImportHistoryItem(BaseModel):
    batch_id: str
    file_name: str
    subject_name: Optional[str] = None
    assessment_code: str
    status: str
    imported_by: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    records_created: int = 0
    records_updated: int = 0
    failed_records: int = 0


class MarksImportHistoryResponse(BaseModel):
    items: List[MarksImportHistoryItem]
    total_imports: int = 0
    completed_imports: int = 0
    total_records_created: int = 0
    total_records_updated: int = 0
    success_rate: float = 0.0
    last_import_at: Optional[datetime] = None
