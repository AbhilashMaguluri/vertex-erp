import uuid
from datetime import date, datetime
from typing import Any, List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.shared.models.base import TimestampMixin
from app.core.enums import (
    AchievementCategory,
    DocumentType,
    InternshipStatus,
    InterviewResult,
)


class StudentProfile(Base, TimestampMixin):
    """One row per student — master profile details & student-maintained preferences."""

    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # ---------------- Personal ----------------
    preferred_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    blood_group: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    aadhaar_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    religion: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    mother_tongue: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    languages_known: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    self_introduction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ---------------- Support needs ----------------
    # A closed vocabulary (core.enums.SupportArea) plus one free-text slot, so
    # the counsellor's caseload view can filter on it.
    support_areas: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    support_areas_other: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ---------------- Residence ----------------
    hostel_type: Mapped[Optional[str]] = mapped_column(String(30), default="DAY_SCHOLAR", nullable=True)
    hostel_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hostel_block: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hostel_floor: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    hostel_room_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # ---------------- Family ----------------
    father_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    father_occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    father_qualification: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    father_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    father_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    mother_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mother_occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mother_qualification: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mother_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mother_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    guardian_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    guardian_relation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    guardian_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    guardian_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    guardian_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    annual_family_income: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)

    # ---------------- Contact ----------------
    # Addresses are two parallel blocks. `current_address` / `city` / `state` /
    # `pin_code` are the CURRENT address (they predate the permanent block and
    # every existing caller reads them as "where the student lives now"), so
    # the permanent side gets its own city/district/state/pin rather than
    # renaming columns other features already query.
    mobile_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    alternate_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    personal_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pin_code: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)

    permanent_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    permanent_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    permanent_district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    permanent_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    permanent_pin_code: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    # Remembered so the "same as current" checkbox survives a reload. The
    # permanent columns are still written out in full — a later edit to the
    # current address must not silently rewrite history on the permanent one.
    permanent_same_as_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    emergency_contact_relation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preferred_communication_method: Mapped[Optional[str]] = mapped_column(String(50), default="WhatsApp", nullable=True)
    preferred_call_time: Mapped[Optional[str]] = mapped_column(String(100), default="Evening 5:00 PM - 7:00 PM", nullable=True)

    # ---------------- Master Assignments & Enrollment ----------------
    assigned_mentor_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    faculty_advisor_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    admission_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    admission_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    placement_status: Mapped[Optional[str]] = mapped_column(String(50), default="SEEKING", nullable=True)
    scholarship_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ---------------- Career & Goals ----------------
    career_goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    higher_studies_goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dream_company: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    areas_to_improve: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ---------------- Skills ----------------
    # Tag lists rather than one "any other skills" blob, so the counsellor can
    # search a caseload for "who knows Python".
    programming_languages: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    technical_skills: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    soft_skills: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    tools_technologies: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    other_skills: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    hobbies: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    interests: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)

    # ---------------- Extracurricular ----------------
    extracurricular_activities: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    extracurricular_other: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extracurricular_achievements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ---------------- Health ----------------
    # Health data is the most sensitive block on the profile: it is written by
    # the student, read by the student, and released to staff only through the
    # same share_contact_with_counsellor consent gate as personal contact
    # details (see profile_router).
    medical_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    disability: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_medications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    health_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ---------------- Portfolio links ----------------
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    leetcode_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    codechef_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hackerrank_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    codeforces_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    other_coding_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    resume_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ---------------- Institution-owned academic record ----------------
    # ERP-sourced. Present on this table for convenience of joins, but no
    # student-facing update schema names any of them — they are writable only
    # through the ADMIN endpoint (see profile_router.admin_update_academic).
    abc_id: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    admission_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    joining_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    academic_year: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ssc_percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    intermediate_percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    eamcet_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    jee_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scholarship_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    fee_reimbursement_status: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    # Credits the programme requires in total, so "credits remaining" is a
    # subtraction against a real number instead of an assumed 160.
    total_credits_required: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ---------------- Preferences ----------------
    notification_preferences: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    share_contact_with_counsellor: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# ---------------- Relational Entities ----------------

class StudentCertification(Base, TimestampMixin):
    """Relational table for certifications earned by student."""
    __tablename__ = "student_certifications"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuing_organization: Mapped[str] = mapped_column(String(150), nullable=False)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    credential_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    credential_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class StudentSkill(Base, TimestampMixin):
    """Relational table for skills."""
    __tablename__ = "student_skills"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    skill_type: Mapped[str] = mapped_column(String(40), default="TECHNICAL", nullable=False)  # TECHNICAL, SOFT, LANGUAGE
    proficiency_level: Mapped[str] = mapped_column(String(30), default="INTERMEDIATE", nullable=False)  # BEGINNER, INTERMEDIATE, ADVANCED, EXPERT


class StudentResearchPaper(Base, TimestampMixin):
    """Relational table for publications."""
    __tablename__ = "student_research_papers"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    journal_conference_name: Mapped[str] = mapped_column(String(200), nullable=False)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    doi_or_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    authors_list: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="PUBLISHED", nullable=False)


class StudentCompetition(Base, TimestampMixin):
    """Relational table for hackathons and competitions."""
    __tablename__ = "student_competitions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_name: Mapped[str] = mapped_column(String(200), nullable=False)
    organizer: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    event_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    position_rank: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    project_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class StudentClub(Base, TimestampMixin):
    """Relational table for extracurricular clubs."""
    __tablename__ = "student_clubs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    club_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(80), default="MEMBER", nullable=False)
    joined_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    active_status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class StudentInternship(Base, TimestampMixin):
    __tablename__ = "student_internships"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(150), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    stipend: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    technologies: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default=InternshipStatus.COMPLETED.value, nullable=False
    )
    certificate_document_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_documents.id", ondelete="SET NULL"), nullable=True
    )


class StudentInterview(Base, TimestampMixin):
    __tablename__ = "student_interviews"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(150), nullable=False)
    interview_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    interview_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    round_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    result: Mapped[str] = mapped_column(
        String(30), default=InterviewResult.PENDING.value, nullable=False, index=True
    )
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    package_offered: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    counsellor_observation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    counsellor_observed_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    counsellor_observed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    offer_document_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_documents.id", ondelete="SET NULL"), nullable=True
    )


class StudentAchievement(Base, TimestampMixin):
    __tablename__ = "student_achievements"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(
        String(40), default=AchievementCategory.OTHER.value, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issuer: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    achieved_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    credential_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    proof_document_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_documents.id", ondelete="SET NULL"), nullable=True
    )


class StudentDocument(Base, TimestampMixin):
    """Document metadata table holding verification status, versioning, and storage keys."""

    __tablename__ = "student_documents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(
        String(40), default=DocumentType.OTHER.value, nullable=False, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Verification workflow: PENDING, VERIFIED, REJECTED
    verification_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    verified_by_user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    uploaded_by_user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class StudentAssignmentHistory(Base, TimestampMixin):
    """Historical log tracking counsellor, mentor, section, and address reassignments."""
    __tablename__ = "student_assignment_histories"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)  # COUNSELLOR, MENTOR, SECTION, ADDRESS, STATUS
    previous_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )


class StudentProfileAuditLog(Base, TimestampMixin):
    """Audit log for student profile modifications."""
    __tablename__ = "student_profile_audit_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(30), default="STUDENT", nullable=False)  # STUDENT, ADMIN, COUNSELLOR
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    device_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
