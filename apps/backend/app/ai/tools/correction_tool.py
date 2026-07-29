"""Academic Correction Tool — manages institution-owned data correction workflows.

Institution-owned data:
- Attendance
- Marks & Subject Grades
- SGPA / CGPA / Credits
- Backlogs & Semester
- Department & Admission Details

Institution records cannot be edited directly by students. This tool automatically
initiates an Academic Correction Request workflow and guides the user.
"""

from __future__ import annotations

from typing import Dict, List

from app.ai.models.context import VertexContext
from app.ai.tools.base import ToolAction, ToolResult, VertexTool


class AcademicCorrectionTool(VertexTool):
    """Initiates Academic Correction Request workflows for institution-owned records."""

    name = "correction"
    description = "Initiates academic correction request workflows for attendance, marks, SGPA, grades, or backlogs."
    domain = "correction"

    def get_actions(self) -> List[ToolAction]:
        return [
            ToolAction(
                name="create_request",
                description="Raise an Academic Correction Request for institution-managed records (attendance, marks, SGPA, grades)",
                parameters={
                    "section": "string — section (attendance, marks, sgpa, grades, backlogs)",
                },
                requires_auth=True,
            ),
        ]

    async def execute(
        self, action: str, params: Dict, context: VertexContext
    ) -> ToolResult:
        if action == "create_request":
            return await self._do_create_request(params, context)
        return ToolResult(
            success=False, error=f"Unknown correction action: {action}"
        )

    async def _do_create_request(
        self, params: Dict, context: VertexContext
    ) -> ToolResult:
        section = params.get("section", "attendance").lower()

        section_names: Dict[str, str] = {
            "attendance": "Attendance",
            "marks": "Subject Marks & Grades",
            "sgpa": "SGPA / CGPA Calculation",
            "grades": "Semester Grades",
            "backlogs": "Backlog Records",
            "institution_data": "Academic Records",
        }

        display_name = section_names.get(section, section.capitalize())

        # Route target
        route_map: Dict[str, str] = {
            "attendance": "/attendance",
            "marks": "/academics",
            "sgpa": "/academics",
            "grades": "/academics",
            "backlogs": "/academics",
        }
        target_route = route_map.get(section, "/attendance")

        msg = (
            f"Your {display_name} records are managed by the Academic Office. "
            f"I have automatically initiated an Academic Correction Request for your {display_name}. "
            f"You have been redirected to the workflow page where you can attach supporting documents if needed."
        )

        return ToolResult(
            success=True,
            message=msg,
            data={
                "section": display_name,
                "workflow": "Academic Correction Request",
                "status": "INITIATED",
                "user": context.user.name,
            },
            ui_action={
                "type": "navigate",
                "route": target_route,
                "workflow": "academic_correction",
                "message": f"Academic Correction Request initiated for {display_name}",
            },
        )
