"""Structured pipeline logging.

Every stage emits one line, every line carries the ``request_id``, and every
line is key=value so it can be grepped or shipped to a log aggregator without
a parser. The set of lines for one request is the trace of that request:

    goal → context → guardrail_input → intent → planner → permission →
    tool_execution → llm → guardrail_output → evaluation → total

Timings are recorded per stage as they are marked, and the accumulated
:class:`StageTimings` is what the evaluation record stores.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from app.ai.core.guardrails import GuardrailResult
from app.ai.core.permissions import PermissionDecision
from app.ai.models.context import VertexContext
from app.ai.models.evaluation import EvaluationReport, StageTimings
from app.ai.models.goal import Goal
from app.ai.models.intent import DetectedIntent
from app.ai.models.plan import ExecutionPlan
from app.ai.tools.base import ToolResult

logger = logging.getLogger("vertex.pipeline")


class PipelineTimer:
    """Wall-clock duration of each stage, in the order they ran."""

    def __init__(self) -> None:
        self._origin = time.perf_counter()
        self._last = self._origin
        self.timings = StageTimings()

    def mark(self, stage: str) -> float:
        """Close out ``stage`` and return its duration in milliseconds."""
        now = time.perf_counter()
        duration_ms = (now - self._last) * 1000
        self._last = now
        if hasattr(self.timings, stage):
            setattr(self.timings, stage, round(duration_ms, 2))
        return duration_ms

    def finish(self) -> StageTimings:
        self.timings.total = round((time.perf_counter() - self._origin) * 1000, 2)
        return self.timings

    @property
    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self._origin) * 1000


class PipelineLogger:
    """Emits one structured line per pipeline stage."""

    def __init__(self, request_id: str = "") -> None:
        self.request_id = request_id
        self.timer = PipelineTimer()

    # ------------------------------------------------------------------

    def log_goal(self, goal: Goal) -> None:
        duration = self.timer.mark("goal")
        logger.info(
            "[VERTEX] stage=goal request_id=%s type=%s target=%s statement='%s' "
            "confidence=%.2f params=%s duration_ms=%.1f",
            self.request_id, goal.type.value, goal.target.value, goal.statement,
            goal.confidence, goal.parameters, duration,
        )

    def log_context(self, context: VertexContext) -> None:
        duration = self.timer.mark("context")
        logger.info(
            "[VERTEX] stage=context request_id=%s %s permissions=%d "
            "workspace_accessible=%s history_turns=%d duration_ms=%.1f",
            self.request_id, context.describe(), len(context.user.permissions),
            context.workspace.accessible, context.session.turn_count, duration,
        )

    def log_guardrail(self, stage: str, result: GuardrailResult) -> None:
        key = "input_guardrails" if stage == "input" else "output_guardrails"
        duration = self.timer.mark(key)
        logger.log(
            logging.WARNING if result.blocked else logging.INFO,
            "[VERTEX] stage=guardrail_%s request_id=%s passed=%s severity=%s "
            "violations=%s duration_ms=%.1f",
            stage, self.request_id, result.passed, result.severity,
            [v.rule for v in result.violations], duration,
        )

    def log_intent(self, intent: DetectedIntent) -> None:
        duration = self.timer.mark("intent")
        logger.info(
            "[VERTEX] stage=intent request_id=%s category=%s confidence=%.2f "
            "source=%s reasoning='%s' duration_ms=%.1f",
            self.request_id, intent.category.value, intent.confidence,
            intent.source, intent.reasoning, duration,
        )

    def log_plan(self, plan: ExecutionPlan) -> None:
        duration = self.timer.mark("planner")
        logger.info(
            "[VERTEX] stage=planner request_id=%s action=%s owner=%s route=%s "
            "tool=%s tool_action=%s params=%s reasoning='%s' duration_ms=%.1f",
            self.request_id, plan.action.value, plan.ownership.owner.value,
            plan.ownership.route.value, plan.tool_name or "none",
            plan.tool_action or "none", plan.tool_params, plan.reasoning, duration,
        )

    def log_permission(self, decision: PermissionDecision, step_label: str) -> None:
        duration = self.timer.mark("permissions")
        logger.log(
            logging.WARNING if decision.denied else logging.INFO,
            "[VERTEX] stage=permission request_id=%s step=%s allowed=%s "
            "checked=%s missing=%s reason='%s' duration_ms=%.1f",
            self.request_id, step_label, decision.allowed, decision.checked,
            decision.missing_permissions, decision.reason, duration,
        )

    def log_tool_execution(
        self, tool_name: str, action: str, result: ToolResult
    ) -> None:
        duration = self.timer.mark("tool_execution")
        logger.log(
            logging.INFO if result.success else logging.WARNING,
            "[VERTEX] stage=tool_execution request_id=%s tool=%s action=%s "
            "success=%s erp_data=%s ui_action=%s message='%s' error='%s' duration_ms=%.1f",
            self.request_id, tool_name, action, result.success, result.is_erp_data,
            bool(result.ui_action), result.message, result.error or "", duration,
        )

    def log_llm_call(self, provider: str, model: str, tokens: int = 0) -> None:
        duration = self.timer.mark("llm")
        logger.info(
            "[VERTEX] stage=llm request_id=%s provider=%s model=%s chars=%d duration_ms=%.1f",
            self.request_id, provider, model, tokens, duration,
        )

    def log_evaluation(self, report: EvaluationReport) -> None:
        self.timer.mark("evaluation")
        logger.log(
            logging.WARNING if report.failures else logging.INFO,
            "[VERTEX] stage=evaluation request_id=%s score=%.2f failures=%s",
            self.request_id, report.overall_score,
            [f"{f.name}:{f.details}" for f in report.failures],
        )

    def log_error(self, stage: str, exc: Exception) -> None:
        logger.error(
            "[VERTEX] stage=%s request_id=%s error=%s detail='%s'",
            stage, self.request_id, type(exc).__name__, exc,
        )

    def log_total(
        self,
        goal: Optional[Goal] = None,
        intent: Optional[DetectedIntent] = None,
        plan: Optional[ExecutionPlan] = None,
    ) -> StageTimings:
        timings = self.timer.finish()
        logger.info(
            "[VERTEX] stage=total request_id=%s goal=%s intent=%s action=%s "
            "tool=%s total_ms=%.1f",
            self.request_id,
            goal.type.value if goal else "none",
            intent.category.value if intent else "none",
            plan.action.value if plan else "none",
            (plan.tool_name if plan else None) or "none",
            timings.total,
        )
        return timings
