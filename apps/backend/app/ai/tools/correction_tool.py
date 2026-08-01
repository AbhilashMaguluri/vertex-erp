"""Academic Correction Tool — the route for institution-owned records.

Attendance, marks, SGPA/CGPA, credits, backlogs, department and enrolment
details belong to the Academic Office. A student cannot edit them, so when one
of them is wrong the answer is not a refusal — it is a correction request.

This tool creates that request for real: a row in
``academic_correction_requests``, an audit log entry, and a notification to the
assigned counsellor, through the same service the Corrections screen uses.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from app.ai.models.ownership import CORRECTION_SECTIONS, DataOwner
from app.ai.tools.base import ToolAction, ToolExecutionContext, ToolResult, VertexTool

logger = logging.getLogger("vertex.tools.correction")

# Where the user is sent to watch the request progress, by section.
_SECTION_ROUTES: Dict[str, str] = {
    "Attendance": "/attendance",
    "Marks & Grades": "/academics",
    "SGPA / CGPA": "/academics",
    "Credits": "/academics",
    "Backlogs": "/academics",
}
_DEFAULT_ROUTE = "/my-workspace"

#: The service requires a description of at least 10 characters, and a request
#: a counsellor has to act on deserves more than "wrong".
_MIN_DESCRIPTION = 10


class AcademicCorrectionTool(VertexTool):
    """Creates and lists Academic Correction Requests."""

    name = "correction"
    description = (
        "Raises Academic Correction Requests for institution-owned records — "
        "attendance, marks, SGPA/CGPA, credits, backlogs and enrolment details"
    )
    domain = "correction"

    def get_actions(self) -> List[ToolAction]:
        return [
            ToolAction(
                name="create_request",
                description=(
                    "Raise an Academic Correction Request for an institution-managed "
                    "record so the Academic Office can review it"
                ),
                parameters={
                    "section": "string — attendance, marks, sgpa, backlogs, …",
                    "description": "string — what is wrong, in the student's words",
                    "current_value": "string — optional, the value shown now",
                    "proposed_value": "string — optional, the value it should be",
                },
                requires_auth=True,
                owner=DataOwner.INSTITUTION,
                mutates_state=True,
            ),
            ToolAction(
                name="list_requests",
                description="List the student's own correction requests and their status",
                requires_auth=True,
                owner=DataOwner.INSTITUTION,
            ),
        ]

    async def execute(
        self, action: str, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        if action == "create_request":
            return await self._do_create_request(params, context)
        if action == "list_requests":
            return await self._do_list_requests(params, context)
        return ToolResult(success=False, error=f"Unknown correction action: {action}")

    # ------------------------------------------------------------------

    async def _do_create_request(
        self, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        section = self._resolve_section(str(params.get("section", "")))
        description = self._build_description(params, section)

        user_id = context.user_id
        if not user_id or context.db is None:
            return ToolResult(
                success=False,
                error="I couldn't reach the corrections workflow right now. Please try again shortly.",
            )

        try:
            from app.features.students.schemas import AcademicCorrectionCreate
            from app.features.students.service import StudentService

            payload = AcademicCorrectionCreate(
                section_name=section,
                current_value=self._clean(params.get("current_value")),
                proposed_value=self._clean(params.get("proposed_value")),
                description=description,
            )
            created = await StudentService(context.db).create_academic_correction_request(
                user_id, payload
            )

        except Exception as exc:
            logger.exception(
                "Correction request creation failed [%s] section=%s user=%s",
                context.request_id, section, user_id,
            )
            return ToolResult(
                success=False,
                error=(
                    f"I couldn't raise the {section} correction request — it didn't "
                    f"go through. You can also raise it from your workspace."
                ),
                data={"exception": type(exc).__name__},
            )

        route = _SECTION_ROUTES.get(section, _DEFAULT_ROUTE)
        counsellor_note = (
            f" Your counsellor, {created.counsellor_name}, has been notified."
            if created.counsellor_name
            else " It's queued for the Academic Office to assign a reviewer."
        )

        logger.info(
            "[VERTEX] correction_created request_id=%s correction_id=%s section=%s user=%s",
            context.request_id, created.id, section, user_id,
        )

        return ToolResult(
            success=True,
            is_erp_data=True,
            message=(
                f"{section} correction request submitted (reference "
                f"{str(created.id)[:8]}), status {created.status}.{counsellor_note}"
            ),
            data={
                "request_id": str(created.id),
                "reference": str(created.id)[:8],
                "section": section,
                "status": created.status,
                "counsellor_name": created.counsellor_name,
                "route": route,
            },
            ui_action={
                "type": "showToast",
                "message": f"{section} correction request submitted",
                "variant": "success",
            },
        )

    async def _do_list_requests(
        self, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        user_id = context.user_id
        if not user_id or context.db is None:
            return ToolResult(
                success=False,
                error="I couldn't load your correction requests right now.",
            )

        try:
            from app.features.students.service import StudentService

            requests = await StudentService(context.db).list_my_academic_corrections(user_id)
        except Exception:
            logger.exception("Correction list failed [%s]", context.request_id)
            return ToolResult(
                success=False,
                error="I couldn't load your correction requests just now.",
            )

        if not requests:
            return ToolResult(
                success=True,
                is_erp_data=True,
                message="You have no academic correction requests.",
                data={"count": 0, "requests": []},
            )

        return ToolResult(
            success=True,
            is_erp_data=True,
            message=f"You have {len(requests)} correction request(s).",
            data={
                "count": len(requests),
                "requests": [
                    {
                        "reference": str(r.id)[:8],
                        "section": r.section_name,
                        "status": r.status,
                        "counsellor": r.counsellor_name,
                        "submitted": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in requests[:10]
                ],
            },
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_section(raw: str) -> str:
        """Map whatever the user called it to a canonical section name."""
        key = raw.strip().lower()
        if not key:
            return "Attendance"
        if key in CORRECTION_SECTIONS:
            return CORRECTION_SECTIONS[key]
        for field, section in CORRECTION_SECTIONS.items():
            if field in key:
                return section
        return raw.strip().title()[:60]

    @staticmethod
    def _build_description(params: Dict, section: str) -> str:
        """Compose the description a counsellor will read.

        The student's own words are the body. Anything Vertex adds is clearly
        its own, so the reviewer can tell what was reported from what was
        inferred.
        """
        stated = str(params.get("description") or "").strip()
        proposed = str(params.get("proposed_value") or "").strip()

        parts: List[str] = []
        if stated:
            parts.append(f'Reported by the student: "{stated}"')
        if proposed:
            parts.append(f"Requested value: {proposed}")

        if not parts:
            parts.append(
                f"The student reports that their {section} record is incorrect."
            )
        parts.append("Raised through the Vertex assistant.")

        description = " ".join(parts)
        if len(description) < _MIN_DESCRIPTION:
            description = (
                f"{description} Please review the student's {section} record."
            )
        return description[:2000]

    @staticmethod
    def _clean(value) -> str | None:
        text = str(value).strip() if value is not None else ""
        return text[:255] or None
