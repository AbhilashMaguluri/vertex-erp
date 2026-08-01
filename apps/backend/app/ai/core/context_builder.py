"""Stage 2 — Context Builder.

Vertex never relies on the user's message alone. Before reasoning starts, this
assembles everything the application already knows so the user never has to
restate it: who they are, what they may do, which department they belong to,
which page they are on, which student is on screen, and what has been said so
far in the conversation.

Trust boundary — the whole reason this stage exists:

    From the bearer token + database : id, name, roles, permissions,
                                       department, linked student record.
    From the client request body     : current route, current page, selected
                                       student id, session id, UI state.

Anything in the first group that arrives in the request body is discarded. A
client that posts ``{"mode": "admin"}`` gets whatever its token actually
grants, which for an anonymous caller is guest.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models.context import (
    PageContext,
    SessionContext,
    UserContext,
    VertexContext,
    WorkspaceContext,
)
from app.ai.models.message import ChatMessage, MessageRole
from app.ai.models.request import VertexRequest

logger = logging.getLogger("vertex.context")

# Primary-role → operating mode. Order matters: a user holding several roles
# operates at the highest authority they hold.
_ROLE_PRECEDENCE: List[tuple[str, str]] = [
    ("SUPER_ADMIN", "admin"),
    ("ADMIN", "admin"),
    ("HOD", "hod"),
    ("COUNSELLOR", "counsellor"),
    ("FACULTY", "faculty"),
    ("STUDENT", "student"),
]

#: How many recent turns to mine for the rolling conversation summary.
_SUMMARY_WINDOW = 8


class ContextBuilder:
    """Builds the authoritative :class:`VertexContext` for one request."""

    def __init__(self, db: Optional[AsyncSession] = None) -> None:
        self._db = db

    async def build(
        self,
        request: VertexRequest,
        user: Optional[object],
        request_id: str = "",
    ) -> VertexContext:
        """Assemble context.

        ``user`` is the authenticated ``app.features.auth.models.User`` or None
        for an anonymous caller. It is the only accepted source of identity.
        """
        user_ctx, mode = await self._build_user(user)
        page_ctx = self._build_page(request)
        session_ctx = self._build_session(request)
        workspace = await self._build_workspace(user_ctx, mode, page_ctx)

        summary, topics = self._summarise_conversation(request.messages)

        return VertexContext(
            user=user_ctx,
            page=page_ctx,
            session=session_ctx,
            workspace=workspace,
            mode=mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_summary=summary,
            recent_topics=topics,
            request_id=request_id,
        )

    # ------------------------------------------------------------------
    # Identity — database-derived, never client-derived
    # ------------------------------------------------------------------

    async def _build_user(self, user) -> tuple[UserContext, str]:
        if user is None:
            return UserContext(is_authenticated=False), "guest"

        roles = [r.name for r in user.roles]
        permissions = sorted({p.name for role in user.roles for p in role.permissions})
        mode = self._derive_mode(roles)

        ctx = UserContext(
            id=str(user.id),
            name=user.full_name,
            email=user.email,
            role=self._primary_role(roles),
            roles=roles,
            department_id=str(user.department_id) if user.department_id else None,
            permissions=permissions,
            is_authenticated=True,
        )

        await self._attach_department(ctx, user)
        if mode == "student":
            await self._attach_student_record(ctx, str(user.id))

        return ctx, mode

    @staticmethod
    def _primary_role(roles: List[str]) -> Optional[str]:
        upper = {r.upper() for r in roles}
        for name, _ in _ROLE_PRECEDENCE:
            if name in upper:
                return name
        return roles[0] if roles else None

    @staticmethod
    def _derive_mode(roles: List[str]) -> str:
        upper = {r.upper() for r in roles}
        for name, mode in _ROLE_PRECEDENCE:
            if name in upper:
                return mode
        return "guest"

    async def _attach_department(self, ctx: UserContext, user) -> None:
        if not self._db or not user.department_id:
            return
        try:
            from app.features.admin.repository import AdminRepository

            dept = await AdminRepository(self._db).get_department_by_id(
                str(user.department_id)
            )
            if dept:
                ctx.department = dept.name
        except Exception as exc:  # context is best-effort; never fail a request
            logger.debug("Department lookup failed for user %s: %s", ctx.id, exc)

    async def _attach_student_record(self, ctx: UserContext, user_id: str) -> None:
        """Resolve the caller's `students` row.

        Student-scoped tools address records by student id, which is distinct
        from the user id. Resolving it once here is what lets a student say
        "my attendance" without supplying anything.
        """
        if not self._db:
            return
        try:
            from app.features.students.repository import StudentRepository

            student = await StudentRepository(self._db).get_student_by_user_id(user_id)
            if student:
                ctx.student_id = str(student.id)
                ctx.roll_number = student.roll_number
        except Exception as exc:
            logger.debug("Student record lookup failed for user %s: %s", user_id, exc)

    # ------------------------------------------------------------------
    # Location — client-supplied hints, sanitised
    # ------------------------------------------------------------------

    @staticmethod
    def _build_page(request: VertexRequest) -> PageContext:
        hint = request.context.page if request.context else PageContext()
        return PageContext(
            page=(hint.page or "unknown")[:80],
            route=(hint.route or "")[:200],
            student_id=hint.student_id,
            params={str(k)[:40]: str(v)[:200] for k, v in list(hint.params.items())[:20]},
            state=hint.state if isinstance(hint.state, dict) else {},
        )

    @staticmethod
    def _build_session(request: VertexRequest) -> SessionContext:
        hint = request.context.session if request.context else SessionContext()
        return SessionContext(
            session_id=(hint.session_id or "")[:64],
            turn_count=len([m for m in request.messages if m.role == MessageRole.USER]),
            started_at=hint.started_at,
        )

    # ------------------------------------------------------------------
    # Workspace — the record in view, access-checked
    # ------------------------------------------------------------------

    async def _build_workspace(
        self, user: UserContext, mode: str, page: PageContext
    ) -> WorkspaceContext:
        """Resolve the student currently in view.

        A student's workspace is always themselves. For staff it is whichever
        student the page is showing — but only after confirming they may see
        that student, so the workspace can never become a back door to a
        record the caller could not open directly.
        """
        if mode == "student":
            return WorkspaceContext(
                student_id=user.student_id,
                student_name=user.name,
                student_roll=user.roll_number,
                accessible=user.student_id is not None,
            )

        selected = page.student_id
        if not selected or not self._db:
            return WorkspaceContext()

        if not user.has_permission("student.read"):
            return WorkspaceContext(
                student_id=selected,
                accessible=False,
                denied_reason="Caller lacks student.read",
            )

        try:
            from app.features.students.repository import StudentRepository

            student = await StudentRepository(self._db).get_student_by_id(selected)
            if not student:
                return WorkspaceContext(
                    student_id=selected,
                    accessible=False,
                    denied_reason="Student not found",
                )

            # A counsellor may only work on their own caseload; HOD/ADMIN are
            # scoped by the feature routers and are allowed here.
            if mode == "counsellor" and not self._is_assigned(student, user.id):
                return WorkspaceContext(
                    student_id=selected,
                    accessible=False,
                    denied_reason="Student is not on this counsellor's caseload",
                )

            return WorkspaceContext(
                student_id=str(student.id),
                student_name=student.user.full_name if student.user else None,
                student_roll=student.roll_number,
                accessible=True,
            )
        except Exception as exc:
            logger.debug("Workspace resolution failed for student %s: %s", selected, exc)
            return WorkspaceContext(
                student_id=selected, accessible=False, denied_reason="Lookup failed"
            )

    @staticmethod
    def _is_assigned(student, counsellor_user_id: Optional[str]) -> bool:
        if not counsellor_user_id:
            return False
        return any(
            a.effective_to is None and str(a.counsellor_id) == counsellor_user_id
            for a in (student.counsellor_assignments or [])
        )

    # ------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------

    @staticmethod
    def _summarise_conversation(
        messages: List[ChatMessage],
    ) -> tuple[str, List[str]]:
        """Condense recent turns so the LLM keeps continuity cheaply.

        Deliberately extractive rather than model-generated: this runs on
        every request and must not add a round-trip.
        """
        history = messages[:-1] if messages else []
        if not history:
            return "", []

        window = history[-_SUMMARY_WINDOW:]
        user_turns = [m.content.strip() for m in window if m.role == MessageRole.USER]
        if not user_turns:
            return "", []

        topics = [t[:90] for t in user_turns[-4:]]
        summary = (
            f"Earlier in this session the user asked about: "
            f"{'; '.join(topics)}."
        )
        return summary, topics
