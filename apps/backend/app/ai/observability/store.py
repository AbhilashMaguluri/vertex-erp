"""Evaluation storage.

Two tiers, because they answer different questions:

    Ring buffer  — the last N interactions, in memory, always available.
                   Survives a database outage; does not survive a restart.
    Database     — durable history for trend analysis.

Writing is fire-and-forget by design. The evaluation layer must never affect
the user's experience, so a failed insert is logged and dropped; the ring
buffer still has the record.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Deque, Dict, List, Optional

from app.ai.models.evaluation import EvaluationReport

logger = logging.getLogger("vertex.observability")

#: Kept small enough to be irrelevant to process memory, large enough to cover
#: a debugging session without reaching for the database.
_BUFFER_SIZE = 200


class EvaluationStore:
    """In-process buffer plus best-effort database persistence."""

    def __init__(self, buffer_size: int = _BUFFER_SIZE) -> None:
        self._buffer: Deque[EvaluationReport] = deque(maxlen=buffer_size)

    # ------------------------------------------------------------------

    async def record(
        self, report: EvaluationReport, db: Optional[object] = None
    ) -> None:
        """Store a report. Never raises."""
        self._buffer.append(report)

        if db is None:
            return
        try:
            await self._persist(report, db)
        except Exception as exc:
            # Telemetry is not worth failing a served request over.
            logger.warning(
                "Could not persist evaluation for request %s: %s: %s",
                report.request_id, type(exc).__name__, exc,
            )

    @staticmethod
    async def _persist(report: EvaluationReport, db) -> None:
        from app.ai.observability.models import VertexInteraction

        row = VertexInteraction(
            request_id=report.request_id,
            session_id=report.session_id or None,
            user_id=report.user_id,
            mode=report.mode,
            user_message=report.user_message,
            goal_type=report.goal_type,
            goal_target=report.goal_target,
            goal_statement=report.goal_statement[:300] if report.goal_statement else None,
            intent_category=report.intent_category,
            intent_confidence=report.intent_confidence,
            plan_action=report.plan_action,
            ownership_owner=report.ownership_owner,
            ownership_route=report.ownership_route,
            tool_name=report.tool_name,
            tool_action=report.tool_action,
            goal_achieved=report.goal_achieved,
            correct_tool_used=report.correct_tool_used,
            permission_validation_passed=report.permission_validation_passed,
            input_guardrails_passed=report.input_guardrails_passed,
            output_guardrails_passed=report.output_guardrails_passed,
            hallucination_risk=report.hallucination_risk,
            response_format_valid=report.response_format_valid,
            execution_success=report.execution_success,
            fallback_used=report.fallback_used,
            overall_score=report.overall_score,
            tool_error=report.tool_error,
            error=report.error,
            latency_ms=report.latency_ms,
            response_length=report.response_length,
            eval_results=[r.model_dump(mode="json") for r in report.results],
            timings=report.timings.model_dump(mode="json"),
        )
        db.add(row)
        await db.commit()

    # ------------------------------------------------------------------
    # Reads — the in-memory tier
    # ------------------------------------------------------------------

    def recent(self, limit: int = 50) -> List[EvaluationReport]:
        return list(self._buffer)[-limit:][::-1]

    def failures(self, limit: int = 50) -> List[EvaluationReport]:
        return [r for r in self.recent(len(self._buffer)) if r.failures][:limit]

    def stats(self) -> Dict:
        """Aggregates over the buffer — the health-at-a-glance view."""
        reports = list(self._buffer)
        if not reports:
            return {"count": 0}

        total = len(reports)
        latencies = sorted(r.latency_ms for r in reports)

        def rate(predicate) -> float:
            return round(sum(1 for r in reports if predicate(r)) / total, 3)

        by_intent: Dict[str, int] = {}
        by_tool: Dict[str, int] = {}
        for report in reports:
            by_intent[report.intent_category] = by_intent.get(report.intent_category, 0) + 1
            if report.tool_name:
                by_tool[report.tool_name] = by_tool.get(report.tool_name, 0) + 1

        return {
            "count": total,
            "mean_score": round(sum(r.overall_score for r in reports) / total, 3),
            "goal_achieved_rate": rate(lambda r: r.goal_achieved),
            "correct_tool_rate": rate(lambda r: r.correct_tool_used),
            "permission_pass_rate": rate(lambda r: r.permission_validation_passed),
            "guardrail_pass_rate": rate(
                lambda r: r.input_guardrails_passed and r.output_guardrails_passed
            ),
            "hallucination_rate": rate(lambda r: r.hallucination_risk > 0),
            "execution_success_rate": rate(lambda r: r.execution_success),
            "fallback_rate": rate(lambda r: r.fallback_used),
            "latency_ms": {
                "p50": round(_percentile(latencies, 0.50), 1),
                "p95": round(_percentile(latencies, 0.95), 1),
                "max": round(latencies[-1], 1),
            },
            "by_intent": dict(sorted(by_intent.items(), key=lambda kv: -kv[1])),
            "by_tool": dict(sorted(by_tool.items(), key=lambda kv: -kv[1])),
        }


def _percentile(sorted_values: List[float], fraction: float) -> float:
    if not sorted_values:
        return 0.0
    index = min(int(len(sorted_values) * fraction), len(sorted_values) - 1)
    return sorted_values[index]


#: Process-wide store. The pipeline writes to it; the observability router
#: reads from it.
evaluation_store = EvaluationStore()
