from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class StudentMarkItem(BaseModel):
    student_id: str
    marks_obtained: float = Field(..., ge=0)
    max_marks: float = Field(..., gt=0)


class BulkMarksCreate(BaseModel):
    subject_id: str
    semester_id: str
    assessment_type: str = Field(..., description="MID_TERM_1, MID_TERM_2, INTERNAL, EXTERNAL")
    records: List[StudentMarkItem]


class MarksResponse(BaseModel):
    id: str
    student_id: str
    subject_id: str
    semester_id: str
    assessment_type: str
    marks_obtained: float
    max_marks: float
    recorded_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class SGPACalculationResponse(BaseModel):
    student_id: str
    semester_id: str
    sgpa: float
    cgpa: float
    total_credits: int
    earned_credits: int


class BacklogResponse(BaseModel):
    id: str
    student_id: str
    subject_id: str
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    semester_id: str
    status: str
    cleared_at_semester_id: Optional[str] = None
    cleared_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SubjectResultRow(BaseModel):
    """One subject's full assessment breakdown within a semester. Every mark
    is Optional — a semester in progress has mids recorded but no external
    yet, and rendering an unrecorded assessment as 0 would misreport it."""

    subject_id: str
    subject_code: str
    subject_name: str
    credits: int
    mid_1: Optional[float] = None
    mid_2: Optional[float] = None
    internal: Optional[float] = None
    external: Optional[float] = None
    total_obtained: Optional[float] = None
    total_max: Optional[float] = None
    percentage: Optional[float] = None
    grade: Optional[str] = None
    # PASS / FAIL / IN_PROGRESS — IN_PROGRESS while the external is unrecorded.
    result: str = "IN_PROGRESS"


class SemesterResultBlock(BaseModel):
    semester_id: str
    semester_name: str
    semester_number: int
    subjects: List[SubjectResultRow] = []
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    total_credits: Optional[int] = None
    active_backlogs: int = 0


class StudentAcademicRecordResponse(BaseModel):
    student_id: str
    cgpa: Optional[float] = None
    latest_sgpa: Optional[float] = None
    total_active_backlogs: int = 0
    semesters: List[SemesterResultBlock] = []


class SubjectMarkDetail(BaseModel):
    subject_code: str
    subject_name: str
    credits: int
    mid_marks: Optional[float] = None
    internal_marks: Optional[float] = None
    external_marks: Optional[float] = None
    grade: Optional[str] = None
    grade_points: Optional[int] = None


class AcademicTranscriptResponse(BaseModel):
    student_id: str
    roll_number: str
    cgpa: float
    active_backlogs_count: int
    completed_semesters_count: int
    semester_marks: List[SubjectMarkDetail] = []
