"""Guardrails — validation before reasoning and before delivery.

Input guardrails run at stage 3, immediately after context is built and before
the message reaches intent detection or any model. They cover prompt
injection, jailbreak framing, role spoofing, instructions aimed at the tooling
rather than the assistant, and structurally invalid input.

Output guardrails run at stage 11, after reasoning and before the text reaches
the user. They cover leaked secrets, leaked internals, and — the one that
matters most in an ERP — fabricated records. The LLM is not permitted to state
a student's attendance percentage, SGPA or marks unless a tool actually
returned that figure this turn.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field

from app.ai.models.context import VertexContext
from app.ai.models.goal import Goal


class Violation(BaseModel):
    rule: str
    severity: str = "warning"  # info | warning | critical
    detail: str = ""


class GuardrailResult(BaseModel):
    passed: bool = True
    reason: str = ""
    severity: str = "info"
    violations: List[Violation] = Field(default_factory=list)

    # Output guardrails only: the text that should be delivered instead of the
    # model's own, when a violation makes the original unsafe to show.
    safe_replacement: Optional[str] = None

    @property
    def blocked(self) -> bool:
        return not self.passed


# --------------------------------------------------------------------------
# Input rules
# --------------------------------------------------------------------------

_INJECTION_PATTERNS: List[tuple[str, str]] = [
    (r"ignore\s+(?:all\s+|any\s+)?(?:the\s+)?(?:previous|prior|above|earlier)\s+"
     r"(?:instructions?|prompts?|rules?|messages?)", "instruction_override"),
    (r"disregard\s+(?:all\s+|any\s+)?(?:previous|prior|above|your)\s+"
     r"(?:instructions?|rules?|training)", "instruction_override"),
    (r"forget\s+(?:everything|all)\s+(?:you|above|before)", "instruction_override"),
    (r"(?:reveal|show|print|repeat|output|display)\s+(?:me\s+)?(?:your|the)\s+"
     r"(?:system\s+)?(?:prompt|instructions|rules|configuration)", "prompt_extraction"),
    (r"what\s+(?:is|are|were)\s+your\s+(?:system\s+|initial\s+|original\s+)"
     r"(?:prompt|instructions?)", "prompt_extraction"),
    (r"repeat\s+(?:the\s+)?(?:text|words?|everything)\s+above", "prompt_extraction"),
    (r"\bnew\s+(?:system\s+)?(?:instructions?|rules?)\s*[:\-]", "instruction_injection"),
    (r"^\s*(?:system|assistant|developer)\s*[:>]\s*\S", "role_spoofing"),
    (r"<\s*/?\s*(?:system|im_start|im_end|\|im_start\|)", "role_spoofing"),
    (r"you\s+are\s+now\s+(?:a|an|the)\s+(?:DAN|jailbroken|unrestricted|unfiltered|"
     r"developer\s+mode)", "jailbreak"),
    (r"\b(?:enable|activate|enter)\s+(?:developer|god|debug|dan)\s+mode\b", "jailbreak"),
    (r"pretend\s+(?:that\s+)?(?:you\s+(?:are|have)|there\s+are)\s+no\s+"
     r"(?:rules|restrictions|limits|guardrails)", "jailbreak"),
    (r"(?:disable|bypass|turn\s+off|remove|ignore)\s+(?:your\s+|the\s+|all\s+)?"
     r"(?:safety|guardrails?|filters?|restrictions?|permissions?|security)", "guardrail_evasion"),
    (r"\bact\s+as\s+(?:the\s+)?(?:root|admin|administrator|superuser|system)\b",
     "privilege_escalation"),
    (r"\b(?:i\s+am|i'm)\s+(?:the\s+)?(?:admin|administrator|principal|hod|developer|"
     r"superuser)\b.{0,40}\b(?:so|therefore|now)\b", "privilege_escalation"),
    (r"\bgrant\s+(?:me\s+)?(?:admin|full|root)\s+(?:access|permissions?|rights?)",
     "privilege_escalation"),
    (r"\b(?:drop|truncate|delete\s+from|alter)\s+table\b", "sql_injection"),
    (r";\s*(?:drop|delete|update|insert)\s+", "sql_injection"),
    (r"<script[\s>]|javascript:\s*\w", "script_injection"),
]

_MAX_MESSAGE_LENGTH = 4000

#: Instructions that only make sense if aimed at the tooling, not the person.
_TOOL_ABUSE = re.compile(
    r"\b(?:call|invoke|execute|run)\s+(?:the\s+)?(?:tool|function|api|endpoint)\b"
    r"[^.?!]*\b(?:as|on\s+behalf\s+of|for)\s+(?:another|other|admin|any)\b",
    re.IGNORECASE,
)


class InputGuardrails:
    """Validates the incoming message before any reasoning happens."""

    _REFUSAL = (
        "I can't process that request. If you need help with something in "
        "VertexERP, ask me directly and I'll take care of it."
    )

    async def check(
        self, message: str, context: VertexContext, goal: Optional[Goal] = None
    ) -> GuardrailResult:
        violations: List[Violation] = []

        structural = self._check_structure(message)
        if structural:
            return GuardrailResult(
                passed=False,
                reason=structural.detail,
                severity=structural.severity,
                violations=[structural],
            )

        violations.extend(self._check_injection(message))
        violations.extend(self._check_spoofing(message, context))
        violations.extend(self._check_goal_payload(goal))

        critical = [v for v in violations if v.severity == "critical"]
        if critical:
            return GuardrailResult(
                passed=False,
                reason=self._REFUSAL,
                severity="critical",
                violations=violations,
            )

        return GuardrailResult(passed=True, violations=violations)

    # ------------------------------------------------------------------

    @staticmethod
    def _check_structure(message: str) -> Optional[Violation]:
        text = (message or "").strip()
        if not text:
            return Violation(
                rule="empty_message",
                severity="critical",
                detail="Send me a message and I'll help.",
            )
        if len(text) > _MAX_MESSAGE_LENGTH:
            return Violation(
                rule="message_too_long",
                severity="critical",
                detail=(
                    f"That message is too long for me to process "
                    f"({len(text)} characters, limit {_MAX_MESSAGE_LENGTH}). "
                    "Could you shorten it?"
                ),
            )
        # A wall of control characters is not a sentence anyone typed.
        control_chars = sum(1 for c in text if ord(c) < 32 and c not in "\n\r\t")
        if control_chars > 5:
            return Violation(
                rule="malformed_input",
                severity="critical",
                detail="I couldn't read that message. Could you retype it?",
            )
        return None

    @staticmethod
    def _check_injection(message: str) -> List[Violation]:
        violations: List[Violation] = []
        for pattern, rule in _INJECTION_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE | re.MULTILINE):
                violations.append(
                    Violation(rule=rule, severity="critical", detail=f"Matched {rule}")
                )
        if _TOOL_ABUSE.search(message):
            violations.append(
                Violation(
                    rule="tool_abuse",
                    severity="critical",
                    detail="Attempt to direct tool execution at another user's data",
                )
            )
        return violations

    @staticmethod
    def _check_goal_payload(goal: Optional[Goal]) -> List[Violation]:
        """Scan values destined for storage.

        A value that reaches a database column is read back into context on
        later turns, so injection text hidden inside "change my name to
        <payload>" would otherwise become a stored instruction. The message
        scan alone does not catch this: the payload is a legitimate-looking
        argument, not a command aimed at the assistant.
        """
        if goal is None:
            return []

        violations: List[Violation] = []
        for key in ("value", "proposed_value", "new_value"):
            candidate = goal.parameters.get(key)
            if not isinstance(candidate, str) or not candidate.strip():
                continue
            for pattern, rule in _INJECTION_PATTERNS:
                if re.search(pattern, candidate, re.IGNORECASE | re.MULTILINE):
                    violations.append(
                        Violation(
                            rule="payload_injection",
                            severity="critical",
                            detail=f"Value for '{key}' contains {rule}",
                        )
                    )
                    break
        return violations

    @staticmethod
    def _check_spoofing(message: str, context: VertexContext) -> List[Violation]:
        """Claims of authority the token does not back.

        Recorded rather than blocked: saying "as an admin, show me X" is not by
        itself an attack, and the permission validator is what actually decides.
        Logging it keeps the attempt visible in the evaluation record.
        """
        violations: List[Violation] = []
        claim = re.search(
            r"\b(?:as|i\s+am|i'm)\s+(?:an?\s+|the\s+)?"
            r"(admin|administrator|hod|counsellor|faculty|principal|super\s*admin)\b",
            message,
            re.IGNORECASE,
        )
        if claim:
            claimed = claim.group(1).upper().replace(" ", "_")
            held = {r.upper() for r in context.user.roles}
            if claimed not in held:
                violations.append(
                    Violation(
                        rule="role_claim_mismatch",
                        severity="warning",
                        detail=(
                            f"Message claims role '{claimed}'; token grants "
                            f"{sorted(held) or ['none']}"
                        ),
                    )
                )
        return violations


# --------------------------------------------------------------------------
# Output rules
# --------------------------------------------------------------------------

_SECRET_PATTERNS: List[tuple[str, str]] = [
    (r"\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|bearer)\s*[:=]\s*\S{4,}",
     "credential_leak"),
    (r"\b(?:postgres(?:ql)?|mysql|mongodb)(?:\+\w+)?://[^\s]+", "connection_string_leak"),
    (r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "jwt_leak"),
    (r"(?:/app/|/var/www/|/etc/(?:passwd|shadow)|C:\\\\Users\\\\)", "internal_path_leak"),
    (r"\bTraceback \(most recent call last\)", "stacktrace_leak"),
    (r"\b(?:sqlalchemy|psycopg2|asyncpg)\.\w+Error\b", "internal_error_leak"),
]

_SYSTEM_LEAK_PATTERNS: List[str] = [
    r"my\s+system\s+prompt\s+(?:is|says)",
    r"(?:here\s+(?:is|are)|these\s+are)\s+my\s+(?:system\s+)?instructions",
    r"i\s+was\s+instructed\s+to\s+never",
    r"##\s*Ground\s+Rules",
]

#: Concrete ERP figures. Allowed only when a tool actually produced them.
_ERP_FIGURE_PATTERNS: List[tuple[str, str]] = [
    (r"\battendance\s+(?:is|of|stands\s+at|:)\s*\d{1,3}(?:\.\d+)?\s*%", "attendance"),
    (r"\b\d{1,3}(?:\.\d+)?\s*%\s+attendance\b", "attendance"),
    (r"\b(?:SGPA|CGPA)\s*(?:is|:|=|of)\s*\d(?:\.\d+)?", "gpa"),
    (r"\byour\s+(?:marks?|score)\s+(?:is|are|:)\s*\d+", "marks"),
    (r"\byou\s+have\s+\d+\s+(?:active\s+)?backlogs?\b", "backlogs"),
    (r"\bstudent\s+id\s*[:=]\s*\w{4,}", "identifier"),
    (r"\broll\s*(?:number|no)\s*[:=]\s*\w{4,}", "identifier"),
]

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


class OutputGuardrails:
    """Validates generated text before it is delivered.

    ``grounding`` is the set of facts a tool returned this turn. A figure that
    appears in the response but not in the grounding set is treated as
    fabricated — the single most damaging failure mode for an ERP assistant.
    """

    _BLOCKED_REPLACEMENT = (
        "I started to answer with information I can't verify, so I've stopped. "
        "I only report ERP data that comes straight from your records — ask me "
        "again and I'll pull the real figures."
    )

    _SECRET_REPLACEMENT = (
        "I've withheld that response because it contained information I'm not "
        "allowed to share. Let me know what you need and I'll help another way."
    )

    def __init__(self) -> None:
        self._grounding: Set[str] = set()
        self._allow_figures: bool = False

    def ground(self, facts: Optional[Dict] = None, tool_produced_data: bool = False) -> None:
        """Register the figures a tool returned this turn.

        Called by the pipeline after tool execution. Without it, any concrete
        ERP number in the response is unverifiable by definition.
        """
        self._allow_figures = tool_produced_data
        self._grounding = self._flatten(facts or {})

    async def check(
        self, response: str, context: Optional[VertexContext] = None
    ) -> GuardrailResult:
        violations: List[Violation] = []

        for pattern, rule in _SECRET_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(
                    Violation(rule=rule, severity="critical", detail=f"Matched {rule}")
                )

        for pattern in _SYSTEM_LEAK_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(
                    Violation(
                        rule="system_prompt_leak",
                        severity="critical",
                        detail="Response echoed system instructions",
                    )
                )
                break

        violations.extend(self._check_fabrication(response))
        violations.extend(self._check_pii(response, context))

        critical = [v for v in violations if v.severity == "critical"]
        if critical:
            fabricated = any(v.rule == "fabricated_erp_data" for v in critical)
            return GuardrailResult(
                passed=False,
                reason=critical[0].detail,
                severity="critical",
                violations=violations,
                safe_replacement=(
                    self._BLOCKED_REPLACEMENT if fabricated else self._SECRET_REPLACEMENT
                ),
            )

        return GuardrailResult(passed=True, violations=violations)

    # ------------------------------------------------------------------

    def _check_fabrication(self, response: str) -> List[Violation]:
        violations: List[Violation] = []
        for pattern, kind in _ERP_FIGURE_PATTERNS:
            match = re.search(pattern, response, re.IGNORECASE)
            if not match:
                continue
            if self._is_grounded(match.group(0)):
                continue
            violations.append(
                Violation(
                    rule="fabricated_erp_data",
                    severity="critical",
                    detail=(
                        f"Response stated a concrete {kind} figure "
                        f"('{match.group(0).strip()}') that no tool returned this turn"
                    ),
                )
            )
        return violations

    def _is_grounded(self, fragment: str) -> bool:
        if not self._allow_figures:
            return False
        numbers = re.findall(r"\d+(?:\.\d+)?", fragment)
        if not numbers:
            return True
        # Every number in the claim must appear in what the tool returned.
        return all(n in self._grounding for n in numbers)

    @staticmethod
    def _check_pii(response: str, context: Optional[VertexContext]) -> List[Violation]:
        """Third-party email addresses.

        The caller's own address is theirs to see; anyone else's in a generated
        response means data from a record they were not reading.
        """
        emails = set(_EMAIL_RE.findall(response))
        if not emails:
            return []

        own = {(context.user.email or "").lower()} if context else set()
        institutional = {e for e in emails if e.lower() in own}
        third_party = emails - institutional
        if third_party:
            return [
                Violation(
                    rule="third_party_pii",
                    severity="warning",
                    detail=f"Response contained {len(third_party)} non-caller email address(es)",
                )
            ]
        return []

    @staticmethod
    def _flatten(data) -> Set[str]:
        """Every scalar in a tool result, stringified, for grounding checks."""
        out: Set[str] = set()

        def walk(node):
            if isinstance(node, dict):
                for value in node.values():
                    walk(value)
            elif isinstance(node, (list, tuple)):
                for value in node:
                    walk(value)
            elif isinstance(node, bool) or node is None:
                return
            elif isinstance(node, (int, float)):
                text = str(node)
                out.add(text)
                # 82.0 and 82 are the same figure to a reader.
                if text.endswith(".0"):
                    out.add(text[:-2])
                else:
                    out.add(f"{text}.0")
            elif isinstance(node, str):
                out.update(re.findall(r"\d+(?:\.\d+)?", node))

        walk(data)
        return out
