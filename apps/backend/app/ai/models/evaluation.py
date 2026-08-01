"""Evaluation models — how every completed request gets scored.

The evaluation layer is observability, not control flow: it runs after the
response has been delivered and never changes what the user sees. What it
produces is a record a developer can query later to answer "did Vertex
actually do the right thing?"
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EvalStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"  # Not applicable to this request shape


class EvalResult(BaseModel):
    """One check against one completed interaction."""

    name: str
    status: EvalStatus = EvalStatus.PASS
    score: float = 1.0  # 0.0 – 1.0
    details: str = ""

    @property
    def passed(self) -> bool:
        return self.status in (EvalStatus.PASS, EvalStatus.SKIP)


class StageTimings(BaseModel):
    """Milliseconds spent in each pipeline stage."""

    goal: float = 0.0
    context: float = 0.0
    input_guardrails: float = 0.0
    intent: float = 0.0
    planner: float = 0.0
    permissions: float = 0.0
    tool_execution: float = 0.0
    llm: float = 0.0
    output_guardrails: float = 0.0
    evaluation: float = 0.0
    total: float = 0.0


class EvaluationReport(BaseModel):
    """The full scorecard for one request.

    Persisted by the observability store and surfaced on
    ``GET /api/vertex/observability/evaluations``.
    """

    request_id: str
    session_id: str = ""
    user_id: Optional[str] = None
    mode: str = "guest"

    # ----- What was asked and what was decided -----
    user_message: str = ""
    goal_type: str = ""
    goal_target: str = ""
    goal_statement: str = ""
    intent_category: str = ""
    intent_confidence: float = 0.0
    plan_action: str = ""
    ownership_owner: str = ""
    ownership_route: str = ""
    tool_name: Optional[str] = None
    tool_action: Optional[str] = None

    # ----- The mandated checks -----
    goal_achieved: bool = False
    correct_tool_used: bool = False
    permission_validation_passed: bool = True
    input_guardrails_passed: bool = True
    output_guardrails_passed: bool = True
    hallucination_risk: float = 0.0     # 0.0 (none) – 1.0 (certain)
    response_format_valid: bool = True
    execution_success: bool = True
    tool_error: Optional[str] = None
    fallback_used: bool = False

    # ----- Detail & timing -----
    results: List[EvalResult] = Field(default_factory=list)
    timings: StageTimings = Field(default_factory=StageTimings)
    latency_ms: float = 0.0
    response_length: int = 0
    error: Optional[str] = None

    created_at: Optional[str] = None

    # ------------------------------------------------------------------

    @property
    def overall_score(self) -> float:
        """Mean of every applicable check. 1.0 when nothing was flagged."""
        scored = [r for r in self.results if r.status is not EvalStatus.SKIP]
        if not scored:
            return 1.0
        return round(sum(r.score for r in scored) / len(scored), 3)

    @property
    def failures(self) -> List[EvalResult]:
        return [r for r in self.results if r.status is EvalStatus.FAIL]

    def to_log_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "mode": self.mode,
            "goal": f"{self.goal_type}:{self.goal_target}",
            "intent": self.intent_category,
            "plan": self.plan_action,
            "tool": self.tool_name or "none",
            "goal_achieved": self.goal_achieved,
            "correct_tool": self.correct_tool_used,
            "permissions_ok": self.permission_validation_passed,
            "guardrails_ok": self.input_guardrails_passed and self.output_guardrails_passed,
            "hallucination_risk": self.hallucination_risk,
            "execution_ok": self.execution_success,
            "fallback": self.fallback_used,
            "score": self.overall_score,
            "latency_ms": round(self.latency_ms, 1),
        }
