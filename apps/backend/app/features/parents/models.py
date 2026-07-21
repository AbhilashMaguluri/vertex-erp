import uuid
from datetime import date
from typing import Optional
from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.shared.models.base import TimestampMixin
from app.core.enums import CommunicationMode, CommunicationOutcome


class ParentCommunication(Base, TimestampMixin):
    __tablename__ = "parent_communications"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    counsellor_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    communication_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    communication_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mode: Mapped[str] = mapped_column(String(30), default=CommunicationMode.PHONE_CALL.value, nullable=False)
    
    parent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    relation: Mapped[str] = mapped_column(String(50), nullable=False)  # Father, Mother, Guardian
    contact_number: Mapped[str] = mapped_column(String(20), nullable=False)
    
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    concerns: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    outcome: Mapped[str] = mapped_column(String(30), default=CommunicationOutcome.POSITIVE.value, nullable=False)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
