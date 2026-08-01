"""Intent detection types — the classification every request must carry.

Detection is deliberately separate from the Goal: the Goal says *what the user
wants*, the Intent says *which capability class handles it*. Keeping them apart
is what lets the detector be swapped (rules → LLM → fine-tuned classifier)
without the Planner changing.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class IntentCategory(str, Enum):
    CONVERSATION = "conversation"
    NAVIGATION = "navigation"
    THEME_CHANGE = "theme_change"
    UI_ACTION = "ui_action"
    PROFILE_UPDATE = "profile_update"            # Student-owned data
    ACADEMIC_CORRECTION = "academic_correction"  # Institution-owned data
    ATTENDANCE_QUERY = "attendance_query"
    ACADEMIC_QUERY = "academic_query"
    STUDENT_SEARCH = "student_search"
    DATA_RETRIEVAL = "data_retrieval"
    REPORT_GENERATION = "report_generation"
    WORKFLOW = "workflow"
    UNKNOWN = "unknown"


# Categories that must end in a tool call — answering them with prose only is
# a failure, and the Evaluator scores them that way.
ACTIONABLE_INTENTS: set[IntentCategory] = {
    IntentCategory.NAVIGATION,
    IntentCategory.THEME_CHANGE,
    IntentCategory.UI_ACTION,
    IntentCategory.PROFILE_UPDATE,
    IntentCategory.ACADEMIC_CORRECTION,
    IntentCategory.ATTENDANCE_QUERY,
    IntentCategory.ACADEMIC_QUERY,
    IntentCategory.STUDENT_SEARCH,
    IntentCategory.WORKFLOW,
}


class DetectedIntent(BaseModel):
    category: IntentCategory = IntentCategory.UNKNOWN
    confidence: float = 0.0
    entities: Dict = Field(default_factory=dict)
    reasoning: str = ""

    # Which detector produced this — "rules", "llm", "fallback". Logged so a
    # regression can be traced to the layer that caused it.
    source: str = "rules"

    # Categories the detector considered but did not pick, best first.
    alternatives: List[str] = Field(default_factory=list)

    @property
    def is_actionable(self) -> bool:
        return self.category in ACTIONABLE_INTENTS

    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.75
