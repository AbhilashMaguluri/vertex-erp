"""Stage 5 — the Planner.

Decides what happens. The LLM does not: by the time a model is invoked, the
plan has already been made, permission-checked and executed, and the model's
only job is to say what happened.

The Planner answers, in order:

    Can this request be completed at all?
    Does it need reasoning, or execution, or both?
    Which capability handles it — one tool, or several?
    Does it need the user to confirm first?

It asks the registry for capabilities by domain and action. It never names a
tool it has not found, so a replaced or unregistered tool degrades to an
honest "I can't do that yet" rather than a crash.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.ai.models.context import VertexContext
from app.ai.models.goal import Goal, GoalTarget, GoalType
from app.ai.models.intent import DetectedIntent, IntentCategory
from app.ai.models.ownership import OwnershipDecision, OwnershipRoute
from app.ai.models.plan import ExecutionPlan, PlanAction, PlanStep
from app.ai.tools.base import ToolRegistry

logger = logging.getLogger("vertex.planner")


class Planner:
    """Builds the execution plan for one request."""

    async def plan(
        self,
        goal: Goal,
        intent: DetectedIntent,
        ownership: OwnershipDecision,
        context: VertexContext,
        registry: ToolRegistry,
    ) -> ExecutionPlan:
        base = {"goal": goal, "intent": intent, "ownership": ownership}

        # ----- 0. Ownership already ruled it out --------------------------
        if ownership.is_denied:
            return ExecutionPlan(
                action=PlanAction.REJECT,
                rejection_reason=ownership.denial_message,
                reasoning=f"Ownership denied: {ownership.reason}",
                **base,
            )

        # ----- 1. The goal is not yet executable ---------------------------
        if goal.type is GoalType.CLARIFICATION or intent.category is IntentCategory.UNKNOWN:
            missing = goal.missing_information or intent.entities.get("missing") or []
            return ExecutionPlan(
                action=PlanAction.CLARIFY,
                clarification_message=self._clarification_for(goal, missing),
                reasoning=f"Goal under-specified, missing: {missing or ['intent']}",
                **base,
            )

        # ----- 2. Application state: theme, navigation, dialogs, logout ----
        if ownership.route is OwnershipRoute.UI_EXECUTION:
            step = self._plan_ui(goal, intent, registry)
            if step:
                return ExecutionPlan(
                    action=PlanAction.EXECUTE_TOOL,
                    steps=[step],
                    reasoning=f"UI capability '{step.tool_action}' resolved from the registry",
                    **base,
                )
            return self._no_capability(base, "that interface action")

        # ----- 3. Student-owned write → update it now ----------------------
        if ownership.route is OwnershipRoute.DIRECT_UPDATE:
            step = self._resolve(
                registry, "profile", "update",
                {
                    "field": goal.parameters.get("field", ""),
                    "value": goal.parameters.get("value", ""),
                },
            )
            if step:
                return ExecutionPlan(
                    action=PlanAction.EXECUTE_TOOL,
                    steps=[step],
                    reasoning="Student-owned field — direct profile update",
                    **base,
                )
            return self._no_capability(base, "profile updates")

        # ----- 4. Institution-owned write → correction workflow -------------
        if ownership.route is OwnershipRoute.CORRECTION_WORKFLOW:
            step = self._resolve(
                registry, "correction", "create_request",
                {
                    "section": goal.parameters.get("field", "attendance"),
                    "description": goal.parameters.get(
                        "description", goal.raw_message
                    ),
                    "proposed_value": goal.parameters.get("proposed_value", ""),
                    "current_value": goal.parameters.get("current_value", ""),
                },
            )
            if step:
                return ExecutionPlan(
                    action=PlanAction.EXECUTE_TOOL,
                    steps=[step],
                    reasoning=(
                        f"Institution-owned '{ownership.resource}' — "
                        "raising an Academic Correction Request"
                    ),
                    **base,
                )
            return self._no_capability(base, "academic correction requests")

        # ----- 5. Staff editing records they own ---------------------------
        if ownership.route is OwnershipRoute.STAFF_UPDATE:
            return ExecutionPlan(
                action=PlanAction.RESPOND,
                reasoning=(
                    "Staff-owned record edit — Vertex explains the module that "
                    "owns it rather than writing academic data itself"
                ),
                **base,
            )

        # ----- 6. Reads that must come from real records --------------------
        step = self._plan_read(intent, context, registry)
        if step:
            return ExecutionPlan(
                action=PlanAction.EXECUTE_TOOL,
                steps=[step],
                reasoning=f"Read capability '{step.tool_name}.{step.tool_action}' resolved",
                **base,
            )

        # A data question with no tool behind it must not be answered from the
        # model's imagination — say what is missing instead.
        if intent.category in (
            IntentCategory.ATTENDANCE_QUERY,
            IntentCategory.ACADEMIC_QUERY,
            IntentCategory.STUDENT_SEARCH,
        ):
            return self._no_capability(base, "that record lookup")

        # ----- 7. Reports ----------------------------------------------------
        if intent.category is IntentCategory.REPORT_GENERATION:
            step = self._resolve(registry, "report", "generate", dict(intent.entities))
            if step:
                return ExecutionPlan(
                    action=PlanAction.EXECUTE_TOOL,
                    steps=[step],
                    reasoning="Report capability resolved",
                    **base,
                )
            # Reports exist as a screen even though no tool drives them yet, so
            # the useful action is to open it rather than to apologise.
            nav = self._resolve(registry, "ui", "navigate", {"page": "reports"})
            if nav:
                return ExecutionPlan(
                    action=PlanAction.EXECUTE_TOOL,
                    steps=[nav],
                    reasoning="No report tool registered — opening the Reports page instead",
                    **base,
                )

        # ----- 8. Reason and answer -------------------------------------------
        return ExecutionPlan(
            action=PlanAction.RESPOND,
            reasoning="No state change required — answering from context",
            **base,
        )

    # ------------------------------------------------------------------
    # Capability resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve(
        registry: ToolRegistry, domain: str, action: str, params: dict
    ) -> Optional[PlanStep]:
        """Find a tool by capability and build the step, or return None."""
        tool = registry.resolve(domain, action)
        if tool is None:
            logger.info(
                "[VERTEX] no_capability domain=%s action=%s registered=%s",
                domain, action, registry.list_tools(),
            )
            return None

        meta = tool.get_action_meta(action)
        return PlanStep(
            tool_name=tool.name,
            tool_action=action,
            tool_params={k: v for k, v in params.items() if v not in ("", None)},
            description=meta.description if meta else "",
            required_permissions=list(meta.required_permissions) if meta else [],
        )

    def _plan_ui(
        self, goal: Goal, intent: DetectedIntent, registry: ToolRegistry
    ) -> Optional[PlanStep]:
        action = str(goal.parameters.get("action") or "")

        if action == "setTheme":
            return self._resolve(
                registry, "ui", "setTheme", {"mode": goal.parameters.get("mode", "")}
            )
        if action == "navigate":
            return self._resolve(
                registry, "ui", "navigate", {"page": goal.parameters.get("page", "")}
            )
        if action == "logout":
            return self._resolve(registry, "ui", "logout", {})

        if intent.category is IntentCategory.UI_ACTION:
            dialog = intent.entities.get("dialog")
            if dialog:
                return self._resolve(registry, "ui", "openDialog", {"dialog": dialog})
        return None

    def _plan_read(
        self, intent: DetectedIntent, context: VertexContext, registry: ToolRegistry
    ) -> Optional[PlanStep]:
        subject = intent.entities.get("subject_student_id") or ""

        if intent.category is IntentCategory.ATTENDANCE_QUERY:
            return self._resolve(
                registry, "attendance", "get_summary", {"student_id": subject}
            )
        if intent.category is IntentCategory.ACADEMIC_QUERY:
            return self._resolve(
                registry, "academics", "get_record", {"student_id": subject}
            )
        if intent.category is IntentCategory.STUDENT_SEARCH:
            return self._resolve(
                registry, "directory", "search_students",
                {
                    "query": intent.entities.get("query", ""),
                    "raw_message": intent.entities.get("raw_message", ""),
                },
            )
        if intent.category is IntentCategory.DATA_RETRIEVAL and context.is_student:
            return self._resolve(registry, "profile", "get", {})
        return None

    # ------------------------------------------------------------------

    @staticmethod
    def _no_capability(base: dict, what: str) -> ExecutionPlan:
        return ExecutionPlan(
            action=PlanAction.REJECT,
            rejection_reason=(
                f"I can't do {what} yet — that capability isn't connected. "
                f"I can still point you to the right screen if that helps."
            ),
            reasoning=f"No registered tool provides {what}",
            **base,
        )

    @staticmethod
    def _clarification_for(goal: Goal, missing: list) -> str:
        field = goal.parameters.get("field")

        if "new_value" in missing and field:
            return f"What should I change your {str(field).replace('_', ' ')} to?"
        if "new_value" in missing:
            return "What would you like me to change it to?"
        if "field" in missing:
            return (
                "Which detail would you like me to change? I can update your name, "
                "phone number, email, address, guardian details or emergency contact."
            )
        if goal.target is GoalTarget.UNKNOWN and not goal.raw_message.strip():
            return "What can I help you with?"
        return (
            "I want to get this right — could you tell me a bit more about what "
            "you'd like me to do?"
        )
