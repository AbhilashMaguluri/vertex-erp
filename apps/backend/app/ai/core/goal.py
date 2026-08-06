"""Stage 1 — Goal Builder.

Runs before anything else. The user's raw message is never handed straight to
the LLM; it is first turned into a structured :class:`Goal` describing what
they are trying to accomplish, which every later stage reads instead of
re-parsing the sentence.

    "Change my dashboard to dark mode."  →  action / application_state
    "Change my name to Rahul."           →  action / student_profile
    "My attendance is incorrect."        →  workflow / attendance
    "What is my attendance?"             →  question / attendance
    "Change it."                         →  clarification (missing: what, value)

The rule layer resolves the overwhelming majority of ERP phrasing on its own.
Only genuinely ambiguous messages pay for an LLM round-trip, and the LLM is
asked for structured JSON — never for a user-facing answer.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from app.ai.models.context import VertexContext
from app.ai.models.goal import Goal, GoalTarget, GoalType
from app.ai.models.message import ChatMessage, MessageRole
from app.ai.providers.base import AIProvider

logger = logging.getLogger("vertex.goal")


# --------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------

_MUTATION_VERBS = (
    r"change|update|edit|set|modify|correct|fix|rename|replace|amend|revise"
)
_QUESTION_OPENERS = (
    r"what|when|where|which|who|whose|how|why|is|are|do|does|did|can|could|"
    r"should|would|will|show|tell|list|give"
)

# Field aliases → canonical field name. Longest phrases first so "emergency
# contact" is not shadowed by "contact".
_FIELD_ALIASES: List[Tuple[str, str]] = [
    (r"emergency\s+contact(?:\s+(?:number|phone|name))?", "emergency_contact"),
    (r"(?:parent|guardian|father|mother)(?:'s)?\s*(?:name|phone|number|details|info)?", "parent_info"),
    (r"(?:permanent|current|residential)\s+address", "address"),
    (r"(?:profile\s+)?(?:photo|picture|avatar|pic)", "photo"),
    (r"(?:medical|health)\s*(?:info|information|details|conditions)?", "medical_info"),
    (r"(?:mobile|phone|contact)\s*(?:number|no)?", "phone"),
    (r"(?:personal\s+)?e-?mail(?:\s+address)?", "email"),
    (r"(?:full\s+|first\s+|last\s+|display\s+)?name", "name"),
    (r"date\s+of\s+birth|dob|birthday", "date_of_birth"),
    (r"blood\s+group", "blood_group"),
    (r"address", "address"),
    (r"attendance", "attendance"),
    (r"sgpa", "sgpa"),
    (r"cgpa", "cgpa"),
    (r"backlogs?", "backlogs"),
    (r"credits?", "credits"),
    (r"marks?|grades?|scores?", "marks"),
    (r"roll\s*(?:number|no)", "roll_number"),
    (r"registration\s*(?:number|no)", "registration_number"),
    (r"(?:department|branch)", "department"),
    (r"semester", "semester"),
    (r"section", "section"),
]

# Field → the resource family it belongs to.
_FIELD_TARGETS: Dict[str, GoalTarget] = {
    "attendance": GoalTarget.ATTENDANCE,
    "marks": GoalTarget.ACADEMIC_RECORD,
    "sgpa": GoalTarget.ACADEMIC_RECORD,
    "cgpa": GoalTarget.ACADEMIC_RECORD,
    "backlogs": GoalTarget.ACADEMIC_RECORD,
    "credits": GoalTarget.ACADEMIC_RECORD,
    "semester": GoalTarget.ACADEMIC_RECORD,
    "department": GoalTarget.ACADEMIC_RECORD,
    "section": GoalTarget.ACADEMIC_RECORD,
    "roll_number": GoalTarget.ACADEMIC_RECORD,
    "registration_number": GoalTarget.ACADEMIC_RECORD,
}

_THEME_WORDS = re.compile(
    r"\b(?:dark|light|night|day|system)\s*(?:mode|theme|appearance)\b|"
    r"\b(?:mode|theme|appearance)\s+(?:to\s+)?(dark|light|system)\b|"
    r"\b(?:enable|activate|switch\s+to|change\s+to|set\s+to|use|turn\s+on)\s+(dark|light|system)\b",
    re.IGNORECASE,
)

_THEME_QUERY = re.compile(
    r"\b(?:what|which|get|check|show|current)\b.*\b(?:theme|mode|appearance)\b|"
    r"\b(?:theme|mode|appearance)\s+(?:is\s+)?(?:active|current|set|selected)\b",
    re.IGNORECASE,
)

_GENERIC_THEME_PHRASES = re.compile(
    r"\b(?:switch|change|toggle)\s+(?:the\s+)?(?:theme|appearance|mode)\b|"
    r"\b(?:theme|appearance|mode)\s+(?:switch|change|toggle)\b|"
    r"\b(?:toggle\s+theme|toggle\s+appearance)\b",
    re.IGNORECASE,
)

_NAV_VERBS = re.compile(
    r"\b(?:open|go\s+to|navigate\s+to|take\s+me\s+to|switch\s+to|visit|"
    r"bring\s+up|jump\s+to)\b",
    re.IGNORECASE,
)

_LOGOUT = re.compile(r"\b(?:log\s*out|sign\s*out|sign\s*me\s*out|log\s*me\s*out)\b", re.IGNORECASE)

_COMPLAINT = re.compile(
    r"\b(?:is|are|seems?|looks?|shows?)\s+(?:showing\s+)?"
    r"(?:incorrect|wrong|invalid|inaccurate|missing|not\s+(?:correct|right|updated|showing))\b"
    r"|\b(?:incorrect|wrong|missing|not\s+updated|hasn'?t\s+been\s+updated)\b",
    re.IGNORECASE,
)

_CORRECTION_REQUEST = re.compile(
    r"\b(?:raise|open|file|submit|create|apply\s+for|request)\s+(?:an?\s+)?"
    r"(?:academic\s+)?correction\b",
    re.IGNORECASE,
)

_REPORT = re.compile(
    r"\b(?:generate|create|build|export|download|produce)\b[^.?!]*\b"
    r"(?:report|pdf|csv|excel|spreadsheet|summary\s+document)\b",
    re.IGNORECASE,
)

_SEARCH = re.compile(
    r"\b(?:find|search\s+for|look\s+up|locate|show\s+me)\b[^.?!]*\b"
    r"(?:student|students|roll\s*(?:number|no))\b",
    re.IGNORECASE,
)

_GREETING = re.compile(
    r"^\s*(?:hi|hey|hello|yo|good\s+(?:morning|afternoon|evening)|thanks?|"
    r"thank\s+you|ok(?:ay)?|cool|nice|bye|goodbye)\b[\s!.?]*$",
    re.IGNORECASE,
)

# Pronouns with no referent — the signal that a mutation is under-specified.
_DANGLING_REFERENCE = re.compile(
    r"^\s*(?:please\s+)?(?:can\s+you\s+)?(?:change|update|fix|correct|set|edit)"
    r"\s+(?:it|this|that|them|mine)\b",
    re.IGNORECASE,
)


def _canonical_field(text: str) -> Optional[str]:
    for pattern, field in _FIELD_ALIASES:
        if re.search(rf"\b{pattern}\b", text, re.IGNORECASE):
            return field
    return None


def _extract_new_value(message: str, field: str) -> str:
    """Pull the value out of "change X to Y" phrasings."""
    patterns = [
        rf"(?:{_MUTATION_VERBS})\s+(?:my\s+|the\s+)?[\w\s']*?\bto\s+(.+)$",
        rf"(?:{_MUTATION_VERBS})\s+(?:my\s+|the\s+)?[\w\s']*?\b(?:as|=|:)\s*(.+)$",
        r"\bshould\s+be\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            value = match.group(1).strip().strip("\"'").rstrip(".,!?")
            # "change my theme to dark mode" → the value is the theme, not a
            # profile value; callers decide. Strip a trailing noun that just
            # repeats the field.
            value = re.sub(r"\s+(?:mode|theme|please)$", "", value, flags=re.IGNORECASE)
            if value and len(value) <= 200:
                return value
    return ""


def _extract_page(message: str) -> str:
    match = _NAV_VERBS.search(message)
    if match:
        tail = message[match.end():].strip()
        tail = re.sub(r"^(?:the|my|a)\s+", "", tail, flags=re.IGNORECASE)
        tail = re.sub(r"\s+(?:page|screen|tab|section)\b.*$", "", tail, flags=re.IGNORECASE)
        return tail.strip().rstrip(".,!?")
    return ""


def _extract_theme(message: str) -> str:
    lowered = message.lower()
    if re.search(r"\b(?:dark|night)\b", lowered):
        return "dark"
    if re.search(r"\b(?:light|day)\b", lowered):
        return "light"
    if re.search(r"\bsystem\b", lowered):
        return "system"
    return ""


class GoalBuilder:
    """Turns a raw message plus context into a structured :class:`Goal`.

    ``provider`` is optional. When supplied, messages the rules cannot classify
    confidently are escalated to the LLM for structured classification only.
    """

    #: Below this, the rule result is treated as a guess worth escalating.
    ESCALATION_THRESHOLD = 0.6

    def __init__(self, provider: Optional[AIProvider] = None) -> None:
        self._provider = provider

    async def build(self, message: str, context: VertexContext) -> Goal:
        goal = self._build_from_rules(message, context)

        if goal.confidence < self.ESCALATION_THRESHOLD and self._provider is not None:
            refined = await self._build_from_llm(message, context, goal)
            if refined is not None:
                return refined

        return goal

    # ------------------------------------------------------------------
    # Rule layer
    # ------------------------------------------------------------------

    def _build_from_rules(self, message: str, context: VertexContext) -> Goal:
        text = message.strip()

        if not text:
            return Goal(
                type=GoalType.CLARIFICATION,
                statement="Determine what the user needs",
                raw_message=message,
                missing_information=["request"],
                confidence=1.0,
                reasoning="Empty message",
            )

        # ----- Small talk -------------------------------------------------
        if _GREETING.match(text):
            return Goal(
                type=GoalType.CONVERSATION,
                target=GoalTarget.KNOWLEDGE,
                statement="Exchange a greeting or acknowledgement",
                raw_message=message,
                success_criteria=["Reply briefly and offer help"],
                confidence=0.95,
                reasoning="Matched greeting/acknowledgement",
            )

        # ----- Under-specified mutation ("change it") ---------------------
        if _DANGLING_REFERENCE.match(text) and not _canonical_field(text):
            return Goal(
                type=GoalType.CLARIFICATION,
                statement="Identify which value the user wants changed",
                raw_message=message,
                missing_information=["field", "new_value"],
                confidence=0.9,
                reasoning="Mutation verb with an unresolved pronoun and no field",
            )

        # ----- Session -----------------------------------------------------
        if _LOGOUT.search(text):
            return Goal(
                type=GoalType.ACTION,
                target=GoalTarget.APPLICATION_STATE,
                statement="End the user's session and sign them out",
                raw_message=message,
                parameters={"action": "logout"},
                success_criteria=["Session terminated", "User returned to login"],
                confidence=0.97,
                reasoning="Matched logout phrasing",
            )

        # ----- Theme --------------------------------------------------------
        if _THEME_QUERY.search(text):
            return Goal(
                type=GoalType.QUESTION,
                target=GoalTarget.APPLICATION_STATE,
                statement="Retrieve the active application theme from live UI state",
                raw_message=message,
                parameters={"action": "getCurrentTheme"},
                success_criteria=["Current theme retrieved from live UI state"],
                confidence=0.95,
                reasoning="Matched theme query phrasing",
            )

        theme = _extract_theme(text)
        if (_THEME_WORDS.search(text) or theme) and theme:
            return Goal(
                type=GoalType.ACTION,
                target=GoalTarget.APPLICATION_STATE,
                statement=f"Update the user's application theme to {theme} mode",
                raw_message=message,
                parameters={"action": "setTheme", "mode": theme},
                success_criteria=[f"Theme set to {theme}"],
                confidence=0.95,
                reasoning=f"Matched theme phrasing, resolved mode='{theme}'",
            )

        if _GENERIC_THEME_PHRASES.search(text):
            return Goal(
                type=GoalType.ACTION,
                target=GoalTarget.APPLICATION_STATE,
                statement="Toggle or switch the application theme",
                raw_message=message,
                parameters={"action": "toggleTheme"},
                success_criteria=["Theme toggled"],
                confidence=0.95,
                reasoning="Matched generic theme switching phrasing",
            )

        # ----- Navigation ---------------------------------------------------
        page = _extract_page(text)
        if page:
            return Goal(
                type=GoalType.ACTION,
                target=GoalTarget.APPLICATION_STATE,
                statement=f"Navigate the user to the {page} page",
                raw_message=message,
                parameters={"action": "navigate", "page": page},
                success_criteria=[f"User is on the {page} page"],
                confidence=0.9,
                reasoning=f"Matched navigation verb, extracted page='{page}'",
            )

        # ----- Explicit correction request ----------------------------------
        field = _canonical_field(text)
        if _CORRECTION_REQUEST.search(text):
            resolved = field or "attendance"
            return Goal(
                type=GoalType.WORKFLOW,
                target=_FIELD_TARGETS.get(resolved, GoalTarget.ACADEMIC_RECORD),
                statement=f"Create an Academic Correction Request for {resolved}",
                raw_message=message,
                parameters={"field": resolved, "description": text},
                success_criteria=["Correction request submitted", "Counsellor notified"],
                confidence=0.93,
                reasoning="Explicit request to open an academic correction",
            )

        # ----- Complaint about a record ("my attendance is incorrect") ------
        if field and _COMPLAINT.search(text):
            target = _FIELD_TARGETS.get(field, GoalTarget.STUDENT_PROFILE)
            if target is not GoalTarget.STUDENT_PROFILE:
                return Goal(
                    type=GoalType.WORKFLOW,
                    target=target,
                    statement=f"Create an Academic Correction Request for {field}",
                    raw_message=message,
                    parameters={"field": field, "description": text},
                    success_criteria=["Correction request submitted", "Counsellor notified"],
                    confidence=0.92,
                    reasoning=f"Complaint about institution-owned '{field}'",
                )

        # ----- Mutation of a named field -------------------------------------
        mutation = re.search(rf"\b(?:{_MUTATION_VERBS})\b", text, re.IGNORECASE)
        if mutation and field:
            target = _FIELD_TARGETS.get(field, GoalTarget.STUDENT_PROFILE)
            value = _extract_new_value(text, field)

            if target is not GoalTarget.STUDENT_PROFILE:
                # Asking to change an institution record is a correction
                # workflow, never a refusal.
                return Goal(
                    type=GoalType.WORKFLOW,
                    target=target,
                    statement=f"Create an Academic Correction Request for {field}",
                    raw_message=message,
                    parameters={"field": field, "proposed_value": value, "description": text},
                    success_criteria=["Correction request submitted"],
                    confidence=0.9,
                    reasoning=f"Mutation requested on institution-owned '{field}'",
                )

            if not value and field not in ("photo", "medical_info"):
                return Goal(
                    type=GoalType.CLARIFICATION,
                    target=GoalTarget.STUDENT_PROFILE,
                    statement=f"Determine the new value for the user's {field}",
                    raw_message=message,
                    parameters={"field": field},
                    missing_information=["new_value"],
                    confidence=0.85,
                    reasoning=f"Mutation on '{field}' with no value supplied",
                )

            return Goal(
                type=GoalType.ACTION,
                target=GoalTarget.STUDENT_PROFILE,
                statement=f"Update the student's {field.replace('_', ' ')} in their personal profile",
                raw_message=message,
                parameters={"field": field, "value": value},
                success_criteria=[f"{field} persisted", "Change confirmed to the user"],
                confidence=0.93,
                reasoning=f"Mutation on student-owned '{field}' with value='{value}'",
            )

        # ----- Reports --------------------------------------------------------
        if _REPORT.search(text):
            return Goal(
                type=GoalType.ACTION,
                target=GoalTarget.REPORT,
                statement="Generate the report the user asked for",
                raw_message=message,
                parameters={"raw": text},
                success_criteria=["Report produced or the user routed to Reports"],
                confidence=0.8,
                reasoning="Matched report generation phrasing",
            )

        # ----- Student search --------------------------------------------------
        if _SEARCH.search(text):
            return Goal(
                type=GoalType.QUESTION,
                target=GoalTarget.STUDENT_DIRECTORY,
                statement="Find the student record the user is looking for",
                raw_message=message,
                parameters={"query": text},
                success_criteria=["Matching students returned from the ERP"],
                confidence=0.82,
                reasoning="Matched student search phrasing",
            )

        # ----- Questions about a record ------------------------------------------
        is_question = bool(
            text.endswith("?")
            or re.match(rf"^\s*(?:{_QUESTION_OPENERS})\b", text, re.IGNORECASE)
        )
        if is_question and field:
            target = _FIELD_TARGETS.get(field, GoalTarget.STUDENT_PROFILE)
            return Goal(
                type=GoalType.QUESTION,
                target=target,
                statement=f"Answer the user's question about their {field.replace('_', ' ')}",
                raw_message=message,
                parameters={"field": field},
                success_criteria=["Answer drawn from real ERP data, not invented"],
                confidence=0.85,
                reasoning=f"Question about '{field}'",
            )

        if is_question:
            return Goal(
                type=GoalType.QUESTION,
                target=GoalTarget.KNOWLEDGE,
                statement="Answer the user's question",
                raw_message=message,
                success_criteria=["Accurate answer, no invented ERP data"],
                confidence=0.7,
                reasoning="Interrogative phrasing with no ERP resource named",
            )

        # ----- Fall through ---------------------------------------------------
        return Goal(
            type=GoalType.CONVERSATION,
            target=GoalTarget.KNOWLEDGE,
            statement="Respond helpfully to the user's message",
            raw_message=message,
            success_criteria=["Helpful, accurate reply"],
            confidence=0.4,
            reasoning="No rule matched — low confidence, eligible for escalation",
        )

    # ------------------------------------------------------------------
    # LLM escalation
    # ------------------------------------------------------------------

    _CLASSIFIER_PROMPT = """\
You classify requests for an Enterprise ERP AI agent. Reply with JSON ONLY —
no prose, no markdown fence.

Schema:
{
  "type": "action" | "question" | "workflow" | "clarification" | "conversation",
  "target": "application_state" | "student_profile" | "academic_record" |
            "attendance" | "student_directory" | "report" | "knowledge" | "unknown",
  "statement": "<one line, from the agent's point of view, e.g. 'Update the user's application theme'>",
  "parameters": {"field": "...", "value": "...", "page": "...", "mode": "..."},
  "missing_information": ["..."],
  "confidence": 0.0-1.0
}

Rules:
- "action"       = change something now (theme, navigation, own profile field, logout).
- "workflow"     = institution-owned record is wrong (attendance, marks, SGPA, backlogs) —
                   these become Academic Correction Requests, never direct edits.
- "question"     = the user wants information back.
- "clarification"= the request names no field, no value, or an unresolved pronoun.
- "conversation" = greetings, thanks, small talk.
Include only parameters you can actually read in the message. Never invent values.
"""

    async def _build_from_llm(
        self, message: str, context: VertexContext, fallback: Goal
    ) -> Optional[Goal]:
        try:
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=self._CLASSIFIER_PROMPT),
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=(
                        f"Caller role: {context.user.role or 'guest'}. "
                        f"Current page: {context.page.page}."
                    ),
                ),
                ChatMessage(role=MessageRole.USER, content=message),
            ]
            raw = await self._provider.complete(
                messages, temperature=0.0, max_tokens=400
            )
            payload = self._parse_json(raw)
            if not payload:
                return None

            goal = Goal(
                type=GoalType(payload.get("type", fallback.type.value)),
                target=GoalTarget(payload.get("target", fallback.target.value)),
                statement=str(payload.get("statement", fallback.statement))[:300],
                raw_message=message,
                parameters={
                    k: v for k, v in (payload.get("parameters") or {}).items() if v
                },
                missing_information=list(payload.get("missing_information") or []),
                confidence=min(float(payload.get("confidence", 0.6)), 0.9),
                reasoning="Classified by LLM escalation",
            )
            if not goal.success_criteria:
                goal.success_criteria = ["Goal satisfied without inventing ERP data"]
            return goal

        except (ValueError, KeyError, TypeError) as exc:
            logger.warning("Goal LLM escalation returned unusable output: %s", exc)
            return None
        except Exception as exc:  # provider/network failure — rules still stand
            logger.warning("Goal LLM escalation failed: %s", exc)
            return None

    @staticmethod
    def _parse_json(raw: str) -> Optional[Dict]:
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
