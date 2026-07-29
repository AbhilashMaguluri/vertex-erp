from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class StudentAttendanceItem(BaseModel):
    student_id: str
    status: str = Field("PRESENT", description="PRESENT, ABSENT, ON_DUTY, MEDICAL_LEAVE")


class BulkAttendanceCreate(BaseModel):
    subject_id: str
    date: date
    records: List[StudentAttendanceItem]


class AttendanceRecordResponse(BaseModel):
    id: str
    student_id: str
    subject_id: str
    date: date
    status: str
    recorded_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class SubjectAttendanceSummary(BaseModel):
    subject_id: str
    subject_code: str
    subject_name: str
    total_classes: int
    attended_classes: int  # PRESENT + ON_DUTY
    percentage: float


class MonthlyAttendancePoint(BaseModel):
    """One month of the attendance trend. Months with no classes recorded are
    absent from the series rather than plotted as 0% — a holiday month is not
    a month of total absence."""

    month: str  # ISO year-month, e.g. "2026-07"
    label: str  # "Jul 2026"
    total_classes: int
    attended_classes: int
    percentage: float


class StudentAttendanceSummaryResponse(BaseModel):
    student_id: str
    # None means "no classes recorded yet", which is NOT the same as 100%.
    # A student with an empty record must not be shown as fully present.
    overall_percentage: Optional[float] = None
    total_classes: int = 0
    attended_classes: int = 0
    subject_summaries: List[SubjectAttendanceSummary]
    monthly_trend: List[MonthlyAttendancePoint] = []


class DefaulterResponse(BaseModel):
    student_id: str
    student_name: str
    roll_number: str
    department_name: str
    subject_code: str
    attendance_percentage: float
    alert_level: str  # WARNING (<80%), DEFAULTER (<75%), CRITICAL (<65%)


class CorrectionRequestCreate(BaseModel):
    attendance_record_id: str
    new_status: str = Field(..., description="PRESENT, ABSENT, ON_DUTY, MEDICAL_LEAVE")
    reason: str = Field(..., min_length=5, description="Reason for correction")


class CorrectionResponse(BaseModel):
    id: str
    attendance_record_id: str
    student_id: str
    requested_by: str
    old_status: str
    new_status: str
    reason: str
    approval_status: str
    reviewed_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
