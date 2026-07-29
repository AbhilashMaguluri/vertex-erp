from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ActionItemCreate(BaseModel):
    description: str = Field(..., min_length=3, max_length=500)
    due_date: date
    assigned_to_user_id: Optional[str] = None


class ActionItemResponse(BaseModel):
    id: UUID | str
    session_id: UUID | str
    description: str
    due_date: date
    status: str
    status_changed_at: Optional[datetime] = None
    assigned_to_user_id: UUID | str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionCreateRequest(BaseModel):
    student_id: str
    session_date: date
    session_type: str = Field(..., description="ACADEMIC, PERSONAL, BEHAVIOURAL, CAREER, HEALTH, FINANCIAL")
    mode: str = Field(..., description="IN_PERSON, PHONE, VIDEO_CALL")
    observations: str = Field(..., min_length=50, description="Observations text (minimum 50 characters required by PRD §23.1)")
    recommendations: Optional[str] = Field(None, max_length=5000, description="Guidance given to the student")
    student_commitments: Optional[str] = Field(None, max_length=5000, description="What the student agreed to do")
    confidential_notes: Optional[str] = Field(
        None,
        max_length=5000,
        description="Counsellor/Admin-only narrative. Never returned to a student.",
    )
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    risk_assessment: Optional[str] = Field("NONE", description="NONE, LOW, MEDIUM, HIGH, CRITICAL")
    confidential: bool = False
    action_items: Optional[List[ActionItemCreate]] = None


class SessionResponse(BaseModel):
    id: UUID | str
    student_id: UUID | str
    counsellor_id: UUID | str
    session_date: date
    session_type: str
    mode: str
    observations: str
    recommendations: Optional[str] = None
    student_commitments: Optional[str] = None
    # Nulled out for student viewers by CounsellingService._to_response.
    confidential_notes: Optional[str] = None
    follow_up_required: bool
    follow_up_date: Optional[date] = None
    student_acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    risk_assessment: Optional[str] = None
    confidential: bool
    action_items: List[ActionItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class FollowUpStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="PENDING, COMPLETED, OVERDUE")


class FollowUpUpdateRequest(BaseModel):
    """Partial update for one action item. Both fields optional so the
    dashboard's "Complete" and "Reschedule" buttons hit the same endpoint."""

    status: Optional[str] = Field(None, description="PENDING, COMPLETED, OVERDUE")
    due_date: Optional[date] = None


class ChartBucket(BaseModel):
    bucket: str
    count: int


class UpcomingFollowUp(BaseModel):
    id: str
    description: str
    due_date: date
    is_overdue: bool
    #: True only for items due exactly today — the dashboard's "Today's tasks"
    #: list, distinct from `is_overdue` (already past) and plain upcoming.
    is_due_today: bool = False
    student_id: str
    student_name: str
    student_roll_number: str
    session_id: str
    session_date: Optional[date] = None


class AttentionStudent(BaseModel):
    id: str
    roll_number: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    section_name: Optional[str] = None
    study_year: Optional[int] = None
    risk_level: str
    attendance_percentage: Optional[float] = None
    cgpa: Optional[float] = None
    active_backlogs: int = 0
    last_session_date: Optional[date] = None
    reason: str
    #: Machine-readable flags behind `reason`, so the client can render an
    #: icon/severity per trigger instead of parsing the prose.
    flags: List[str] = []


class ActivityEntry(BaseModel):
    """One row of the "recent counselling activity" feed — a session that was
    actually recorded. Grouped client-side into Today / Yesterday / earlier."""

    session_id: str
    student_id: str
    student_name: str
    student_roll_number: str
    session_type: str
    mode: str
    session_date: date
    #: Row insertion time. session_date is a plain date (the day the meeting
    #: happened), so this is the only ordering signal within a single day.
    recorded_at: datetime
    follow_up_required: bool = False


class AgendaEntry(BaseModel):
    """One item on today's agenda.

    NOTE ON TIMES: this system has no appointment entity — CounsellingSession
    stores a `session_date` (a plain date) and action items store a `due_date`.
    Nothing anywhere carries a clock time, so agenda items are ordered by
    urgency, not by hour, and no time-of-day is emitted. Rendering "10:00" here
    would be invented data.
    """

    kind: str = Field(..., description="FOLLOW_UP (action item due) or SESSION (recorded today)")
    reference_id: str
    student_id: str
    student_name: str
    student_roll_number: str
    label: str
    due_date: date
    is_overdue: bool = False


class CounsellorDashboardResponse(BaseModel):
    """Everything the counsellor landing page renders, in one round trip."""

    # Cohort
    total_students: int
    male: int
    female: int
    gender_unknown: int
    average_attendance: Optional[float] = None
    average_cgpa: Optional[float] = None

    # Sessions
    sessions_total: int
    sessions_today: int
    sessions_this_month: int
    sessions_acknowledged: int

    # Follow-ups
    follow_ups_pending: int
    follow_ups_completed: int
    follow_ups_overdue: int
    follow_ups_upcoming: int

    #: Distinct students carrying at least one open action item — the caseload
    #: the counsellor currently owes work on, as opposed to headcount.
    active_cases: int = 0

    # At-risk buckets
    high_risk_count: int
    below_attendance_count: int
    with_backlogs_count: int

    # Risk centre. NONE and LOW collapse into `risk_low` — "not flagged" and
    # "flagged low" are the same intervention tier for a counsellor.
    risk_high: int = 0
    risk_medium: int = 0
    risk_low: int = 0

    # Charts
    by_year: List[ChartBucket] = []
    by_section: List[ChartBucket] = []
    by_risk: List[ChartBucket] = []
    by_attendance_band: List[ChartBucket] = []
    sessions_by_month: List[ChartBucket] = []
    sessions_by_type: List[ChartBucket] = []

    # Worklists
    upcoming_follow_ups: List[UpcomingFollowUp] = []
    students_needing_attention: List[AttentionStudent] = []
    recent_activity: List[ActivityEntry] = []
    agenda_today: List[AgendaEntry] = []


class ComplianceResponse(BaseModel):
    counsellor_id: str
    counsellor_name: str
    students_assigned: int
    sessions_conducted_this_month: int
    sessions_expected_this_month: int
    compliance_percentage: float
