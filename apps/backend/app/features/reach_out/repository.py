from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from app.features.students.models import Student, CounsellorAssignment
from app.features.students.profile_models import StudentProfile
from app.features.auth.models import User
from app.features.admin.models import Department, Semester


class ReachOutRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------- Counsellor Profiles ----------------
    async def get_counsellor_profile_by_user_id(self, counsellor_user_id: str) -> Optional[CounsellorContactProfile]:
        query = (
            select(CounsellorContactProfile)
            .where(CounsellorContactProfile.counsellor_id == counsellor_user_id)
            .options(selectinload(CounsellorContactProfile.counsellor))
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def create_or_update_counsellor_profile(
        self, profile: CounsellorContactProfile
    ) -> CounsellorContactProfile:
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def list_all_counsellor_profiles(self) -> List[CounsellorContactProfile]:
        query = select(CounsellorContactProfile).options(selectinload(CounsellorContactProfile.counsellor))
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_counsellor_profiles_by_department(self, department_id: str) -> List[CounsellorContactProfile]:
        # Filter counsellors belonging to department_id
        query = (
            select(CounsellorContactProfile)
            .join(User, CounsellorContactProfile.counsellor_id == User.id)
            .where(User.department_id == department_id)
            .options(selectinload(CounsellorContactProfile.counsellor))
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    # ---------------- Schedule Exceptions ----------------
    async def get_counsellor_schedule_exceptions(
        self, counsellor_id: str
    ) -> List[ScheduleException]:
        today = date.today()
        query = (
            select(ScheduleException)
            .where(
                ScheduleException.counsellor_id == counsellor_id,
                ScheduleException.end_date >= today,
            )
            .order_by(ScheduleException.start_date)
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create_schedule_exception(
        self, exception: ScheduleException
    ) -> ScheduleException:
        self.db.add(exception)
        await self.db.flush()
        return exception

    # ---------------- Privacy Settings ----------------
    async def get_student_privacy(self, student_id: str) -> Optional[StudentCommunicationPrivacy]:
        query = select(StudentCommunicationPrivacy).where(
            StudentCommunicationPrivacy.student_id == student_id
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def save_student_privacy(
        self, privacy: StudentCommunicationPrivacy
    ) -> StudentCommunicationPrivacy:
        self.db.add(privacy)
        await self.db.flush()
        return privacy

    # ---------------- Favorites ----------------
    async def get_favorite_student_ids(self, counsellor_id: str) -> List[str]:
        query = select(CounsellorFavoriteStudent.student_id).where(
            CounsellorFavoriteStudent.counsellor_id == counsellor_id
        )
        res = await self.db.execute(query)
        return [str(row) for row in res.scalars().all()]

    async def add_favorite_student(self, counsellor_id: str, student_id: str) -> None:
        existing = await self.db.execute(
            select(CounsellorFavoriteStudent).where(
                CounsellorFavoriteStudent.counsellor_id == counsellor_id,
                CounsellorFavoriteStudent.student_id == student_id,
            )
        )
        if not existing.scalar_one_or_none():
            fav = CounsellorFavoriteStudent(counsellor_id=counsellor_id, student_id=student_id)
            self.db.add(fav)
            await self.db.flush()

    async def remove_favorite_student(self, counsellor_id: str, student_id: str) -> None:
        await self.db.execute(
            delete(CounsellorFavoriteStudent).where(
                CounsellorFavoriteStudent.counsellor_id == counsellor_id,
                CounsellorFavoriteStudent.student_id == student_id,
            )
        )

    # ---------------- Timeline Logs ----------------
    async def get_student_timeline(
        self, student_id: str, limit: int = 50
    ) -> List[CommunicationTimelineLog]:
        query = (
            select(CommunicationTimelineLog)
            .where(CommunicationTimelineLog.student_id == student_id)
            .options(selectinload(CommunicationTimelineLog.counsellor))
            .order_by(CommunicationTimelineLog.occurred_at.desc())
            .limit(limit)
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create_timeline_log(
        self, log: CommunicationTimelineLog
    ) -> CommunicationTimelineLog:
        self.db.add(log)
        await self.db.flush()
        return log

    # ---------------- Appointments ----------------
    async def get_appointments_by_student(self, student_id: str) -> List[AppointmentRequest]:
        query = (
            select(AppointmentRequest)
            .where(AppointmentRequest.student_id == student_id)
            .options(
                selectinload(AppointmentRequest.student).selectinload(Student.user),
                selectinload(AppointmentRequest.counsellor),
            )
            .order_by(AppointmentRequest.created_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_appointments_by_counsellor(self, counsellor_id: str) -> List[AppointmentRequest]:
        query = (
            select(AppointmentRequest)
            .where(AppointmentRequest.counsellor_id == counsellor_id)
            .options(
                selectinload(AppointmentRequest.student).selectinload(Student.user),
                selectinload(AppointmentRequest.counsellor),
            )
            .order_by(AppointmentRequest.created_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_appointment_by_id(self, appointment_id: str) -> Optional[AppointmentRequest]:
        query = (
            select(AppointmentRequest)
            .where(AppointmentRequest.id == appointment_id)
            .options(
                selectinload(AppointmentRequest.student).selectinload(Student.user),
                selectinload(AppointmentRequest.counsellor),
            )
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def create_appointment(self, appt: AppointmentRequest) -> AppointmentRequest:
        self.db.add(appt)
        await self.db.flush()
        return appt

    # ---------------- Templates ----------------
    async def get_communication_templates(self) -> List[CommunicationTemplate]:
        query = select(CommunicationTemplate).order_by(CommunicationTemplate.category, CommunicationTemplate.title)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    # ---------------- Channel Policy ----------------
    async def get_institutional_channel_policy(self) -> InstitutionalChannelPolicy:
        query = select(InstitutionalChannelPolicy).limit(1)
        res = await self.db.execute(query)
        policy = res.scalar_one_or_none()
        if not policy:
            policy = InstitutionalChannelPolicy()
            self.db.add(policy)
            await self.db.flush()
        return policy

    # ---------------- Emergency Contacts ----------------
    async def get_campus_emergency_contacts(self) -> List[CampusEmergencyContact]:
        query = select(CampusEmergencyContact).order_by(CampusEmergencyContact.display_order, CampusEmergencyContact.name)
        res = await self.db.execute(query)
        contacts = list(res.scalars().all())
        if not contacts:
            # Seed standard campus emergency contacts if empty
            defaults = [
                CampusEmergencyContact(name="Counselling Office Hotline", category="COUNSELLING", phone="+91 863 2288201", email="counselling@vvit.edu.in", location="Block B, Room 301", is_24_7=True, display_order=1),
                CampusEmergencyContact(name="HOD Desk - AI & DS", category="DEPARTMENT", phone="+91 863 2288210", email="hod_aids@vvit.edu.in", location="Block B, Room 310", is_24_7=False, display_order=2),
                CampusEmergencyContact(name="Anti-Ragging Helpline", category="HEPLINE", phone="+91 1800 180 5522", email="antiragging@vvit.edu.in", location="Administrative Block", is_24_7=True, display_order=3),
                CampusEmergencyContact(name="Women Protection Cell", category="SAFETY", phone="+91 863 2288220", email="wpc@vvit.edu.in", location="Block A, Room 104", is_24_7=True, display_order=4),
                CampusEmergencyContact(name="Campus Medical Center", category="MEDICAL", phone="+91 863 2288299", email="medical@vvit.edu.in", location="Amenities Block", is_24_7=True, display_order=5),
                CampusEmergencyContact(name="Campus Security Main Gate", category="SECURITY", phone="+91 863 2288200", email="security@vvit.edu.in", location="Main Gate", is_24_7=True, display_order=6),
            ]
            for d in defaults:
                self.db.add(d)
            await self.db.flush()
            contacts = defaults
        return contacts

    async def get_emergency_contact_by_id(self, contact_id: str) -> Optional[CampusEmergencyContact]:
        query = select(CampusEmergencyContact).where(CampusEmergencyContact.id == contact_id)
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def create_campus_emergency_contact(self, contact: CampusEmergencyContact) -> CampusEmergencyContact:
        self.db.add(contact)
        await self.db.flush()
        return contact

    async def delete_campus_emergency_contact(self, contact_id: str) -> None:
        await self.db.execute(delete(CampusEmergencyContact).where(CampusEmergencyContact.id == contact_id))

    # ---------------- Audit Logging ----------------
    async def create_audit_log(
        self,
        actor_id: str,
        action: str,
        target_type: str,
        target_id: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
    ) -> ReachOutAuditLog:
        log = ReachOutAuditLog(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            old_values=old_values,
            new_values=new_values,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def list_audit_logs(self, limit: int = 100, offset: int = 0) -> List[ReachOutAuditLog]:
        query = (
            select(ReachOutAuditLog)
            .options(selectinload(ReachOutAuditLog.actor))
            .order_by(ReachOutAuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())
