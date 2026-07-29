import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.shared.models.base import TimestampMixin
from app.core.enums import SessionType, SessionMode, RiskLevel, FollowUpStatus


class CounsellingSession(Base, TimestampMixin):
    __tablename__ = "counselling_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    counsellor_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    session_type: Mapped[str] = mapped_column(String(50), default=SessionType.ACADEMIC.value, nullable=False)
    mode: Mapped[str] = mapped_column(String(50), default=SessionMode.IN_PERSON.value, nullable=False)
    
    observations: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    student_commitments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Counsellor/Admin-only narrative. Distinct from `confidential` (which
    # marks the WHOLE session sensitive): these notes are stripped from every
    # student-facing response unconditionally — see
    # CounsellingService._to_response.
    confidential_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    student_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    risk_assessment: Mapped[Optional[str]] = mapped_column(String(30), default=RiskLevel.NONE.value, nullable=True)
    confidential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    action_items: Mapped[List["SessionActionItem"]] = relationship("SessionActionItem", back_populates="session", cascade="all, delete-orphan")


class SessionActionItem(Base, TimestampMixin):
    __tablename__ = "session_action_items"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("counselling_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default=FollowUpStatus.PENDING.value, nullable=False, index=True)
    status_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    assigned_to_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    session: Mapped[CounsellingSession] = relationship("CounsellingSession", back_populates="action_items")
