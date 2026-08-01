"""Stage 6 — Permission Validation.

Runs after planning and before any tool executes. Four questions, in order:

    Who is the current user?      → context.user, derived from the token
    What role do they hold?       → context.user.roles
    Who owns the resource?        → the plan's ownership decision
    Is this action allowed?       → the tool action's declared permissions

Nothing executes without passing all four. This is a second, independent
enforcement layer: the feature routers already guard their own endpoints with
``require_permission``, and this stage makes sure Vertex cannot be used as a
path around them.

The validator only ever *denies*. It never widens what a user can do.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from pydantic import BaseModel, Field

from app.ai.models.context import VertexContext
from app.ai.models.ownership import DataOwner, OwnershipDecision
from app.ai.models.plan import PlanStep
from app.ai.tools.base import ToolAction, ToolRegistry

logger = logging.getLogger("vertex.permissions")


class PermissionDecision(BaseModel):
    allowed: bool = True
    reason: str = ""

    #: Message shown to the user when denied. Explains what they *can* do
    #: rather than only what they cannot.
    user_message: str = ""

    missing_permissions: List[str] = Field(default_factory=list)
    checked: List[str] = Field(default_factory=list)

    @property
    def denied(self) -> bool:
        return not self.allowed


class PermissionValidator:
    """Validates a planned step against the caller's real authority."""

    def validate(
        self,
        step: PlanStep,
        ownership: OwnershipDecision,
        context: VertexContext,
        registry: ToolRegistry,
    ) -> PermissionDecision:
        tool = registry.get(step.tool_name)
        if tool is None:
            return PermissionDecision(
                allowed=False,
                reason=f"Tool '{step.tool_name}' is not registered",
                user_message="I can't do that yet — that capability isn't available.",
            )

        meta = tool.get_action_meta(step.tool_action)
        if meta is None:
            return PermissionDecision(
                allowed=False,
                reason=f"Tool '{step.tool_name}' does not support '{step.tool_action}'",
                user_message="I can't do that yet — that capability isn't available.",
            )

        for check in (
            self._check_authentication,
            self._check_permissions,
            self._check_ownership,
            self._check_subject_scope,
        ):
            decision = check(meta, ownership, context)
            if decision.denied:
                logger.info(
                    "[VERTEX] permission_denied tool=%s action=%s user=%s role=%s reason='%s'",
                    step.tool_name,
                    step.tool_action,
                    context.user.id or "anonymous",
                    context.user.role or "guest",
                    decision.reason,
                )
                return decision

        return PermissionDecision(
            allowed=True,
            reason="All permission checks passed",
            checked=list(meta.required_permissions),
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _check_authentication(
        meta: ToolAction, ownership: OwnershipDecision, context: VertexContext
    ) -> PermissionDecision:
        # An action carrying permissions implies authentication even if the
        # tool author forgot to say so.
        needs_auth = meta.requires_auth or bool(meta.required_permissions) or meta.mutates_state
        if needs_auth and not context.user.is_authenticated:
            return PermissionDecision(
                allowed=False,
                reason="Action requires authentication; caller is anonymous",
                user_message=(
                    "You'll need to sign in before I can do that. "
                    "Would you like me to take you to the login page?"
                ),
            )
        return PermissionDecision(allowed=True)

    @staticmethod
    def _check_permissions(
        meta: ToolAction, ownership: OwnershipDecision, context: VertexContext
    ) -> PermissionDecision:
        missing = [p for p in meta.required_permissions if not context.user.has_permission(p)]
        if missing:
            return PermissionDecision(
                allowed=False,
                reason=f"Missing permission(s): {', '.join(missing)}",
                user_message=(
                    "You don't have access to that. If you think you should, "
                    "your administrator can grant it."
                ),
                missing_permissions=missing,
                checked=list(meta.required_permissions),
            )
        return PermissionDecision(allowed=True, checked=list(meta.required_permissions))

    @staticmethod
    def _check_ownership(
        meta: ToolAction, ownership: OwnershipDecision, context: VertexContext
    ) -> PermissionDecision:
        """Ownership rules layered on top of raw permissions.

        A student holds ``profile.self.manage``, which is exactly enough to
        edit their own personal details and not remotely enough to edit an
        institution record. The permission alone cannot express that
        distinction; ownership can.
        """
        if ownership.owner is DataOwner.FOREIGN:
            return PermissionDecision(
                allowed=False,
                reason="Resource belongs to another user",
                user_message=(
                    ownership.denial_message
                    or "That record belongs to someone else, so I can't act on it."
                ),
            )

        if (
            meta.mutates_state
            and meta.owner is DataOwner.INSTITUTION
            and context.is_student
        ):
            # Students never write institution-owned data directly. Reaching
            # here means the plan skipped the correction workflow, which is a
            # planner bug — deny and say so.
            return PermissionDecision(
                allowed=False,
                reason="Student attempted a direct write to an institution-owned record",
                user_message=(
                    "Academic records are maintained by the Academic Office, so I "
                    "can't change them directly — but I can raise a correction "
                    "request for you."
                ),
            )

        return PermissionDecision(allowed=True)

    @staticmethod
    def _check_subject_scope(
        meta: ToolAction, ownership: OwnershipDecision, context: VertexContext
    ) -> PermissionDecision:
        """The record in view must be one the caller may open.

        ContextBuilder already resolved this; re-reading its verdict here means
        an inaccessible workspace cannot be used as a tool argument.
        """
        workspace = context.workspace
        if workspace.student_id and not workspace.accessible and not context.is_student:
            return PermissionDecision(
                allowed=False,
                reason=f"Workspace student not accessible: {workspace.denied_reason}",
                user_message=(
                    "I can't work with that student's record — they're not on your caseload."
                ),
            )
        return PermissionDecision(allowed=True)


def summarise_permissions(context: VertexContext, limit: int = 12) -> Optional[str]:
    """Short capability line for the prompt chain.

    Lets the model describe what the user can do without guessing, and without
    dumping the whole permission table into every request.
    """
    if not context.user.permissions:
        return None
    shown = context.user.permissions[:limit]
    suffix = f" (+{len(context.user.permissions) - limit} more)" if len(
        context.user.permissions
    ) > limit else ""
    return ", ".join(shown) + suffix
