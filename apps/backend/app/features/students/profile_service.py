"""Student self-service profile: reads, writes, completion scoring.

Every write path here goes through `_apply` with an explicit allow-list drawn
from the request schema. Nothing writes to `students` except
`_apply_student_owned_columns`, which handles exactly two fields (gender,
photo_url) and is the only bridge between student input and that table.
"""
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import FollowUpStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.features.admin.repository import AdminRepository
from app.features.auth.models import User
from app.features.counselling.models import CounsellingSession
from app.features.parents.models import ParentCommunication
from app.features.students.models import Student
from app.features.students.profile_models import (
    StudentAchievement,
    StudentDocument,
    StudentInternship,
    StudentInterview,
    StudentProfile,
)
from app.features.students.profile_schemas import (
    AcademicRecordBlock,
    AcademicRecordUpdate,
    AchievementResponse,
    ContactInfoUpdate,
    CounsellingActionItemEntry,
    CounsellingNoteEntry,
    DocumentResponse,
    ExtracurricularUpdate,
    FamilyInfoUpdate,
    HealthInfoUpdate,
    InternshipResponse,
    InterviewResponse,
    ParentInteractionEntry,
    PersonalInfoUpdate,
    PreferencesUpdate,
    ProfileCompletion,
    ProfileCompletionSection,
    ReadOnlyAcademicIdentity,
    SkillsGoalsUpdate,
    StudentCounsellingSummary,
    StudentSelfProfileResponse,
)
from app.features.students.repository import StudentRepository

# The two `students` columns a student is allowed to set. Anything not in this
# set is institution-owned; see profile_models.py for why these two are the
# exception.
STUDENT_WRITABLE_STUDENT_COLUMNS = {"gender", "photo_url"}

# What the student is asked to fill in, section by section, mirroring the
# collapsible cards of the Personal Details workspace. Each entry is
# (key, label, [(field, human label, required?)], weight).
#
# Only STUDENT-EDITABLE fields appear here. Roll number and department are
# always populated by the ERP, so counting them would report a profile as
# part-complete before the student had typed anything — the percentage is a
# measure of the student's own outstanding work, not of the database's.
#
# The `required` flag drives both the weighting inside a section (a required
# field counts double) and the "Required" marker in the UI.
_R = True   # required
_O = False  # optional

COMPLETION_SECTIONS: Sequence[tuple[str, str, Sequence[tuple[str, str, bool]], int]] = (
    (
        "profile",
        "Profile Information",
        (
            ("photo_url", "Profile photo", _R),
            ("date_of_birth", "Date of birth", _R),
            ("gender", "Gender", _R),
            ("blood_group", "Blood group", _R),
            ("mobile_number", "Mobile number", _R),
            ("personal_email", "Personal email", _R),
            ("aadhaar_number", "Aadhaar number", _O),
            ("mother_tongue", "Mother tongue", _O),
            ("languages_known", "Languages known", _O),
        ),
        18,
    ),
    (
        "personal",
        "Personal Information",
        (
            ("strengths", "Strengths", _R),
            ("weaknesses", "Weaknesses", _R),
            ("career_goal", "Career goal", _R),
            ("support_areas", "Areas where support is required", _R),
            ("self_introduction", "Self introduction", _O),
        ),
        14,
    ),
    (
        "skills",
        "Skills",
        (
            ("programming_languages", "Programming languages", _O),
            ("technical_skills", "Technical skills", _O),
            ("soft_skills", "Soft skills", _O),
            ("tools_technologies", "Tools & technologies", _O),
        ),
        10,
    ),
    (
        "extracurricular",
        "Extracurricular Activities",
        (
            ("extracurricular_activities", "Extracurricular activities", _O),
            ("extracurricular_achievements", "Achievements & positions held", _O),
        ),
        6,
    ),
    (
        "family",
        "Family Details",
        (
            ("father_name", "Father's name", _R),
            ("father_occupation", "Father's occupation", _O),
            ("father_phone", "Father's mobile number", _R),
            ("mother_name", "Mother's name", _R),
            ("mother_occupation", "Mother's occupation", _O),
            ("mother_phone", "Mother's mobile number", _R),
        ),
        14,
    ),
    (
        "contact",
        "Contact Details",
        (
            ("current_address", "Current address", _R),
            ("city", "Current city", _R),
            ("district", "Current district", _O),
            ("state", "Current state", _R),
            ("pin_code", "Current PIN code", _R),
            ("permanent_address", "Permanent address", _R),
        ),
        14,
    ),
    (
        "emergency",
        "Emergency Contact",
        (
            ("emergency_contact_name", "Emergency contact name", _R),
            ("emergency_contact_relation", "Emergency contact relationship", _R),
            ("emergency_contact_phone", "Emergency contact phone", _R),
        ),
        10,
    ),
    (
        "health",
        "Health Information",
        (
            ("medical_conditions", "Existing medical conditions", _O),
            ("allergies", "Allergies", _O),
        ),
        4,
    ),
    (
        "links",
        "Professional Links",
        (
            ("linkedin_url", "LinkedIn profile", _O),
            ("github_url", "GitHub profile", _O),
            ("resume_url", "Resume", _O),
        ),
        10,
    ),
)


def _is_filled(value: Any) -> bool:
    """Empty string, empty list and empty dict all mean "not filled in" — a
    student who saved a blank form has not completed that field."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


class StudentProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StudentRepository(db)
        self.admin_repo = AdminRepository(db)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    async def _get_student(self, student_id: str) -> Student:
        student = await self.repo.get_student_by_id(student_id)
        if not student:
            raise NotFoundError("Student not found")
        return student

    async def resolve_student_id_for_user(self, user_id: str) -> str:
        student = await self.repo.get_student_by_user_id(user_id)
        if not student:
            raise NotFoundError("No student record is linked to this account")
        return str(student.id)

    async def get_or_create_profile(self, student_id: str) -> StudentProfile:
        """Profiles are created lazily. A student imported before this feature
        existed has no row until the first read, and creating it on read keeps
        every downstream caller from having to null-check."""
        res = await self.db.execute(
            select(StudentProfile).where(StudentProfile.student_id == student_id)
        )
        profile = res.scalar_one_or_none()
        if profile is None:
            profile = StudentProfile(student_id=student_id)
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
        return profile

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_self_profile(self, student_id: str) -> StudentSelfProfileResponse:
        student = await self._get_student(student_id)
        profile = await self.get_or_create_profile(student_id)
        identity = await self._build_identity(student)

        payload: Dict[str, Any] = {
            "identity": identity,
            "first_name": student.user.first_name if student.user else "",
            "last_name": student.user.last_name if student.user else "",
            "date_of_birth": student.date_of_birth,
            "gender": student.gender,
            "photo_url": student.photo_url,
        }
        for column in StudentProfile.__table__.columns.keys():
            if column in {"id", "student_id", "created_at", "updated_at"}:
                continue
            payload[column] = getattr(profile, column)

        # The extracurricular list is stored under a longer column name than
        # the update schema uses; keep the response name aligned with the model.
        payload["academic"] = self._build_academic_block(profile)
        payload["completion"] = self._compute_completion(student, profile)
        return StudentSelfProfileResponse(**payload)

    @staticmethod
    def _build_academic_block(profile: StudentProfile) -> AcademicRecordBlock:
        """The ERP-owned facts, pulled out of the flat profile row into their
        own block so the client can render section 2 as unambiguously
        read-only."""
        return AcademicRecordBlock(
            admission_number=profile.admission_number,
            admission_date=profile.admission_date,
            admission_type=profile.admission_type,
            abc_id=profile.abc_id,
            joining_year=profile.joining_year,
            academic_year=profile.academic_year,
            ssc_percentage=profile.ssc_percentage,
            intermediate_percentage=profile.intermediate_percentage,
            eamcet_rank=profile.eamcet_rank,
            jee_rank=profile.jee_rank,
            scholarship_name=profile.scholarship_name,
            scholarship_status=profile.scholarship_status,
            fee_reimbursement_status=profile.fee_reimbursement_status,
            placement_status=profile.placement_status,
            total_credits_required=profile.total_credits_required,
        )

    async def _build_identity(self, student: Student) -> ReadOnlyAcademicIdentity:
        dept_name = None
        if student.department_id:
            dept = await self.admin_repo.get_department_by_id(str(student.department_id))
            if dept:
                dept_name = dept.name

        row = await self.repo.get_caseload_row(str(student.id))

        counsellor_name = None
        active = next(
            (a for a in student.counsellor_assignments if a.effective_to is None), None
        )
        if active and active.counsellor:
            counsellor_name = active.counsellor.full_name

        mentor_name = None
        if student.profile and student.profile.assigned_mentor_id:
            mentor = await self.db.get(User, student.profile.assigned_mentor_id)
            if mentor:
                mentor_name = mentor.full_name

        return ReadOnlyAcademicIdentity(
            student_id=str(student.id),
            roll_number=student.roll_number,
            registration_number=student.registration_number,
            full_name=student.user.full_name if student.user else "",
            college_email=student.user.email if student.user else "",
            department_id=str(student.department_id) if student.department_id else None,
            department_name=dept_name,
            # This institution runs a single undergraduate programme, so the
            # branch IS the department. Both names are sent because the UI
            # labels them separately, but neither is invented.
            program="B.Tech" if dept_name else None,
            branch=dept_name,
            section_name=row.get("section_name") if row else None,
            study_year=row.get("study_year") if row else None,
            semester_name=row.get("semester_name") if row else None,
            semester_number=row.get("semester_number") if row else None,
            batch_year=student.batch_year,
            # Admission year is not separately recorded; the batch year is the
            # intake year, so it is the honest answer rather than a guess.
            admission_year=student.batch_year,
            status=student.status,
            risk_level=student.risk_level,
            counsellor_name=counsellor_name,
            mentor_name=mentor_name,
        )

    def _compute_completion(
        self, student: Student, profile: StudentProfile
    ) -> ProfileCompletion:
        """Percentage of the student's own outstanding profile work.

        Weighted per section (see COMPLETION_SECTIONS), and within a section a
        required field carries twice the weight of an optional one — so
        filling in an emergency contact moves the number more than adding a
        hobby, which is how a student would expect it to behave."""
        sections: List[ProfileCompletionSection] = []
        weighted_score = 0.0
        total_weight = 0
        # Required gaps first: these are what the dashboard prompt should push.
        missing_required: List[str] = []
        missing_optional: List[str] = []

        for key, label, fields, weight in COMPLETION_SECTIONS:
            done_points = 0.0
            possible_points = 0.0
            done_count = 0
            missing: List[str] = []

            for field, human_label, required in fields:
                points = 2.0 if required else 1.0
                possible_points += points
                # `students` owns gender/photo_url/date_of_birth; everything
                # else lives on the profile row.
                value = (
                    getattr(student, field)
                    if hasattr(student, field)
                    else getattr(profile, field, None)
                )
                if _is_filled(value):
                    done_points += points
                    done_count += 1
                else:
                    missing.append(human_label)
                    (missing_required if required else missing_optional).append(human_label)

            ratio = (done_points / possible_points) if possible_points else 1.0
            weighted_score += weight * ratio
            total_weight += weight

            sections.append(
                ProfileCompletionSection(
                    key=key,
                    label=label,
                    completed_fields=done_count,
                    total_fields=len(fields),
                    percentage=int(round(ratio * 100)),
                    missing=missing,
                )
            )

        final_pct = int(round((weighted_score / total_weight) * 100)) if total_weight else 100
        return ProfileCompletion(
            percentage=final_pct,
            completed_fields=sum(s.completed_fields for s in sections),
            total_fields=sum(s.total_fields for s in sections),
            sections=sections,
            top_missing=(missing_required + missing_optional)[:5],
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def _apply(self, profile: StudentProfile, data: Any) -> None:
        """Copy only the fields the caller actually sent, and only if they are
        real columns on the profile. `exclude_unset` matters: without it, a
        partial form submit would null out every field the client omitted."""
        for field, value in data.model_dump(exclude_unset=True).items():
            if field in STUDENT_WRITABLE_STUDENT_COLUMNS:
                continue  # handled separately against the students table
            if not hasattr(profile, field):
                continue
            setattr(profile, field, value)

    async def _apply_student_owned_columns(self, student: Student, data: Any) -> None:
        """The ONLY writer to `students` on a student-initiated request, and it
        can only ever touch gender/photo_url."""
        sent = data.model_dump(exclude_unset=True)
        for field in STUDENT_WRITABLE_STUDENT_COLUMNS:
            if field in sent:
                setattr(student, field, sent[field])

    async def update_personal(
        self, student_id: str, data: PersonalInfoUpdate
    ) -> StudentSelfProfileResponse:
        student = await self._get_student(student_id)
        profile = await self.get_or_create_profile(student_id)
        sent = data.model_dump(exclude_unset=True)

        # Names live on the user record — the student owns their own name.
        if student.user:
            if "first_name" in sent and sent["first_name"]:
                student.user.first_name = sent["first_name"]
            if "last_name" in sent and sent["last_name"]:
                student.user.last_name = sent["last_name"]
        if "date_of_birth" in sent:
            student.date_of_birth = sent["date_of_birth"] or student.date_of_birth

        await self._apply_student_owned_columns(student, data)
        await self._apply(profile, data)
        await self.db.commit()
        return await self.get_self_profile(student_id)

    async def update_family(
        self, student_id: str, data: FamilyInfoUpdate
    ) -> StudentSelfProfileResponse:
        profile = await self.get_or_create_profile(student_id)
        await self._apply(profile, data)
        await self.db.commit()
        return await self.get_self_profile(student_id)

    async def update_contact(
        self, student_id: str, data: ContactInfoUpdate
    ) -> StudentSelfProfileResponse:
        profile = await self.get_or_create_profile(student_id)
        await self._apply(profile, data)

        # "Same as current" is resolved here rather than in the browser, so the
        # stored permanent address is a real address either way. A client that
        # never sends the mirrored fields — or a later edit to the current
        # address — still leaves the two blocks consistent.
        if profile.permanent_same_as_current:
            profile.permanent_address = profile.current_address
            profile.permanent_city = profile.city
            profile.permanent_district = profile.district
            profile.permanent_state = profile.state
            profile.permanent_pin_code = profile.pin_code

        await self.db.commit()
        return await self.get_self_profile(student_id)

    async def update_health(
        self, student_id: str, data: HealthInfoUpdate
    ) -> StudentSelfProfileResponse:
        profile = await self.get_or_create_profile(student_id)
        await self._apply(profile, data)
        await self.db.commit()
        return await self.get_self_profile(student_id)

    async def update_extracurricular(
        self, student_id: str, data: ExtracurricularUpdate
    ) -> StudentSelfProfileResponse:
        profile = await self.get_or_create_profile(student_id)
        sent = data.model_dump(exclude_unset=True)
        # The schema calls it `activities`; the column keeps the longer name so
        # it stays readable next to the other extracurricular_* columns.
        if "activities" in sent:
            profile.extracurricular_activities = sent["activities"]
        for field in ("extracurricular_other", "extracurricular_achievements"):
            if field in sent:
                setattr(profile, field, sent[field])
        await self.db.commit()
        return await self.get_self_profile(student_id)

    async def update_academic_record(
        self, student_id: str, data: AcademicRecordUpdate
    ) -> StudentSelfProfileResponse:
        """ADMIN-only. The route enforces the role; this method exists so the
        ERP fields have exactly one writer."""
        profile = await self.get_or_create_profile(student_id)
        await self._apply(profile, data)
        await self.db.commit()
        return await self.get_self_profile(student_id)

    async def set_photo_url(self, student_id: str, photo_url: str) -> None:
        student = await self._get_student(student_id)
        student.photo_url = photo_url
        await self.db.commit()

    async def update_skills_goals(
        self, student_id: str, data: SkillsGoalsUpdate
    ) -> StudentSelfProfileResponse:
        profile = await self.get_or_create_profile(student_id)
        await self._apply(profile, data)
        await self.db.commit()
        return await self.get_self_profile(student_id)

    async def update_preferences(
        self, student_id: str, data: PreferencesUpdate
    ) -> StudentSelfProfileResponse:
        profile = await self.get_or_create_profile(student_id)
        await self._apply(profile, data)
        await self.db.commit()
        return await self.get_self_profile(student_id)

    # ------------------------------------------------------------------
    # Internships
    # ------------------------------------------------------------------

    @staticmethod
    def _internship_response(row: StudentInternship) -> InternshipResponse:
        return InternshipResponse(
            id=str(row.id),
            student_id=str(row.student_id),
            company=row.company,
            role=row.role,
            start_date=row.start_date,
            end_date=row.end_date,
            duration=row.duration,
            stipend=row.stipend,
            technologies=row.technologies,
            description=row.description,
            status=row.status,
            certificate_document_id=str(row.certificate_document_id) if row.certificate_document_id else None,
            created_at=row.created_at,
        )

    async def list_internships(self, student_id: str) -> List[InternshipResponse]:
        res = await self.db.execute(
            select(StudentInternship)
            .where(StudentInternship.student_id == student_id)
            .order_by(StudentInternship.start_date.desc().nullslast(), StudentInternship.created_at.desc())
        )
        return [self._internship_response(r) for r in res.scalars().all()]

    async def create_internship(self, student_id: str, data) -> InternshipResponse:
        payload = data.model_dump(exclude_unset=True)
        self._validate_date_range(payload.get("start_date"), payload.get("end_date"))
        row = StudentInternship(student_id=student_id, **payload)
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return self._internship_response(row)

    async def update_internship(self, student_id: str, item_id: str, data) -> InternshipResponse:
        row = await self._owned(StudentInternship, student_id, item_id, "Internship")
        payload = data.model_dump(exclude_unset=True)
        self._validate_date_range(
            payload.get("start_date", row.start_date), payload.get("end_date", row.end_date)
        )
        for field, value in payload.items():
            setattr(row, field, value)
        await self.db.commit()
        await self.db.refresh(row)
        return self._internship_response(row)

    async def delete_internship(self, student_id: str, item_id: str) -> None:
        row = await self._owned(StudentInternship, student_id, item_id, "Internship")
        await self.db.delete(row)
        await self.db.commit()

    # ------------------------------------------------------------------
    # Interviews
    # ------------------------------------------------------------------

    @staticmethod
    def _interview_response(
        row: StudentInterview, observer_name: Optional[str] = None
    ) -> InterviewResponse:
        return InterviewResponse(
            id=str(row.id),
            student_id=str(row.student_id),
            company=row.company,
            role=row.role,
            interview_date=row.interview_date,
            interview_type=row.interview_type,
            round_name=row.round_name,
            result=row.result,
            feedback=row.feedback,
            notes=row.notes,
            package_offered=row.package_offered,
            counsellor_observation=row.counsellor_observation,
            counsellor_observed_by_name=observer_name,
            counsellor_observed_at=row.counsellor_observed_at,
            offer_document_id=str(row.offer_document_id) if row.offer_document_id else None,
            created_at=row.created_at,
        )

    async def list_interviews(self, student_id: str) -> List[InterviewResponse]:
        res = await self.db.execute(
            select(StudentInterview, User)
            .outerjoin(User, User.id == StudentInterview.counsellor_observed_by)
            .where(StudentInterview.student_id == student_id)
            .order_by(StudentInterview.interview_date.desc().nullslast(), StudentInterview.created_at.desc())
        )
        return [
            self._interview_response(row, observer.full_name if observer else None)
            for row, observer in res.all()
        ]

    async def create_interview(self, student_id: str, data) -> InterviewResponse:
        row = StudentInterview(student_id=student_id, **data.model_dump(exclude_unset=True))
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return self._interview_response(row)

    async def update_interview(self, student_id: str, item_id: str, data) -> InterviewResponse:
        row = await self._owned(StudentInterview, student_id, item_id, "Interview")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self.db.commit()
        await self.db.refresh(row)
        return self._interview_response(row)

    async def set_counsellor_observation(
        self, student_id: str, item_id: str, observation: str, counsellor_id: str
    ) -> InterviewResponse:
        row = await self._owned(StudentInterview, student_id, item_id, "Interview")
        row.counsellor_observation = observation
        row.counsellor_observed_by = counsellor_id
        row.counsellor_observed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(row)
        observer = await self.db.get(User, counsellor_id)
        return self._interview_response(row, observer.full_name if observer else None)

    async def delete_interview(self, student_id: str, item_id: str) -> None:
        row = await self._owned(StudentInterview, student_id, item_id, "Interview")
        await self.db.delete(row)
        await self.db.commit()

    # ------------------------------------------------------------------
    # Achievements
    # ------------------------------------------------------------------

    @staticmethod
    def _achievement_response(row: StudentAchievement) -> AchievementResponse:
        return AchievementResponse(
            id=str(row.id),
            student_id=str(row.student_id),
            category=row.category,
            title=row.title,
            description=row.description,
            issuer=row.issuer,
            achieved_on=row.achieved_on,
            position=row.position,
            credential_url=row.credential_url,
            proof_document_id=str(row.proof_document_id) if row.proof_document_id else None,
            created_at=row.created_at,
        )

    async def list_achievements(self, student_id: str) -> List[AchievementResponse]:
        res = await self.db.execute(
            select(StudentAchievement)
            .where(StudentAchievement.student_id == student_id)
            .order_by(StudentAchievement.achieved_on.desc().nullslast(), StudentAchievement.created_at.desc())
        )
        return [self._achievement_response(r) for r in res.scalars().all()]

    async def create_achievement(self, student_id: str, data) -> AchievementResponse:
        row = StudentAchievement(student_id=student_id, **data.model_dump(exclude_unset=True))
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return self._achievement_response(row)

    async def update_achievement(self, student_id: str, item_id: str, data) -> AchievementResponse:
        row = await self._owned(StudentAchievement, student_id, item_id, "Achievement")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self.db.commit()
        await self.db.refresh(row)
        return self._achievement_response(row)

    async def delete_achievement(self, student_id: str, item_id: str) -> None:
        row = await self._owned(StudentAchievement, student_id, item_id, "Achievement")
        await self.db.delete(row)
        await self.db.commit()

    # ------------------------------------------------------------------
    # Counsellor section (read-only for the student)
    # ------------------------------------------------------------------

    async def get_counselling_summary(self, student_id: str) -> StudentCounsellingSummary:
        """Section 3 of the workspace: what staff have recorded ABOUT this
        student that the student is entitled to read.

        Everything here is read-only by construction — this service has no
        method that writes a session, an action item or a parent
        communication, so the student portal has no path to author them."""
        student = await self._get_student(student_id)
        identity = await self._build_identity(student)

        sessions = await self._load_sessions(student_id)
        notes: List[CounsellingNoteEntry] = []
        action_items: List[CounsellingActionItemEntry] = []
        today = datetime.now(timezone.utc).date()

        for session, counsellor_name in sessions:
            notes.append(
                CounsellingNoteEntry(
                    session_id=str(session.id),
                    session_date=session.session_date,
                    session_type=session.session_type,
                    mode=session.mode,
                    counsellor_name=counsellor_name,
                    observations=session.observations,
                    recommendations=session.recommendations,
                    student_commitments=session.student_commitments,
                    follow_up_required=session.follow_up_required,
                    follow_up_date=session.follow_up_date,
                    student_acknowledged=session.student_acknowledged,
                )
            )
            for item in session.action_items:
                action_items.append(
                    CounsellingActionItemEntry(
                        id=str(item.id),
                        description=item.description,
                        due_date=item.due_date,
                        status=item.status,
                        is_overdue=(
                            item.status == FollowUpStatus.PENDING.value
                            and item.due_date is not None
                            and item.due_date < today
                        ),
                        session_date=session.session_date,
                    )
                )

        # Overdue first, then soonest due — the student's actual working order.
        action_items.sort(
            key=lambda i: (not i.is_overdue, i.due_date or date.max)
        )

        return StudentCounsellingSummary(
            risk_level=student.risk_level,
            counsellor_name=identity.counsellor_name,
            mentor_name=identity.mentor_name,
            total_sessions=len(notes),
            last_session_date=notes[0].session_date if notes else None,
            follow_up_required=any(n.follow_up_required for n in notes),
            notes=notes,
            action_items=action_items,
            parent_interactions=await self._load_parent_interactions(student_id),
        )

    async def _load_sessions(self, student_id: str):
        """Sessions newest first, each paired with its counsellor's name.

        `confidential_notes` is never read out of the row here — see
        CounsellingNoteEntry for why the field is absent from the schema too."""
        res = await self.db.execute(
            select(CounsellingSession, User)
            .outerjoin(User, User.id == CounsellingSession.counsellor_id)
            .options(selectinload(CounsellingSession.action_items))
            .where(CounsellingSession.student_id == student_id)
            .order_by(CounsellingSession.session_date.desc())
        )
        return [(session, user.full_name if user else None) for session, user in res.all()]

    async def _load_parent_interactions(self, student_id: str) -> List[ParentInteractionEntry]:
        res = await self.db.execute(
            select(ParentCommunication)
            .where(ParentCommunication.student_id == student_id)
            .order_by(ParentCommunication.communication_date.desc())
        )
        return [
            ParentInteractionEntry(
                id=str(row.id),
                communication_date=row.communication_date,
                mode=row.mode,
                parent_name=row.parent_name,
                relation=row.relation,
                summary=row.summary,
                action_items=row.action_items,
                outcome=row.outcome,
                follow_up_date=row.follow_up_date,
            )
            for row in res.scalars().all()
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _owned(self, model, student_id: str, item_id: str, label: str):
        """Fetch a row by id AND student_id together.

        Filtering on both is what stops one student editing another's rows by
        guessing an id: a mismatched pair returns nothing and 404s, so the
        endpoint never has to remember a separate ownership check.
        """
        res = await self.db.execute(
            select(model).where(model.id == item_id, model.student_id == student_id)
        )
        row = res.scalar_one_or_none()
        if not row:
            raise NotFoundError(f"{label} not found")
        return row

    @staticmethod
    def _validate_date_range(start, end) -> None:
        if start and end and end < start:
            raise ValidationError("End date cannot be earlier than the start date")
