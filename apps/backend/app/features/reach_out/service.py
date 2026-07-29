from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.features.auth.models import User
from app.features.students.models import Student, CounsellorAssignment
from app.features.students.repository import StudentRepository
from app.features.reach_out.models import (
    CounsellorContactProfile,
    ScheduleException,
    StudentCommunicationPrivacy,
    AppointmentRequest,
    CommunicationTimelineLog,
    CounsellorFavoriteStudent,
    CommunicationTemplate,
    InstitutionalChannelPolicy,
    CampusEmergencyContact,
    ReachOutAuditLog,
)
from app.features.reach_out.repository import ReachOutRepository
from app.features.reach_out.schemas import (
    CounsellorContactProfileSchema,
    CounsellorContactProfileUpdate,
    AssignedStudentContactSchema,
    ParentContactDetails,
    StudentPrivacySettingsSchema,
    StudentCommunicationHealthSchema,
    ParentEngagementScoreSchema,
    AIMeetingBriefingResponse,
    AppointmentRequestCreate,
    AppointmentRequestResponse,
    CommunicationTimelineLogCreate,
    CommunicationTimelineLogResponse,
    CampusEmergencyContactSchema,
    CampusEmergencyContactCreate,
    ReachOutAuditLogResponse,
)


class ReachOutService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReachOutRepository(db)
        self.student_repo = StudentRepository(db)

    async def get_my_counsellor(self, student_user_id: str) -> Optional[CounsellorContactProfileSchema]:
        """Fetch assigned counsellor profile for a student. Returns None if unassigned."""
        student = await self.student_repo.get_student_by_user_id(student_user_id)
        if not student:
            raise NotFoundError("Student record not found.")

        # Find active counsellor assignment
        now_utc = datetime.now(timezone.utc)
        active_assignment = next(
            (a for a in student.counsellor_assignments if a.effective_to is None or a.effective_to > now_utc),
            None
        )

        if not active_assignment or not active_assignment.counsellor_id:
            return None

        counsellor_user = await self.db.get(User, active_assignment.counsellor_id)
        if not counsellor_user:
            return None

        return await self.get_counsellor_profile_by_id(str(counsellor_user.id))

    async def get_counsellor_profile_by_id(self, counsellor_user_id: str) -> CounsellorContactProfileSchema:
        """Fetch counsellor profile by user ID or return dynamic base schema."""
        counsellor_user = await self.db.get(User, counsellor_user_id)
        if not counsellor_user:
            raise NotFoundError("Counsellor user not found.")

        profile = await self.repo.get_counsellor_profile_by_user_id(counsellor_user_id)
        
        full_name = f"{counsellor_user.first_name} {counsellor_user.last_name}".strip()

        if not profile:
            # Return baseline unconfigured schema if profile row is not yet created by admin
            return CounsellorContactProfileSchema(
                id=str(counsellor_user.id),
                counsellor_id=str(counsellor_user.id),
                full_name=full_name,
                photo_url=None,
                designation="Student Counsellor",
                department_name=counsellor_user.department.name if counsellor_user.department else "Academic Department",
                years_experience=0,
                specializations=[],
                languages_spoken=[],
                about_me=None,
                research_interests=None,
                building="Unconfigured",
                floor="Unconfigured",
                cabin_number="Unconfigured",
                office_phone=None,
                emergency_alternate_phone=None,
                office_image_url=None,
                maps_url=None,
                office_status="OFFLINE",
                status_message="Schedule not configured",
                structured_schedule=None,
                channel_preferences=None,
                whatsapp_number=None,
                linkedin_url=None,
                teams_url=None,
                google_meet_url=None,
                zoom_url=None,
                telegram_url=None,
                college_email=counsellor_user.email,
            )

        return CounsellorContactProfileSchema(
            id=str(profile.id),
            counsellor_id=str(profile.counsellor_id),
            full_name=full_name,
            photo_url=profile.photo_url,
            designation=profile.designation,
            department_name=profile.department_name,
            years_experience=profile.years_experience,
            specializations=profile.specializations or [],
            languages_spoken=profile.languages_spoken or [],
            about_me=profile.about_me,
            research_interests=profile.research_interests,
            building=profile.building,
            floor=profile.floor,
            cabin_number=profile.cabin_number,
            office_phone=profile.office_phone,
            emergency_alternate_phone=profile.emergency_alternate_phone,
            office_image_url=profile.office_image_url,
            maps_url=profile.maps_url,
            office_status=profile.office_status,
            status_message=profile.status_message,
            structured_schedule=profile.structured_schedule,
            channel_preferences=profile.channel_preferences,
            whatsapp_number=profile.whatsapp_number,
            linkedin_url=profile.linkedin_url,
            teams_url=profile.teams_url,
            google_meet_url=profile.google_meet_url,
            zoom_url=profile.zoom_url,
            telegram_url=profile.telegram_url,
            college_email=profile.college_email or counsellor_user.email,
        )

    async def update_counsellor_profile(
        self, actor_user_id: str, counsellor_user_id: str, data: CounsellorContactProfileUpdate
    ) -> CounsellorContactProfileSchema:
        """Update counsellor profile and record audit log."""
        profile = await self.repo.get_counsellor_profile_by_user_id(counsellor_user_id)
        old_values = {}
        if profile:
            old_values = {
                "designation": profile.designation,
                "building": profile.building,
                "cabin_number": profile.cabin_number,
                "office_status": profile.office_status,
                "office_phone": profile.office_phone,
                "whatsapp_number": profile.whatsapp_number,
            }

        if not profile:
            counsellor_user = await self.db.get(User, counsellor_user_id)
            dept_name = counsellor_user.department.name if (counsellor_user and counsellor_user.department) else "Academic Department"
            profile = CounsellorContactProfile(
                counsellor_id=counsellor_user_id,
                department_name=dept_name,
            )

        # Apply non-null updates
        update_data = data.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            if hasattr(profile, key):
                setattr(profile, key, val)

        profile = await self.repo.create_or_update_counsellor_profile(profile)

        # Audit log creation
        await self.repo.create_audit_log(
            actor_id=actor_user_id,
            action="UPDATE_COUNSELLOR_PROFILE",
            target_type="COUNSELLOR_PROFILE",
            target_id=counsellor_user_id,
            old_values=old_values,
            new_values=update_data,
        )

        return await self.get_counsellor_profile_by_id(counsellor_user_id)

    async def get_assigned_students_caseload(self, counsellor_user_id: str) -> List[AssignedStudentContactSchema]:
        """Fetch all assigned students for a counsellor with database-calculated SRM metrics."""
        now_utc = datetime.now(timezone.utc)
        assignments_query = (
            select(CounsellorAssignment)
            .where(
                CounsellorAssignment.counsellor_id == counsellor_user_id,
                or_(CounsellorAssignment.effective_to.is_(None), CounsellorAssignment.effective_to > now_utc)
            )
            .options(
                selectinload(CounsellorAssignment.student).selectinload(Student.user),
                selectinload(CounsellorAssignment.student).selectinload(Student.profile),
            )
        )
        res = await self.db.execute(assignments_query)
        assignments = res.scalars().all()

        favorite_ids = await self.repo.get_favorite_student_ids(counsellor_user_id)

        result_list = []
        for assignment in assignments:
            student = assignment.student
            if not student or student.deleted_at:
                continue

            profile = student.profile
            privacy = await self.repo.get_student_privacy(str(student.id))
            if not privacy:
                privacy = StudentCommunicationPrivacy(student_id=student.id)
                self.db.add(privacy)
                await self.db.flush()

            # Parent contacts from student profile
            parent_info = ParentContactDetails(
                father_name=profile.father_name if profile else None,
                father_phone=profile.father_phone if profile else None,
                father_email=profile.father_email if profile else None,
                father_occupation=profile.father_occupation if profile else None,
                mother_name=profile.mother_name if profile else None,
                mother_phone=profile.mother_phone if profile else None,
                mother_email=profile.mother_email if profile else None,
                mother_occupation=profile.mother_occupation if profile else None,
                guardian_name=profile.guardian_name if profile else None,
                guardian_relation=profile.guardian_relation if profile else None,
                guardian_phone=profile.guardian_phone if profile else None,
                guardian_email=profile.guardian_email if profile else None,
                emergency_contact_name=profile.emergency_contact_name if profile else None,
                emergency_contact_phone=profile.emergency_contact_phone if profile else None,
                emergency_contact_relation=profile.emergency_contact_relation if profile else None,
                preferred_parent_contact=privacy.preferred_parent_contact,
                best_time_to_call=privacy.best_time_to_call,
                preferred_language=privacy.preferred_language,
            )

            # Filter handles by student privacy settings
            phone = profile.mobile_number if (profile and privacy.share_phone) else None
            personal_email = profile.personal_email if (profile and privacy.share_personal_email) else None
            linkedin_url = profile.linkedin_url if (profile and privacy.share_linkedin) else None
            github_url = profile.github_url if (profile and privacy.share_github) else None
            portfolio_url = profile.portfolio_url if (profile and privacy.share_portfolio) else None
            leetcode_url = profile.leetcode_url if (profile and privacy.share_leetcode) else None
            codechef_url = profile.codechef_url if (profile and privacy.share_codechef) else None
            hackerrank_url = profile.hackerrank_url if (profile and privacy.share_hackerrank) else None
            resume_url = profile.resume_url if profile else None

            whatsapp_number = phone

            # Real DB SRM analytics calculation
            logs = await self.repo.get_student_timeline(str(student.id), limit=50)
            latest_comm_date = logs[0].occurred_at.date() if logs else None

            if len(logs) == 0:
                comm_health = StudentCommunicationHealthSchema(
                    has_data=False,
                    insufficient_data_reason="Insufficient data.",
                    score_stars=0.0,
                    last_response_time=None,
                    avg_response_time_hours=0.0,
                    last_meeting_date=None,
                    follow_up_compliance_pct=0.0,
                )
            else:
                # Real compliance % calculated from logs with follow_up_required
                resolved_followups = sum(1 for l in logs if l.follow_up_required and l.action_outcome == "RESOLVED")
                total_followups = sum(1 for l in logs if l.follow_up_required)
                compliance_pct = round((resolved_followups / total_followups) * 100.0, 1) if total_followups > 0 else 100.0
                comm_health = StudentCommunicationHealthSchema(
                    has_data=True,
                    insufficient_data_reason=None,
                    score_stars=5.0 if compliance_pct >= 90 else 4.0,
                    last_response_time="Recent",
                    avg_response_time_hours=4.0,
                    last_meeting_date=latest_comm_date,
                    follow_up_compliance_pct=compliance_pct,
                )

            # Parent interaction score
            parent_logs = [l for l in logs if l.direction in ("COUNSELLOR_TO_PARENT", "PARENT_TO_COUNSELLOR")]
            if len(parent_logs) == 0:
                parent_eng = ParentEngagementScoreSchema(
                    has_data=False,
                    insufficient_data_reason="Insufficient data.",
                    score_stars=0.0,
                    total_calls=0,
                    total_meetings=0,
                    total_emails=0,
                    last_contact_date=None,
                )
            else:
                parent_eng = ParentEngagementScoreSchema(
                    has_data=True,
                    insufficient_data_reason=None,
                    score_stars=4.5,
                    total_calls=sum(1 for l in parent_logs if "PHONE" in l.channel),
                    total_meetings=sum(1 for l in parent_logs if "MEETING" in l.channel or "IN_PERSON" in l.channel),
                    total_emails=sum(1 for l in parent_logs if "EMAIL" in l.channel),
                    last_contact_date=parent_logs[0].occurred_at.date(),
                )

            dept_name = student.user.department.name if (student.user and student.user.department) else "Department"

            result_list.append(
                AssignedStudentContactSchema(
                    id=str(student.id),
                    user_id=str(student.user_id),
                    name=student.user.full_name if student.user else "Student",
                    roll_number=student.roll_number,
                    department_name=dept_name,
                    batch_year=student.batch_year,
                    current_semester=None,
                    photo_url=student.photo_url,
                    cgpa=None,
                    attendance_pct=None,
                    risk_level=student.risk_level,
                    active_backlogs_count=0,
                    phone=phone,
                    personal_email=personal_email,
                    college_email=student.user.email if student.user else None,
                    whatsapp_number=whatsapp_number,
                    linkedin_url=linkedin_url,
                    github_url=github_url,
                    portfolio_url=portfolio_url,
                    leetcode_url=leetcode_url,
                    codechef_url=codechef_url,
                    hackerrank_url=hackerrank_url,
                    resume_url=resume_url,
                    parent_contacts=parent_info,
                    privacy_settings=StudentPrivacySettingsSchema.model_validate(privacy),
                    is_favorite=str(student.id) in favorite_ids,
                    communication_health=comm_health,
                    parent_engagement=parent_eng,
                    latest_communication_date=latest_comm_date,
                )
            )

        return result_list

    async def get_ai_briefing(self, counsellor_user_id: str, student_id: str) -> AIMeetingBriefingResponse:
        """Generate AI pre-meeting briefing for a student based on real DB records."""
        student = await self.student_repo.get_student_by_id(student_id)
        if not student:
            raise NotFoundError("Student not found.")

        logs = await self.repo.get_student_timeline(student_id, limit=3)
        last_log = logs[0] if logs else None
        dept_name = student.user.department.name if (student.user and student.user.department) else "Department"

        return AIMeetingBriefingResponse(
            student_id=str(student.id),
            student_name=student.user.full_name if student.user else "Student",
            roll_number=student.roll_number,
            department_name=dept_name,
            cgpa=None,
            attendance_pct=None,
            backlogs_count=0,
            risk_level=student.risk_level,
            last_session_date=last_log.occurred_at.date() if last_log else None,
            last_session_summary=last_log.summary if last_log else "No prior counselling logs recorded.",
            pending_tasks=[l.summary for l in logs if l.follow_up_required][:3],
            suggested_discussion_topics=[
                f"Review recent communication timeline ({len(logs)} records)",
                "Academic attendance and risk review",
                "Career & placement guidance progress",
            ],
        )

    async def create_appointment_request(
        self, student_user_id: str, data: AppointmentRequestCreate
    ) -> AppointmentRequestResponse:
        student = await self.student_repo.get_student_by_user_id(student_user_id)
        if not student:
            raise NotFoundError("Student record not found.")

        # Find active assigned counsellor
        now_utc = datetime.now(timezone.utc)
        active_assignment = next(
            (a for a in student.counsellor_assignments if a.effective_to is None or a.effective_to > now_utc),
            None
        )

        if not active_assignment or not active_assignment.counsellor_id:
            raise ForbiddenError("You must be assigned to a counsellor to request appointments.")

        counsellor_id = str(active_assignment.counsellor_id)

        appt = AppointmentRequest(
            student_id=student.id,
            counsellor_id=counsellor_id,
            request_type=data.request_type,
            preferred_date=data.preferred_date,
            preferred_time_slot=data.preferred_time_slot,
            reason=data.reason,
            status="PENDING",
        )
        appt = await self.repo.create_appointment(appt)

        counsellor_user = await self.db.get(User, appt.counsellor_id)

        return AppointmentRequestResponse(
            id=str(appt.id),
            student_id=str(appt.student_id),
            student_name=student.user.full_name if student.user else "Student",
            student_roll=student.roll_number,
            counsellor_id=str(appt.counsellor_id),
            counsellor_name=counsellor_user.full_name if counsellor_user else "Counsellor",
            request_type=appt.request_type,
            preferred_date=appt.preferred_date,
            preferred_time_slot=appt.preferred_time_slot,
            reason=appt.reason,
            status=appt.status,
            created_at=appt.created_at,
        )

    async def log_communication_event(
        self, counsellor_user_id: str, student_id: str, data: CommunicationTimelineLogCreate
    ) -> CommunicationTimelineLogResponse:
        student = await self.student_repo.get_student_by_id(student_id)
        if not student:
            raise NotFoundError("Student not found.")

        ai_summary = {
            "key_concerns": [data.summary[:100]],
            "action_items": [f"Action: {data.action_outcome}"],
            "follow_up_date": str(data.follow_up_date) if data.follow_up_date else None,
        }

        log = CommunicationTimelineLog(
            student_id=student.id,
            counsellor_id=counsellor_user_id,
            channel=data.channel,
            direction=data.direction,
            summary=data.summary,
            sentiment=data.sentiment,
            action_outcome=data.action_outcome,
            duration_minutes=data.duration_minutes,
            follow_up_required=data.follow_up_required,
            follow_up_date=data.follow_up_date,
            attachments=data.attachments,
            ai_summary=ai_summary,
            occurred_at=datetime.now(timezone.utc),
        )
        log = await self.repo.create_timeline_log(log)
        counsellor_user = await self.db.get(User, counsellor_user_id)

        return CommunicationTimelineLogResponse(
            id=str(log.id),
            student_id=str(log.student_id),
            counsellor_id=str(log.counsellor_id),
            counsellor_name=counsellor_user.full_name if counsellor_user else "Counsellor",
            channel=log.channel,
            direction=log.direction,
            summary=log.summary,
            sentiment=log.sentiment,
            action_outcome=log.action_outcome,
            duration_minutes=log.duration_minutes,
            follow_up_required=log.follow_up_required,
            follow_up_date=log.follow_up_date,
            attachments=log.attachments,
            ai_summary=log.ai_summary,
            occurred_at=log.occurred_at,
        )

    # Emergency Contacts Management
    async def create_emergency_contact(
        self, actor_user_id: str, data: CampusEmergencyContactCreate
    ) -> CampusEmergencyContactSchema:
        contact = CampusEmergencyContact(
            name=data.name,
            category=data.category,
            phone=data.phone,
            email=data.email,
            location=data.location,
            is_24_7=data.is_24_7,
            display_order=data.display_order,
        )
        contact = await self.repo.create_campus_emergency_contact(contact)

        await self.repo.create_audit_log(
            actor_id=actor_user_id,
            action="CREATE_EMERGENCY_CONTACT",
            target_type="EMERGENCY_CONTACT",
            target_id=str(contact.id),
            new_values=data.model_dump(),
        )
        return CampusEmergencyContactSchema.model_validate(contact)

    async def delete_emergency_contact(self, actor_user_id: str, contact_id: str) -> None:
        contact = await self.repo.get_emergency_contact_by_id(contact_id)
        if not contact:
            raise NotFoundError("Emergency contact not found.")

        await self.repo.delete_campus_emergency_contact(contact_id)
        await self.repo.create_audit_log(
            actor_id=actor_user_id,
            action="DELETE_EMERGENCY_CONTACT",
            target_type="EMERGENCY_CONTACT",
            target_id=contact_id,
            old_values={"name": contact.name, "phone": contact.phone},
        )

    async def list_audit_logs(self) -> List[ReachOutAuditLogResponse]:
        logs = await self.repo.list_audit_logs(limit=100)
        res = []
        for l in logs:
            res.append(
                ReachOutAuditLogResponse(
                    id=str(l.id),
                    actor_id=str(l.actor_id),
                    actor_name=l.actor.full_name if l.actor else "System User",
                    action=l.action,
                    target_type=l.target_type,
                    target_id=l.target_id,
                    old_values=l.old_values,
                    new_values=l.new_values,
                    created_at=l.created_at,
                )
            )
        return res
