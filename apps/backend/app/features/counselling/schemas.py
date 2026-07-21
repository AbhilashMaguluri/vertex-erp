from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ActionItemCreate(BaseModel):
    description: str = Field(..., min_length=3, max_length=500)
    due_date: date
    assigned_to_user_id: Optional[str] = None


class ActionItemResponse(BaseModel):
    id: str
    session_id: str
    description: str
    due_date: date
    status: str
    status_changed_at: Optional[datetime] = None
    assigned_to_user_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionCreateRequest(BaseModel):
    student_id: str
    session_date: date
    session_type: str = Field(..., description="ACADEMIC, PERSONAL, BEHAVIOURAL, CAREER, HEALTH, FINANCIAL")
    mode: str = Field(..., description="IN_PERSON, PHONE, VIDEO_CALL")
    observations: str = Field(..., min_length=50, description="Observations text (minimum 50 characters required by PRD §23.1)")
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    risk_assessment: Optional[str] = Field("NONE", description="NONE, LOW, MEDIUM, HIGH, CRITICAL")
    confidential: bool = False
    action_items: Optional[List[ActionItemCreate]] = None


class SessionResponse(BaseModel):
    id: str
    student_id: str
    counsellor_id: str
    session_date: date
    session_type: str
    mode: str
    observations: str
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


class ComplianceResponse(BaseModel):
    counsellor_id: str
    counsellor_name: str
    students_assigned: int
    sessions_conducted_this_month: int
    sessions_expected_this_month: int
    compliance_percentage: float
