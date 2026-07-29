"""Intent detection types — classifies what the user wants Vertex to do."""

from __future__ import annotations

from enum import Enum
from typing import Dict

from pydantic import BaseModel


class IntentCategory(str, Enum):
    CONVERSATION = "conversation"
    NAVIGATION = "navigation"
    UI_ACTION = "ui_action"
    UPDATE_PROFILE = "update_profile"         # Student-owned data modification
    ACADEMIC_CORRECTION = "academic_correction" # Institution-owned data correction workflow
    DATA_RETRIEVAL = "data_retrieval"
    REPORT_GENERATION = "report_generation"
    WORKFLOW = "workflow"
    UNKNOWN = "unknown"


class DetectedIntent(BaseModel):
    category: IntentCategory
    confidence: float = 0.0
    entities: Dict = {}
    reasoning: str = ""
