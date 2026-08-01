"""Stage 12 — Evaluation.

Every completed request is scored. This layer is observability only: it runs
after the response has been delivered, it cannot change what the user saw, and
a failure inside it is swallowed rather than surfaced.

What it answers, per the required checks:

    goal_achieved                did the outcome satisfy the goal?
    correct_tool_used            did an actionable intent actually run a tool?
    permission_validation_passed did every step clear the validator?
    guardrails_passed            input and output, separately recorded
    hallucination_risk           did the text state figures no tool returned?
    response_format              is the reply well-formed and appropriately sized?
    execution_success            did the tools succeed?
    latency / tool errors / fallback usage
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.ai.core.guardrails import GuardrailResult
from app.ai.core.permissions import PermissionDecision
from app.ai.models.context import VertexContext
from app.ai.models.evaluation import (
    EvalResult,
    EvalStatus,
    EvaluationReport,
    StageTimings,
)
from app.ai.models.goal import Goal, GoalType
from app.ai.models.intent import DetectedIntent
from app.ai.models.plan import ExecutionPlan, PlanAction
from app.ai.tools.base import ToolResult

logger = logging.getLogger("vertex.evaluation")

#: Anything past this is a wall of text in a chat panel, not an answer.
_MAX_RESPONSE_CHARS = 8000


class EvaluationInput:
    """Everything one interaction produced, gathered for scoring."""

    def __init__(
        self,
        request_id: str,
        context: VertexContext,
        user_message: str,
        goal: Goal,
        intent: DetectedIntent,
        plan: ExecutionPlan,
        response: str,
        timings: StageTimings,
        input_guardrail: Optional[GuardrailResult] = None,
        output_guardrail: Optional[GuardrailResult] = None,
        permission: Optional[PermissionDecision] = None,
        tool_results: Optional[List[ToolResult]] = None,
        fallback_used: bool = False,
        error: Optional[str] = None,
    ) -> None:
        self.request_id = request_id
        self.context = context
        self.user_message = user_message
        self.goal = goal
        self.intent = intent
        self.plan = plan
        self.response = response
        self.timings = timings
        self.input_guardrail = input_guardrail
        self.output_guardrail = output_guardrail
        self.permission = permission
        self.tool_results = tool_results or []
        self.fallback_used = fallback_used
        self.error = error

    @property
    def tools_succeeded(self) -> bool:
        return all(r.success for r in self.tool_results)

    @property
    def tool_error(self) -> Optional[str]:
        for result in self.tool_results:
            if not result.success:
                return result.error or "unspecified tool failure"
        return None

    @property
    def erp_data(self) -> Dict:
        merged: Dict = {}
        for result in self.tool_results:
            if result.is_erp_data:
                merged.update(result.data)
        return merged


class BaseEval(ABC):
    name: str

    @abstractmethod
    async def evaluate(self, data: EvaluationInput) -> EvalResult:
        ...  # pragma: no cover


# --------------------------------------------------------------------------
# The checks
# --------------------------------------------------------------------------

class GoalAchievementEval(BaseEval):
    """Did the outcome actually satisfy what the user was trying to do?"""

    name = "goal_achieved"

    async def evaluate(self, data: EvaluationInput) -> EvalResult:
        goal, plan = data.goal, data.plan

        if data.error:
            return EvalResult(
                name=self.name, status=EvalStatus.FAIL, score=0.0,
                details=f"Request errored: {data.error}",
            )

        # Clarifying and refusing are legitimate outcomes — the goal was
        # handled correctly even though nothing was executed.
        if plan.action is PlanAction.CLARIFY:
            return EvalResult(
                name=self.name,
                status=EvalStatus.PASS if goal.type is GoalType.CLARIFICATION else EvalStatus.WARN,
                score=1.0 if goal.type is GoalType.CLARIFICATION else 0.6,
                details="Asked the user for the missing detail",
            )
        if plan.action is PlanAction.REJECT:
            return EvalResult(
                name=self.name, status=EvalStatus.PASS, score=1.0,
                details=f"Correctly declined: {plan.reasoning}",
            )

        if goal.requires_execution:
            if not plan.executes_tools:
                return EvalResult(
                    name=self.name, status=EvalStatus.FAIL, score=0.0,
                    details=(
                        f"Goal '{goal.statement}' required execution but the plan "
                        f"only responded — Vertex explained instead of acting"
                    ),
                )
            if not data.tools_succeeded:
                return EvalResult(
                    name=self.name, status=EvalStatus.FAIL, score=0.0,
                    details=f"Tool execution failed: {data.tool_error}",
                )
            return EvalResult(
                name=self.name, status=EvalStatus.PASS, score=1.0,
                details=f"Executed: {goal.statement}",
            )

        if not data.response.strip():
            return EvalResult(
                name=self.name, status=EvalStatus.FAIL, score=0.0,
                details="Answer-shaped goal produced no response",
            )

        return EvalResult(
            name=self.name, status=EvalStatus.PASS, score=1.0,
            details="Answered without needing a state change",
        )


class ToolSelectionEval(BaseEval):
    """Was the right capability chosen — and chosen at all?"""

    name = "correct_tool_used"

    async def evaluate(self, data: EvaluationInput) -> EvalResult:
        intent, plan = data.intent, data.plan

        if not intent.is_actionable:
            return EvalResult(
                name=self.name, status=EvalStatus.SKIP, score=1.0,
                details="Intent is not actionable — no tool expected",
            )

        if plan.action in (PlanAction.CLARIFY, PlanAction.REJECT):
            return EvalResult(
                name=self.name, status=EvalStatus.SKIP, score=1.0,
                details=f"Plan resolved to {plan.action.value} before tool selection",
            )

        if not plan.executes_tools:
            return EvalResult(
                name=self.name, status=EvalStatus.FAIL, score=0.0,
                details=(
                    f"Actionable intent '{intent.category.value}' produced no tool call — "
                    "the user was told how instead of being helped"
                ),
            )

        expected_domain = _EXPECTED_DOMAIN.get(intent.category.value)
        actual = plan.tool_name or ""
        if expected_domain and actual != expected_domain:
            return EvalResult(
                name=self.name, status=EvalStatus.WARN, score=0.5,
                details=f"Intent '{intent.category.value}' used tool '{actual}', expected '{expected_domain}'",
            )

        return EvalResult(
            name=self.name, status=EvalStatus.PASS, score=1.0,
            details=f"Used {actual}.{plan.tool_action}",
        )


class PermissionEval(BaseEval):
    """Did permission validation run, and did it hold?"""

    name = "permission_validation"

    async def evaluate(self, data: EvaluationInput) -> EvalResult:
        if not data.plan.executes_tools:
            return EvalResult(
                name=self.name, status=EvalStatus.SKIP, score=1.0,
                details="No tool executed — nothing to authorise",
            )

        if data.permission is None:
            # Reaching a tool without validation is a pipeline defect, and a
            # far more serious finding than any denial.
            return EvalResult(
                name=self.name, status=EvalStatus.FAIL, score=0.0,
                details="Tool executed without a permission decision on record",
            )

        if data.permission.denied:
            return EvalResult(
                name=self.name, status=EvalStatus.PASS, score=1.0,
                details=f"Correctly denied: {data.permission.reason}",
            )

        return EvalResult(
            name=self.name, status=EvalStatus.PASS, score=1.0,
            details=f"Authorised: {', '.join(data.permission.checked) or 'no explicit permissions required'}",
        )


class GuardrailEval(BaseEval):
    """Did both guardrail stages run, and what did they find?"""

    name = "guardrails"

    async def evaluate(self, data: EvaluationInput) -> EvalResult:
        notes: List[str] = []
        status = EvalStatus.PASS
        score = 1.0

        if data.input_guardrail is None:
            return EvalResult(
                name=self.name, status=EvalStatus.FAIL, score=0.0,
                details="Input guardrails did not run",
            )

        if data.input_guardrail.blocked:
            return EvalResult(
                name=self.name, status=EvalStatus.PASS, score=1.0,
                details=f"Input blocked: {[v.rule for v in data.input_guardrail.violations]}",
            )

        warnings = [v.rule for v in data.input_guardrail.violations]
        if warnings:
            notes.append(f"input warnings: {warnings}")
            status, score = EvalStatus.WARN, 0.7

        if data.response.strip():
            if data.output_guardrail is None:
                return EvalResult(
                    name=self.name, status=EvalStatus.FAIL, score=0.0,
                    details="Response delivered without an output guardrail check",
                )
            if data.output_guardrail.blocked:
                notes.append(
                    f"output blocked: {[v.rule for v in data.output_guardrail.violations]}"
                )
                status, score = EvalStatus.WARN, 0.4
            elif data.output_guardrail.violations:
                notes.append(
                    f"output warnings: {[v.rule for v in data.output_guardrail.violations]}"
                )
                status, score = EvalStatus.WARN, 0.7

        return EvalResult(
            name=self.name, status=status, score=score,
            details="; ".join(notes) or "Input and output guardrails passed cleanly",
        )


class HallucinationEval(BaseEval):
    """Did the response state ERP figures no tool produced?

    The most damaging failure available to this system: a confidently wrong
    attendance percentage is worse than no answer.
    """

    name = "hallucination"

    _FIGURE_CLAIMS = [
        r"\battendance\s+(?:is|of|stands\s+at)\s*(\d{1,3}(?:\.\d+)?)\s*%",
        r"\b(?:SGPA|CGPA)\s*(?:is|:|=|of)\s*(\d(?:\.\d+)?)",
        r"\byou\s+have\s+(\d+)\s+(?:active\s+)?backlogs?",
        r"\byour\s+(?:marks?|score)\s+(?:is|are)\s*(\d+)",
    ]

    async def evaluate(self, data: EvaluationInput) -> EvalResult:
        response = data.response
        if not response.strip():
            return EvalResult(name=self.name, status=EvalStatus.SKIP, score=1.0)

        grounded = _numbers_in(data.erp_data)
        claims: List[str] = []
        for pattern in self._FIGURE_CLAIMS:
            for match in re.finditer(pattern, response, re.IGNORECASE):
                claims.append(match.group(1))

        if not claims:
            return EvalResult(
                name=self.name, status=EvalStatus.PASS, score=1.0,
                details="No concrete ERP figures asserted",
            )

        ungrounded = [c for c in claims if c not in grounded]
        if ungrounded:
            return EvalResult(
                name=self.name, status=EvalStatus.FAIL, score=0.0,
                details=f"Asserted ungrounded figure(s): {ungrounded}",
            )

        return EvalResult(
            name=self.name, status=EvalStatus.PASS, score=1.0,
            details=f"All {len(claims)} figure(s) traced to tool output",
        )


class ResponseFormatEval(BaseEval):
    """Is the reply well-formed, and does it match the channel?"""

    name = "response_format"

    async def evaluate(self, data: EvaluationInput) -> EvalResult:
        response = data.response

        if not response.strip():
            # A pure UI action with no narration is a legitimate shape.
            if data.plan.executes_tools and data.tools_succeeded:
                return EvalResult(
                    name=self.name, status=EvalStatus.WARN, score=0.6,
                    details="Tool executed but nothing was said back to the user",
                )
            return EvalResult(
                name=self.name, status=EvalStatus.FAIL, score=0.0,
                details="Empty response",
            )

        if len(response) > _MAX_RESPONSE_CHARS:
            return EvalResult(
                name=self.name, status=EvalStatus.WARN, score=0.5,
                details=f"Response was {len(response)} chars (soft limit {_MAX_RESPONSE_CHARS})",
            )

        # Execution over explanation: after a successful action, walking the
        # user through doing it manually means the action was not communicated.
        if data.plan.executes_tools and data.tools_succeeded:
            if re.search(
                r"\b(?:go\s+to|navigate\s+to|click\s+on|open\s+the)\b[^.?!]*\b"
                r"(?:then|and\s+then|next)\b",
                response,
                re.IGNORECASE,
            ):
                return EvalResult(
                    name=self.name, status=EvalStatus.WARN, score=0.5,
                    details="Response gave manual steps for an action already performed",
                )

        return EvalResult(name=self.name, status=EvalStatus.PASS, score=1.0)


class ExecutionEval(BaseEval):
    """Did the machinery work — tools, fallbacks, latency?"""

    name = "execution"

    #: A chat turn slower than this feels broken regardless of correctness.
    SLOW_MS = 12_000

    async def evaluate(self, data: EvaluationInput) -> EvalResult:
        problems: List[str] = []
        score = 1.0
        status = EvalStatus.PASS

        if data.error:
            return EvalResult(
                name=self.name, status=EvalStatus.FAIL, score=0.0,
                details=f"Pipeline error: {data.error}",
            )

        if not data.tools_succeeded:
            problems.append(f"tool error: {data.tool_error}")
            status, score = EvalStatus.FAIL, 0.0

        if data.fallback_used:
            problems.append("fallback path used")
            if status is EvalStatus.PASS:
                status, score = EvalStatus.WARN, 0.6

        if data.timings.total > self.SLOW_MS:
            problems.append(f"slow: {data.timings.total:.0f}ms")
            if status is EvalStatus.PASS:
                status, score = EvalStatus.WARN, 0.7

        return EvalResult(
            name=self.name, status=status, score=score,
            details="; ".join(problems) or f"Completed in {data.timings.total:.0f}ms",
        )


# Intent → the tool expected to serve it. Used to spot mis-routing.
_EXPECTED_DOMAIN: Dict[str, str] = {
    "navigation": "ui",
    "theme_change": "ui",
    "ui_action": "ui",
    "profile_update": "profile",
    "academic_correction": "correction",
    "attendance_query": "attendance",
    "academic_query": "academics",
    "student_search": "directory",
}


def _numbers_in(data) -> set:
    """Every number a tool returned, as strings, for grounding comparisons."""
    found: set = set()

    def walk(node):
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, (list, tuple)):
            for value in node:
                walk(value)
        elif isinstance(node, bool) or node is None:
            return
        elif isinstance(node, (int, float)):
            text = str(node)
            found.add(text)
            found.add(text[:-2] if text.endswith(".0") else f"{text}.0")
        elif isinstance(node, str):
            found.update(re.findall(r"\d+(?:\.\d+)?", node))

    walk(data)
    return found


# --------------------------------------------------------------------------


class Evaluator:
    """Runs every check and assembles the report.

    Registered evals are additive: a new check is a ``register`` call, and one
    that raises is recorded as an eval error rather than being allowed to break
    a request that already succeeded.
    """

    def __init__(self, evals: Optional[List[BaseEval]] = None) -> None:
        self._evals: List[BaseEval] = evals or [
            GoalAchievementEval(),
            ToolSelectionEval(),
            PermissionEval(),
            GuardrailEval(),
            HallucinationEval(),
            ResponseFormatEval(),
            ExecutionEval(),
        ]

    def register(self, evaluation: BaseEval) -> None:
        self._evals.append(evaluation)

    async def evaluate(self, data: EvaluationInput) -> EvaluationReport:
        results: List[EvalResult] = []
        for check in self._evals:
            try:
                results.append(await check.evaluate(data))
            except Exception as exc:
                logger.exception("Eval '%s' raised", check.name)
                results.append(
                    EvalResult(
                        name=check.name,
                        status=EvalStatus.WARN,
                        score=0.5,
                        details=f"Eval error: {type(exc).__name__}: {exc}",
                    )
                )

        by_name = {r.name: r for r in results}
        hallucination = by_name.get("hallucination")

        report = EvaluationReport(
            request_id=data.request_id,
            session_id=data.context.session.session_id,
            user_id=data.context.user.id,
            mode=data.context.mode,
            user_message=data.user_message[:1000],
            goal_type=data.goal.type.value,
            goal_target=data.goal.target.value,
            goal_statement=data.goal.statement,
            intent_category=data.intent.category.value,
            intent_confidence=data.intent.confidence,
            plan_action=data.plan.action.value,
            ownership_owner=data.plan.ownership.owner.value,
            ownership_route=data.plan.ownership.route.value,
            tool_name=data.plan.tool_name,
            tool_action=data.plan.tool_action,
            goal_achieved=_passed(by_name.get("goal_achieved")),
            correct_tool_used=_passed(by_name.get("correct_tool_used")),
            permission_validation_passed=(
                data.permission is None or data.permission.allowed
            ),
            input_guardrails_passed=(
                data.input_guardrail is None or not data.input_guardrail.blocked
            ),
            output_guardrails_passed=(
                data.output_guardrail is None or not data.output_guardrail.blocked
            ),
            hallucination_risk=(
                0.0 if hallucination is None or hallucination.passed else 1.0
            ),
            response_format_valid=_passed(by_name.get("response_format")),
            execution_success=data.tools_succeeded and data.error is None,
            tool_error=data.tool_error,
            fallback_used=data.fallback_used,
            results=results,
            timings=data.timings,
            latency_ms=data.timings.total,
            response_length=len(data.response),
            error=data.error,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        level = logging.WARNING if report.failures else logging.INFO
        logger.log(level, "[VERTEX] evaluation %s", report.to_log_dict())
        return report


def _passed(result: Optional[EvalResult]) -> bool:
    return result is None or result.passed
