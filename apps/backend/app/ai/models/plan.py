"""Planner decision types — what Vertex will do, decided before anything runs.

The LLM never manipulates application state. It receives a plan that has
already been made, executed and permission-checked, and its only job is to
communicate the outcome.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.ai.models.goal import Goal
from app.ai.models.intent import DetectedIntent
from app.ai.models.ownership import OwnershipDecision


class PlanAction(str, Enum):
    RESPOND = "respond"              # Reason and answer, no state change
    EXECUTE_TOOL = "execute_tool"
    MULTI_TOOL = "multi_tool"
    CLARIFY = "clarify"              # Ask back — goal not yet executable
    CONFIRM = "confirm"              # Destructive/irreversible; ask first
    REJECT = "reject"                # Not permitted or not possible


class PlanStep(BaseModel):
    """One tool invocation inside a plan.

    A single-tool plan carries exactly one step; MULTI_TOOL carries several,
    executed in order and short-circuited on the first failure.
    """

    tool_name: str
    tool_action: str
    tool_params: Dict = Field(default_factory=dict)
    description: str = ""

    # Permissions this step needs, copied off the tool's action metadata at
    # planning time so the validator never has to re-look-up the tool.
    required_permissions: List[str] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    """The complete decision for one request."""

    action: PlanAction
    goal: Goal
    intent: DetectedIntent
    ownership: OwnershipDecision = Field(default_factory=OwnershipDecision)

    steps: List[PlanStep] = Field(default_factory=list)

    clarification_message: Optional[str] = None
    confirmation_message: Optional[str] = None
    rejection_reason: Optional[str] = None

    # Why the planner chose this branch — logged, and read by the Evaluator.
    reasoning: str = ""

    # ------------------------------------------------------------------
    # Convenience accessors — most plans are single-step, and the pipeline
    # reads them constantly.
    # ------------------------------------------------------------------

    @property
    def primary_step(self) -> Optional[PlanStep]:
        return self.steps[0] if self.steps else None

    @property
    def tool_name(self) -> Optional[str]:
        step = self.primary_step
        return step.tool_name if step else None

    @property
    def tool_action(self) -> Optional[str]:
        step = self.primary_step
        return step.tool_action if step else None

    @property
    def tool_params(self) -> Dict:
        step = self.primary_step
        return step.tool_params if step else {}

    @property
    def executes_tools(self) -> bool:
        return self.action in (PlanAction.EXECUTE_TOOL, PlanAction.MULTI_TOOL)
