from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StudentProfileResponse(BaseModel):
    id: str
    user_id: str
    roll_number: str
    registration_number: str
    full_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: date
    batch_year: int
    status: str
    risk_level: str
    department_id: str
    department_name: Optional[str] = None
    current_semester_id: Optional[str] = None
    counsellor_name: Optional[str] = None
    
    father_name: Optional[str] = None
    father_phone: Optional[str] = None
    mother_name: Optional[str] = None
    mother_phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskFlagUpdateRequest(BaseModel):
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL, NONE")
    reason: str = Field(..., min_length=5, description="Reason for risk level change")


class TimelineEventResponse(BaseModel):
    id: str
    student_id: str
    event_type: str
    title: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    created_at: datetime


class OverviewStat(BaseModel):
    title: str
    value: str
    change: Optional[str] = None
    trend: Optional[str] = None
    description: Optional[str] = None


class Student360Response(BaseModel):
    profile: StudentProfileResponse
    stats: List[OverviewStat]
    attention_items: List[str]
    recent_events: List[TimelineEventResponse]


class RosterStudentResponse(BaseModel):
    id: str
    roll_number: str
    full_name: str


class CaseloadStudentResponse(BaseModel):
    """One row of the counsellor's Assigned Students table.

    Every metric is Optional because a freshly-imported student legitimately
    has no attendance, no marks and no counselling history yet — the UI shows
    "No data" for those rather than a misleading 0.
    """

    id: str
    roll_number: str
    registration_number: str
    full_name: str
    email: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    photo_url: Optional[str] = None

    study_year: Optional[int] = None
    section_id: Optional[str] = None
    section_name: Optional[str] = None
    semester_id: Optional[str] = None
    semester_name: Optional[str] = None
    batch_year: int
    department_id: str
    department_name: Optional[str] = None
    department_code: Optional[str] = None

    attendance_percentage: Optional[float] = None
    total_classes: Optional[int] = None
    attended_classes: Optional[int] = None
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    active_backlogs: int = 0

    risk_level: str
    status: str
    last_session_date: Optional[date] = None
    session_count: int = 0

    counsellor_id: Optional[str] = None
    counsellor_name: Optional[str] = None

    # Derived server-side so the "below threshold" rule lives in one place
    # rather than being re-implemented by every client.
    attendance_below_threshold: bool = False


class PendingActionItem(BaseModel):
    id: str
    description: str
    due_date: date
    status: str
    is_overdue: bool = False
    session_id: str
    session_date: date


class SessionContextResponse(BaseModel):
    """Everything the session recorder auto-populates once a counsellor picks a
    student — replaces the old "type the Student ID" field entirely."""

    student_id: str
    roll_number: str
    full_name: str
    email: str
    department_name: Optional[str] = None
    section_name: Optional[str] = None
    study_year: Optional[int] = None
    semester_id: Optional[str] = None
    semester_name: Optional[str] = None

    attendance_percentage: Optional[float] = None
    cgpa: Optional[float] = None
    sgpa: Optional[float] = None
    active_backlogs: int = 0
    risk_level: str

    last_session_date: Optional[date] = None
    last_session_summary: Optional[str] = None
    last_session_type: Optional[str] = None
    total_sessions: int = 0
    pending_action_items: List[PendingActionItem] = []
    attention_items: List[str] = []


class FacetOption(BaseModel):
    id: str
    label: str


class CaseloadFacets(BaseModel):
    """Distinct values present in the caller's own caseload, so the filter
    dropdowns only ever offer options that actually return rows."""

    years: List[int] = []
    sections: List[FacetOption] = []
    semesters: List[FacetOption] = []
    departments: List[FacetOption] = []
    batch_years: List[int] = []
    risk_levels: List[str] = []
    statuses: List[str] = []


class AcademicCorrectionCreate(BaseModel):
    section_name: str = Field(..., description="Section being corrected (e.g. Attendance, SGPA, Backlogs, Department)")
    current_value: Optional[str] = None
    proposed_value: Optional[str] = None
    description: str = Field(..., min_length=10, description="Detailed explanation of the correction requested")
    document_id: Optional[str] = None


class AcademicCorrectionReview(BaseModel):
    status: str = Field(..., description="APPROVED, REJECTED, NEED_MORE_INFO, UNDER_REVIEW")
    remarks: Optional[str] = None


class AcademicCorrectionClarification(BaseModel):
    remarks: Optional[str] = None
    document_id: Optional[str] = None


class AcademicCorrectionLogResponse(BaseModel):
    id: str
    actor_id: str
    actor_name: Optional[str] = None
    action: str
    from_status: Optional[str] = None
    to_status: str
    remarks: Optional[str] = None
    document_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AcademicCorrectionResponse(BaseModel):
    id: str
    student_id: str
    student_name: Optional[str] = None
    student_roll: Optional[str] = None
    counsellor_id: Optional[str] = None
    counsellor_name: Optional[str] = None
    section_name: str
    current_value: Optional[str] = None
    proposed_value: Optional[str] = None
    description: str
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    document_url: Optional[str] = None
    status: str
    counsellor_remarks: Optional[str] = None
    reviewed_by_user_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    logs: List[AcademicCorrectionLogResponse] = []

    class Config:
        from_attributes = True

