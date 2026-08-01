"""Observability endpoints for the Vertex pipeline.

Developer-facing, not user-facing: every route is gated on ``audit.read``,
the same permission that guards the audit log, because these records contain
what users typed.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.observability.store import evaluation_store
from app.core.permissions import require_permission
from app.database import get_async_db

router = APIRouter(prefix="/api/vertex/observability", tags=["Vertex AI — Observability"])


@router.get("/stats")
async def pipeline_stats(_=Depends(require_permission("audit.read"))):
    """Aggregate health of recent Vertex traffic, from the in-process buffer."""
    return evaluation_store.stats()


@router.get("/evaluations")
async def recent_evaluations(
    limit: int = Query(50, ge=1, le=200),
    failures_only: bool = Query(False),
    _=Depends(require_permission("audit.read")),
):
    """The most recent interaction scorecards, newest first."""
    reports = (
        evaluation_store.failures(limit)
        if failures_only
        else evaluation_store.recent(limit)
    )
    return {
        "count": len(reports),
        "source": "memory",
        "evaluations": [
            {**r.to_log_dict(), "failures": [f.model_dump(mode="json") for f in r.failures]}
            for r in reports
        ],
    }


@router.get("/evaluations/history")
async def evaluation_history(
    limit: int = Query(50, ge=1, le=200),
    mode: Optional[str] = Query(None),
    intent: Optional[str] = Query(None),
    failures_only: bool = Query(False),
    _=Depends(require_permission("audit.read")),
    db: AsyncSession = Depends(get_async_db),
):
    """Durable history from the database, with the filters worth having."""
    from app.ai.observability.models import VertexInteraction

    query = select(VertexInteraction).order_by(desc(VertexInteraction.created_at))
    if mode:
        query = query.where(VertexInteraction.mode == mode)
    if intent:
        query = query.where(VertexInteraction.intent_category == intent)
    if failures_only:
        query = query.where(VertexInteraction.overall_score < 1.0)

    rows: List[VertexInteraction] = (
        (await db.execute(query.limit(limit))).scalars().all()
    )

    return {
        "count": len(rows),
        "source": "database",
        "evaluations": [
            {
                "request_id": row.request_id,
                "created_at": row.created_at.isoformat(),
                "mode": row.mode,
                "goal": f"{row.goal_type}:{row.goal_target}",
                "goal_statement": row.goal_statement,
                "intent": row.intent_category,
                "plan": row.plan_action,
                "tool": row.tool_name,
                "goal_achieved": row.goal_achieved,
                "correct_tool": row.correct_tool_used,
                "permissions_ok": row.permission_validation_passed,
                "guardrails_ok": row.input_guardrails_passed and row.output_guardrails_passed,
                "hallucination_risk": row.hallucination_risk,
                "execution_ok": row.execution_success,
                "fallback": row.fallback_used,
                "score": row.overall_score,
                "latency_ms": row.latency_ms,
                "tool_error": row.tool_error,
                "error": row.error,
            }
            for row in rows
        ],
    }
