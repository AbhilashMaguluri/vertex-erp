"""Context models — everything Vertex knows about a request besides the words.

Stage 2 of the pipeline builds these. The rule that shapes the whole file:

    Identity, role and permissions are SERVER-DERIVED, never client-supplied.

The browser may tell us where the user is standing (route, selected student,
open dialog) because only the browser knows that. It may not tell us who the
user is — that comes from the bearer token and the database, so a crafted
request body cannot promote a student to admin.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserContext(BaseModel):
    """Identity and authority of the caller. Rebuilt server-side every request."""

    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None  # Primary role — "STUDENT", "COUNSELLOR", …
    roles: List[str] = Field(default_factory=list)
    department: Optional[str] = None
    department_id: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

    # Set only when the caller is a student — the id of their `students` row,
    # which is NOT the same as their user id. Every student-scoped tool
    # resolves through this rather than trusting anything in the message.
    student_id: Optional[str] = None
    roll_number: Optional[str] = None

    is_authenticated: bool = False

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_any_permission(self, permissions: List[str]) -> bool:
        return any(p in self.permissions for p in permissions)

    def has_role(self, *roles: str) -> bool:
        upper = {r.upper() for r in roles}
        return bool(upper & {r.upper() for r in self.roles})


class PageContext(BaseModel):
    """Where the user is standing inside the ERP.

    ``populate_by_name`` + camelCase aliases: the React client sends
    ``studentId``/``params``; accepting both spellings keeps the selected
    student from silently arriving as None.
    """

    model_config = ConfigDict(populate_by_name=True)

    page: str = "unknown"
    route: str = ""
    student_id: Optional[str] = Field(default=None, alias="studentId")
    params: Dict[str, str] = Field(default_factory=dict)

    # Free-form UI state the client volunteers (open dialog, active tab,
    # applied filters). Read-only hints — never trusted for authorisation.
    state: Dict = Field(default_factory=dict)


class SessionContext(BaseModel):
    """Conversation-level facts that outlive a single message."""

    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(default="", alias="sessionId")
    turn_count: int = Field(default=0, alias="turnCount")
    started_at: Optional[str] = Field(default=None, alias="startedAt")


class WorkspaceContext(BaseModel):
    """The record the user is actively working on, resolved server-side.

    A counsellor on /students/<id> is working *on that student*; Vertex should
    not ask "which student?" when the answer is on screen. Populated only after
    the caller's right to see that student has been confirmed.
    """

    student_id: Optional[str] = None
    student_name: Optional[str] = None
    student_roll: Optional[str] = None
    accessible: bool = False
    denied_reason: Optional[str] = None


class VertexContext(BaseModel):
    """The complete picture handed to every downstream stage.

    Instances that arrive on the request body are *hints*. The authoritative
    instance is produced by ContextBuilder and is what the pipeline uses.
    """

    user: UserContext = Field(default_factory=UserContext)
    page: PageContext = Field(default_factory=PageContext)
    session: SessionContext = Field(default_factory=SessionContext)
    workspace: WorkspaceContext = Field(default_factory=WorkspaceContext)

    mode: str = "guest"  # guest | student | counsellor | faculty | hod | admin
    timestamp: Optional[str] = None

    # Rolling summary of what has already been discussed, so the LLM keeps
    # continuity without the client resending unbounded history.
    conversation_summary: str = ""
    recent_topics: List[str] = Field(default_factory=list)

    request_id: str = ""

    # ------------------------------------------------------------------
    # Convenience accessors used across the pipeline
    # ------------------------------------------------------------------

    @property
    def is_guest(self) -> bool:
        return not self.user.is_authenticated

    @property
    def is_student(self) -> bool:
        return self.mode == "student"

    @property
    def is_staff(self) -> bool:
        return self.mode in ("counsellor", "faculty", "hod", "admin")

    def describe(self) -> str:
        """One-line rendering for logs."""
        return (
            f"mode={self.mode} user={self.user.id or 'anonymous'} "
            f"role={self.user.role or 'none'} page={self.page.page} "
            f"student={self.workspace.student_id or self.user.student_id or 'none'}"
        )
