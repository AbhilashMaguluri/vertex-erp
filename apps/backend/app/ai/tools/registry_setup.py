"""Default tool registry — registers all built-in tools at startup."""

from __future__ import annotations

from app.ai.tools.base import ToolRegistry
from app.ai.tools.ui_tool import UITool
from app.ai.tools.profile_tool import ProfileTool
from app.ai.tools.correction_tool import AcademicCorrectionTool


def create_default_registry() -> ToolRegistry:
    """Create a ToolRegistry with all built-in tools registered."""
    registry = ToolRegistry()
    registry.register(UITool())
    registry.register(ProfileTool())
    registry.register(AcademicCorrectionTool())
    return registry
