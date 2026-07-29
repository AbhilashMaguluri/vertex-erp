"""Structured pipeline logging for Vertex.

Logs every stage: intent, plan, tool, guardrail, LLM, total response.
Uses Python stdlib logging with structured formatting.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Optional

from app.ai.core.guardrails import GuardrailResult
from app.ai.models.intent import DetectedIntent
from app.ai.models.plan import ExecutionPlan
from app.ai.tools.base import ToolResult

logger = logging.getLogger("vertex.pipeline")


class PipelineTimer:
    """Simple timer for measuring pipeline stage durations."""

    def __init__(self) -> None:
        self._start = time.perf_counter()
        self._stages: dict[str, float] = {}

    def mark(self, stage: str) -> float:
        """Mark a stage complete and return its duration in ms."""
        now = time.perf_counter()
        duration_ms = (now - self._start) * 1000
        self._stages[stage] = duration_ms
        self._start = now
        return duration_ms

    @property
    def total_ms(self) -> float:
        return sum(self._stages.values())


class PipelineLogger:
    """Logs each pipeline stage with structured data."""

    def __init__(self, request_id: str = "") -> None:
        self.request_id = request_id
        self.timer = PipelineTimer()

    def log_intent(self, intent: DetectedIntent) -> None:
        duration = self.timer.mark("intent")
        logger.info(
            "[VERTEX] stage=intent category=%s confidence=%.2f entities=%s reasoning='%s' duration_ms=%.1f request_id=%s",
            intent.category.value,
            intent.confidence,
            intent.entities,
            intent.reasoning,
            duration,
            self.request_id,
        )

    def log_guardrail(self, stage: str, result: GuardrailResult) -> None:
        duration = self.timer.mark(f"guardrail_{stage}")
        level = logging.WARNING if not result.passed else logging.INFO
        logger.log(
            level,
            "[VERTEX] stage=guardrail_%s passed=%s severity=%s reason='%s' duration_ms=%.1f request_id=%s",
            stage,
            result.passed,
            result.severity,
            result.reason,
            duration,
            self.request_id,
        )

    def log_plan(self, plan: ExecutionPlan) -> None:
        duration = self.timer.mark("planner")
        logger.info(
            "[VERTEX] stage=planner action=%s tool=%s tool_action=%s params=%s duration_ms=%.1f request_id=%s",
            plan.action.value,
            plan.tool_name or "none",
            plan.tool_action or "none",
            plan.tool_params,
            duration,
            self.request_id,
        )

    def log_tool_execution(
        self, tool_name: str, action: str, result: ToolResult
    ) -> None:
        duration = self.timer.mark("tool_execution")
        level = logging.INFO if result.success else logging.WARNING
        logger.log(
            level,
            "[VERTEX] stage=tool_execution tool=%s action=%s success=%s message='%s' has_ui_action=%s duration_ms=%.1f request_id=%s",
            tool_name,
            action,
            result.success,
            result.message,
            result.ui_action is not None,
            duration,
            self.request_id,
        )

    def log_llm_call(self, provider: str, model: str) -> None:
        duration = self.timer.mark("llm")
        logger.info(
            "[VERTEX] stage=llm_call provider=%s model=%s duration_ms=%.1f request_id=%s",
            provider,
            model,
            duration,
            self.request_id,
        )

    def log_total(self, intent_category: str, plan_action: str) -> None:
        total = self.timer.total_ms
        logger.info(
            "[VERTEX] stage=total request_id=%s intent=%s action=%s total_ms=%.1f",
            self.request_id,
            intent_category,
            plan_action,
            total,
        )
