"""Data Ownership Guardrail.

Sits between the Goal and the Planner and answers one question:

    Who owns the data this request touches?

The answer decides the route, and it is why Vertex does not refuse a student
who says "my attendance is wrong". Attendance is institution-owned, so the
correct response is not "you can't do that" — it is to open an Academic
Correction Request on their behalf.

Refusal is reserved for FOREIGN data (someone else's record) and for the case
where no route exists at all.
"""

from __future__ import annotations

import logging

from app.ai.models.context import VertexContext
from app.ai.models.goal import Goal, GoalTarget, GoalType
from app.ai.models.ownership import (
    CORRECTION_SECTIONS,
    INSTITUTION_OWNED_FIELDS,
    STUDENT_OWNED_FIELDS,
    DataOwner,
    OwnershipDecision,
    OwnershipRoute,
)

logger = logging.getLogger("vertex.ownership")


class DataOwnershipResolver:
    """Resolves who owns the resource a goal targets."""

    def resolve(self, goal: Goal, context: VertexContext) -> OwnershipDecision:
        field = str(goal.parameters.get("field") or "").strip().lower()

        # ----- Application state: theme, navigation, session ---------------
        if goal.target is GoalTarget.APPLICATION_STATE:
            return OwnershipDecision(
                owner=DataOwner.APPLICATION,
                route=OwnershipRoute.UI_EXECUTION,
                resource=str(goal.parameters.get("action") or "ui"),
                reason="UI and session state belong to the application",
            )

        # ----- Nothing owned: pure knowledge questions ----------------------
        if goal.target in (GoalTarget.KNOWLEDGE, GoalTarget.UNKNOWN) and not field:
            return OwnershipDecision(
                owner=DataOwner.NONE,
                route=OwnershipRoute.NOT_APPLICABLE,
                reason="No ERP resource involved",
            )

        # ----- Another student's record ------------------------------------
        if goal.target is GoalTarget.STUDENT_DIRECTORY:
            return self._resolve_directory(goal, context)

        # ----- Reads never mutate, so ownership only gates visibility -------
        if goal.type in (GoalType.QUESTION, GoalType.CONVERSATION):
            return self._resolve_read(goal, context, field)

        # ----- Writes -------------------------------------------------------
        return self._resolve_write(goal, context, field)

    # ------------------------------------------------------------------

    def _resolve_directory(
        self, goal: Goal, context: VertexContext
    ) -> OwnershipDecision:
        """Records belonging to other people."""
        if context.user.has_permission("student.caseload.read"):
            return OwnershipDecision(
                owner=DataOwner.INSTITUTION,
                route=OwnershipRoute.NOT_APPLICABLE,
                resource="student_directory",
                reason="Caller holds student.caseload.read",
            )
        return OwnershipDecision(
            owner=DataOwner.FOREIGN,
            route=OwnershipRoute.DENY,
            resource="student_directory",
            reason="Caller may not browse other students",
            denial_message=(
                "I can only work with your own records. Browsing other students' "
                "information requires staff access."
            ),
        )

    def _resolve_read(
        self, goal: Goal, context: VertexContext, field: str
    ) -> OwnershipDecision:
        owner = self._classify_field(field, goal.target)

        # A student reading their own attendance/marks is fine — institution
        # ownership restricts *writes*, not visibility of one's own record.
        if owner is DataOwner.INSTITUTION and context.is_student:
            return OwnershipDecision(
                owner=DataOwner.INSTITUTION,
                route=OwnershipRoute.NOT_APPLICABLE,
                resource=field or goal.target.value,
                fields=[field] if field else [],
                reason="Student reading their own institution-owned record",
            )

        return OwnershipDecision(
            owner=owner,
            route=OwnershipRoute.NOT_APPLICABLE,
            resource=field or goal.target.value,
            fields=[field] if field else [],
            reason="Read request — ownership does not block reads of own data",
        )

    def _resolve_write(
        self, goal: Goal, context: VertexContext, field: str
    ) -> OwnershipDecision:
        owner = self._classify_field(field, goal.target)

        if owner is DataOwner.STUDENT:
            # Staff editing a student's personal details is an administrative
            # action with its own permission; students edit their own.
            if context.is_student:
                return OwnershipDecision(
                    owner=DataOwner.STUDENT,
                    route=OwnershipRoute.DIRECT_UPDATE,
                    resource=field or "profile",
                    fields=[field] if field else [],
                    reason=f"'{field or 'profile'}' is student-owned — update directly",
                )
            return OwnershipDecision(
                owner=DataOwner.STUDENT,
                route=OwnershipRoute.STAFF_UPDATE,
                resource=field or "profile",
                fields=[field] if field else [],
                reason="Staff editing a student-owned field requires student.profile.manage",
            )

        if owner is DataOwner.INSTITUTION:
            section = CORRECTION_SECTIONS.get(field, "Academic Records")

            # Staff who own the record edit it through the feature modules;
            # Vertex routes them there rather than editing academic data itself.
            if context.is_staff:
                return OwnershipDecision(
                    owner=DataOwner.INSTITUTION,
                    route=OwnershipRoute.STAFF_UPDATE,
                    resource=section,
                    fields=[field] if field else [],
                    reason="Institution-owned record edited by staff through the ERP modules",
                )

            return OwnershipDecision(
                owner=DataOwner.INSTITUTION,
                route=OwnershipRoute.CORRECTION_WORKFLOW,
                resource=section,
                fields=[field] if field else [],
                reason=(
                    f"'{field or 'record'}' is institution-owned — "
                    f"open an Academic Correction Request for {section}"
                ),
            )

        if owner is DataOwner.FOREIGN:
            return OwnershipDecision(
                owner=DataOwner.FOREIGN,
                route=OwnershipRoute.DENY,
                resource=field or "record",
                reason="Resource belongs to another user",
                denial_message=(
                    "That record belongs to someone else, so I can't change it from here."
                ),
            )

        # Unknown field on a profile-shaped goal: treat as student-owned and
        # let the Profile Tool reject it if the column does not exist. Failing
        # closed here would refuse legitimate edits over a vocabulary gap.
        if goal.target is GoalTarget.STUDENT_PROFILE:
            return OwnershipDecision(
                owner=DataOwner.STUDENT,
                route=OwnershipRoute.DIRECT_UPDATE,
                resource=field or "profile",
                fields=[field] if field else [],
                reason="Unrecognised profile field — routed to the profile tool for validation",
            )

        return OwnershipDecision(
            owner=DataOwner.NONE,
            route=OwnershipRoute.NOT_APPLICABLE,
            resource=field or goal.target.value,
            reason="No owning resource identified",
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _classify_field(field: str, target: GoalTarget) -> DataOwner:
        if field:
            if field in STUDENT_OWNED_FIELDS:
                return DataOwner.STUDENT
            if field in INSTITUTION_OWNED_FIELDS:
                return DataOwner.INSTITUTION

        if target in (GoalTarget.ATTENDANCE, GoalTarget.ACADEMIC_RECORD):
            return DataOwner.INSTITUTION
        if target is GoalTarget.STUDENT_PROFILE:
            return DataOwner.STUDENT
        if target is GoalTarget.STUDENT_DIRECTORY:
            return DataOwner.FOREIGN
        if target is GoalTarget.APPLICATION_STATE:
            return DataOwner.APPLICATION
        return DataOwner.NONE
