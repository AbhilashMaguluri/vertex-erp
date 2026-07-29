"""Planner — decides execution strategy based on Data Ownership & Decision Engine rules.

Decision Engine Evaluation Flow:
  1. What is the user's intent?
  2. Which data/feature is being requested?
  3. Who owns this data?
     - Student-Owned Data (Name, Phone, Address, Guardian, Emergency Contacts, etc.)
     - Institution-Owned Data (Attendance, SGPA, CGPA, Marks, Grades, Backlogs, etc.)
  4. Does a tool exist for this action?
  5. Does the user have permission?
  6. Execute action / Launch workflow automatically!

The Planner queries the ToolRegistry — never hardcoding tool names.
"""

from __future__ import annotations

import logging

from app.ai.models.context import VertexContext
from app.ai.models.intent import DetectedIntent, IntentCategory
from app.ai.models.plan import ExecutionPlan, PlanAction
from app.ai.tools.base import ToolRegistry

logger = logging.getLogger(__name__)


class Planner:
    """Decides execution strategy using the Data Ownership Decision Engine."""

    async def plan(
        self,
        intent: DetectedIntent,
        context: VertexContext,
        registry: ToolRegistry,
    ) -> ExecutionPlan:
        category = intent.category

        # ----- 1. Student-Owned Profile Data Modification -----
        if category == IntentCategory.UPDATE_PROFILE:
            profile_tools = registry.find_by_domain("profile")
            if profile_tools and profile_tools[0].supports_action("update"):
                field = intent.entities.get("field", "profile")
                val = intent.entities.get("value", "")
                return ExecutionPlan(
                    action=PlanAction.EXECUTE_TOOL,
                    intent=intent,
                    tool_name=profile_tools[0].name,
                    tool_action="update",
                    tool_params={"field": field, "value": val},
                )

        # ----- 2. Institution-Owned Data Academic Correction Workflow -----
        if category == IntentCategory.ACADEMIC_CORRECTION:
            correction_tools = registry.find_by_domain("correction")
            if correction_tools and correction_tools[0].supports_action("create_request"):
                section = intent.entities.get("section", "attendance")
                return ExecutionPlan(
                    action=PlanAction.EXECUTE_TOOL,
                    intent=intent,
                    tool_name=correction_tools[0].name,
                    tool_action="create_request",
                    tool_params={"section": section},
                )

        # ----- 3. Navigation → ui.navigate -----
        if category == IntentCategory.NAVIGATION:
            page = intent.entities.get("page", "")
            ui_tools = registry.find_by_domain("ui")
            if ui_tools and ui_tools[0].supports_action("navigate"):
                return ExecutionPlan(
                    action=PlanAction.EXECUTE_TOOL,
                    intent=intent,
                    tool_name=ui_tools[0].name,
                    tool_action="navigate",
                    tool_params={"page": page},
                )
            return ExecutionPlan(action=PlanAction.RESPOND, intent=intent)

        # ----- 4. UI Actions (theme, toast, dialog) -----
        if category == IntentCategory.UI_ACTION:
            action = intent.entities.get("action", "")
            params = {k: v for k, v in intent.entities.items() if k != "action"}
            ui_tools = registry.find_by_domain("ui")
            if ui_tools and ui_tools[0].supports_action(action):
                return ExecutionPlan(
                    action=PlanAction.EXECUTE_TOOL,
                    intent=intent,
                    tool_name=ui_tools[0].name,
                    tool_action=action,
                    tool_params=params,
                )
            return ExecutionPlan(action=PlanAction.RESPOND, intent=intent)

        # ----- 5. Workflows (logout, etc.) -----
        if category == IntentCategory.WORKFLOW:
            workflow = intent.entities.get("workflow", "")
            if workflow == "logout":
                ui_tools = registry.find_by_domain("ui")
                if ui_tools and ui_tools[0].supports_action("logout"):
                    return ExecutionPlan(
                        action=PlanAction.EXECUTE_TOOL,
                        intent=intent,
                        tool_name=ui_tools[0].name,
                        tool_action="logout",
                        tool_params={},
                    )
            return ExecutionPlan(action=PlanAction.RESPOND, intent=intent)

        # ----- 6. Data retrieval -----
        if category == IntentCategory.DATA_RETRIEVAL:
            data_tools = registry.find_by_domain("student") + registry.find_by_domain("attendance")
            if data_tools:
                return ExecutionPlan(
                    action=PlanAction.EXECUTE_TOOL,
                    intent=intent,
                    tool_name=data_tools[0].name,
                    tool_action="get",
                    tool_params=intent.entities,
                )
            return ExecutionPlan(action=PlanAction.RESPOND, intent=intent)

        # ----- 7. Report generation -----
        if category == IntentCategory.REPORT_GENERATION:
            report_tools = registry.find_by_domain("report")
            if report_tools:
                return ExecutionPlan(
                    action=PlanAction.EXECUTE_TOOL,
                    intent=intent,
                    tool_name=report_tools[0].name,
                    tool_action="generate",
                    tool_params=intent.entities,
                )
            return ExecutionPlan(action=PlanAction.RESPOND, intent=intent)

        # ----- 8. Conversation / Fallback -----
        return ExecutionPlan(action=PlanAction.RESPOND, intent=intent)
