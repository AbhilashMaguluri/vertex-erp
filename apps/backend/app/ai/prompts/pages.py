"""Page-context prompt fragments.

When the user is on a specific ERP page, a short contextual prompt is added
to the chain so Vertex automatically knows *where* the user is and what
entities are in view — the user never has to type IDs or explain context.
"""

from app.ai.models.context import PageContext

# Template strings may contain ``{student_id}`` or other PageContext fields.
PAGE_PROMPTS: dict[str, str] = {
    "dashboard": (
        "## Page Context: Dashboard\n"
        "The user is on the main Dashboard and can see overview statistics, "
        "recent activity, and quick-access cards."
    ),
    "student-profile": (
        "## Page Context: Student Profile\n"
        "The user is viewing a specific student's 360° profile.  "
        "Student ID: **{student_id}**.  If the user says \"this student\" or "
        "\"summarize\", they mean this student."
    ),
    "attendance": (
        "## Page Context: Attendance\n"
        "The user is on the Attendance page where attendance is recorded or "
        "reviewed."
    ),
    "counselling": (
        "## Page Context: Counselling\n"
        "The user is on the Counselling sessions page where sessions are "
        "logged and managed."
    ),
    "reports": (
        "## Page Context: Reports\n"
        "The user is on the Reports page and may want to generate, download, "
        "or understand reports."
    ),
    "reach-out": (
        "## Page Context: Reach Out Hub\n"
        "The user is on the Reach Out (Student Relationship Management) page."
    ),
    "settings": (
        "## Page Context: Settings\n"
        "The user is on the Settings page for personal or system preferences."
    ),
    "admin-users": (
        "## Page Context: User Management\n"
        "The user is on the Admin → User Management page."
    ),
    "admin-imports": (
        "## Page Context: Data Imports\n"
        "The user is on the Admin → Import page for bulk data uploads."
    ),
    "login": (
        "## Page Context: Login\n"
        "The user is on the login page.  Help with credentials and access."
    ),
    "my-workspace": (
        "## Page Context: My Workspace (Student)\n"
        "The student is on their personal workspace viewing their own data."
    ),
    "academics": (
        "## Page Context: Academics / Marks Entry\n"
        "The user is on the Academics page for marks entry or review."
    ),
}


def get_page_prompt(page_ctx: PageContext) -> str:
    """Return the page-context prompt, with template variables filled in."""
    template = PAGE_PROMPTS.get(page_ctx.page, "")
    if not template:
        return ""

    # Fill template placeholders from the PageContext fields
    try:
        return template.format(
            student_id=page_ctx.student_id or "unknown",
            **page_ctx.params,
        )
    except KeyError:
        # If a template references a param we don't have, return as-is.
        return template
