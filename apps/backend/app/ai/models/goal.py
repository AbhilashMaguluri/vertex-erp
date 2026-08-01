"""Goal model — the structured objective Vertex derives *before* reasoning.

Stage 1 of the pipeline. Nothing downstream (context, planner, tools, evals)
reads the raw user message to decide what to do; they read this.

The distinction that matters most is ``GoalType``: an ACTION is something
Vertex must *execute*, a QUESTION is something it must *answer*, a WORKFLOW is
a multi-step process it must *launch*, and CLARIFICATION means the request is
not yet executable. The Planner branches on this, and the Evaluator scores the
final response against ``success_criteria``.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class GoalType(str, Enum):
    """What kind of work the request implies."""

    ACTION = "action"              # Execute something in the application
    QUESTION = "question"          # Answer from context / knowledge
    WORKFLOW = "workflow"          # Launch a multi-step business process
    CLARIFICATION = "clarification"  # Under-specified — must ask back
    CONVERSATION = "conversation"  # Small talk, greetings, thanks


class GoalTarget(str, Enum):
    """The subject the goal operates on. Drives ownership resolution."""

    APPLICATION_STATE = "application_state"  # Theme, navigation, session
    STUDENT_PROFILE = "student_profile"      # Student-owned personal data
    ACADEMIC_RECORD = "academic_record"      # Institution-owned records
    ATTENDANCE = "attendance"                # Institution-owned records
    STUDENT_DIRECTORY = "student_directory"  # Other students' records
    REPORT = "report"
    KNOWLEDGE = "knowledge"                  # No ERP resource involved
    UNKNOWN = "unknown"


class Goal(BaseModel):
    """Structured objective handed to the Planner.

    ``statement`` is written from Vertex's point of view ("Update the user's
    application theme"), never echoed back to the user — it exists so every
    downstream stage and every log line agrees on what was being attempted.
    """

    type: GoalType = GoalType.CONVERSATION
    target: GoalTarget = GoalTarget.UNKNOWN
    statement: str = ""
    raw_message: str = ""

    # Values pulled out of the phrasing (field names, new values, page names).
    parameters: Dict = Field(default_factory=dict)

    # What "done" looks like — read by the Evaluator's goal_achieved check.
    success_criteria: List[str] = Field(default_factory=list)

    # Set when type is CLARIFICATION.
    missing_information: List[str] = Field(default_factory=list)

    confidence: float = 0.0
    reasoning: str = ""

    @property
    def requires_execution(self) -> bool:
        """True when answering with prose alone would be a failure."""
        return self.type in (GoalType.ACTION, GoalType.WORKFLOW)

    def summary(self) -> str:
        return f"{self.type.value}:{self.target.value} — {self.statement}"


class GoalMetadata(BaseModel):
    """Compact form carried into logs and evaluation records."""

    type: str
    target: str
    statement: str
    confidence: float
    parameters: Dict = Field(default_factory=dict)

    @classmethod
    def from_goal(cls, goal: Goal) -> "GoalMetadata":
        return cls(
            type=goal.type.value,
            target=goal.target.value,
            statement=goal.statement,
            confidence=goal.confidence,
            parameters=goal.parameters,
        )


class ClarificationNeeded(BaseModel):
    """Returned by the Goal Builder when the request cannot be acted on yet."""

    question: str
    missing: List[str] = Field(default_factory=list)
    original_goal: Optional[Goal] = None
