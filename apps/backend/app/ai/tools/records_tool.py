"""Record tools — real ERP data, read through the feature services.

These exist so Vertex can answer "what's my attendance?" with the actual
figure instead of prose about where to find it. Every number in the response
comes back through ``ToolResult.data`` with ``is_erp_data=True``, which is what
lets the output guardrail tell a real figure from an invented one: anything
numeric the model states that did not come through here is treated as
fabricated and blocked.

Each tool reads through the same service the corresponding screen uses, so
scoping, permissions and derivation rules stay in one place.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.ai.models.ownership import DataOwner
from app.ai.tools.base import ToolAction, ToolExecutionContext, ToolResult, VertexTool

logger = logging.getLogger("vertex.tools.records")

#: Institutional minimum. Matches the threshold the attendance screens use.
_ATTENDANCE_THRESHOLD = 75.0


def _no_record(what: str) -> ToolResult:
    return ToolResult(
        success=True,
        is_erp_data=True,
        message=(
            f"There are no {what} recorded for you yet. Once the office publishes "
            f"them they'll appear here."
        ),
        data={"empty": True},
    )


class AttendanceTool(VertexTool):
    """Reads attendance figures from the attendance module."""

    name = "attendance"
    description = "Reads real attendance percentages, subject breakdowns and monthly trends"
    domain = "attendance"

    def get_actions(self) -> List[ToolAction]:
        return [
            ToolAction(
                name="get_summary",
                description="Read the attendance summary for the student in context",
                parameters={"student_id": "string — optional, defaults to the caller"},
                requires_auth=True,
                required_permissions=["attendance.read"],
                owner=DataOwner.INSTITUTION,
            ),
        ]

    async def execute(
        self, action: str, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        if action != "get_summary":
            return ToolResult(success=False, error=f"Unknown attendance action: {action}")

        student_id = _resolve_student(params, context)
        if not student_id:
            return ToolResult(
                success=False,
                error="I need to know which student you mean — open their workspace and ask again.",
            )
        if context.db is None:
            return ToolResult(
                success=False, error="I can't reach attendance records right now."
            )

        try:
            from app.features.attendance.service import AttendanceService

            summary = await AttendanceService(context.db).get_student_attendance_summary(
                student_id
            )
        except Exception:
            logger.exception("Attendance read failed [%s]", context.request_id)
            return ToolResult(
                success=False,
                error="I couldn't load the attendance records just now. Please try again shortly.",
            )

        if summary.overall_percentage is None:
            return _no_record("attendance records")

        overall = summary.overall_percentage
        subjects = [
            {
                "subject": s.subject_name,
                "code": s.subject_code,
                "percentage": s.percentage,
                "attended": s.attended_classes,
                "total": s.total_classes,
            }
            for s in summary.subject_summaries
        ]
        below = [s for s in subjects if s["percentage"] < _ATTENDANCE_THRESHOLD]

        return ToolResult(
            success=True,
            is_erp_data=True,
            message=(
                f"Overall attendance is {overall}% "
                f"({summary.attended_classes} of {summary.total_classes} classes)."
            ),
            data={
                "overall_percentage": overall,
                "attended_classes": summary.attended_classes,
                "total_classes": summary.total_classes,
                "threshold": _ATTENDANCE_THRESHOLD,
                "meets_threshold": overall >= _ATTENDANCE_THRESHOLD,
                "subjects": subjects,
                "subjects_below_threshold": below,
            },
        )


class AcademicsTool(VertexTool):
    """Reads marks, SGPA/CGPA and backlogs from the academics module."""

    name = "academics"
    description = "Reads real marks, SGPA, CGPA, credits and backlog records"
    domain = "academics"

    def get_actions(self) -> List[ToolAction]:
        return [
            ToolAction(
                name="get_record",
                description="Read the academic record (marks, SGPA, CGPA, backlogs)",
                parameters={"student_id": "string — optional, defaults to the caller"},
                requires_auth=True,
                required_permissions=["academics.read"],
                owner=DataOwner.INSTITUTION,
            ),
        ]

    async def execute(
        self, action: str, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        if action != "get_record":
            return ToolResult(success=False, error=f"Unknown academics action: {action}")

        student_id = _resolve_student(params, context)
        if not student_id:
            return ToolResult(
                success=False,
                error="I need to know which student you mean — open their workspace and ask again.",
            )
        if context.db is None:
            return ToolResult(
                success=False, error="I can't reach academic records right now."
            )

        try:
            from app.features.academics.service import AcademicsService

            record = await AcademicsService(context.db).get_student_academic_record(
                student_id
            )
        except Exception:
            logger.exception("Academic record read failed [%s]", context.request_id)
            return ToolResult(
                success=False,
                error="I couldn't load the academic records just now. Please try again shortly.",
            )

        if not record.semesters:
            return _no_record("marks or results")

        latest = record.semesters[-1]
        return ToolResult(
            success=True,
            is_erp_data=True,
            message=(
                f"Latest semester {latest.semester_name}: "
                f"SGPA {latest.sgpa if latest.sgpa is not None else 'not published'}, "
                f"CGPA {record.cgpa if record.cgpa is not None else 'not published'}, "
                f"{record.total_active_backlogs} active backlog(s)."
            ),
            data={
                "cgpa": record.cgpa,
                "latest_sgpa": record.latest_sgpa,
                "active_backlogs": record.total_active_backlogs,
                "latest_semester": latest.semester_name,
                "semesters": [
                    {
                        "semester": block.semester_name,
                        "sgpa": block.sgpa,
                        "cgpa": block.cgpa,
                        "credits": block.total_credits,
                        "active_backlogs": block.active_backlogs,
                        "subjects": [
                            {
                                "code": row.subject_code,
                                "name": row.subject_name,
                                "percentage": row.percentage,
                                "grade": row.grade,
                                "result": row.result,
                            }
                            for row in block.subjects
                        ],
                    }
                    for block in record.semesters
                ],
            },
        )


class DirectoryTool(VertexTool):
    """Finds students, scoped by whatever the caller may already see."""

    name = "directory"
    description = "Searches the student directory by name or roll number"
    domain = "directory"

    def get_actions(self) -> List[ToolAction]:
        return [
            ToolAction(
                name="search_students",
                description="Find students by name or roll number",
                parameters={"query": "string — name or roll number"},
                requires_auth=True,
                required_permissions=["student.caseload.read"],
                owner=DataOwner.INSTITUTION,
            ),
        ]

    async def execute(
        self, action: str, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        if action != "search_students":
            return ToolResult(success=False, error=f"Unknown directory action: {action}")

        query = _extract_query(params)
        if len(query) < 2:
            return ToolResult(
                success=False,
                error="Tell me the student's name or roll number and I'll look them up.",
            )
        if context.db is None or context.auth_user is None:
            return ToolResult(
                success=False, error="I can't reach the student directory right now."
            )

        try:
            from app.features.search.service import SearchService

            # SearchService scopes results by the caller's own permissions and
            # caseload assignments — the same scoping the global search bar
            # gets, rather than a second implementation that could drift.
            results = await SearchService(context.db).search(query, context.auth_user)
        except Exception:
            logger.exception("Directory search failed [%s]", context.request_id)
            return ToolResult(
                success=False,
                error="I couldn't search the directory just now. Please try again shortly.",
            )

        students = [r for r in results if r.type == "student"]
        if not students:
            return ToolResult(
                success=True,
                is_erp_data=True,
                message=f"No students matched '{query}'.",
                data={"query": query, "count": 0, "students": []},
            )

        return ToolResult(
            success=True,
            is_erp_data=True,
            message=f"Found {len(students)} student(s) matching '{query}'.",
            data={
                "query": query,
                "count": len(students),
                "students": [
                    {"name": s.title, "detail": s.subtitle, "url": s.url}
                    for s in students
                ],
            },
        )


# --------------------------------------------------------------------------


def _resolve_student(params: Dict, context: ToolExecutionContext) -> Optional[str]:
    """Whose record to read.

    An explicit id is honoured only when the workspace already resolved to it,
    which ContextBuilder does only after checking access. That keeps a
    parameter from becoming a way to address arbitrary students.
    """
    requested = str(params.get("student_id") or "").strip()
    if requested and requested == context.vertex.workspace.student_id:
        return requested
    return context.student_id


def _extract_query(params: Dict) -> str:
    for key in ("query", "name", "raw_message"):
        value = str(params.get(key) or "").strip()
        if value:
            if key == "raw_message":
                return _strip_search_phrasing(value)
            return value[:80]
    return ""


def _strip_search_phrasing(message: str) -> str:
    """Reduce "find the student named Ravi Kumar" to "Ravi Kumar"."""
    import re

    cleaned = re.sub(
        r"\b(?:find|search\s+for|look\s+up|locate|show\s+me|get|the|a|an|"
        r"student|students|named|called|with|roll\s*(?:number|no)|please)\b",
        " ",
        message,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", cleaned).strip(" ?.!,")[:80]
