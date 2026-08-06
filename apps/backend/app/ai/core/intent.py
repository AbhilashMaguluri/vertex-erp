"""Stage 4 — Intent Detection.

Classifies every request into a capability category. The Planner consumes only
:class:`DetectedIntent`, never the detector, so the implementation can be
swapped — rules today, a fine-tuned classifier later — without the Planner
changing a line.

Three implementations ship here:

    RuleBasedIntentDetector  fast, deterministic, no network
    LLMIntentDetector        structured classification for open phrasing
    HybridIntentDetector     rules first, LLM only when rules are unsure

The Goal already carries most of the signal, so detection reads the goal
rather than re-parsing the sentence from scratch. That keeps the two stages
consistent: an intent that contradicts the goal is a bug, not a tie to break.
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Optional

from app.ai.models.context import VertexContext
from app.ai.models.goal import Goal, GoalTarget, GoalType
from app.ai.models.intent import DetectedIntent, IntentCategory
from app.ai.models.message import ChatMessage, MessageRole
from app.ai.providers.base import AIProvider

logger = logging.getLogger("vertex.intent")


class IntentDetector(ABC):
    """Contract every detector implements."""

    @abstractmethod
    async def detect(
        self, message: str, goal: Goal, context: VertexContext
    ) -> DetectedIntent:
        ...  # pragma: no cover


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------

_ATTENDANCE_QUERY = re.compile(
    r"\battendance\b.*\b(?:percentage|percent|%|status|summary|report|record|"
    r"how\s+much|how\s+many|what)\b|"
    r"\b(?:what|show|check|tell)\b.*\battendance\b",
    re.IGNORECASE,
)

_ACADEMIC_QUERY = re.compile(
    r"\b(?:sgpa|cgpa|marks?|grades?|backlogs?|credits?|results?|transcript)\b",
    re.IGNORECASE,
)

_UI_DIALOG = re.compile(r"\b(?:open|close)\s+(?:the\s+)?(?:dialog|modal|popup)\b", re.IGNORECASE)


class RuleBasedIntentDetector(IntentDetector):
    """Deterministic classification derived from the structured goal."""

    async def detect(
        self, message: str, goal: Goal, context: VertexContext
    ) -> DetectedIntent:
        entities: Dict = dict(goal.parameters)
        entities.setdefault("raw_message", message)

        # Resolve *whose* record the request is about while the context is
        # still in hand. "Show attendance" means the caller's own record for a
        # student, and the student on screen for staff — so the Planner never
        # has to ask a question the application can already answer.
        subject = context.workspace.student_id or context.user.student_id
        if subject:
            entities.setdefault("subject_student_id", subject)

        action = str(goal.parameters.get("action") or "")

        # ----- Application state ------------------------------------------
        if goal.target is GoalTarget.APPLICATION_STATE:
            if action in ("setTheme", "getCurrentTheme"):
                return self._intent(
                    IntentCategory.THEME_CHANGE, 0.95, entities,
                    "Goal targets application theme",
                )
            if action == "navigate":
                return self._intent(
                    IntentCategory.NAVIGATION, 0.93, entities,
                    "Goal targets page navigation",
                )
            if action == "logout":
                return self._intent(
                    IntentCategory.WORKFLOW, 0.96, {**entities, "workflow": "logout"},
                    "Goal targets session termination",
                )
            if _UI_DIALOG.search(message):
                return self._intent(
                    IntentCategory.UI_ACTION, 0.85, entities, "Dialog control phrasing"
                )
            return self._intent(
                IntentCategory.UI_ACTION, 0.7, entities,
                "Application-state goal with no specific UI action",
            )

        # ----- Writes ------------------------------------------------------
        if goal.type is GoalType.WORKFLOW and goal.target in (
            GoalTarget.ATTENDANCE,
            GoalTarget.ACADEMIC_RECORD,
        ):
            return self._intent(
                IntentCategory.ACADEMIC_CORRECTION, 0.94, entities,
                "Goal is a correction workflow on an institution-owned record",
            )

        if goal.type is GoalType.ACTION and goal.target is GoalTarget.STUDENT_PROFILE:
            return self._intent(
                IntentCategory.PROFILE_UPDATE, 0.94, entities,
                "Goal mutates a student-owned profile field",
            )

        # ----- Reads --------------------------------------------------------
        if goal.target is GoalTarget.STUDENT_DIRECTORY:
            return self._intent(
                IntentCategory.STUDENT_SEARCH, 0.88, entities,
                "Goal searches the student directory",
            )

        if goal.target is GoalTarget.ATTENDANCE or _ATTENDANCE_QUERY.search(message):
            return self._intent(
                IntentCategory.ATTENDANCE_QUERY, 0.9, entities,
                "Goal reads attendance data",
            )

        if goal.target is GoalTarget.ACADEMIC_RECORD or _ACADEMIC_QUERY.search(message):
            return self._intent(
                IntentCategory.ACADEMIC_QUERY, 0.88, entities,
                "Goal reads academic records",
            )

        if goal.target is GoalTarget.REPORT:
            return self._intent(
                IntentCategory.REPORT_GENERATION, 0.85, entities,
                "Goal generates a report",
            )

        if goal.type is GoalType.CLARIFICATION:
            return self._intent(
                IntentCategory.UNKNOWN, 0.8,
                {**entities, "missing": goal.missing_information},
                "Goal is under-specified — clarification required",
            )

        if goal.target is GoalTarget.STUDENT_PROFILE:
            return self._intent(
                IntentCategory.DATA_RETRIEVAL, 0.82, entities,
                "Goal reads the caller's own profile",
            )

        # ----- Everything else ------------------------------------------------
        confidence = 0.85 if goal.type is GoalType.CONVERSATION else 0.55
        return self._intent(
            IntentCategory.CONVERSATION, confidence, entities,
            "No actionable capability matched — conversational reply",
        )

    @staticmethod
    def _intent(
        category: IntentCategory, confidence: float, entities: Dict, reasoning: str
    ) -> DetectedIntent:
        return DetectedIntent(
            category=category,
            confidence=confidence,
            entities=entities,
            reasoning=reasoning,
            source="rules",
        )


# --------------------------------------------------------------------------
# LLM
# --------------------------------------------------------------------------

class LLMIntentDetector(IntentDetector):
    """Structured classification for phrasing the rules do not cover.

    Asks only for a label. The model never sees this as a chance to answer the
    user, and its output is validated against the enum before use.
    """

    _PROMPT = """\
Classify the user's request into exactly one category. Reply with JSON only:
{"category": "<category>", "confidence": 0.0-1.0, "entities": {}, "reasoning": "<short>"}

Categories:
- conversation        : greetings, thanks, general chat, advice
- navigation          : go to / open a page
- theme_change        : switch light/dark/system appearance
- ui_action           : other interface control (dialogs, toasts)
- profile_update      : change the user's OWN personal details (name, phone, address, guardian)
- academic_correction : an institution record is wrong (attendance, marks, SGPA, backlogs)
- attendance_query    : asking about attendance figures
- academic_query      : asking about marks, SGPA, CGPA, backlogs, results
- student_search      : find a student record
- data_retrieval      : other ERP data lookup
- report_generation   : produce or export a report
- workflow            : logout or another multi-step process
- unknown             : cannot tell

Extract entities only if literally present (field, value, page, mode). Never invent them.
"""

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    async def detect(
        self, message: str, goal: Goal, context: VertexContext
    ) -> DetectedIntent:
        try:
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=self._PROMPT),
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=(
                        f"Caller role: {context.user.role or 'guest'}. "
                        f"Page: {context.page.page}. "
                        f"Derived goal: {goal.summary()}"
                    ),
                ),
                ChatMessage(role=MessageRole.USER, content=message),
            ]
            raw = await self._provider.complete(messages, temperature=0.0, max_tokens=250)
            payload = self._parse(raw)
            if not payload:
                raise ValueError("no JSON object in classifier output")

            category = IntentCategory(str(payload.get("category", "unknown")).lower())
            entities = payload.get("entities") or {}
            return DetectedIntent(
                category=category,
                confidence=min(float(payload.get("confidence", 0.6)), 0.9),
                entities={
                    **{k: v for k, v in entities.items() if v},
                    "raw_message": message,
                },
                reasoning=str(payload.get("reasoning", "LLM classification"))[:200],
                source="llm",
            )
        except (ValueError, KeyError, TypeError) as exc:
            logger.warning("LLM intent classification unusable: %s", exc)
        except Exception as exc:
            logger.warning("LLM intent classification failed: %s", exc)

        return DetectedIntent(
            category=IntentCategory.UNKNOWN,
            confidence=0.0,
            entities={"raw_message": message},
            reasoning="LLM classification unavailable",
            source="fallback",
        )

    @staticmethod
    def _parse(raw: str) -> Optional[Dict]:
        text = (raw or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            parsed = json.loads(text[start : end + 1])
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None


# --------------------------------------------------------------------------
# Hybrid — the default
# --------------------------------------------------------------------------

class HybridIntentDetector(IntentDetector):
    """Rules first; escalate to the LLM only when the rules are unsure.

    Obvious requests ("switch to dark mode") never pay for a round-trip, and
    open phrasing still gets classified rather than falling into a generic
    chat reply.
    """

    ESCALATION_THRESHOLD = 0.7

    def __init__(self, provider: Optional[AIProvider] = None) -> None:
        self._rules = RuleBasedIntentDetector()
        self._llm = LLMIntentDetector(provider) if provider is not None else None

    async def detect(
        self, message: str, goal: Goal, context: VertexContext
    ) -> DetectedIntent:
        rule_intent = await self._rules.detect(message, goal, context)

        if rule_intent.confidence >= self.ESCALATION_THRESHOLD or self._llm is None:
            return rule_intent

        llm_intent = await self._llm.detect(message, goal, context)
        if llm_intent.confidence > rule_intent.confidence:
            llm_intent.alternatives = [rule_intent.category.value]
            # Entities the rules extracted are literal matches; keep them
            # alongside whatever the model found.
            llm_intent.entities = {**rule_intent.entities, **llm_intent.entities}
            return llm_intent

        rule_intent.alternatives = [llm_intent.category.value]
        return rule_intent


def create_default_detector(provider: Optional[AIProvider] = None) -> IntentDetector:
    """Factory used by the pipeline. One place to change the default."""
    return HybridIntentDetector(provider)


__all__ = [
    "IntentDetector",
    "RuleBasedIntentDetector",
    "LLMIntentDetector",
    "HybridIntentDetector",
    "create_default_detector",
]
