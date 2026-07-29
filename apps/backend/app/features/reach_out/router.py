from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_token_payload
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.core.enums import UserRole
from app.core.permissions import require_permission, require_role
from app.features.reach_out.schemas import (
    CounsellorContactProfileSchema,
    CounsellorContactProfileUpdate,
    AssignedStudentContactSchema,
    StudentPrivacySettingsSchema,
    AppointmentRequestCreate,
    AppointmentRequestStatusUpdate,
    AppointmentRequestResponse,
    CommunicationTimelineLogCreate,
    CommunicationTimelineLogResponse,
    AIMeetingBriefingResponse,
    CommunicationTemplateResponse,
    InstitutionalChannelPolicySchema,
    CampusEmergencyContactSchema,
    CampusEmergencyContactCreate,
    ReachOutAuditLogResponse,
)
from app.features.reach_out.service import ReachOutService
from app.features.reach_out.repository import ReachOutRepository
from app.features.reach_out.models import StudentCommunicationPrivacy, CounsellorContactProfile, CampusEmergencyContact

router = APIRouter(prefix="/reach-out", tags=["Reach Out & Communication"])


@router.get("/my-counsellor")
async def get_my_counsellor(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Student endpoint: Retrieve active assigned counsellor profile. Returns assigned: false if unassigned."""
    service = ReachOutService(db)
    profile = await service.get_my_counsellor(str(current_user.id))
    if not profile:
        return {"assigned": False, "message": "No counsellor has been assigned yet."}
    return {"assigned": True, "profile": profile}


@router.get("/counsellors", response_model=List[CounsellorContactProfileSchema])
async def list_counsellors(
    department_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List counsellors (filtered by department for HOD, or all for Admin)."""
    service = ReachOutService(db)
    repo = ReachOutRepository(db)

    # Check if HOD: scope to user's department
    role_names = {r.name for r in current_user.roles}
    target_dept = department_id
    if "HOD" in role_names and not target_dept:
        target_dept = str(current_user.department_id) if current_user.department_id else None

    if target_dept:
        profiles = await repo.list_counsellor_profiles_by_department(target_dept)
    else:
        profiles = await repo.list_all_counsellor_profiles()

    res = []
    for p in profiles:
        prof_schema = await service.get_counsellor_profile_by_id(str(p.counsellor_id))
        res.append(prof_schema)
    return res


@router.get("/counsellors/{counsellor_id}", response_model=CounsellorContactProfileSchema)
async def get_counsellor_profile(
    counsellor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch specific counsellor profile."""
    service = ReachOutService(db)
    return await service.get_counsellor_profile_by_id(counsellor_id)


@router.get("/caseload", response_model=List[AssignedStudentContactSchema])
async def get_assigned_students_caseload(
    counsellor_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Counsellor/HOD endpoint: Retrieve assigned students with real SRM metrics."""
    target_counsellor = str(current_user.id)
    role_names = {r.name for r in current_user.roles}
    if ("HOD" in role_names or "ADMIN" in role_names) and counsellor_id:
        target_counsellor = counsellor_id

    service = ReachOutService(db)
    return await service.get_assigned_students_caseload(target_counsellor)


@router.get("/caseload/{student_id}/ai-briefing", response_model=AIMeetingBriefingResponse)
async def get_ai_meeting_briefing(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate pre-meeting AI briefing with attendance, CGPA, backlogs, pending tasks, and discussion topics."""
    service = ReachOutService(db)
    return await service.get_ai_briefing(str(current_user.id), student_id)


@router.post("/favorites/{student_id}", status_code=status.HTTP_200_OK)
async def add_favorite_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pin a student as favorite / high-touch for counsellor."""
    repo = ReachOutRepository(db)
    await repo.add_favorite_student(str(current_user.id), student_id)
    return {"message": "Student pinned as favorite."}


@router.delete("/favorites/{student_id}", status_code=status.HTTP_200_OK)
async def remove_favorite_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unpin a student from favorites."""
    repo = ReachOutRepository(db)
    await repo.remove_favorite_student(str(current_user.id), student_id)
    return {"message": "Student unpinned from favorites."}


@router.get("/caseload/{student_id}/timeline", response_model=List[CommunicationTimelineLogResponse])
async def get_student_timeline(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve communication timeline history for a student."""
    repo = ReachOutRepository(db)
    logs = await repo.get_student_timeline(student_id)
    return [
        CommunicationTimelineLogResponse(
            id=str(l.id),
            student_id=str(l.student_id),
            counsellor_id=str(l.counsellor_id),
            counsellor_name=l.counsellor.full_name if l.counsellor else "Counsellor",
            channel=l.channel,
            direction=l.direction,
            summary=l.summary,
            sentiment=l.sentiment,
            action_outcome=l.action_outcome,
            duration_minutes=l.duration_minutes,
            follow_up_required=l.follow_up_required,
            follow_up_date=l.follow_up_date,
            attachments=l.attachments,
            ai_summary=l.ai_summary,
            occurred_at=l.occurred_at,
        )
        for l in logs
    ]


@router.post("/caseload/{student_id}/timeline", response_model=CommunicationTimelineLogResponse)
async def log_communication_event(
    student_id: str,
    data: CommunicationTimelineLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log a new communication event with direction, duration, action outcome, and AI summary."""
    service = ReachOutService(db)
    return await service.log_communication_event(str(current_user.id), student_id, data)


@router.get("/appointments", response_model=List[AppointmentRequestResponse])
async def list_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List appointment requests for current student or counsellor."""
    repo = ReachOutRepository(db)
    role_names = {r.name for r in current_user.roles}
    if "STUDENT" in role_names:
        from app.features.students.repository import StudentRepository
        s_repo = StudentRepository(db)
        student = await s_repo.get_student_by_user_id(str(current_user.id))
        if not student:
            return []
        appts = await repo.get_appointments_by_student(str(student.id))
    else:
        appts = await repo.get_appointments_by_counsellor(str(current_user.id))

    return [
        AppointmentRequestResponse(
            id=str(a.id),
            student_id=str(a.student_id),
            student_name=a.student.user.full_name if a.student and a.student.user else "Student",
            student_roll=a.student.roll_number if a.student else "N/A",
            counsellor_id=str(a.counsellor_id),
            counsellor_name=a.counsellor.full_name if a.counsellor else "Counsellor",
            request_type=a.request_type,
            preferred_date=a.preferred_date,
            preferred_time_slot=a.preferred_time_slot,
            reason=a.reason,
            status=a.status,
            rescheduled_date=a.rescheduled_date,
            rescheduled_slot=a.rescheduled_slot,
            counsellor_notes=a.counsellor_notes,
            created_at=a.created_at,
        )
        for a in appts
    ]


@router.post("/appointments", response_model=AppointmentRequestResponse)
async def create_appointment_request(
    data: AppointmentRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Student endpoint: Submit an appointment or guidance request."""
    service = ReachOutService(db)
    return await service.create_appointment_request(str(current_user.id), data)


@router.put("/appointments/{appointment_id}/status", response_model=AppointmentRequestResponse)
async def update_appointment_status(
    appointment_id: str,
    data: AppointmentRequestStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Counsellor endpoint: Update appointment request status (ACCEPTED, RESCHEDULED, DECLINED, COMPLETED, etc.)."""
    repo = ReachOutRepository(db)
    appt = await repo.get_appointment_by_id(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    appt.status = data.status
    if data.rescheduled_date:
        appt.rescheduled_date = data.rescheduled_date
    if data.rescheduled_slot:
        appt.rescheduled_slot = data.rescheduled_slot
    if data.counsellor_notes:
        appt.counsellor_notes = data.counsellor_notes

    await db.flush()

    return AppointmentRequestResponse(
        id=str(appt.id),
        student_id=str(appt.student_id),
        student_name=appt.student.user.full_name if appt.student and appt.student.user else "Student",
        student_roll=appt.student.roll_number if appt.student else "N/A",
        counsellor_id=str(appt.counsellor_id),
        counsellor_name=appt.counsellor.full_name if appt.counsellor else "Counsellor",
        request_type=appt.request_type,
        preferred_date=appt.preferred_date,
        preferred_time_slot=appt.preferred_time_slot,
        reason=appt.reason,
        status=appt.status,
        rescheduled_date=appt.rescheduled_date,
        rescheduled_slot=appt.rescheduled_slot,
        counsellor_notes=appt.counsellor_notes,
        created_at=appt.created_at,
    )


@router.get("/privacy", response_model=StudentPrivacySettingsSchema)
async def get_my_privacy_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Student endpoint: Get personal profile sharing and parent call privacy preferences."""
    from app.features.students.repository import StudentRepository
    s_repo = StudentRepository(db)
    student = await s_repo.get_student_by_user_id(str(current_user.id))
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found.")

    repo = ReachOutRepository(db)
    privacy = await repo.get_student_privacy(str(student.id))
    if not privacy:
        privacy = StudentCommunicationPrivacy(student_id=student.id)
        db.add(privacy)
        await db.flush()
    return privacy


@router.put("/privacy", response_model=StudentPrivacySettingsSchema)
async def update_my_privacy_settings(
    data: StudentPrivacySettingsSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Student endpoint: Update profile sharing toggles and parent preferences."""
    from app.features.students.repository import StudentRepository
    s_repo = StudentRepository(db)
    student = await s_repo.get_student_by_user_id(str(current_user.id))
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found.")

    repo = ReachOutRepository(db)
    privacy = await repo.get_student_privacy(str(student.id))
    if not privacy:
        privacy = StudentCommunicationPrivacy(student_id=student.id)

    for field, val in data.model_dump().items():
        setattr(privacy, field, val)

    privacy = await repo.save_student_privacy(privacy)
    return privacy


@router.get("/templates", response_model=List[CommunicationTemplateResponse])
async def get_communication_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get quick communication message templates for counsellor."""
    repo = ReachOutRepository(db)
    return await repo.get_communication_templates()


@router.get("/emergency-contacts", response_model=List[CampusEmergencyContactSchema])
async def get_campus_emergency_contacts(
    db: AsyncSession = Depends(get_db),
):
    """Public / Student endpoint: Get campus emergency hotline directory."""
    repo = ReachOutRepository(db)
    return await repo.get_campus_emergency_contacts()


@router.post("/admin/emergency-contacts", response_model=CampusEmergencyContactSchema)
async def create_campus_emergency_contact(
    data: CampusEmergencyContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint: Add a campus emergency hotline contact."""
    service = ReachOutService(db)
    return await service.create_emergency_contact(str(current_user.id), data)


@router.delete("/admin/emergency-contacts/{contact_id}", status_code=status.HTTP_200_OK)
async def delete_campus_emergency_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint: Delete a campus emergency hotline contact."""
    service = ReachOutService(db)
    await service.delete_emergency_contact(str(current_user.id), contact_id)
    return {"message": "Emergency contact deleted."}


@router.get("/channel-policy", response_model=InstitutionalChannelPolicySchema)
async def get_channel_policy(
    db: AsyncSession = Depends(get_db),
):
    """Get institutional channel policy settings."""
    repo = ReachOutRepository(db)
    return await repo.get_institutional_channel_policy()


@router.put("/admin/channel-policy", response_model=InstitutionalChannelPolicySchema)
async def update_channel_policy(
    data: InstitutionalChannelPolicySchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint: Update institutional channel policy settings with audit log."""
    repo = ReachOutRepository(db)
    policy = await repo.get_institutional_channel_policy()
    old_vals = data.model_dump()
    for field, val in old_vals.items():
        setattr(policy, field, val)
    await db.flush()
    await repo.create_audit_log(
        actor_id=str(current_user.id),
        action="UPDATE_CHANNEL_POLICY",
        target_type="CHANNEL_POLICY",
        target_id=str(policy.id),
        new_values=old_vals,
    )
    return policy


@router.get("/admin/audit-logs", response_model=List[ReachOutAuditLogResponse])
async def admin_list_audit_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint: Retrieve reach out configuration audit log history."""
    service = ReachOutService(db)
    return await service.list_audit_logs()


@router.put("/admin/counsellors/{counsellor_id}", response_model=CounsellorContactProfileSchema)
async def admin_update_counsellor_profile(
    counsellor_id: str,
    data: CounsellorContactProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint: Update counsellor persona, cabin, schedule, and channels with audit log."""
    service = ReachOutService(db)
    return await service.update_counsellor_profile(str(current_user.id), counsellor_id, data)
