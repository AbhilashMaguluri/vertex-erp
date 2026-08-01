"""Data ownership model.

Vertex never refuses a change request before asking *who owns the data*.
That single question decides between two very different outcomes:

    Student-owned      →  execute the Profile Tool, change it now
    Institution-owned  →  launch the Academic Correction workflow
    Application-owned  →  execute a UI tool (theme, navigation, session)

A refusal is only correct when the answer is FOREIGN (someone else's record)
or when no route exists at all.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DataOwner(str, Enum):
    STUDENT = "student"              # The requesting student owns it outright
    INSTITUTION = "institution"      # Academic office owns it; corrections only
    APPLICATION = "application"      # UI/session state, owned by the app
    FOREIGN = "foreign"              # Another user's record
    NONE = "none"                    # No ERP resource involved


class OwnershipRoute(str, Enum):
    """What the owner implies the Planner should do."""

    DIRECT_UPDATE = "direct_update"
    CORRECTION_WORKFLOW = "correction_workflow"
    UI_EXECUTION = "ui_execution"
    STAFF_UPDATE = "staff_update"        # Staff editing an institution record
    DENY = "deny"
    NOT_APPLICABLE = "not_applicable"


class OwnershipDecision(BaseModel):
    """Result of resolving ownership for a goal."""

    owner: DataOwner = DataOwner.NONE
    route: OwnershipRoute = OwnershipRoute.NOT_APPLICABLE
    resource: str = ""
    reason: str = ""

    # Fields the decision covers, for logging and evaluation.
    fields: List[str] = Field(default_factory=list)

    # Populated when route is DENY.
    denial_message: Optional[str] = None

    @property
    def is_denied(self) -> bool:
        return self.route == OwnershipRoute.DENY


# --------------------------------------------------------------------------
# The ownership catalogue — the single source of truth for who owns what.
# Mirrors STUDENT_WRITABLE_STUDENT_COLUMNS and the student profile schemas in
# app/features/students/.
# --------------------------------------------------------------------------

STUDENT_OWNED_FIELDS: set[str] = {
    "name",
    "first_name",
    "last_name",
    "preferred_name",
    "date_of_birth",
    "gender",
    "blood_group",
    "nationality",
    "religion",
    "mother_tongue",
    "languages_known",
    "phone",
    "mobile_number",
    "alternate_phone",
    "personal_email",
    "address",
    "current_address",
    "permanent_address",
    "city",
    "district",
    "state",
    "pin_code",
    "emergency_contact",
    "emergency_contact_name",
    "emergency_contact_phone",
    "emergency_contact_relation",
    "parent_info",
    "father_name",
    "father_phone",
    "father_occupation",
    "mother_name",
    "mother_phone",
    "mother_occupation",
    "guardian_name",
    "guardian_phone",
    "guardian_relation",
    "medical_info",
    "allergies",
    "medical_conditions",
    "photo",
    "photo_url",
    "linkedin_url",
    "github_url",
    "portfolio_url",
    "career_goal",
    "technical_skills",
}

INSTITUTION_OWNED_FIELDS: set[str] = {
    "attendance",
    "marks",
    "grade",
    "grades",
    "sgpa",
    "cgpa",
    "credits",
    "backlog",
    "backlogs",
    "semester",
    "department",
    "branch",
    "section",
    "roll_number",
    "registration_number",
    "admission_number",
    "admission_type",
    "batch_year",
    "academic_year",
    "college_email",
    "risk_level",
    "counsellor",
}

# Section label used when opening an Academic Correction Request, keyed by the
# field the user complained about. Matches AcademicCorrectionCreate.section_name.
CORRECTION_SECTIONS: dict[str, str] = {
    "attendance": "Attendance",
    "marks": "Marks & Grades",
    "grade": "Marks & Grades",
    "grades": "Marks & Grades",
    "sgpa": "SGPA / CGPA",
    "cgpa": "SGPA / CGPA",
    "credits": "Credits",
    "backlog": "Backlogs",
    "backlogs": "Backlogs",
    "semester": "Semester",
    "department": "Department",
    "branch": "Department",
    "section": "Section",
    "roll_number": "Roll Number",
    "registration_number": "Registration Number",
    "admission_number": "Admission Details",
    "admission_type": "Admission Details",
    "batch_year": "Batch Year",
    "academic_year": "Academic Year",
    "college_email": "College Email",
}
