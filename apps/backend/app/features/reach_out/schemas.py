import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


def validate_phone_number(v: Optional[str]) -> Optional[str]:
    if v is None or v.strip() == "":
        return None
    cleaned = v.strip()
    # Accept standard international / national format e.g. +91 863 2288200 or 9876543210
    pattern = r"^\+?[0-9\s\-\(\)]{7,20}$"
    if not re.match(pattern, cleaned):
        raise ValueError("Invalid phone or WhatsApp number format. Must contain 7-20 digits.")
    return cleaned


def validate_url_link(v: Optional[str]) -> Optional[str]:
    if v is None or v.strip() == "":
        return None
    cleaned = v.strip()
    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        raise ValueError("Invalid URL format. Must start with http:// or https://")
    return cleaned


class ScheduleSlotSchema(BaseModel):
    start: str = Field(..., example="09:30")
    end: str = Field(..., example="12:30")


class DailyScheduleSchema(BaseModel):
    is_available: bool = True
    slots: List[ScheduleSlotSchema] = []


class WeeklyScheduleSchema(BaseModel):
    monday: DailyScheduleSchema = Field(default_factory=DailyScheduleSchema)
    tuesday: DailyScheduleSchema = Field(default_factory=DailyScheduleSchema)
    wednesday: DailyScheduleSchema = Field(default_factory=DailyScheduleSchema)
    thursday: DailyScheduleSchema = Field(default_factory=DailyScheduleSchema)
    friday: DailyScheduleSchema = Field(default_factory=DailyScheduleSchema)
    saturday: DailyScheduleSchema = Field(default_factory=DailyScheduleSchema)
    sunday: DailyScheduleSchema = Field(default_factory=DailyScheduleSchema)


class ChannelPreferencesSchema(BaseModel):
    whatsapp: bool = True
    email: bool = True
    teams: bool = True
    google_meet: bool = True
    zoom: bool = True
    telegram: bool = True
    personal_call: bool = False


class CounsellorContactProfileSchema(BaseModel):
    id: str
    counsellor_id: str
    full_name: str
    photo_url: Optional[str] = None
    designation: str
    department_name: str
    years_experience: int
    specializations: List[str] = []
    languages_spoken: List[str] = []
    about_me: Optional[str] = None
    research_interests: Optional[str] = None

    building: str
    floor: str
    cabin_number: str
    office_phone: Optional[str] = None
    emergency_alternate_phone: Optional[str] = None
    office_image_url: Optional[str] = None
    maps_url: Optional[str] = None

    office_status: str
    status_message: Optional[str] = None

    structured_schedule: Optional[Dict[str, Any]] = None
    channel_preferences: Optional[Dict[str, bool]] = None

    whatsapp_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    teams_url: Optional[str] = None
    google_meet_url: Optional[str] = None
    zoom_url: Optional[str] = None
    telegram_url: Optional[str] = None
    college_email: Optional[str] = None

    class Config:
        from_attributes = True


class CounsellorContactProfileUpdate(BaseModel):
    photo_url: Optional[str] = None
    designation: Optional[str] = None
    department_name: Optional[str] = None
    years_experience: Optional[int] = None
    specializations: Optional[List[str]] = None
    languages_spoken: Optional[List[str]] = None
    about_me: Optional[str] = None
    research_interests: Optional[str] = None

    building: Optional[str] = None
    floor: Optional[str] = None
    cabin_number: Optional[str] = None
    office_phone: Optional[str] = None
    emergency_alternate_phone: Optional[str] = None
    office_image_url: Optional[str] = None
    maps_url: Optional[str] = None

    office_status: Optional[str] = None
    status_message: Optional[str] = None

    structured_schedule: Optional[Dict[str, Any]] = None
    channel_preferences: Optional[Dict[str, bool]] = None

    whatsapp_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    teams_url: Optional[str] = None
    google_meet_url: Optional[str] = None
    zoom_url: Optional[str] = None
    telegram_url: Optional[str] = None
    college_email: Optional[str] = None

    @field_validator(
        "office_phone", "emergency_alternate_phone", "whatsapp_number", mode="before"
    )
    @classmethod
    def check_phone(cls, v: Optional[str]) -> Optional[str]:
        return validate_phone_number(v)

    @field_validator(
        "photo_url",
        "office_image_url",
        "maps_url",
        "linkedin_url",
        "teams_url",
        "google_meet_url",
        "zoom_url",
        "telegram_url",
        mode="before",
    )
    @classmethod
    def check_url(cls, v: Optional[str]) -> Optional[str]:
        return validate_url_link(v)


class ScheduleExceptionCreate(BaseModel):
    exception_type: str = "SPECIAL_HOURS"
    title: str
    start_date: date
    end_date: date
    custom_hours: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class ScheduleExceptionResponse(ScheduleExceptionCreate):
    id: str
    counsellor_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class StudentPrivacySettingsSchema(BaseModel):
    share_phone: bool = True
    share_personal_email: bool = True
    share_linkedin: bool = True
    share_github: bool = True
    share_portfolio: bool = True
    share_leetcode: bool = True
    share_codechef: bool = True
    share_hackerrank: bool = True

    preferred_parent_contact: str = "FATHER"
    best_time_to_call: Optional[str] = "Evening 5:00 PM - 7:00 PM"
    preferred_language: Optional[str] = "Telugu"

    class Config:
        from_attributes = True


class ParentContactDetails(BaseModel):
    father_name: Optional[str] = None
    father_phone: Optional[str] = None
    father_email: Optional[str] = None
    father_occupation: Optional[str] = None

    mother_name: Optional[str] = None
    mother_phone: Optional[str] = None
    mother_email: Optional[str] = None
    mother_occupation: Optional[str] = None

    guardian_name: Optional[str] = None
    guardian_relation: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[str] = None

    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    preferred_parent_contact: str = "FATHER"
    best_time_to_call: Optional[str] = None
    preferred_language: Optional[str] = None


class StudentCommunicationHealthSchema(BaseModel):
    has_data: bool = False
    insufficient_data_reason: Optional[str] = "Insufficient data."
    score_stars: float = 0.0
    last_response_time: Optional[str] = None
    avg_response_time_hours: float = 0.0
    last_meeting_date: Optional[date] = None
    follow_up_compliance_pct: float = 0.0


class ParentEngagementScoreSchema(BaseModel):
    has_data: bool = False
    insufficient_data_reason: Optional[str] = "Insufficient data."
    score_stars: float = 0.0
    total_calls: int = 0
    total_meetings: int = 0
    total_emails: int = 0
    last_contact_date: Optional[date] = None


class AssignedStudentContactSchema(BaseModel):
    id: str
    user_id: str
    name: str
    roll_number: str
    department_name: str
    batch_year: int
    current_semester: Optional[str] = None
    photo_url: Optional[str] = None

    # Academic & Risk Snapshot
    cgpa: Optional[float] = None
    attendance_pct: Optional[float] = None
    risk_level: str = "NONE"
    active_backlogs_count: int = 0

    # Handles (filtered by privacy)
    phone: Optional[str] = None
    personal_email: Optional[str] = None
    college_email: Optional[str] = None
    whatsapp_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    codechef_url: Optional[str] = None
    hackerrank_url: Optional[str] = None
    resume_url: Optional[str] = None

    # Parent & Emergency
    parent_contacts: ParentContactDetails
    privacy_settings: StudentPrivacySettingsSchema

    # SRM Metrics
    is_favorite: bool = False
    communication_health: StudentCommunicationHealthSchema
    parent_engagement: ParentEngagementScoreSchema
    latest_communication_date: Optional[date] = None

    class Config:
        from_attributes = True


class AppointmentRequestCreate(BaseModel):
    request_type: str = "APPOINTMENT"
    preferred_date: date
    preferred_time_slot: str
    reason: Optional[str] = None


class AppointmentRequestStatusUpdate(BaseModel):
    status: str
    rescheduled_date: Optional[date] = None
    rescheduled_slot: Optional[str] = None
    counsellor_notes: Optional[str] = None


class AppointmentRequestResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    student_roll: str
    counsellor_id: str
    counsellor_name: str
    request_type: str
    preferred_date: date
    preferred_time_slot: str
    reason: Optional[str] = None
    status: str
    rescheduled_date: Optional[date] = None
    rescheduled_slot: Optional[str] = None
    counsellor_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CommunicationTimelineLogCreate(BaseModel):
    channel: str
    direction: str = "COUNSELLOR_TO_STUDENT"
    summary: str
    sentiment: str = "POSITIVE"
    action_outcome: str = "RESOLVED"
    duration_minutes: Optional[int] = None
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    attachments: Optional[List[str]] = None


class CommunicationTimelineLogResponse(BaseModel):
    id: str
    student_id: str
    counsellor_id: str
    counsellor_name: str
    channel: str
    direction: str
    summary: str
    sentiment: str
    action_outcome: str
    duration_minutes: Optional[int] = None
    follow_up_required: bool
    follow_up_date: Optional[date] = None
    attachments: Optional[List[str]] = None
    ai_summary: Optional[Dict[str, Any]] = None
    occurred_at: datetime

    class Config:
        from_attributes = True


class AIMeetingBriefingResponse(BaseModel):
    student_id: str
    student_name: str
    roll_number: str
    department_name: str
    cgpa: Optional[float] = None
    attendance_pct: Optional[float] = None
    backlogs_count: int = 0
    risk_level: str = "NONE"
    last_session_date: Optional[date] = None
    last_session_summary: Optional[str] = None
    pending_tasks: List[str] = []
    suggested_discussion_topics: List[str] = []


class CommunicationTemplateResponse(BaseModel):
    id: str
    title: str
    category: str
    channel: str
    subject_template: Optional[str] = None
    body_template: str
    is_system: bool

    class Config:
        from_attributes = True


class InstitutionalChannelPolicySchema(BaseModel):
    whatsapp_enabled: bool = True
    linkedin_enabled: bool = True
    telegram_enabled: bool = True
    teams_enabled: bool = True
    google_meet_enabled: bool = True
    zoom_enabled: bool = True
    phone_enabled: bool = True
    email_enabled: bool = True

    class Config:
        from_attributes = True


class CampusEmergencyContactSchema(BaseModel):
    id: str
    name: str
    category: str
    phone: str
    email: Optional[str] = None
    location: Optional[str] = None
    is_24_7: bool
    display_order: int

    class Config:
        from_attributes = True


class CampusEmergencyContactCreate(BaseModel):
    name: str
    category: str = "GENERAL"
    phone: str
    email: Optional[str] = None
    location: Optional[str] = None
    is_24_7: bool = True
    display_order: int = 0

    @field_validator("phone", mode="before")
    @classmethod
    def check_phone(cls, v: str) -> str:
        res = validate_phone_number(v)
        if not res:
            raise ValueError("Phone number is required")
        return res


class ReachOutAuditLogResponse(BaseModel):
    id: str
    actor_id: str
    actor_name: str
    action: str
    target_type: str
    target_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
