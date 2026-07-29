"""UI Tool — controls VertexERP frontend actions.

Actions: navigate, setTheme, showToast, logout, openDialog, closeDialog

This tool does NOT call backend APIs. It returns ui_action dicts that the
frontend executes. The LLM never directly manipulates the application.
"""

from __future__ import annotations

import re
from typing import Dict, List

from app.ai.models.context import VertexContext
from app.ai.tools.base import ToolAction, ToolResult, VertexTool


# Page name → route mapping
PAGE_ROUTES: Dict[str, str] = {
    "dashboard": "/dashboard",
    "home": "/dashboard",
    "attendance": "/attendance",
    "counselling": "/counselling",
    "counseling": "/counselling",
    "academics": "/academics",
    "marks": "/academics",
    "reports": "/reports",
    "report": "/reports",
    "reach out": "/reach-out",
    "reach-out": "/reach-out",
    "reachout": "/reach-out",
    "notifications": "/notifications",
    "settings": "/settings",
    "my workspace": "/my-workspace",
    "my-workspace": "/my-workspace",
    "workspace": "/my-workspace",
    "my profile": "/my-profile",
    "my-profile": "/my-profile",
    "profile": "/my-profile",
    "students": "/students",
    "student": "/students",
    "admin": "/admin",
    "users": "/admin/users",
    "user management": "/admin/users",
    "imports": "/admin/imports",
    "data imports": "/admin/imports",
    "audit": "/admin/audit-logs",
    "audit logs": "/admin/audit-logs",
    "academic config": "/admin/academic-config",
    "parent communication": "/parent-communication",
    "parents": "/parent-communication",
    "login": "/login",
}

VALID_THEMES = {"light", "dark", "system"}


def resolve_page_route(page: str) -> str | None:
    """Resolve a natural language page name to a route path."""
    normalized = page.strip().lower()
    # Direct match
    if normalized in PAGE_ROUTES:
        return PAGE_ROUTES[normalized]
    # Fuzzy: try partial matching
    for key, route in PAGE_ROUTES.items():
        if normalized in key or key in normalized:
            return route
    # If it already looks like a route path, use it directly
    if normalized.startswith("/"):
        return normalized
    return None


class UITool(VertexTool):
    """Controls VertexERP user interface actions."""

    name = "ui"
    description = "Controls VertexERP user interface — navigation, theme, toasts, logout, dialogs"
    domain = "ui"

    def get_actions(self) -> List[ToolAction]:
        return [
            ToolAction(
                name="navigate",
                description="Navigate to a page in VertexERP",
                parameters={"page": "string — page name or route path"},
            ),
            ToolAction(
                name="setTheme",
                description="Change the UI theme (light, dark, or system)",
                parameters={"mode": "string — light | dark | system"},
            ),
            ToolAction(
                name="showToast",
                description="Show a notification toast",
                parameters={
                    "message": "string — toast message",
                    "variant": "string — success | error | info | warning",
                },
            ),
            ToolAction(
                name="logout",
                description="Log the user out of VertexERP",
            ),
            ToolAction(
                name="openDialog",
                description="Open a dialog/modal",
                parameters={"dialog": "string — dialog identifier"},
            ),
            ToolAction(
                name="closeDialog",
                description="Close the currently open dialog",
            ),
        ]

    async def execute(
        self, action: str, params: Dict, context: VertexContext
    ) -> ToolResult:
        handler = getattr(self, f"_do_{action}", None)
        if handler is None:
            return ToolResult(
                success=False,
                error=f"Unknown UI action: {action}",
            )
        return await handler(params, context)

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    async def _do_navigate(self, params: Dict, context: VertexContext) -> ToolResult:
        page = params.get("page", "")
        if not page:
            return ToolResult(success=False, error="No page specified for navigation.")

        route = resolve_page_route(page)
        if not route:
            return ToolResult(
                success=False,
                error=f"Unknown page: '{page}'. I couldn't find a matching page in VertexERP.",
            )

        # Build a friendly name for the confirmation message
        display_name = page.strip().title()

        return ToolResult(
            success=True,
            message=f"Navigated to {display_name}.",
            ui_action={"type": "navigate", "route": route},
        )

    async def _do_setTheme(self, params: Dict, context: VertexContext) -> ToolResult:
        mode = params.get("mode", "").strip().lower()
        if mode not in VALID_THEMES:
            return ToolResult(
                success=False,
                error=f"Invalid theme: '{mode}'. Use light, dark, or system.",
            )
        display = mode.capitalize()
        return ToolResult(
            success=True,
            message=f"Theme switched to {display} Mode.",
            ui_action={"type": "setTheme", "mode": mode},
        )

    async def _do_showToast(self, params: Dict, context: VertexContext) -> ToolResult:
        message = params.get("message", "")
        variant = params.get("variant", "info")
        if not message:
            return ToolResult(success=False, error="No toast message provided.")
        return ToolResult(
            success=True,
            message="Notification shown.",
            ui_action={"type": "showToast", "message": message, "variant": variant},
        )

    async def _do_logout(self, params: Dict, context: VertexContext) -> ToolResult:
        if context.mode == "guest":
            return ToolResult(
                success=False,
                error="You are not logged in.",
            )
        return ToolResult(
            success=True,
            message="You have been logged out. See you next time!",
            ui_action={"type": "logout"},
        )

    async def _do_openDialog(self, params: Dict, context: VertexContext) -> ToolResult:
        dialog = params.get("dialog", "")
        if not dialog:
            return ToolResult(success=False, error="No dialog specified.")
        return ToolResult(
            success=True,
            message=f"Opened {dialog} dialog.",
            ui_action={"type": "openDialog", "dialog": dialog},
        )

    async def _do_closeDialog(self, params: Dict, context: VertexContext) -> ToolResult:
        return ToolResult(
            success=True,
            message="Dialog closed.",
            ui_action={"type": "closeDialog"},
        )
