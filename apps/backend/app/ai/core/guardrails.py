"""Guardrails — input and output validation for the Vertex pipeline.

Input guardrails run BEFORE the planner.
Output guardrails run AFTER the LLM response.
"""

from __future__ import annotations

import re
from typing import List

from pydantic import BaseModel

from app.ai.models.context import VertexContext
from app.ai.models.intent import DetectedIntent, IntentCategory


class GuardrailResult(BaseModel):
    passed: bool
    reason: str = ""
    severity: str = "info"  # info | warning | critical


# Injection patterns
_INJECTION_PATTERNS: List[str] = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above",
    r"you\s+are\s+now\s+(?:a|an|the)\s+(?:DAN|jailbroken|unrestricted)",
    r"system\s*:\s*",
    r"act\s+as\s+(?:root|admin|system|developer|hacker)",
    r"pretend\s+(?:you\s+are|to\s+be)\s+(?:a|an|the)?",
    r"override\s+(?:your|system|safety)",
    r"disable\s+(?:safety|guardrails|filters|restrictions)",
    r"reveal\s+(?:your|system|the)\s+(?:prompt|instructions|system\s+message)",
    r"what\s+(?:is|are)\s+your\s+(?:system|initial)\s+(?:prompt|instructions)",
]

# Guest mode restrictions
_GUEST_BLOCKED_INTENTS = {
    IntentCategory.DATA_RETRIEVAL,
    IntentCategory.REPORT_GENERATION,
    IntentCategory.UPDATE_PROFILE,
    IntentCategory.ACADEMIC_CORRECTION,
}


class InputGuardrails:
    """Validates incoming requests before planning."""

    async def check(
        self, message: str, intent: DetectedIntent, context: VertexContext
    ) -> GuardrailResult:
        # 1. Prompt injection check
        injection = self._check_injection(message)
        if not injection.passed:
            return injection

        # 2. Permission check
        permission = self._check_permissions(intent, context)
        if not permission.passed:
            return permission

        return GuardrailResult(passed=True)

    def _check_injection(self, message: str) -> GuardrailResult:
        lower = message.lower()
        for pattern in _INJECTION_PATTERNS:
            if re.search(pattern, lower):
                return GuardrailResult(
                    passed=False,
                    reason="I can't process that request. If you need help, please rephrase your question.",
                    severity="critical",
                )
        return GuardrailResult(passed=True)

    def _check_permissions(
        self, intent: DetectedIntent, context: VertexContext
    ) -> GuardrailResult:
        # Guest mode restrictions
        if context.mode == "guest" and intent.category in _GUEST_BLOCKED_INTENTS:
            return GuardrailResult(
                passed=False,
                reason="You need to sign in to perform that action. Would you like help with the login process?",
                severity="warning",
            )

        # Students can update their profile or raise academic corrections
        if intent.category in (IntentCategory.UPDATE_PROFILE, IntentCategory.ACADEMIC_CORRECTION):
            return GuardrailResult(passed=True)

        # Students can't access admin workflows
        if context.mode == "student" and intent.category == IntentCategory.WORKFLOW:
            workflow = intent.entities.get("workflow", "")
            if workflow and workflow not in ("logout",):
                return GuardrailResult(
                    passed=False,
                    reason="You don't have permission to perform that action.",
                    severity="warning",
                )

        return GuardrailResult(passed=True)


class OutputGuardrails:
    """Validates LLM output before it reaches the user."""

    _SENSITIVE_PATTERNS = [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Emails
        r"\b(?:password|secret|api[_-]?key|token)\s*[:=]\s*\S+",   # Secrets
        r"(?:\/app\/|\/var\/|\/etc\/|C:\\\\)",                        # Internal paths
    ]

    async def check(self, response: str) -> GuardrailResult:
        """Scan response for sensitive data leaks."""
        for pattern in self._SENSITIVE_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                return GuardrailResult(
                    passed=False,
                    reason="Response contained potentially sensitive information and was filtered.",
                    severity="warning",
                )
        return GuardrailResult(passed=True)
