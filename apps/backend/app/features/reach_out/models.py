import uuid
from datetime import date, datetime, timezone
from typing import Any, List, Optional
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.shared.models.base import TimestampMixin


class CounsellorContactProfile(Base, TimestampMixin):
    """Counsellor professional persona, cabin, structured schedule, and contact channels."""

    __tablename__ = "counsellor_contact_profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    counsellor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    designation: Mapped[str] = mapped_column(String(100), default="Student Counsellor", nullable=False)
    department_name: Mapped[str] = mapped_column(String(150), default="Artificial Intelligence & Data Science", nullable=False)
    years_experience: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    
    specializations: Mapped[Optional[List[Any]]] = mapped_column(
        JSONB, default=["Academic Counselling", "Career Guidance", "Mental Wellness", "Higher Studies"], nullable=True
    )
    languages_spoken: Mapped[Optional[List[Any]]] = mapped_column(
        JSONB, default=["English", "Telugu", "Hindi"], nullable=True
    )
    about_me: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    research_interests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    building: Mapped[str] = mapped_column(String(100), default="Block B", nullable=False)
    floor: Mapped[str] = mapped_column(String(50), default="3rd Floor", nullable=False)
    cabin_number: Mapped[str] = mapped_column(String(50), default="Room 302", nullable=False)
    office_phone: Mapped[Optional[str]] = mapped_column(String(30), default="+91 863 2288200", nullable=True)
    emergency_alternate_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    office_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    maps_url: Mapped[Optional[str]] = mapped_column(
        String(1000), default="https://maps.google.com/?q=VVIT+Guntur", nullable=True
    )

    # Status: AVAILABLE, BUSY, IN_SESSION, ON_LEAVE, OFFLINE
    office_status: Mapped[str] = mapped_column(String(30), default="AVAILABLE", nullable=False)
    status_message: Mapped[Optional[str]] = mapped_column(String(255), default="Available for student counselling", nullable=True)

    # Weekly structured schedule: day -> list of slots e.g. [{"start": "09:30", "end": "12:30"}, ...]
    structured_schedule: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Allowed counsellor-specific contact channels
    channel_preferences: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Direct contact handles
    whatsapp_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    teams_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    google_meet_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    zoom_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    telegram_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    college_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    counsellor: Mapped["User"] = relationship("User", foreign_keys=[counsellor_id])


class ScheduleException(Base, TimestampMixin):
    """Temporary schedule overrides like holidays, exam weeks, special hours."""

    __tablename__ = "schedule_exceptions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    counsellor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # HOLIDAY, VACATION, SPECIAL_HOURS, EXAM_WEEK, EMERGENCY_LEAVE
    exception_type: Mapped[str] = mapped_column(String(40), default="SPECIAL_HOURS", nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    custom_hours: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class StudentCommunicationPrivacy(Base, TimestampMixin):
    """Student granular privacy preferences for sharing platform links and parent contact preferences."""

    __tablename__ = "student_communication_privacies"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    share_phone: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    share_personal_email: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    share_linkedin: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    share_github: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    share_portfolio: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    share_leetcode: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    share_codechef: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    share_hackerrank: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    preferred_parent_contact: Mapped[str] = mapped_column(String(30), default="FATHER", nullable=False)
    best_time_to_call: Mapped[Optional[str]] = mapped_column(String(100), default="Evening 5:00 PM - 7:00 PM", nullable=True)
    preferred_language: Mapped[Optional[str]] = mapped_column(String(50), default="Telugu", nullable=True)


class AppointmentRequest(Base, TimestampMixin):
    """Appointments & meeting requests between student and counsellor."""

    __tablename__ = "appointment_requests"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    counsellor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # APPOINTMENT, COUNSELLING, PARENT_MEETING, CAREER_GUIDANCE, ACADEMIC_GUIDANCE
    request_type: Mapped[str] = mapped_column(String(50), default="APPOINTMENT", nullable=False)
    preferred_date: Mapped[date] = mapped_column(Date, nullable=False)
    preferred_time_slot: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # PENDING, ACCEPTED, DECLINED, COMPLETED, RESCHEDULED, CANCELLED, NO_SHOW, EXPIRED
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    rescheduled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    rescheduled_slot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    counsellor_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    student: Mapped["Student"] = relationship("Student", foreign_keys=[student_id])
    counsellor: Mapped["User"] = relationship("User", foreign_keys=[counsellor_id])


class CommunicationTimelineLog(Base, TimestampMixin):
    """Communication history log entries between counsellor, student, and parents."""

    __tablename__ = "communication_timeline_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    counsellor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Channel: WHATSAPP, EMAIL, PHONE_CALL, PARENT_MEETING, TEAMS, GOOGLE_MEET, IN_PERSON
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    # Direction: STUDENT_TO_COUNSELLOR, COUNSELLOR_TO_STUDENT, COUNSELLOR_TO_PARENT, PARENT_TO_COUNSELLOR
    direction: Mapped[str] = mapped_column(String(40), default="COUNSELLOR_TO_STUDENT", nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Sentiment: POSITIVE, NEUTRAL, CONCERNING, UNRESPONSIVE
    sentiment: Mapped[str] = mapped_column(String(30), default="POSITIVE", nullable=False)
    # Action Outcome: ACTION_REQUIRED, RESOLVED, ESCALATED, PARENT_INFORMED, FOLLOW_UP_SCHEDULED, REFERRAL_NEEDED
    action_outcome: Mapped[str] = mapped_column(String(50), default="RESOLVED", nullable=False)
    
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    attachments: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    ai_summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    student: Mapped["Student"] = relationship("Student", foreign_keys=[student_id])
    counsellor: Mapped["User"] = relationship("User", foreign_keys=[counsellor_id])


class CounsellorFavoriteStudent(Base, TimestampMixin):
    """Pinned / favorite high-touch students for counsellors."""

    __tablename__ = "counsellor_favorite_students"
    __table_args__ = (UniqueConstraint("counsellor_id", "student_id", name="uq_counsellor_favorite_student"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    counsellor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )


class CommunicationTemplate(Base, TimestampMixin):
    """Reusable quick communication templates for counsellors."""

    __tablename__ = "communication_templates"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="GENERAL", nullable=False)
    channel: Mapped[str] = mapped_column(String(40), default="WHATSAPP", nullable=False)
    subject_template: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class InstitutionalChannelPolicy(Base, TimestampMixin):
    """Master institutional channel policies configured by Admin."""

    __tablename__ = "institutional_channel_policies"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    linkedin_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    teams_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    google_meet_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    zoom_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    phone_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CampusEmergencyContact(Base, TimestampMixin):
    """Campus emergency hotline contacts directory."""

    __tablename__ = "campus_emergency_contacts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="GENERAL", nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    is_24_7: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ReachOutAuditLog(Base, TimestampMixin):
    """Audit log for recording all admin configuration and profile modifications."""

    __tablename__ = "reach_out_audit_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    old_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])
