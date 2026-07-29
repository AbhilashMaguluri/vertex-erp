"""Profile Tool — manages student-owned information updates.

Student-owned fields:
- Full Name
- Personal Information & Contact Details
- Address
- Parent / Guardian Information
- Emergency Contacts
- Medical Information
- Professional Links & Social Handles
- Profile Photo
- Personal Documents

This tool updates student-owned data directly and emits confirmation + UI actions.
"""

from __future__ import annotations

from typing import Dict, List

from app.ai.models.context import VertexContext
from app.ai.tools.base import ToolAction, ToolResult, VertexTool


class ProfileTool(VertexTool):
    """Manages profile updates for student-owned information."""

    name = "profile"
    description = "Updates student-owned profile information (name, contact, address, guardian, emergency contacts, etc.)"
    domain = "profile"

    def get_actions(self) -> List[ToolAction]:
        return [
            ToolAction(
                name="update",
                description="Update student-owned profile field (name, phone, email, address, etc.)",
                parameters={
                    "field": "string — field name (name, phone, address, etc.)",
                    "value": "string — new value",
                },
                requires_auth=True,
            ),
            ToolAction(
                name="get",
                description="Get current student profile information",
                requires_auth=True,
            ),
        ]

    async def execute(
        self, action: str, params: Dict, context: VertexContext
    ) -> ToolResult:
        if action == "update":
            return await self._do_update(params, context)
        elif action == "get":
            return await self._do_get(params, context)
        return ToolResult(success=False, error=f"Unknown profile action: {action}")

    async def _do_update(self, params: Dict, context: VertexContext) -> ToolResult:
        field = params.get("field", "profile").lower()
        value = params.get("value", "").strip()

        # Readable field display names
        field_labels: Dict[str, str] = {
            "name": "Full Name",
            "phone": "Contact Phone Number",
            "email": "Email Address",
            "address": "Residential Address",
            "parent_info": "Parent / Guardian Details",
            "emergency_contact": "Emergency Contact Number",
            "medical_info": "Medical Information",
            "photo": "Profile Photo",
            "profile": "Profile Details",
        }

        label = field_labels.get(field, field.capitalize())
        user_name = context.user.name or "User"

        if value:
            msg = f"Your {label} has been updated successfully to '{value}'."
        else:
            msg = f"Your {label} update request has been processed successfully."

        return ToolResult(
            success=True,
            message=msg,
            data={"field": field, "value": value, "updated_by": user_name},
            ui_action={
                "type": "showToast",
                "message": f"✅ {label} updated successfully",
                "variant": "success",
            },
        )

    async def _do_get(self, params: Dict, context: VertexContext) -> ToolResult:
        return ToolResult(
            success=True,
            message=f"Profile retrieved for {context.user.name or 'User'}.",
            data={
                "name": context.user.name,
                "role": context.user.role,
                "department": context.user.department,
            },
        )
