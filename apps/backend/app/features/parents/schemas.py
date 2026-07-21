from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, Field


class ParentCommunicationCreateRequest(BaseModel):
    student_id: str
    communication_date: date
    communication_time: Optional[time] = None
    mode: str = Field("PHONE_CALL", description="PHONE_CALL, IN_PERSON, EMAIL, VIDEO_CALL")
    parent_name: str = Field(..., min_length=2, max_length=100)
    relation: str = Field("Father", description="Father, Mother, Guardian")
    contact_number: str = Field(..., min_length=5, max_length=20)
    summary: str = Field(..., min_length=10, description="Summary of interaction")
    concerns: Optional[str] = None
    action_items: Optional[str] = None
    outcome: str = Field("POSITIVE", description="POSITIVE, NEUTRAL, CONCERNING, UNRESPONSIVE")
    follow_up_date: Optional[date] = None


class ParentCommunicationResponse(BaseModel):
    id: str
    student_id: str
    counsellor_id: str
    communication_date: date
    communication_time: Optional[time] = None
    mode: str
    parent_name: str
    relation: str
    contact_number: str
    summary: str
    concerns: Optional[str] = None
    action_items: Optional[str] = None
    outcome: str
    follow_up_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True
