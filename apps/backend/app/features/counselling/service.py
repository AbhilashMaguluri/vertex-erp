from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.events import event_bus, DomainEvent
from app.core.scoping import is_assignment_scoped_counsellor
from app.features.auth.models import User
from app.features.counselling.models import CounsellingSession, SessionActionItem
from app.features.counselling.repository import CounsellingRepository
from app.features.counselling.schemas import (
    SessionCreateRequest,
    SessionResponse,
    ActionItemResponse,
    ComplianceResponse,
    CounsellorDashboardResponse,
    ChartBucket,
    UpcomingFollowUp,
    AttentionStudent,
    ActivityEntry,
    AgendaEntry,
)
from app.features.students.repository import StudentRepository
from app.core.enums import TimelineEventType, FollowUpStatus


def _is_student(user: Optional[User]) -> bool:
    if user is None:
        return False
    return "STUDENT" in {r.name for r in user.roles}


class CounsellingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CounsellingRepository(db)
        self.student_repo = StudentRepository(db)

    @staticmethod
    def _to_response(
        session: CounsellingSession, viewer: Optional[User] = None
    ) -> SessionResponse:
        """The ONLY place a session becomes a wire response.

        Confidential notes are counsellor/admin narrative and are stripped for
        any student viewer — unconditionally, regardless of which endpoint is
        serving the record. Passing `viewer=None` (internal/staff callers)
        keeps the notes; every student-reachable path must pass the viewer.
        """
        response = SessionResponse.model_validate(session)
        if _is_student(viewer):
            response.confidential_notes = None
        return response

    async def create_session(self, data: SessionCreateRequest, counsellor_id: str) -> SessionResponse:
        if len(data.observations.strip()) < 50:
            raise ValidationError("Observations must contain at least 50 characters (PRD §23.1 requirement)")

        session = CounsellingSession(
            student_id=data.student_id,
            counsellor_id=counsellor_id,
            session_date=data.session_date,
            session_type=data.session_type.upper(),
            mode=data.mode.upper(),
            observations=data.observations,
            recommendations=data.recommendations,
            student_commitments=data.student_commitments,
            confidential_notes=data.confidential_notes,
            follow_up_required=data.follow_up_required,
            follow_up_date=data.follow_up_date,
            risk_assessment=data.risk_assessment.upper() if data.risk_assessment else "NONE",
            confidential=data.confidential,
        )

        if data.action_items:
            for item in data.action_items:
                action = SessionActionItem(
                    description=item.description,
                    due_date=item.due_date,
                    status=FollowUpStatus.PENDING.value,
                    assigned_to_user_id=item.assigned_to_user_id,
                )
                session.action_items.append(action)

        created_session = await self.repo.create_session(session)
        await self.db.commit()

        # Emit Domain Events
        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.SESSION_CONDUCTED.value,
                student_id=data.student_id,
                actor_id=counsellor_id,
                metadata={
                    "session_id": str(created_session.id),
                    "session_type": created_session.session_type,
                    "mode": created_session.mode,
                    "follow_up_required": created_session.follow_up_required,
                },
            )
        )

        if created_session.action_items:
            for item in created_session.action_items:
                await event_bus.publish(
                    DomainEvent(
                        type=TimelineEventType.FOLLOW_UP_CREATED.value,
                        student_id=data.student_id,
                        actor_id=counsellor_id,
                        metadata={
                            "action_item_id": str(item.id),
                            "description": item.description,
                            "due_date": str(item.due_date),
                        },
                    )
                )

        return self._to_response(created_session)

    async def get_session_by_id(self, session_id: str, current_user: Optional[User] = None) -> SessionResponse:
        session = await self.repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundError("Counselling session not found")
        if (
            current_user is not None
            and is_assignment_scoped_counsellor(current_user)
            and session.counsellor_id != current_user.id
        ):
            raise ForbiddenError("You may only access your own counselling sessions.")
        if _is_student(current_user):
            await self._ensure_own_record(session.student_id, current_user)
        return self._to_response(session, current_user)

    async def _ensure_own_record(self, student_id, current_user: User) -> None:
        """A student may only read counselling records attached to their own
        student row. Without this, holding counselling.acknowledge/read would
        let any student fetch any other student's session by id."""
        own = await self.student_repo.get_student_by_user_id(str(current_user.id))
        if not own or str(own.id) != str(student_id):
            raise ForbiddenError("You may only access your own counselling records.")

    async def list_sessions(
        self,
        student_id: Optional[str] = None,
        counsellor_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        viewer: Optional[User] = None,
    ) -> Tuple[List[SessionResponse], int]:
        sessions, total = await self.repo.list_sessions(student_id, counsellor_id, page, per_page)
        return [self._to_response(s, viewer) for s in sessions], total

    async def list_my_sessions(
        self, user_id: str, page: int = 1, per_page: int = 50, viewer: Optional[User] = None
    ) -> List[SessionResponse]:
        student = await self.student_repo.get_student_by_user_id(user_id)
        if not student:
            raise NotFoundError("No student record is linked to this account")
        sessions, _ = await self.repo.list_sessions(
            student_id=str(student.id), counsellor_id=None, page=page, per_page=per_page
        )
        return [self._to_response(s, viewer) for s in sessions]

    async def list_follow_ups(
        self, counsellor_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[ActionItemResponse]:
        items = await self.repo.list_follow_ups(counsellor_id, status)
        return [ActionItemResponse.model_validate(i) for i in items]

    _FOLLOW_UP_STATUSES = {s.value for s in FollowUpStatus}

    async def update_follow_up(
        self,
        action_item_id: str,
        current_user: Optional[User] = None,
        new_status: Optional[str] = None,
        new_due_date: Optional[date] = None,
    ) -> ActionItemResponse:
        """Complete or reschedule one action item.

        Ownership is enforced here, not just at the permission layer:
        `counselling.update` says a counsellor may edit follow-ups at all, not
        WHICH ones. Without this check the action item id in the URL is a
        straight IDOR — any counsellor could close or move an item belonging to
        a colleague's session. ADMIN/SUPER_ADMIN/HOD stay institution-wide.
        """
        found = await self.repo.get_action_item_with_session(action_item_id)
        if not found:
            raise NotFoundError("Follow-up action item not found")
        item, session = found

        if (
            current_user is not None
            and is_assignment_scoped_counsellor(current_user)
            and str(session.counsellor_id) != str(current_user.id)
        ):
            raise ForbiddenError("You may only update follow-ups from your own sessions.")

        if new_status is not None:
            status = new_status.upper()
            if status not in self._FOLLOW_UP_STATUSES:
                raise ValidationError(
                    f"Unknown follow-up status '{new_status}'. "
                    f"Expected one of: {', '.join(sorted(self._FOLLOW_UP_STATUSES))}."
                )
            item.status = status
            item.status_changed_at = datetime.now(timezone.utc)

        if new_due_date is not None:
            # A follow-up can be pushed out but not backdated — rescheduling
            # into the past would silently mark the item overdue on save.
            if new_due_date < date.today():
                raise ValidationError("A follow-up cannot be rescheduled to a past date.")
            item.due_date = new_due_date
            # Rescheduling a closed item reopens it; otherwise the new date
            # would sit on a COMPLETED row and never surface again.
            if item.status == FollowUpStatus.COMPLETED.value:
                item.status = FollowUpStatus.PENDING.value
                item.status_changed_at = datetime.now(timezone.utc)

        if new_status is None and new_due_date is None:
            raise ValidationError("Provide a status or a due date to update.")

        await self.db.commit()
        await self.db.refresh(item)
        return ActionItemResponse.model_validate(item)

    async def update_follow_up_status(
        self, action_item_id: str, new_status: str, current_user: Optional[User] = None
    ) -> ActionItemResponse:
        return await self.update_follow_up(
            action_item_id, current_user=current_user, new_status=new_status
        )

    async def acknowledge_session(
        self, session_id: str, student_user_id: str, current_user: Optional[User] = None
    ) -> SessionResponse:
        session = await self.repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundError("Counselling session not found")

        if _is_student(current_user):
            await self._ensure_own_record(session.student_id, current_user)

        session.student_acknowledged = True
        session.acknowledged_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Emit acknowledgment event
        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.SESSION_ACKNOWLEDGED.value,
                student_id=str(session.student_id),
                actor_id=student_user_id,
                metadata={"session_id": session_id},
            )
        )

        return self._to_response(session, current_user)

    # ------------------------------------------------------------------
    # Counsellor dashboard
    # ------------------------------------------------------------------

    async def get_counsellor_dashboard(
        self, counsellor_id: Optional[str]
    ) -> CounsellorDashboardResponse:
        today = date.today()
        # 12 months back, snapped to the 1st, for the session trend chart.
        since = (today.replace(day=1) - timedelta(days=365)).replace(day=1)

        cohort = await self.student_repo.caseload_aggregates(counsellor_id)
        sessions = await self.repo.counsellor_session_stats(counsellor_id, today)
        follow_ups = await self.repo.follow_up_stats(counsellor_id, today)
        by_month = await self.repo.sessions_by_month(counsellor_id, since)
        by_type = await self.repo.sessions_by_type(counsellor_id)
        # 25 rather than 10: the workspace splits these across "today's tasks"
        # and the follow-up tracker, and paging both off one fetch beats two.
        upcoming_raw = await self.repo.list_upcoming_follow_ups(counsellor_id, limit=25)
        active_cases = await self.repo.count_active_cases(counsellor_id)
        activity_raw = await self.repo.list_recent_activity(counsellor_id, limit=12)
        sessions_today_raw = await self.repo.list_sessions_on(counsellor_id, today)

        student_ids = {str(sess.student_id) for _, sess in upcoming_raw}
        student_lookup: dict[str, tuple[str, str]] = {}
        for sid in student_ids:
            row = await self.student_repo.get_caseload_row(sid)
            if row:
                student_lookup[sid] = (
                    f"{row['first_name']} {row['last_name']}",
                    row["roll_number"],
                )

        upcoming = []
        for item, sess in upcoming_raw:
            sid = str(sess.student_id)
            name, roll = student_lookup.get(sid, ("Unknown", "—"))
            upcoming.append(
                UpcomingFollowUp(
                    id=str(item.id),
                    description=item.description,
                    due_date=item.due_date,
                    is_overdue=item.due_date < today,
                    is_due_today=item.due_date == today,
                    student_id=sid,
                    student_name=name,
                    student_roll_number=roll,
                    session_id=str(sess.id),
                    session_date=sess.session_date,
                )
            )

        attention = await self._students_needing_attention(counsellor_id)

        recent_activity = [
            ActivityEntry(
                session_id=str(r["session_id"]),
                student_id=str(r["student_id"]),
                student_name=f"{r['first_name']} {r['last_name']}",
                student_roll_number=r["roll_number"],
                session_type=r["session_type"],
                mode=r["mode"],
                session_date=r["session_date"],
                recorded_at=r["created_at"],
                follow_up_required=bool(r["follow_up_required"]),
            )
            for r in activity_raw
        ]

        agenda = self._build_agenda(upcoming, sessions_today_raw, today)

        risk_counts = {b["bucket"]: b["count"] for b in cohort["by_risk"]}

        return CounsellorDashboardResponse(
            total_students=cohort["total_students"],
            male=cohort["male"],
            female=cohort["female"],
            gender_unknown=cohort["gender_unknown"],
            average_attendance=cohort["average_attendance"],
            average_cgpa=cohort["average_cgpa"],
            sessions_total=sessions["total"],
            sessions_today=sessions["today"],
            sessions_this_month=sessions["this_month"],
            sessions_acknowledged=sessions["acknowledged"],
            follow_ups_pending=follow_ups["pending"],
            follow_ups_completed=follow_ups["completed"],
            follow_ups_overdue=follow_ups["overdue"],
            follow_ups_upcoming=follow_ups["upcoming"],
            active_cases=active_cases,
            high_risk_count=cohort["high_risk_count"],
            below_attendance_count=cohort["below_attendance_count"],
            with_backlogs_count=cohort["with_backlogs_count"],
            risk_high=risk_counts.get("HIGH", 0) + risk_counts.get("CRITICAL", 0),
            risk_medium=risk_counts.get("MEDIUM", 0),
            risk_low=risk_counts.get("LOW", 0) + risk_counts.get("NONE", 0),
            by_year=[ChartBucket(**b) for b in cohort["by_year"]],
            by_section=[ChartBucket(**b) for b in cohort["by_section"]],
            by_risk=[ChartBucket(**b) for b in cohort["by_risk"]],
            by_attendance_band=[ChartBucket(**b) for b in cohort["by_attendance_band"]],
            sessions_by_month=[ChartBucket(bucket=m, count=c) for m, c in by_month],
            sessions_by_type=[ChartBucket(bucket=t, count=c) for t, c in by_type],
            upcoming_follow_ups=upcoming,
            students_needing_attention=attention,
            recent_activity=recent_activity,
            agenda_today=agenda,
        )

    @staticmethod
    def _build_agenda(
        upcoming: List[UpcomingFollowUp], sessions_today: List[dict], today: date
    ) -> List[AgendaEntry]:
        """Today's agenda, assembled from the only dated work this system
        actually stores: action items that have come due, and sessions already
        recorded today. Overdue items lead — they were owed before today.

        There is deliberately no clock time on these entries; see AgendaEntry.
        """
        entries: List[AgendaEntry] = [
            AgendaEntry(
                kind="FOLLOW_UP",
                reference_id=f.id,
                student_id=f.student_id,
                student_name=f.student_name,
                student_roll_number=f.student_roll_number,
                label=f.description,
                due_date=f.due_date,
                is_overdue=f.is_overdue,
            )
            for f in upcoming
            if f.due_date <= today
        ]
        entries.sort(key=lambda e: (not e.is_overdue, e.due_date))

        entries.extend(
            AgendaEntry(
                kind="SESSION",
                reference_id=str(r["session_id"]),
                student_id=str(r["student_id"]),
                student_name=f"{r['first_name']} {r['last_name']}",
                student_roll_number=r["roll_number"],
                label=f"{r['session_type'].title()} session recorded",
                due_date=r["session_date"],
                is_overdue=False,
            )
            for r in sessions_today
        )
        return entries

    async def _students_needing_attention(
        self, counsellor_id: Optional[str], limit: int = 12
    ) -> List[AttentionStudent]:
        """Highest-risk students first, then the attendance and backlog
        defaulters — the worklist the counsellor should open first."""
        rows, _ = await self.student_repo.list_caseload(
            counsellor_id=counsellor_id,
            sort_by="risk",
            sort_dir="desc",
            per_page=60,
        )

        out: List[AttentionStudent] = []
        for r in rows:
            attendance = float(r["attendance_percentage"]) if r.get("attendance_percentage") is not None else None
            backlogs = r.get("active_backlogs") or 0
            reasons: List[str] = []
            flags: List[str] = []
            if r["risk_level"] in ("HIGH", "CRITICAL"):
                reasons.append(f"{r['risk_level']} risk")
                flags.append("HIGH_RISK")
            if attendance is not None and attendance < 75:
                reasons.append(f"attendance {attendance}%")
                flags.append("LOW_ATTENDANCE")
            # "More than 3 backlogs" is its own escalation tier, above simply
            # carrying one.
            if backlogs > 3:
                reasons.append(f"{backlogs} backlogs")
                flags.append("MANY_BACKLOGS")
            elif backlogs:
                reasons.append(f"{backlogs} backlog(s)")
                flags.append("BACKLOGS")
            if r.get("last_session_date") is None:
                flags.append("NEVER_COUNSELLED")
            if not reasons:
                continue
            out.append(
                AttentionStudent(
                    id=str(r["id"]),
                    roll_number=r["roll_number"],
                    full_name=f"{r['first_name']} {r['last_name']}",
                    email=r.get("email"),
                    phone=r.get("phone"),
                    section_name=r.get("section_name"),
                    study_year=r.get("study_year"),
                    risk_level=r["risk_level"],
                    attendance_percentage=attendance,
                    cgpa=float(r["cgpa"]) if r.get("cgpa") is not None else None,
                    active_backlogs=backlogs,
                    last_session_date=r.get("last_session_date"),
                    reason=", ".join(reasons),
                    flags=flags,
                )
            )
            if len(out) >= limit:
                break
        return out
