"""Profile Tool — writes student-owned personal information.

This tool performs the update. It does not describe how to perform it, and it
does not pretend: if the write fails, the result says so and the user is told
the truth.

Every field it accepts is student-owned. It routes through
``StudentProfileService``, the same service the Personal Details screen uses,
so Vertex and the UI share one validation path, one allow-list and one audit
trail. Institution-owned fields are not reachable from here at all — those go
through the Academic Correction workflow.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

from app.ai.models.ownership import DataOwner
from app.ai.tools.base import ToolAction, ToolExecutionContext, ToolResult, VertexTool

logger = logging.getLogger("vertex.tools.profile")


# canonical field → (service method, schema class name, payload builder key)
_FIELD_ROUTING: Dict[str, Tuple[str, str, str]] = {
    "name": ("update_personal", "PersonalInfoUpdate", "name"),
    "first_name": ("update_personal", "PersonalInfoUpdate", "first_name"),
    "last_name": ("update_personal", "PersonalInfoUpdate", "last_name"),
    "preferred_name": ("update_personal", "PersonalInfoUpdate", "preferred_name"),
    "date_of_birth": ("update_personal", "PersonalInfoUpdate", "date_of_birth"),
    "gender": ("update_personal", "PersonalInfoUpdate", "gender"),
    "blood_group": ("update_personal", "PersonalInfoUpdate", "blood_group"),
    "nationality": ("update_personal", "PersonalInfoUpdate", "nationality"),
    "religion": ("update_personal", "PersonalInfoUpdate", "religion"),
    "mother_tongue": ("update_personal", "PersonalInfoUpdate", "mother_tongue"),

    "phone": ("update_contact", "ContactInfoUpdate", "mobile_number"),
    "mobile_number": ("update_contact", "ContactInfoUpdate", "mobile_number"),
    "alternate_phone": ("update_contact", "ContactInfoUpdate", "alternate_phone"),
    "email": ("update_contact", "ContactInfoUpdate", "personal_email"),
    "personal_email": ("update_contact", "ContactInfoUpdate", "personal_email"),
    "address": ("update_contact", "ContactInfoUpdate", "current_address"),
    "current_address": ("update_contact", "ContactInfoUpdate", "current_address"),
    "permanent_address": ("update_contact", "ContactInfoUpdate", "permanent_address"),
    "city": ("update_contact", "ContactInfoUpdate", "city"),
    "district": ("update_contact", "ContactInfoUpdate", "district"),
    "state": ("update_contact", "ContactInfoUpdate", "state"),
    "pin_code": ("update_contact", "ContactInfoUpdate", "pin_code"),
    "emergency_contact": ("update_contact", "ContactInfoUpdate", "emergency_contact_phone"),
    "emergency_contact_name": ("update_contact", "ContactInfoUpdate", "emergency_contact_name"),
    "emergency_contact_phone": ("update_contact", "ContactInfoUpdate", "emergency_contact_phone"),
    "emergency_contact_relation": ("update_contact", "ContactInfoUpdate", "emergency_contact_relation"),

    "parent_info": ("update_family", "FamilyInfoUpdate", "guardian_name"),
    "father_name": ("update_family", "FamilyInfoUpdate", "father_name"),
    "father_phone": ("update_family", "FamilyInfoUpdate", "father_phone"),
    "father_occupation": ("update_family", "FamilyInfoUpdate", "father_occupation"),
    "mother_name": ("update_family", "FamilyInfoUpdate", "mother_name"),
    "mother_phone": ("update_family", "FamilyInfoUpdate", "mother_phone"),
    "mother_occupation": ("update_family", "FamilyInfoUpdate", "mother_occupation"),
    "guardian_name": ("update_family", "FamilyInfoUpdate", "guardian_name"),
    "guardian_phone": ("update_family", "FamilyInfoUpdate", "guardian_phone"),
    "guardian_relation": ("update_family", "FamilyInfoUpdate", "guardian_relation"),

    "medical_info": ("update_health", "HealthInfoUpdate", "health_notes"),
    "medical_conditions": ("update_health", "HealthInfoUpdate", "medical_conditions"),
    "allergies": ("update_health", "HealthInfoUpdate", "allergies"),

    "linkedin_url": ("update_skills_goals", "SkillsGoalsUpdate", "linkedin_url"),
    "github_url": ("update_skills_goals", "SkillsGoalsUpdate", "github_url"),
    "portfolio_url": ("update_skills_goals", "SkillsGoalsUpdate", "portfolio_url"),
    "career_goal": ("update_skills_goals", "SkillsGoalsUpdate", "career_goal"),
}

_FIELD_LABELS: Dict[str, str] = {
    "name": "full name",
    "phone": "mobile number",
    "email": "personal email address",
    "address": "current address",
    "emergency_contact": "emergency contact number",
    "parent_info": "guardian details",
    "medical_info": "health notes",
    "date_of_birth": "date of birth",
    "blood_group": "blood group",
    "pin_code": "PIN code",
}

# Fields Vertex will not set from a chat sentence. A photo needs a file and a
# date needs an unambiguous format; both belong on the profile screen.
_REQUIRES_UI: Dict[str, str] = {
    "photo": "/my-profile",
}


def label_for(field: str) -> str:
    return _FIELD_LABELS.get(field, field.replace("_", " "))


def split_name(value: str) -> Tuple[str, Optional[str]]:
    """Split a spoken full name into first and last.

    A single word is a first name with no surname to set — writing an empty
    string into last_name would erase a surname the student never mentioned.
    """
    parts = [p for p in re.split(r"\s+", value.strip()) if p]
    if not parts:
        return "", None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], " ".join(parts[1:])


class ProfileTool(VertexTool):
    """Reads and writes the student's own personal profile."""

    name = "profile"
    description = (
        "Reads and updates student-owned personal information — name, contact "
        "details, address, guardian details, emergency contacts and health notes"
    )
    domain = "profile"

    def get_actions(self) -> List[ToolAction]:
        return [
            ToolAction(
                name="update",
                description=(
                    "Update a student-owned profile field (name, phone, email, "
                    "address, guardian, emergency contact, health notes)"
                ),
                parameters={
                    "field": "string — canonical field name",
                    "value": "string — the new value",
                },
                requires_auth=True,
                required_permissions=["profile.self.manage"],
                owner=DataOwner.STUDENT,
                mutates_state=True,
            ),
            ToolAction(
                name="get",
                description="Read the student's own profile details",
                requires_auth=True,
                required_permissions=["profile.self.manage"],
                owner=DataOwner.STUDENT,
            ),
        ]

    async def execute(
        self, action: str, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        if action == "update":
            return await self._do_update(params, context)
        if action == "get":
            return await self._do_get(params, context)
        return ToolResult(success=False, error=f"Unknown profile action: {action}")

    # ------------------------------------------------------------------

    async def _do_update(
        self, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        field = str(params.get("field", "")).strip().lower()
        value = str(params.get("value", "")).strip()

        if field in _REQUIRES_UI:
            return ToolResult(
                success=False,
                error=(
                    f"Updating your {label_for(field)} needs the profile screen — "
                    f"I can take you there if you'd like."
                ),
                data={"requires_ui": _REQUIRES_UI[field]},
            )

        routing = _FIELD_ROUTING.get(field)
        if routing is None:
            return ToolResult(
                success=False,
                error=(
                    f"'{field or 'that field'}' isn't something I can change on your "
                    f"profile. I can update your name, phone, email, address, "
                    f"guardian details, emergency contact or health notes."
                ),
            )

        if not value:
            return ToolResult(
                success=False,
                error=f"I need the new {label_for(field)} to make that change.",
            )

        student_id = context.student_id
        if not student_id:
            return ToolResult(
                success=False,
                error="I couldn't find a student record linked to your account.",
            )
        if context.db is None:
            return ToolResult(
                success=False,
                error="I can't reach your profile records right now. Please try again shortly.",
            )

        method_name, schema_name, payload_key = routing
        payload = self._build_payload(field, payload_key, value)

        try:
            from app.features.students import profile_schemas
            from app.features.students.profile_service import StudentProfileService

            schema_cls = getattr(profile_schemas, schema_name)
            data = schema_cls(**payload)

            service = StudentProfileService(context.db)
            await getattr(service, method_name)(student_id, data)

        except ValueError as exc:
            # Pydantic validation — the value itself was rejected.
            return ToolResult(
                success=False,
                error=(
                    f"'{value}' isn't a valid {label_for(field)}: "
                    f"{self._first_validation_message(exc)}"
                ),
            )
        except Exception as exc:
            logger.exception(
                "Profile update failed [%s] field=%s student=%s",
                context.request_id, field, student_id,
            )
            return ToolResult(
                success=False,
                error=(
                    f"I couldn't save your {label_for(field)} — the update didn't "
                    f"go through. Please try again in a moment."
                ),
                data={"exception": type(exc).__name__},
            )

        logger.info(
            "[VERTEX] profile_updated request_id=%s student=%s field=%s",
            context.request_id, student_id, field,
        )

        return ToolResult(
            success=True,
            message=f"Your {label_for(field)} is now {value}.",
            data={"field": field, "value": value, "student_id": student_id},
            ui_action={
                "type": "showToast",
                "message": f"{label_for(field).capitalize()} updated",
                "variant": "success",
            },
        )

    async def _do_get(
        self, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        student_id = context.student_id
        if not student_id or context.db is None:
            return ToolResult(
                success=False,
                error="I couldn't find a student record linked to your account.",
            )

        try:
            from app.features.students.profile_service import StudentProfileService

            profile = await StudentProfileService(context.db).get_self_profile(student_id)
        except Exception:
            logger.exception("Profile read failed [%s]", context.request_id)
            return ToolResult(
                success=False,
                error="I couldn't load your profile just now. Please try again shortly.",
            )

        identity = profile.identity
        return ToolResult(
            success=True,
            is_erp_data=True,
            message="Profile loaded.",
            data={
                "full_name": identity.full_name,
                "roll_number": identity.roll_number,
                "department": identity.department_name,
                "semester": identity.semester_name,
                "mobile_number": profile.mobile_number,
                "personal_email": profile.personal_email,
                "current_address": profile.current_address,
                "emergency_contact_name": profile.emergency_contact_name,
                "emergency_contact_phone": profile.emergency_contact_phone,
                "completion_percentage": profile.completion.percentage
                if profile.completion else None,
            },
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _build_payload(field: str, payload_key: str, value: str) -> Dict:
        if field == "name":
            first, last = split_name(value)
            payload = {"first_name": first}
            if last:
                payload["last_name"] = last
            return payload
        return {payload_key: value}

    @staticmethod
    def _first_validation_message(exc: Exception) -> str:
        """Pull the human-readable half out of a pydantic error.

        Raw ValidationError text names the schema and line numbers, which means
        nothing to a student being told their phone number was rejected.
        """
        errors = getattr(exc, "errors", None)
        if callable(errors):
            try:
                first = exc.errors()[0]
                message = str(first.get("msg", "")).replace("Value error, ", "")
                if message:
                    return message
            except (IndexError, KeyError, TypeError):
                pass
        text = str(exc).split("\n")[-1].strip()
        return text[:160] or "it wasn't in a format I could accept"
