"""Intent detection — classifies user requests into actionable categories.

Fast path: keyword/pattern matching for obvious intents:
  - Profile Updates (Student-Owned Data)
  - Academic Corrections (Institution-Owned Data)
  - Navigation, Theme, Logout, Data, Reports.

Slow path: LLM classification for ambiguous requests.
"""

from __future__ import annotations

import re
from typing import Optional, Dict

from app.ai.models.context import VertexContext
from app.ai.models.intent import DetectedIntent, IntentCategory
from app.ai.providers.base import AIProvider


# -------------------------------------------------------------------------
# Pattern rules — ordered by specificity. First match wins.
# -------------------------------------------------------------------------

# Student-Owned Data Update Patterns
_PROFILE_UPDATE_PATTERNS = [
    (r"\b(?:change|update|edit|set|modify|fix)\s+(?:my\s+)?name\s+(?:to|as|=|:)?\s*(.+)", "name"),
    (r"\b(?:change|update|edit|set|modify|fix)\s+(?:my\s+)?(?:phone|mobile|number|contact)\s+(?:to|as|=|:)?\s*(.+)", "phone"),
    (r"\b(?:change|update|edit|set|modify|fix)\s+(?:my\s+)?(?:email|mail)\s+(?:to|as|=|:)?\s*(.+)", "email"),
    (r"\b(?:change|update|edit|set|modify|fix)\s+(?:my\s+)?(?:address|location|city)\s+(?:to|as|=|:)?\s*(.+)", "address"),
    (r"\b(?:change|update|edit|set|modify|fix)\s+(?:my\s+)?(?:parent|guardian|father|mother)\s+(?:to|as|=|:)?\s*(.+)", "parent_info"),
    (r"\b(?:change|update|edit|set|modify|fix)\s+(?:my\s+)?emergency\s+(?:contact|number)\s+(?:to|as|=|:)?\s*(.+)", "emergency_contact"),
    (r"\b(?:change|update|edit|set|modify|fix)\s+(?:my\s+)?(?:medical|health)\s+(?:info|details)\s*(.*)", "medical_info"),
    (r"\b(?:change|update|edit|set|modify|fix)\s+(?:my\s+)?(?:photo|avatar|picture|profile\s+pic)\s*(.*)", "photo"),
    (r"\b(?:change|update|edit|set|modify)\s+(?:my\s+)?profile\b", "profile"),
]

# Institution-Owned Data Correction Patterns
_CORRECTION_PATTERNS = [
    (r"\b(?:my\s+)?attendance\s+(?:is\s+)?(?:incorrect|wrong|mistake|error|missing|not\s+updated|low|faulty)\b", "attendance"),
    (r"\b(?:my\s+)?(?:marks|grade|grades|sgpa|cgpa|credits|backlogs?)\s+(?:is|are)\s+(?:incorrect|wrong|mistake|error|missing|faulty)\b", "marks"),
    (r"\b(?:request|apply\s+for|open|raise)\s+(?:an?\s+)?academic\s+correction\b", "academic_correction"),
    (r"\b(?:correct|fix)\s+(?:my\s+)?(?:attendance|sgpa|cgpa|marks|grades|credits|backlog)\b", "institution_data"),
]

_LOGOUT_PATTERNS = [
    (r"\b(?:log\s*out|sign\s*out|sign\s*off|exit|quit)\b", None),
]

_THEME_PATTERNS = [
    (r"\b(?:change|switch|set|toggle|turn\s+on|enable|activate)\b.*\b(?:theme|mode|dark\s*mode|light\s*mode|dark|light|system)\b", None),
    (r"\b(?:dark|light|system)\s*(?:mode|theme)\b", None),
]

_NAVIGATION_PATTERNS = [
    (r"\b(?:open|go\s+to|navigate\s+to|take\s+me\s+to|show\s+me|switch\s+to|visit)\s+(.+)", None),
]

_DATA_PATTERNS = [
    (r"\b(?:show|get|fetch|find|search|look\s*up|retrieve|what\s+is|what\s+are)\b.*\b(?:student|attendance|marks|grades|schedule|timetable|data|record|report)\b", None),
]

_REPORT_PATTERNS = [
    (r"\b(?:generate|create|build|export|download)\b.*\b(?:report|pdf|csv|excel|summary)\b", None),
]


def _extract_page_name(message: str) -> str:
    for pattern, _ in _NAVIGATION_PATTERNS:
        m = re.search(pattern, message, re.IGNORECASE)
        if m and m.group(1):
            return m.group(1).strip().rstrip(".,!?")
    cleaned = re.sub(
        r"\b(?:open|go\s+to|navigate\s+to|take\s+me\s+to|show\s+me|please|can\s+you|the|page)\b",
        "",
        message,
        flags=re.IGNORECASE,
    ).strip().rstrip(".,!?")
    return cleaned or message


def _extract_theme(message: str) -> str:
    lower = message.lower()
    if "dark" in lower:
        return "dark"
    if "light" in lower:
        return "light"
    if "system" in lower:
        return "system"
    return "dark"


class IntentDetector:
    """Classifies user messages into intent categories."""

    def __init__(self, provider: Optional[AIProvider] = None) -> None:
        self._provider = provider

    async def detect(self, message: str, context: VertexContext) -> DetectedIntent:
        lower = message.strip().lower()

        # 1. Student-Owned Profile Data Update
        for pattern, field in _PROFILE_UPDATE_PATTERNS:
            m = re.search(pattern, lower, re.IGNORECASE)
            if m:
                extracted_val = m.group(1).strip().rstrip(".,!?") if m.lastindex and m.lastindex >= 1 else ""
                return DetectedIntent(
                    category=IntentCategory.UPDATE_PROFILE,
                    confidence=0.96,
                    entities={"field": field, "value": extracted_val, "raw_message": message},
                    reasoning=f"Matched student profile update pattern for field '{field}'",
                )

        # 2. Institution-Owned Data Correction Request
        for pattern, section in _CORRECTION_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                return DetectedIntent(
                    category=IntentCategory.ACADEMIC_CORRECTION,
                    confidence=0.96,
                    entities={"section": section, "raw_message": message},
                    reasoning=f"Matched institution data academic correction pattern for section '{section}'",
                )

        # 3. Logout
        for pattern, _ in _LOGOUT_PATTERNS:
            if re.search(pattern, lower):
                return DetectedIntent(
                    category=IntentCategory.WORKFLOW,
                    confidence=0.98,
                    entities={"workflow": "logout"},
                    reasoning="Matched logout keyword pattern",
                )

        # 4. Theme
        for pattern, _ in _THEME_PATTERNS:
            if re.search(pattern, lower):
                theme = _extract_theme(message)
                return DetectedIntent(
                    category=IntentCategory.UI_ACTION,
                    confidence=0.95,
                    entities={"action": "setTheme", "mode": theme},
                    reasoning="Matched theme/mode keyword pattern",
                )

        # 5. Navigation
        for pattern, _ in _NAVIGATION_PATTERNS:
            if re.search(pattern, lower):
                page = _extract_page_name(message)
                return DetectedIntent(
                    category=IntentCategory.NAVIGATION,
                    confidence=0.92,
                    entities={"page": page},
                    reasoning=f"Matched navigation pattern, extracted page: {page}",
                )

        # 6. Report generation
        for pattern, _ in _REPORT_PATTERNS:
            if re.search(pattern, lower):
                return DetectedIntent(
                    category=IntentCategory.REPORT_GENERATION,
                    confidence=0.85,
                    entities={},
                    reasoning="Matched report generation pattern",
                )

        # 7. Data retrieval
        for pattern, _ in _DATA_PATTERNS:
            if re.search(pattern, lower):
                return DetectedIntent(
                    category=IntentCategory.DATA_RETRIEVAL,
                    confidence=0.80,
                    entities={},
                    reasoning="Matched data retrieval pattern",
                )

        # Default: Conversation
        return DetectedIntent(
            category=IntentCategory.CONVERSATION,
            confidence=0.70,
            entities={},
            reasoning="No action pattern matched — treating as conversation",
        )
