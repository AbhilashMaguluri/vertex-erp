from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy import case, select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.features.auth.models import User
from app.features.counselling.models import CounsellingSession, SessionActionItem
from app.features.students.models import Student
from app.core.enums import FollowUpStatus


class CounsellingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, session: CounsellingSession) -> CounsellingSession:
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session_by_id(self, session_id: str) -> Optional[CounsellingSession]:
        query = (
            select(CounsellingSession)
            .options(selectinload(CounsellingSession.action_items))
            .where(CounsellingSession.id == session_id)
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def list_sessions(
        self, student_id: Optional[str] = None, counsellor_id: Optional[str] = None, page: int = 1, per_page: int = 20
    ) -> Tuple[List[CounsellingSession], int]:
        query = select(CounsellingSession)
        count_query = select(func.count(CounsellingSession.id))

        if student_id:
            query = query.where(CounsellingSession.student_id == student_id)
            count_query = count_query.where(CounsellingSession.student_id == student_id)

        if counsellor_id:
            query = query.where(CounsellingSession.counsellor_id == counsellor_id)
            count_query = count_query.where(CounsellingSession.counsellor_id == counsellor_id)

        query = (
            query.options(selectinload(CounsellingSession.action_items))
            .order_by(CounsellingSession.session_date.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )

        sessions_res = await self.db.execute(query)
        count_res = await self.db.execute(count_query)

        return list(sessions_res.scalars().all()), count_res.scalar_one()

    async def list_follow_ups(
        self, counsellor_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[SessionActionItem]:
        query = select(SessionActionItem).join(CounsellingSession)

        if status:
            query = query.where(SessionActionItem.status == status.upper())
        else:
            query = query.where(SessionActionItem.status == FollowUpStatus.PENDING.value)

        if counsellor_id:
            query = query.where(CounsellingSession.counsellor_id == counsellor_id)

        query = query.order_by(SessionActionItem.due_date.asc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def count_sessions_by_counsellor(self) -> List[Tuple[str, int]]:
        # NB: CounsellingSession is TimestampMixin-only — it has no deleted_at
        # column, so the soft-delete filter this query used to carry raised
        # AttributeError at statement-build time and broke the counsellor
        # compliance report outright. Sessions are an immutable clinical
        # record and are never soft-deleted, so counting all rows is correct.
        query = (
            select(CounsellingSession.counsellor_id, func.count(CounsellingSession.id))
            .group_by(CounsellingSession.counsellor_id)
        )
        res = await self.db.execute(query)
        return [(str(counsellor_id), count) for counsellor_id, count in res.all()]

    async def get_last_session_for_student(
        self, student_id: str
    ) -> Optional[CounsellingSession]:
        query = (
            select(CounsellingSession)
            .where(CounsellingSession.student_id == student_id)
            .order_by(CounsellingSession.session_date.desc(), CounsellingSession.created_at.desc())
            .limit(1)
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def list_student_sessions(self, student_id: str) -> List[CounsellingSession]:
        query = (
            select(CounsellingSession)
            .options(selectinload(CounsellingSession.action_items))
            .where(CounsellingSession.student_id == student_id)
            .order_by(CounsellingSession.session_date.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_pending_items_for_student(self, student_id: str) -> List[Tuple[SessionActionItem, CounsellingSession]]:
        query = (
            select(SessionActionItem, CounsellingSession)
            .join(CounsellingSession, CounsellingSession.id == SessionActionItem.session_id)
            .where(
                CounsellingSession.student_id == student_id,
                SessionActionItem.status != FollowUpStatus.COMPLETED.value,
            )
            .order_by(SessionActionItem.due_date.asc())
        )
        res = await self.db.execute(query)
        return [(item, sess) for item, sess in res.all()]

    async def counsellor_session_stats(self, counsellor_id: Optional[str], today: date) -> dict:
        """Session counts powering the counsellor dashboard tiles, as one
        grouped scan rather than four separate count queries."""
        month_start = today.replace(day=1)
        base = select(
            func.count(CounsellingSession.id).label("total"),
            func.sum(case((CounsellingSession.session_date == today, 1), else_=0)).label("today"),
            func.sum(case((CounsellingSession.session_date >= month_start, 1), else_=0)).label("this_month"),
            func.sum(
                case((CounsellingSession.follow_up_required.is_(True), 1), else_=0)
            ).label("with_follow_up"),
            func.sum(
                case((CounsellingSession.student_acknowledged.is_(True), 1), else_=0)
            ).label("acknowledged"),
        )
        if counsellor_id:
            base = base.where(CounsellingSession.counsellor_id == counsellor_id)
        res = await self.db.execute(base)
        row = res.first()
        return {
            "total": row.total or 0,
            "today": int(row.today or 0),
            "this_month": int(row.this_month or 0),
            "with_follow_up": int(row.with_follow_up or 0),
            "acknowledged": int(row.acknowledged or 0),
        }

    async def follow_up_stats(self, counsellor_id: Optional[str], today: date) -> dict:
        base = select(
            func.count(SessionActionItem.id).label("total"),
            func.sum(
                case((SessionActionItem.status == FollowUpStatus.PENDING.value, 1), else_=0)
            ).label("pending"),
            func.sum(
                case((SessionActionItem.status == FollowUpStatus.COMPLETED.value, 1), else_=0)
            ).label("completed"),
            # "Overdue" is derived from the due date rather than trusted from
            # the stored status — nothing sweeps PENDING rows to OVERDUE on a
            # schedule, so the stored value goes stale the moment a due date
            # passes.
            func.sum(
                case(
                    (
                        (SessionActionItem.status != FollowUpStatus.COMPLETED.value)
                        & (SessionActionItem.due_date < today),
                        1,
                    ),
                    else_=0,
                )
            ).label("overdue"),
            func.sum(
                case(
                    (
                        (SessionActionItem.status != FollowUpStatus.COMPLETED.value)
                        & (SessionActionItem.due_date >= today),
                        1,
                    ),
                    else_=0,
                )
            ).label("upcoming"),
        ).join(CounsellingSession, CounsellingSession.id == SessionActionItem.session_id)
        if counsellor_id:
            base = base.where(CounsellingSession.counsellor_id == counsellor_id)
        res = await self.db.execute(base)
        row = res.first()
        return {
            "total": row.total or 0,
            "pending": int(row.pending or 0),
            "completed": int(row.completed or 0),
            "overdue": int(row.overdue or 0),
            "upcoming": int(row.upcoming or 0),
        }

    async def sessions_by_month(
        self, counsellor_id: Optional[str], since: date
    ) -> List[Tuple[str, int]]:
        month = func.to_char(CounsellingSession.session_date, "YYYY-MM")
        query = (
            select(month.label("month"), func.count(CounsellingSession.id).label("count"))
            .where(CounsellingSession.session_date >= since)
            .group_by(month)
            .order_by(month)
        )
        if counsellor_id:
            query = query.where(CounsellingSession.counsellor_id == counsellor_id)
        res = await self.db.execute(query)
        return [(m, c) for m, c in res.all()]

    async def sessions_by_type(self, counsellor_id: Optional[str]) -> List[Tuple[str, int]]:
        query = (
            select(CounsellingSession.session_type, func.count(CounsellingSession.id))
            .group_by(CounsellingSession.session_type)
        )
        if counsellor_id:
            query = query.where(CounsellingSession.counsellor_id == counsellor_id)
        res = await self.db.execute(query)
        return [(t, c) for t, c in res.all()]

    async def list_upcoming_follow_ups(
        self, counsellor_id: Optional[str], limit: int = 10
    ) -> List[Tuple[SessionActionItem, CounsellingSession]]:
        query = (
            select(SessionActionItem, CounsellingSession)
            .join(CounsellingSession, CounsellingSession.id == SessionActionItem.session_id)
            .where(SessionActionItem.status != FollowUpStatus.COMPLETED.value)
            .order_by(SessionActionItem.due_date.asc())
            .limit(limit)
        )
        if counsellor_id:
            query = query.where(CounsellingSession.counsellor_id == counsellor_id)
        res = await self.db.execute(query)
        return [(item, sess) for item, sess in res.all()]

    async def list_recent_activity(
        self, counsellor_id: Optional[str], limit: int = 12
    ) -> List[dict]:
        """The counsellor's own audit trail: sessions most recently recorded,
        already joined to the student's name so the feed is one query rather
        than a lookup per row."""
        query = (
            select(
                CounsellingSession.id.label("session_id"),
                CounsellingSession.student_id,
                CounsellingSession.session_type,
                CounsellingSession.mode,
                CounsellingSession.session_date,
                CounsellingSession.created_at,
                CounsellingSession.follow_up_required,
                Student.roll_number,
                User.first_name,
                User.last_name,
            )
            .join(Student, Student.id == CounsellingSession.student_id)
            .join(User, User.id == Student.user_id)
            # session_date is a plain date, so rows recorded on the same day
            # need created_at to break the tie deterministically.
            .order_by(CounsellingSession.session_date.desc(), CounsellingSession.created_at.desc())
            .limit(limit)
        )
        if counsellor_id:
            query = query.where(CounsellingSession.counsellor_id == counsellor_id)
        res = await self.db.execute(query)
        return [dict(r._mapping) for r in res.all()]

    async def count_active_cases(self, counsellor_id: Optional[str]) -> int:
        """Distinct students carrying at least one open action item — the work
        actually outstanding, as distinct from total headcount."""
        query = (
            select(func.count(func.distinct(CounsellingSession.student_id)))
            .select_from(SessionActionItem)
            .join(CounsellingSession, CounsellingSession.id == SessionActionItem.session_id)
            .where(SessionActionItem.status != FollowUpStatus.COMPLETED.value)
        )
        if counsellor_id:
            query = query.where(CounsellingSession.counsellor_id == counsellor_id)
        res = await self.db.execute(query)
        return res.scalar_one() or 0

    async def list_sessions_on(
        self, counsellor_id: Optional[str], on_date: date
    ) -> List[dict]:
        """Sessions recorded for a specific day, for the agenda widget."""
        query = (
            select(
                CounsellingSession.id.label("session_id"),
                CounsellingSession.student_id,
                CounsellingSession.session_type,
                CounsellingSession.session_date,
                Student.roll_number,
                User.first_name,
                User.last_name,
            )
            .join(Student, Student.id == CounsellingSession.student_id)
            .join(User, User.id == Student.user_id)
            .where(CounsellingSession.session_date == on_date)
            .order_by(CounsellingSession.created_at.asc())
        )
        if counsellor_id:
            query = query.where(CounsellingSession.counsellor_id == counsellor_id)
        res = await self.db.execute(query)
        return [dict(r._mapping) for r in res.all()]

    async def get_action_item_with_session(
        self, action_item_id: str
    ) -> Optional[Tuple[SessionActionItem, CounsellingSession]]:
        """Loads an action item alongside the session that owns it, so callers
        can check who the session belongs to before mutating the item."""
        query = (
            select(SessionActionItem, CounsellingSession)
            .join(CounsellingSession, CounsellingSession.id == SessionActionItem.session_id)
            .where(SessionActionItem.id == action_item_id)
        )
        res = await self.db.execute(query)
        row = res.first()
        return (row[0], row[1]) if row else None

    async def update_action_item_status(self, action_item_id: str, new_status: str) -> Optional[SessionActionItem]:
        query = select(SessionActionItem).where(SessionActionItem.id == action_item_id)
        res = await self.db.execute(query)
        item = res.scalar_one_or_none()

        if item:
            item.status = new_status.upper()
            await self.db.flush()

        return item
