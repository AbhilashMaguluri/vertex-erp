"""Wire contracts for the student self-service profile.

The *Update schemas below are the write surface. They are deliberately narrow:
no update schema anywhere in this file contains roll_number, department,
semester, batch, CGPA, SGPA, attendance, backlogs, risk_level or counsellor —
so there is no request body a student can construct that reaches an
institution-owned field, regardless of what they put in the JSON.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.enums import AdmissionType, ExtracurricularActivity, SupportArea


# --------------------------------------------------------------------------
# Shared validators
# --------------------------------------------------------------------------

def _strip_or_none(v: Optional[str]) -> Optional[str]:
    """Treat a cleared form field ("" or whitespace) as NULL, so clearing a
    value in the UI actually clears it instead of storing an empty string that
    then counts as "filled in" for profile completion."""
    if v is None:
        return None
    v = v.strip()
    return v or None


class _StrippedModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        if isinstance(v, str):
            return _strip_or_none(v)
        return v


# --------------------------------------------------------------------------
# Personal
# --------------------------------------------------------------------------

BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
GENDERS = {"MALE", "FEMALE", "OTHER"}


def _clean_tag_list(v: Optional[List[str]], limit: int = 60) -> Optional[List[str]]:
    """De-duplicate case-insensitively, preserving entry order and first-seen
    casing, and cap the list so one student can't store megabytes of tags."""
    if v is None:
        return None
    seen, out = set(), []
    for tag in v:
        tag = (tag or "").strip()
        if not tag or tag.lower() in seen:
            continue
        seen.add(tag.lower())
        out.append(tag[:60])
    if len(out) > limit:
        raise ValueError(f"At most {limit} entries are allowed in a single list")
    return out


def _validate_vocabulary(values: Optional[List[str]], allowed: set, label: str) -> Optional[List[str]]:
    """Closed vocabularies are checked here rather than in the UI alone: these
    lists are filtered on by staff views, so an unrecognised member would
    quietly drop a student out of a caseload query."""
    if values is None:
        return None
    out = []
    for raw in values:
        item = (raw or "").strip().upper()
        if not item:
            continue
        if item not in allowed:
            raise ValueError(f"'{raw}' is not a valid {label}. Allowed: {', '.join(sorted(allowed))}")
        if item not in out:
            out.append(item)
    return out


class PersonalInfoUpdate(_StrippedModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    aadhaar_number: Optional[str] = Field(None, max_length=20)
    nationality: Optional[str] = Field(None, max_length=60)
    category: Optional[str] = Field(None, max_length=40)
    religion: Optional[str] = Field(None, max_length=60)
    mother_tongue: Optional[str] = Field(None, max_length=60)
    languages_known: Optional[List[str]] = None
    photo_url: Optional[str] = Field(None, max_length=500)

    @field_validator("languages_known")
    @classmethod
    def clean_languages(cls, v):
        return _clean_tag_list(v, limit=20)

    @field_validator("gender")
    @classmethod
    def valid_gender(cls, v):
        if v and v.upper() not in GENDERS:
            raise ValueError(f"Gender must be one of: {', '.join(sorted(GENDERS))}")
        return v.upper() if v else v

    @field_validator("blood_group")
    @classmethod
    def valid_blood_group(cls, v):
        if v and v.upper() not in BLOOD_GROUPS:
            raise ValueError(f"Blood group must be one of: {', '.join(sorted(BLOOD_GROUPS))}")
        return v.upper() if v else v

    @field_validator("aadhaar_number")
    @classmethod
    def valid_aadhaar(cls, v):
        if v and (not v.isdigit() or len(v) != 12):
            raise ValueError("Aadhaar number must be exactly 12 digits")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def dob_in_past(cls, v):
        if v and v >= date.today():
            raise ValueError("Date of birth must be in the past")
        return v


# --------------------------------------------------------------------------
# Family
# --------------------------------------------------------------------------

class FamilyInfoUpdate(_StrippedModel):
    father_name: Optional[str] = Field(None, max_length=100)
    father_occupation: Optional[str] = Field(None, max_length=100)
    father_qualification: Optional[str] = Field(None, max_length=100)
    father_phone: Optional[str] = Field(None, max_length=20)
    father_email: Optional[EmailStr] = None

    mother_name: Optional[str] = Field(None, max_length=100)
    mother_occupation: Optional[str] = Field(None, max_length=100)
    mother_qualification: Optional[str] = Field(None, max_length=100)
    mother_phone: Optional[str] = Field(None, max_length=20)
    mother_email: Optional[EmailStr] = None

    guardian_name: Optional[str] = Field(None, max_length=100)
    guardian_relation: Optional[str] = Field(None, max_length=50)
    guardian_phone: Optional[str] = Field(None, max_length=20)
    guardian_email: Optional[EmailStr] = None
    guardian_address: Optional[str] = None

    annual_family_income: Optional[Decimal] = Field(None, ge=0, le=Decimal("999999999999"))


# --------------------------------------------------------------------------
# Contact
# --------------------------------------------------------------------------

class ContactInfoUpdate(_StrippedModel):
    mobile_number: Optional[str] = Field(None, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    personal_email: Optional[EmailStr] = None

    # Current address
    current_address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pin_code: Optional[str] = Field(None, max_length=12)

    # Permanent address
    permanent_address: Optional[str] = None
    permanent_city: Optional[str] = Field(None, max_length=100)
    permanent_district: Optional[str] = Field(None, max_length=100)
    permanent_state: Optional[str] = Field(None, max_length=100)
    permanent_pin_code: Optional[str] = Field(None, max_length=12)
    permanent_same_as_current: Optional[bool] = None

    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)

    @field_validator("pin_code", "permanent_pin_code")
    @classmethod
    def valid_pin(cls, v):
        if v and (not v.isdigit() or len(v) != 6):
            raise ValueError("PIN code must be exactly 6 digits")
        return v

    @field_validator("mobile_number", "alternate_phone", "emergency_contact_phone")
    @classmethod
    def valid_phone(cls, v):
        if v:
            digits = v.lstrip("+").replace(" ", "").replace("-", "")
            if not digits.isdigit() or not (7 <= len(digits) <= 15):
                raise ValueError("Enter a valid phone number")
        return v


# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------

class HealthInfoUpdate(_StrippedModel):
    """Student-authored health information. Its own endpoint and schema so the
    consent rule that governs it stays visible: staff read this only when the
    student has left share_contact_with_counsellor on."""

    medical_conditions: Optional[str] = Field(None, max_length=2000)
    allergies: Optional[str] = Field(None, max_length=2000)
    disability: Optional[str] = Field(None, max_length=2000)
    current_medications: Optional[str] = Field(None, max_length=2000)
    health_notes: Optional[str] = Field(None, max_length=2000)


# --------------------------------------------------------------------------
# Extracurricular
# --------------------------------------------------------------------------

class ExtracurricularUpdate(_StrippedModel):
    activities: Optional[List[str]] = None
    extracurricular_other: Optional[str] = Field(None, max_length=255)
    extracurricular_achievements: Optional[str] = Field(None, max_length=4000)

    @field_validator("activities")
    @classmethod
    def valid_activities(cls, v):
        return _validate_vocabulary(
            v, {a.value for a in ExtracurricularActivity}, "activity"
        )


# --------------------------------------------------------------------------
# Skills & goals
# --------------------------------------------------------------------------

class SkillsGoalsUpdate(_StrippedModel):
    technical_skills: Optional[List[str]] = None
    programming_languages: Optional[List[str]] = None
    soft_skills: Optional[List[str]] = None
    tools_technologies: Optional[List[str]] = None
    other_skills: Optional[List[str]] = None
    hobbies: Optional[List[str]] = None
    interests: Optional[List[str]] = None

    career_goal: Optional[str] = None
    higher_studies_goal: Optional[str] = None
    dream_company: Optional[str] = Field(None, max_length=150)
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    areas_to_improve: Optional[str] = None
    self_introduction: Optional[str] = Field(None, max_length=4000)

    support_areas: Optional[List[str]] = None
    support_areas_other: Optional[str] = Field(None, max_length=255)

    linkedin_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    portfolio_url: Optional[str] = Field(None, max_length=500)
    leetcode_url: Optional[str] = Field(None, max_length=500)
    codechef_url: Optional[str] = Field(None, max_length=500)
    hackerrank_url: Optional[str] = Field(None, max_length=500)
    codeforces_url: Optional[str] = Field(None, max_length=500)
    other_coding_url: Optional[str] = Field(None, max_length=500)
    resume_url: Optional[str] = Field(None, max_length=500)

    @field_validator(
        "linkedin_url", "github_url", "portfolio_url",
        "leetcode_url", "codechef_url", "hackerrank_url",
        "codeforces_url", "other_coding_url", "resume_url",
    )
    @classmethod
    def valid_url(cls, v):
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Links must start with http:// or https://")
        return v

    @field_validator(
        "technical_skills", "programming_languages", "soft_skills",
        "tools_technologies", "other_skills", "hobbies", "interests",
    )
    @classmethod
    def clean_tags(cls, v):
        return _clean_tag_list(v)

    @field_validator("support_areas")
    @classmethod
    def valid_support_areas(cls, v):
        return _validate_vocabulary(v, {a.value for a in SupportArea}, "support area")


# --------------------------------------------------------------------------
# Institution-owned academic record (ADMIN write only)
# --------------------------------------------------------------------------

class AcademicRecordUpdate(_StrippedModel):
    """ERP-sourced facts. This schema is reachable ONLY from the admin route —
    it is deliberately absent from every /me/... endpoint, so no request a
    student can construct reaches an admission number or an entrance rank."""

    admission_number: Optional[str] = Field(None, max_length=50)
    admission_date: Optional[date] = None
    admission_type: Optional[str] = None
    abc_id: Optional[str] = Field(None, max_length=30)
    joining_year: Optional[int] = Field(None, ge=1950, le=2100)
    academic_year: Optional[str] = Field(None, max_length=20)

    ssc_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    intermediate_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    eamcet_rank: Optional[int] = Field(None, ge=1)
    jee_rank: Optional[int] = Field(None, ge=1)

    scholarship_name: Optional[str] = Field(None, max_length=150)
    scholarship_status: Optional[str] = Field(None, max_length=100)
    fee_reimbursement_status: Optional[str] = Field(None, max_length=60)
    placement_status: Optional[str] = Field(None, max_length=50)
    total_credits_required: Optional[int] = Field(None, ge=0, le=500)

    assigned_mentor_id: Optional[str] = None
    faculty_advisor_id: Optional[str] = None

    @field_validator("admission_type")
    @classmethod
    def valid_admission_type(cls, v):
        if v is None:
            return None
        value = v.strip().upper()
        allowed = {t.value for t in AdmissionType}
        if value not in allowed:
            raise ValueError(f"Admission type must be one of: {', '.join(sorted(allowed))}")
        return value


class PreferencesUpdate(BaseModel):
    notification_preferences: Optional[dict] = None
    share_contact_with_counsellor: Optional[bool] = None


# --------------------------------------------------------------------------
# Collections
# --------------------------------------------------------------------------

class InternshipBase(_StrippedModel):
    company: str = Field(..., min_length=1, max_length=150)
    role: str = Field(..., min_length=1, max_length=150)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration: Optional[str] = Field(None, max_length=60)
    stipend: Optional[Decimal] = Field(None, ge=0)
    technologies: Optional[List[str]] = None
    description: Optional[str] = None
    status: str = "COMPLETED"
    certificate_document_id: Optional[str] = None


class InternshipCreate(InternshipBase):
    pass


class InternshipUpdate(InternshipBase):
    company: Optional[str] = Field(None, min_length=1, max_length=150)
    role: Optional[str] = Field(None, min_length=1, max_length=150)
    status: Optional[str] = None


class InternshipResponse(BaseModel):
    id: str
    student_id: str
    company: str
    role: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration: Optional[str] = None
    stipend: Optional[Decimal] = None
    technologies: Optional[List[str]] = None
    description: Optional[str] = None
    status: str
    certificate_document_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewBase(_StrippedModel):
    company: str = Field(..., min_length=1, max_length=150)
    role: str = Field(..., min_length=1, max_length=150)
    interview_date: Optional[date] = None
    interview_type: Optional[str] = Field(None, max_length=40)
    round_name: Optional[str] = Field(None, max_length=100)
    result: str = "PENDING"
    feedback: Optional[str] = None
    notes: Optional[str] = None
    package_offered: Optional[Decimal] = Field(None, ge=0)
    offer_document_id: Optional[str] = None


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(InterviewBase):
    company: Optional[str] = Field(None, min_length=1, max_length=150)
    role: Optional[str] = Field(None, min_length=1, max_length=150)
    result: Optional[str] = None


class CounsellorObservationUpdate(BaseModel):
    """Staff-only write on an interview. Kept a separate schema from
    InterviewUpdate so the student's own update path has no field that could
    set it."""

    counsellor_observation: str = Field(..., min_length=1, max_length=5000)


class InterviewResponse(BaseModel):
    id: str
    student_id: str
    company: str
    role: str
    interview_date: Optional[date] = None
    interview_type: Optional[str] = None
    round_name: Optional[str] = None
    result: str
    feedback: Optional[str] = None
    notes: Optional[str] = None
    package_offered: Optional[Decimal] = None
    counsellor_observation: Optional[str] = None
    counsellor_observed_by_name: Optional[str] = None
    counsellor_observed_at: Optional[datetime] = None
    offer_document_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AchievementBase(_StrippedModel):
    category: str = "OTHER"
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    issuer: Optional[str] = Field(None, max_length=150)
    achieved_on: Optional[date] = None
    position: Optional[str] = Field(None, max_length=100)
    credential_url: Optional[str] = Field(None, max_length=500)
    proof_document_id: Optional[str] = None


class AchievementCreate(AchievementBase):
    pass


class AchievementUpdate(AchievementBase):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = None


class AchievementResponse(BaseModel):
    id: str
    student_id: str
    category: str
    title: str
    description: Optional[str] = None
    issuer: Optional[str] = None
    achieved_on: Optional[date] = None
    position: Optional[str] = None
    credential_url: Optional[str] = None
    proof_document_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    student_id: str
    document_type: str
    title: Optional[str] = None
    original_filename: str
    stored_filename: Optional[str] = None
    file_url: Optional[str] = None
    content_type: str
    size_bytes: int
    version: int = 1
    verification_status: str = "PENDING"
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    uploaded_by_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CertificationSchema(BaseModel):
    id: str
    student_id: str
    name: str
    issuing_organization: str
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None

    class Config:
        from_attributes = True


class CertificationCreate(_StrippedModel):
    name: str = Field(..., min_length=1, max_length=200)
    issuing_organization: str = Field(..., min_length=1, max_length=150)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class SkillSchema(BaseModel):
    id: str
    student_id: str
    skill_name: str
    skill_type: str = "TECHNICAL"
    proficiency_level: str = "INTERMEDIATE"

    class Config:
        from_attributes = True


class SkillCreate(_StrippedModel):
    skill_name: str = Field(..., min_length=1, max_length=100)
    skill_type: str = "TECHNICAL"
    proficiency_level: str = "INTERMEDIATE"


class ResearchPaperSchema(BaseModel):
    id: str
    student_id: str
    title: str
    journal_conference_name: str
    publication_date: Optional[date] = None
    doi_or_url: Optional[str] = None
    authors_list: Optional[List[str]] = None
    status: str = "PUBLISHED"

    class Config:
        from_attributes = True


class ResearchPaperCreate(_StrippedModel):
    title: str = Field(..., min_length=1, max_length=255)
    journal_conference_name: str = Field(..., min_length=1, max_length=200)
    publication_date: Optional[date] = None
    doi_or_url: Optional[str] = None
    authors_list: Optional[List[str]] = None
    status: str = "PUBLISHED"


class CompetitionSchema(BaseModel):
    id: str
    student_id: str
    event_name: str
    organizer: Optional[str] = None
    event_date: Optional[date] = None
    position_rank: Optional[str] = None
    project_title: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class CompetitionCreate(_StrippedModel):
    event_name: str = Field(..., min_length=1, max_length=200)
    organizer: Optional[str] = None
    event_date: Optional[date] = None
    position_rank: Optional[str] = None
    project_title: Optional[str] = None
    description: Optional[str] = None


class ClubSchema(BaseModel):
    id: str
    student_id: str
    club_name: str
    role: str = "MEMBER"
    joined_date: Optional[date] = None
    active_status: bool = True

    class Config:
        from_attributes = True


class ClubCreate(_StrippedModel):
    club_name: str = Field(..., min_length=1, max_length=150)
    role: str = "MEMBER"
    joined_date: Optional[date] = None
    active_status: bool = True


class ProfileAuditLogResponse(BaseModel):
    id: str
    student_id: str
    actor_id: str
    actor_name: str
    source: str
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# Aggregate profile
# --------------------------------------------------------------------------

class ReadOnlyAcademicIdentity(BaseModel):
    """Institution-owned facts, surfaced on the profile page for context and
    explicitly rendered read-only. Nothing here appears in any update schema."""

    student_id: str
    roll_number: str
    registration_number: str
    full_name: str
    college_email: str
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    program: Optional[str] = None
    branch: Optional[str] = None
    section_name: Optional[str] = None
    study_year: Optional[int] = None
    semester_name: Optional[str] = None
    semester_number: Optional[int] = None
    batch_year: int
    admission_year: Optional[int] = None
    status: str
    risk_level: str
    counsellor_name: Optional[str] = None
    mentor_name: Optional[str] = None


class AcademicRecordBlock(BaseModel):
    """Section 2 of the workspace: ERP-owned, read-only for the student.

    Marks, attendance and semester results are NOT duplicated here — they are
    served by the academics and attendance modules, which are the systems of
    record for them. This block carries only the admission-time and
    scholarship facts that live on the profile row."""

    admission_number: Optional[str] = None
    admission_date: Optional[date] = None
    admission_type: Optional[str] = None
    abc_id: Optional[str] = None
    joining_year: Optional[int] = None
    academic_year: Optional[str] = None

    ssc_percentage: Optional[Decimal] = None
    intermediate_percentage: Optional[Decimal] = None
    eamcet_rank: Optional[int] = None
    jee_rank: Optional[int] = None

    scholarship_name: Optional[str] = None
    scholarship_status: Optional[str] = None
    fee_reimbursement_status: Optional[str] = None
    placement_status: Optional[str] = None
    total_credits_required: Optional[int] = None


class ProfileCompletionSection(BaseModel):
    key: str
    label: str
    completed_fields: int
    total_fields: int
    percentage: int
    missing: List[str] = []


class ProfileCompletion(BaseModel):
    percentage: int
    completed_fields: int
    total_fields: int
    sections: List[ProfileCompletionSection] = []
    # Flat list of the highest-value gaps, for the dashboard prompt.
    top_missing: List[str] = []


class StudentSelfProfileResponse(BaseModel):
    identity: ReadOnlyAcademicIdentity

    # Personal (first/last name, dob live on the user/student records)
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    photo_url: Optional[str] = None

    preferred_name: Optional[str] = None
    blood_group: Optional[str] = None
    aadhaar_number: Optional[str] = None
    nationality: Optional[str] = None
    category: Optional[str] = None
    religion: Optional[str] = None
    mother_tongue: Optional[str] = None
    languages_known: Optional[List[str]] = None
    self_introduction: Optional[str] = None

    support_areas: Optional[List[str]] = None
    support_areas_other: Optional[str] = None

    father_name: Optional[str] = None
    father_occupation: Optional[str] = None
    father_qualification: Optional[str] = None
    father_phone: Optional[str] = None
    father_email: Optional[str] = None
    mother_name: Optional[str] = None
    mother_occupation: Optional[str] = None
    mother_qualification: Optional[str] = None
    mother_phone: Optional[str] = None
    mother_email: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_relation: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[str] = None
    guardian_address: Optional[str] = None
    annual_family_income: Optional[Decimal] = None

    mobile_number: Optional[str] = None
    alternate_phone: Optional[str] = None
    personal_email: Optional[str] = None
    current_address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    permanent_address: Optional[str] = None
    permanent_city: Optional[str] = None
    permanent_district: Optional[str] = None
    permanent_state: Optional[str] = None
    permanent_pin_code: Optional[str] = None
    permanent_same_as_current: bool = False
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    hostel_type: Optional[str] = None
    hostel_name: Optional[str] = None
    hostel_block: Optional[str] = None
    hostel_floor: Optional[str] = None
    hostel_room_number: Optional[str] = None
    preferred_communication_method: Optional[str] = None
    preferred_call_time: Optional[str] = None

    career_goal: Optional[str] = None
    higher_studies_goal: Optional[str] = None
    dream_company: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    areas_to_improve: Optional[str] = None

    technical_skills: Optional[List[str]] = None
    programming_languages: Optional[List[str]] = None
    soft_skills: Optional[List[str]] = None
    tools_technologies: Optional[List[str]] = None
    other_skills: Optional[List[str]] = None
    hobbies: Optional[List[str]] = None
    interests: Optional[List[str]] = None

    extracurricular_activities: Optional[List[str]] = None
    extracurricular_other: Optional[str] = None
    extracurricular_achievements: Optional[str] = None

    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    disability: Optional[str] = None
    current_medications: Optional[str] = None
    health_notes: Optional[str] = None

    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    codechef_url: Optional[str] = None
    hackerrank_url: Optional[str] = None
    codeforces_url: Optional[str] = None
    other_coding_url: Optional[str] = None
    resume_url: Optional[str] = None

    notification_preferences: Optional[dict] = None
    share_contact_with_counsellor: bool = True

    academic: AcademicRecordBlock = AcademicRecordBlock()
    completion: ProfileCompletion


# --------------------------------------------------------------------------
# Counsellor section — read-only for the student
# --------------------------------------------------------------------------

class CounsellingNoteEntry(BaseModel):
    """One counselling session as the STUDENT is allowed to see it.

    `confidential_notes` has no field here at all. The counselling module
    strips it for student callers; leaving it out of the schema as well means
    a regression there still cannot leak it through this endpoint."""

    session_id: str
    session_date: date
    session_type: str
    mode: str
    counsellor_name: Optional[str] = None
    observations: str
    recommendations: Optional[str] = None
    student_commitments: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    student_acknowledged: bool = False


class CounsellingActionItemEntry(BaseModel):
    id: str
    description: str
    due_date: Optional[date] = None
    status: str
    is_overdue: bool = False
    session_date: Optional[date] = None


class ParentInteractionEntry(BaseModel):
    """A parent conversation, as shown to the student.

    Carries what was discussed and what the student is expected to do. It
    deliberately omits the counsellor's `concerns` field and the parent's
    contact number: the first is a private staff assessment of the family, the
    second has no purpose in the student's own view."""

    id: str
    communication_date: date
    mode: str
    parent_name: str
    relation: str
    summary: str
    action_items: Optional[str] = None
    outcome: str
    follow_up_date: Optional[date] = None


class StudentCounsellingSummary(BaseModel):
    risk_level: str
    counsellor_name: Optional[str] = None
    mentor_name: Optional[str] = None
    total_sessions: int = 0
    last_session_date: Optional[date] = None
    follow_up_required: bool = False
    notes: List[CounsellingNoteEntry] = []
    action_items: List[CounsellingActionItemEntry] = []
    parent_interactions: List[ParentInteractionEntry] = []
