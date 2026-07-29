from datetime import date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.core.events import event_bus, DomainEvent
from app.core.pagination import PaginatedResponse, PaginationParams
from app.features.students.repository import StudentRepository
from app.features.students.schemas import (
    StudentProfileResponse,
    Student360Response,
    RosterStudentResponse,
    OverviewStat,
    RiskFlagUpdateRequest,
    CaseloadStudentResponse,
    CaseloadFacets,
    FacetOption,
    SessionContextResponse,
    PendingActionItem,
    AcademicCorrectionResponse,
)

from app.features.admin.repository import AdminRepository
from app.features.attendance.repository import AttendanceRepository
from app.features.academics.repository import AcademicsRepository
from app.features.counselling.repository import CounsellingRepository
from app.core.enums import TimelineEventType

# Institutional minimum attendance. Single source of truth for the caseload
# "below threshold" flag, the dashboard tile, and the 360 attention items.
ATTENDANCE_THRESHOLD = 75.0


class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StudentRepository(db)
        self.admin_repo = AdminRepository(db)
        self.attendance_repo = AttendanceRepository(db)
        self.academics_repo = AcademicsRepository(db)
        self.counselling_repo = CounsellingRepository(db)

    # ------------------------------------------------------------------
    # Caseload — the counsellor's primary view
    # ------------------------------------------------------------------

    @staticmethod
    def _to_caseload_row(row: dict) -> CaseloadStudentResponse:
        attendance = row.get("attendance_percentage")
        attendance = float(attendance) if attendance is not None else None

        counsellor_name = None
        if row.get("counsellor_first_name"):
            counsellor_name = f"{row['counsellor_first_name']} {row['counsellor_last_name']}"

        return CaseloadStudentResponse(
            id=str(row["id"]),
            roll_number=row["roll_number"],
            registration_number=row["registration_number"],
            full_name=f"{row['first_name']} {row['last_name']}",
            email=row["email"],
            phone=row.get("phone"),
            gender=row.get("gender"),
            photo_url=row.get("photo_url"),
            study_year=row.get("study_year"),
            section_id=str(row["section_id"]) if row.get("section_id") else None,
            section_name=row.get("section_name"),
            semester_id=str(row["semester_id"]) if row.get("semester_id") else None,
            semester_name=row.get("semester_name"),
            batch_year=row["batch_year"],
            department_id=str(row["department_id"]),
            department_name=row.get("department_name"),
            department_code=row.get("department_code"),
            attendance_percentage=attendance,
            total_classes=row.get("total_classes"),
            attended_classes=int(row["attended_classes"]) if row.get("attended_classes") is not None else None,
            sgpa=float(row["sgpa"]) if row.get("sgpa") is not None else None,
            cgpa=float(row["cgpa"]) if row.get("cgpa") is not None else None,
            active_backlogs=row.get("active_backlogs") or 0,
            risk_level=row["risk_level"],
            status=row["status"],
            last_session_date=row.get("last_session_date"),
            session_count=row.get("session_count") or 0,
            counsellor_id=str(row["counsellor_id"]) if row.get("counsellor_id") else None,
            counsellor_name=counsellor_name,
            attendance_below_threshold=attendance is not None and attendance < ATTENDANCE_THRESHOLD,
        )

    async def list_caseload(
        self, page: int = 1, per_page: int = 25, **filters
    ) -> PaginatedResponse[CaseloadStudentResponse]:
        rows, total = await self.repo.list_caseload(page=page, per_page=per_page, **filters)
        return PaginatedResponse.create(
            [self._to_caseload_row(r) for r in rows],
            total,
            PaginationParams(page=page, per_page=per_page),
        )

    async def get_caseload_facets(self, counsellor_id: Optional[str] = None) -> CaseloadFacets:
        raw = await self.repo.caseload_facets(counsellor_id)
        return CaseloadFacets(
            years=raw["years"],
            sections=[FacetOption(**s) for s in raw["sections"]],
            semesters=[FacetOption(**s) for s in raw["semesters"]],
            departments=[FacetOption(**d) for d in raw["departments"]],
            batch_years=raw["batch_years"],
            risk_levels=raw["risk_levels"],
            statuses=raw["statuses"],
        )

    async def get_session_context(self, student_id: str) -> SessionContextResponse:
        """Auto-populated header for the session recorder. The counsellor picks
        a student from their caseload; every field below is resolved server-side
        from that id, so no Student ID is ever typed or spoofable."""
        row = await self.repo.get_caseload_row(student_id)
        if not row:
            raise NotFoundError("Student not found")

        student = await self.repo.get_student_by_id(student_id)
        dept_name = None
        if student and student.department_id:
            dept = await self.admin_repo.get_department_by_id(str(student.department_id))
            if dept:
                dept_name = dept.name

        last_session = await self.counselling_repo.get_last_session_for_student(student_id)
        pending_raw = await self.counselling_repo.list_pending_items_for_student(student_id)
        today = date.today()

        pending = [
            PendingActionItem(
                id=str(item.id),
                description=item.description,
                due_date=item.due_date,
                status=item.status,
                is_overdue=item.due_date < today,
                session_id=str(sess.id),
                session_date=sess.session_date,
            )
            for item, sess in pending_raw
        ]

        attendance = float(row["attendance_percentage"]) if row.get("attendance_percentage") is not None else None
        cgpa = float(row["cgpa"]) if row.get("cgpa") is not None else None
        backlogs = row.get("active_backlogs") or 0

        attention: list[str] = []
        if row["risk_level"] in ("HIGH", "CRITICAL"):
            attention.append(f"Flagged as {row['risk_level']} risk.")
        if attendance is not None and attendance < ATTENDANCE_THRESHOLD:
            attention.append(f"Attendance is {attendance}%, below the {ATTENDANCE_THRESHOLD:.0f}% threshold.")
        if backlogs:
            attention.append(f"{backlogs} active backlog(s) pending clearance.")
        overdue = [p for p in pending if p.is_overdue]
        if overdue:
            attention.append(f"{len(overdue)} action item(s) from a previous session are overdue.")

        return SessionContextResponse(
            student_id=str(row["id"]),
            roll_number=row["roll_number"],
            full_name=f"{row['first_name']} {row['last_name']}",
            email=row["email"],
            department_name=dept_name,
            section_name=row.get("section_name"),
            study_year=row.get("study_year"),
            semester_id=str(row["semester_id"]) if row.get("semester_id") else None,
            semester_name=row.get("semester_name"),
            attendance_percentage=attendance,
            cgpa=cgpa,
            sgpa=float(row["sgpa"]) if row.get("sgpa") is not None else None,
            active_backlogs=backlogs,
            risk_level=row["risk_level"],
            last_session_date=last_session.session_date if last_session else None,
            # A summary, not the full note — this header is a memory aid, and
            # the full record lives in the 360 workspace's Counselling tab.
            last_session_summary=(
                (last_session.observations[:280] + "…")
                if last_session and len(last_session.observations) > 280
                else (last_session.observations if last_session else None)
            ),
            last_session_type=last_session.session_type if last_session else None,
            total_sessions=row.get("session_count") or 0,
            pending_action_items=pending,
            attention_items=attention,
        )

    async def get_student_profile(self, student_id: str) -> StudentProfileResponse:
        student = await self.repo.get_student_by_id(student_id)
        if not student:
            raise NotFoundError("Student not found")

        dept_name = None
        if student.department_id:
            dept = await self.admin_repo.get_department_by_id(str(student.department_id))
            if dept:
                dept_name = dept.name

        profile = student.profile

        counsellor_name = None
        if student.counsellor_assignments:
            active_assign = next(
                (a for a in student.counsellor_assignments if a.effective_to is None), None
            )
            if active_assign and active_assign.counsellor:
                counsellor_name = active_assign.counsellor.full_name

        return StudentProfileResponse(
            id=str(student.id),
            user_id=str(student.user_id),
            roll_number=student.roll_number,
            registration_number=student.registration_number,
            full_name=student.user.full_name if student.user else "Unknown",
            email=student.user.email if student.user else "",
            phone=student.user.phone if student.user else None,
            date_of_birth=student.date_of_birth,
            batch_year=student.batch_year,
            status=student.status,
            risk_level=student.risk_level,
            department_id=str(student.department_id),
            department_name=dept_name,
            current_semester_id=str(student.current_semester_id) if student.current_semester_id else None,
            counsellor_name=counsellor_name,
            # Family details are student-maintained and now live on
            # student_profiles; a student who hasn't filled theirs in yet has
            # no profile row loaded, hence the guard.
            father_name=profile.father_name if profile else None,
            father_phone=profile.father_phone if profile else None,
            mother_name=profile.mother_name if profile else None,
            mother_phone=profile.mother_phone if profile else None,
            guardian_name=profile.guardian_name if profile else None,
            guardian_phone=profile.guardian_phone if profile else None,
            created_at=student.created_at,
            updated_at=student.updated_at,
        )

    async def get_section_roster(self, section_id: str, semester_id: str) -> list[RosterStudentResponse]:
        students = await self.repo.list_roster(section_id, semester_id)
        return [
            RosterStudentResponse(
                id=str(s.id),
                roll_number=s.roll_number,
                full_name=s.user.full_name if s.user else "Unknown",
            )
            for s in students
        ]

    async def get_my_student_id(self, user_id: str) -> str:
        student = await self.repo.get_student_by_user_id(user_id)
        if not student:
            raise NotFoundError("No student record is linked to this account")
        return str(student.id)

    async def get_student_360_workspace(self, student_id: str) -> Student360Response:
        profile = await self.get_student_profile(student_id)

        attendance_records = await self.attendance_repo.get_student_attendance_records(student_id)
        if attendance_records:
            attended = sum(1 for r in attendance_records if r.status in ["PRESENT", "ON_DUTY"])
            attendance_pct = round((attended / len(attendance_records)) * 100, 1)
        else:
            attendance_pct = None

        sgpa_history = await self.academics_repo.get_student_sgpa_history(student_id)
        latest_sgpa = sgpa_history[-1] if sgpa_history else None

        backlogs = await self.academics_repo.get_student_backlogs(student_id)
        active_backlogs = [b for b in backlogs if b.status == "ACTIVE"]

        stats = [
            OverviewStat(
                title="Overall Attendance",
                value=f"{attendance_pct}%" if attendance_pct is not None else "No data",
                trend=(
                    "up" if attendance_pct is not None and attendance_pct >= 75
                    else "down" if attendance_pct is not None
                    else "neutral"
                ),
                description=(
                    "Above 75% threshold" if attendance_pct is not None and attendance_pct >= 75
                    else "Below 75% threshold" if attendance_pct is not None
                    else "No attendance recorded yet"
                ),
            ),
            OverviewStat(
                title="Current SGPA",
                value=f"{latest_sgpa.sgpa:.2f}" if latest_sgpa else "No data",
                description=f"CGPA: {latest_sgpa.cgpa:.2f}" if latest_sgpa else "No marks recorded yet",
            ),
            OverviewStat(
                title="Active Backlogs",
                value=str(len(active_backlogs)),
                trend="neutral" if not active_backlogs else "down",
                description="All subjects cleared" if not active_backlogs else "Subjects pending clearance",
            ),
            OverviewStat(
                title="Risk Level",
                value=profile.risk_level,
                trend="neutral",
                description=f"Current Status: {profile.status}",
            ),
        ]

        attention_items = []
        if profile.risk_level in ["HIGH", "CRITICAL"]:
            attention_items.append(f"Student is flagged as {profile.risk_level} risk level.")
        if attendance_pct is not None and attendance_pct < 75:
            attention_items.append(f"Attendance is {attendance_pct}%, below the 75% threshold.")
        if active_backlogs:
            attention_items.append(f"{len(active_backlogs)} active backlog(s) pending clearance.")

        return Student360Response(
            profile=profile,
            stats=stats,
            attention_items=attention_items,
            # No persisted, queryable timeline store exists yet (domain events
            # are published in-process only) — an honest empty list rather
            # than fabricated history entries.
            recent_events=[],
        )

    async def update_risk_flag(
        self, student_id: str, data: RiskFlagUpdateRequest, actor_id: str
    ) -> StudentProfileResponse:
        student = await self.repo.get_student_by_id(student_id)
        if not student:
            raise NotFoundError("Student not found")

        old_risk = student.risk_level
        student.risk_level = data.risk_level.upper()
        student.updated_by = actor_id
        await self.db.commit()

        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.RISK_FLAG_CHANGED.value,
                student_id=str(student.id),
                actor_id=actor_id,
                metadata={
                    "previous_risk_level": old_risk,
                    "new_risk_level": student.risk_level,
                    "reason": data.reason,
                },
            )
        )

        return await self.get_student_profile(student_id)

    # ------------------------------------------------------------------
    # Academic Record Correction Request & CRM Workflow
    # ------------------------------------------------------------------

    async def _to_correction_response(self, req) -> AcademicCorrectionResponse:
        from app.features.students.schemas import AcademicCorrectionResponse, AcademicCorrectionLogResponse
        doc_name = req.document.original_filename if req.document else None
        doc_url = req.document.file_url if req.document else None

        student_name = req.student.user.full_name if req.student and req.student.user else None
        student_roll = req.student.roll_number if req.student else None
        counsellor_name = req.counsellor.full_name if req.counsellor else None

        logs_resp = [
            AcademicCorrectionLogResponse(
                id=str(log.id),
                actor_id=str(log.actor_id),
                actor_name=log.actor.full_name if log.actor else "System",
                action=log.action,
                from_status=log.from_status,
                to_status=log.to_status,
                remarks=log.remarks,
                document_id=str(log.document_id) if log.document_id else None,
                created_at=log.created_at,
            )
            for log in req.logs
        ]

        return AcademicCorrectionResponse(
            id=str(req.id),
            student_id=str(req.student_id),
            student_name=student_name,
            student_roll=student_roll,
            counsellor_id=str(req.counsellor_id) if req.counsellor_id else None,
            counsellor_name=counsellor_name,
            section_name=req.section_name,
            current_value=req.current_value,
            proposed_value=req.proposed_value,
            description=req.description,
            document_id=str(req.document_id) if req.document_id else None,
            document_name=doc_name,
            document_url=doc_url,
            status=req.status,
            counsellor_remarks=req.counsellor_remarks,
            reviewed_by_user_id=str(req.reviewed_by_user_id) if req.reviewed_by_user_id else None,
            reviewed_at=req.reviewed_at,
            created_at=req.created_at,
            updated_at=req.updated_at,
            logs=logs_resp,
        )

    async def create_academic_correction_request(
        self, student_user_id: str, data
    ) -> AcademicCorrectionResponse:
        from app.features.students.models import AcademicCorrectionRequest, AcademicCorrectionLog
        from app.features.notifications.models import Notification
        from app.features.notifications.repository import NotificationRepository

        student = await self.repo.get_student_by_user_id(student_user_id)
        if not student:
            raise NotFoundError("Student record not found for user")

        # Resolve active assigned counsellor
        counsellor_id = None
        if student.counsellor_assignments:
            active_assign = next(
                (a for a in student.counsellor_assignments if a.effective_to is None), None
            )
            if active_assign:
                counsellor_id = str(active_assign.counsellor_id)

        request = AcademicCorrectionRequest(
            student_id=str(student.id),
            counsellor_id=counsellor_id,
            section_name=data.section_name,
            current_value=data.current_value,
            proposed_value=data.proposed_value,
            description=data.description,
            document_id=data.document_id,
            status="SUBMITTED",
        )

        log = AcademicCorrectionLog(
            request_id=str(request.id),
            actor_id=student_user_id,
            action="SUBMITTED",
            from_status="DRAFT",
            to_status="SUBMITTED",
            remarks="Submitted initial academic correction request",
            document_id=data.document_id,
        )

        created_req = await self.repo.create_correction_request(request, log)

        # Notify counsellor if assigned
        if counsellor_id:
            notif_repo = NotificationRepository(self.db)
            student_name = student.user.full_name if student.user else "Student"
            await notif_repo.create_notification(
                Notification(
                    user_id=counsellor_id,
                    type="APPROVAL_REQUEST",
                    category="ACADEMIC",
                    priority="HIGH",
                    title=f"Academic Correction Request: {data.section_name}",
                    message=f"{student_name} ({student.roll_number}) submitted a correction request for {data.section_name}.",
                    action_url=f"/student-360/corrections",
                )
            )

        await self.db.commit()
        refreshed = await self.repo.get_correction_request_by_id(str(created_req.id))
        return await self._to_correction_response(refreshed)

    async def list_my_academic_corrections(self, student_user_id: str) -> list[AcademicCorrectionResponse]:
        student = await self.repo.get_student_by_user_id(student_user_id)
        if not student:
            raise NotFoundError("Student record not found")
        requests = await self.repo.list_correction_requests_by_student(str(student.id))
        return [await self._to_correction_response(r) for r in requests]

    async def list_counsellor_academic_corrections(self, counsellor_user_id: Optional[str] = None) -> list[AcademicCorrectionResponse]:
        requests = await self.repo.list_correction_requests_by_counsellor(counsellor_user_id)
        return [await self._to_correction_response(r) for r in requests]

    async def get_academic_correction(self, request_id: str) -> AcademicCorrectionResponse:
        req = await self.repo.get_correction_request_by_id(request_id)
        if not req:
            raise NotFoundError("Correction request not found")
        return await self._to_correction_response(req)

    async def review_academic_correction(
        self, request_id: str, reviewer_user_id: str, data
    ) -> AcademicCorrectionResponse:
        from datetime import datetime, timezone
        from app.features.students.models import AcademicCorrectionLog
        from app.features.notifications.models import Notification
        from app.features.notifications.repository import NotificationRepository

        req = await self.repo.get_correction_request_by_id(request_id)
        if not req:
            raise NotFoundError("Correction request not found")

        old_status = req.status
        new_status = data.status.upper()

        req.status = new_status
        req.counsellor_remarks = data.remarks
        req.reviewed_by_user_id = reviewer_user_id
        req.reviewed_at = datetime.now(timezone.utc)

        log = AcademicCorrectionLog(
            request_id=str(req.id),
            actor_id=reviewer_user_id,
            action=new_status,
            from_status=old_status,
            to_status=new_status,
            remarks=data.remarks,
        )
        await self.repo.add_correction_log(log)

        # Notify student
        student_user_id = str(req.student.user_id)
        notif_repo = NotificationRepository(self.db)

        if new_status == "NEED_MORE_INFO":
            title = f"Clarification Requested: {req.section_name} Correction"
            msg = f"Your counsellor requested additional information regarding your {req.section_name} correction request: {data.remarks or ''}"
        elif new_status == "APPROVED":
            title = f"Approved: {req.section_name} Correction Request"
            msg = f"Your {req.section_name} academic correction request has been approved."
        elif new_status == "REJECTED":
            title = f"Rejected: {req.section_name} Correction Request"
            msg = f"Your {req.section_name} academic correction request was rejected. Remarks: {data.remarks or 'None'}"
        else:
            title = f"Update on {req.section_name} Correction Request"
            msg = f"Status updated to {new_status}."

        await notif_repo.create_notification(
            Notification(
                user_id=student_user_id,
                type="SYSTEM",
                category="ACADEMIC",
                priority="HIGH",
                title=title,
                message=msg,
                action_url=f"/student-360/corrections",
            )
        )

        await self.db.commit()
        refreshed = await self.repo.get_correction_request_by_id(request_id)
        return await self._to_correction_response(refreshed)

    async def submit_clarification(
        self, request_id: str, student_user_id: str, data
    ) -> AcademicCorrectionResponse:
        from datetime import datetime, timezone
        from app.features.students.models import AcademicCorrectionLog
        from app.features.notifications.models import Notification
        from app.features.notifications.repository import NotificationRepository

        req = await self.repo.get_correction_request_by_id(request_id)
        if not req:
            raise NotFoundError("Correction request not found")

        old_status = req.status
        new_status = "UNDER_REVIEW"

        req.status = new_status
        if data.document_id:
            req.document_id = data.document_id

        log = AcademicCorrectionLog(
            request_id=str(req.id),
            actor_id=student_user_id,
            action="CLARIFICATION_SUBMITTED",
            from_status=old_status,
            to_status=new_status,
            remarks=data.remarks or "Student provided clarification and supporting document",
            document_id=data.document_id,
        )
        await self.repo.add_correction_log(log)

        # Notify counsellor
        if req.counsellor_id:
            notif_repo = NotificationRepository(self.db)
            student_name = req.student.user.full_name if req.student and req.student.user else "Student"
            await notif_repo.create_notification(
                Notification(
                    user_id=str(req.counsellor_id),
                    type="APPROVAL_REQUEST",
                    category="ACADEMIC",
                    priority="HIGH",
                    title=f"Clarification Provided: {req.section_name}",
                    message=f"{student_name} submitted requested information for {req.section_name} correction.",
                    action_url=f"/student-360/corrections",
                )
            )

        await self.db.commit()
        refreshed = await self.repo.get_correction_request_by_id(request_id)
        return await self._to_correction_response(refreshed)

