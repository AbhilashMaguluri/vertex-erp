"""UI Tool — drives the VertexERP frontend.

Returns ``ui_action`` payloads the client executes. No backend state changes
here, which is why these actions declare ``mutates_state=False`` even though
they visibly change what the user sees.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from app.ai.models.ownership import DataOwner
from app.ai.tools.base import ToolAction, ToolExecutionContext, ToolResult, VertexTool

# Page name → route. Keys are what users actually say.
PAGE_ROUTES: Dict[str, str] = {
    "dashboard": "/dashboard",
    "home": "/dashboard",
    "attendance": "/attendance",
    "counselling": "/counselling",
    "counseling": "/counselling",
    "academics": "/academics",
    "marks": "/academics",
    "results": "/academics",
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

# Friendly labels for confirmation copy, keyed by route.
_ROUTE_LABELS: Dict[str, str] = {
    "/dashboard": "Dashboard",
    "/attendance": "Attendance",
    "/counselling": "Counselling",
    "/academics": "Academics",
    "/reports": "Reports",
    "/reach-out": "Reach Out Hub",
    "/notifications": "Notifications",
    "/settings": "Settings",
    "/my-workspace": "My Workspace",
    "/my-profile": "My Profile",
    "/students": "Students",
    "/admin": "Admin",
    "/admin/users": "User Management",
    "/admin/imports": "Data Imports",
    "/admin/audit-logs": "Audit Logs",
    "/admin/academic-config": "Academic Config",
    "/parent-communication": "Parent Communication",
    "/login": "Login",
}


def resolve_page_route(page: str) -> Optional[str]:
    """Resolve a spoken page name to a route.

    Exact match wins, then the longest partial match — so "user management"
    does not resolve to "/students" just because "student" appears in the
    table first.
    """
    normalized = (page or "").strip().lower().rstrip("?.!")
    if not normalized:
        return None
    if normalized in PAGE_ROUTES:
        return PAGE_ROUTES[normalized]

    best: Optional[str] = None
    best_len = 0
    for key, route in PAGE_ROUTES.items():
        if (key in normalized or normalized in key) and len(key) > best_len:
            best, best_len = route, len(key)
    if best:
        return best

    if normalized.startswith("/"):
        return normalized
    return None


def route_label(route: str, fallback: str) -> str:
    return _ROUTE_LABELS.get(route, fallback.strip().title() or route)


class UITool(VertexTool):
    """Controls navigation, appearance, dialogs and session end."""

    name = "ui"
    description = (
        "Controls the VertexERP interface — navigation, theme, notifications, "
        "dialogs and sign-out"
    )
    domain = "ui"

    def get_actions(self) -> List[ToolAction]:
        return [
            ToolAction(
                name="navigate",
                description="Navigate to a page in VertexERP",
                parameters={"page": "string — page name or route path"},
                owner=DataOwner.APPLICATION,
            ),
            ToolAction(
                name="setTheme",
                description="Change the interface theme (light, dark or system)",
                parameters={"mode": "string — light | dark | system"},
                owner=DataOwner.APPLICATION,
            ),
            ToolAction(
                name="showToast",
                description="Show a notification toast",
                parameters={
                    "message": "string — toast text",
                    "variant": "string — success | error | info | warning",
                },
                owner=DataOwner.APPLICATION,
            ),
            ToolAction(
                name="logout",
                description="Sign the user out of VertexERP",
                requires_auth=True,
                owner=DataOwner.APPLICATION,
            ),
            ToolAction(
                name="openDialog",
                description="Open a dialog or modal",
                parameters={"dialog": "string — dialog identifier"},
                owner=DataOwner.APPLICATION,
            ),
            ToolAction(
                name="closeDialog",
                description="Close the open dialog",
                owner=DataOwner.APPLICATION,
            ),
        ]

    async def execute(
        self, action: str, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        handler = getattr(self, f"_do_{action}", None)
        if handler is None:
            return ToolResult(success=False, error=f"Unknown UI action: {action}")
        return await handler(params, context)

    # ------------------------------------------------------------------

    async def _do_navigate(
        self, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        page = str(params.get("page", "")).strip()
        if not page:
            return ToolResult(success=False, error="No page specified for navigation.")

        route = resolve_page_route(page)
        if not route:
            available = ", ".join(sorted(_ROUTE_LABELS.values())[:8])
            return ToolResult(
                success=False,
                error=(
                    f"I couldn't find a page called '{page}'. "
                    f"Pages I can open include: {available}."
                ),
            )

        label = route_label(route, page)

        if context.vertex.page.route == route:
            return ToolResult(
                success=True,
                message=f"You're already on {label}.",
                data={"route": route, "already_there": True},
            )

        return ToolResult(
            success=True,
            message=f"Opened {label}.",
            data={"route": route, "label": label},
            ui_action={"type": "navigate", "route": route},
        )

    async def _do_setTheme(
        self, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        mode = str(params.get("mode", "")).strip().lower()
        if mode not in VALID_THEMES:
            return ToolResult(
                success=False,
                error=f"'{mode or 'that'}' isn't a theme I recognise. Use light, dark or system.",
            )
        return ToolResult(
            success=True,
            message=f"Theme switched to {mode} mode.",
            data={"mode": mode},
            ui_action={"type": "setTheme", "mode": mode},
        )

    async def _do_showToast(
        self, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        message = str(params.get("message", "")).strip()
        if not message:
            return ToolResult(success=False, error="No toast message provided.")
        variant = str(params.get("variant", "info")).strip().lower()
        return ToolResult(
            success=True,
            message="Notification shown.",
            ui_action={"type": "showToast", "message": message[:200], "variant": variant},
        )

    async def _do_logout(
        self, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        if not context.vertex.user.is_authenticated:
            return ToolResult(success=False, error="You're not signed in.")
        return ToolResult(
            success=True,
            message="Signed out.",
            ui_action={"type": "logout"},
        )

    async def _do_openDialog(
        self, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        dialog = str(params.get("dialog", "")).strip()
        if not dialog:
            return ToolResult(success=False, error="No dialog specified.")
        return ToolResult(
            success=True,
            message=f"Opened the {dialog} dialog.",
            ui_action={"type": "openDialog", "dialog": dialog},
        )

    async def _do_closeDialog(
        self, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        return ToolResult(
            success=True,
            message="Dialog closed.",
            ui_action={"type": "closeDialog"},
        )
