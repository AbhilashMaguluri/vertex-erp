"""Planner decision types — what Vertex should do with the request."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel

from app.ai.models.intent import DetectedIntent


class PlanAction(str, Enum):
    RESPOND = "respond"
    EXECUTE_TOOL = "execute_tool"
    MULTI_TOOL = "multi_tool"
    CLARIFY = "clarify"
    REJECT = "reject"


class ExecutionPlan(BaseModel):
    action: PlanAction
    intent: DetectedIntent
    tool_name: Optional[str] = None
    tool_action: Optional[str] = None
    tool_params: Dict = {}
    clarification_message: Optional[str] = None
    rejection_reason: Optional[str] = None
