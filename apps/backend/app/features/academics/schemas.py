from datetime import datetime
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
    semester_failed_id: str
    attempts_count: int
    status: str
    semester_cleared_id: Optional[str] = None
    cleared_grade: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


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
