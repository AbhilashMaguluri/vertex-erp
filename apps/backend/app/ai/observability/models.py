"""Persistence for Vertex interaction evaluations.

One row per request handled by the agent. Deliberately denormalised and
free of foreign keys to the rest of the schema (``user_id`` is a plain UUID
column, not a reference): telemetry must never block a user deletion or
cascade into application data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VertexInteraction(Base):
    """Scorecard and trace for a single Vertex request."""

    __tablename__ = "vertex_interactions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String(30), nullable=False, default="guest", index=True)

    # ----- What was asked, and what the pipeline decided -----
    user_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    goal_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    goal_target: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    goal_statement: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    intent_category: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    intent_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    plan_action: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    ownership_owner: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    ownership_route: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    tool_name: Mapped[Optional[str]] = mapped_column(String(60), nullable=True, index=True)
    tool_action: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    # ----- The mandated checks -----
    goal_achieved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    correct_tool_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    permission_validation_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    input_guardrails_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    output_guardrails_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hallucination_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    response_format_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    execution_success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0, index=True)

    # ----- Detail -----
    tool_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    response_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Per-eval results and per-stage timings, kept whole so a new check does
    # not need a migration to be queryable.
    eval_results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    timings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        # The two queries the observability endpoint actually runs: recent
        # activity, and recent failures.
        Index("ix_vertex_interactions_created_score", "created_at", "overall_score"),
    )
