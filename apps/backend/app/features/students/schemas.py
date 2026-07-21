from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


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
