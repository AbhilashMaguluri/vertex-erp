"""Default tool registry.

The Planner discovers capabilities by domain and action, so registering a tool
here is all it takes to make it reachable. Nothing else needs editing.
"""

from __future__ import annotations

from app.ai.tools.base import ToolRegistry
from app.ai.tools.correction_tool import AcademicCorrectionTool
from app.ai.tools.profile_tool import ProfileTool
from app.ai.tools.records_tool import AcademicsTool, AttendanceTool, DirectoryTool
from app.ai.tools.ui_tool import UITool


def create_default_registry() -> ToolRegistry:
    """Build the registry with every built-in tool."""
    registry = ToolRegistry()
    registry.register(UITool())
    registry.register(ProfileTool())
    registry.register(AcademicCorrectionTool())
    registry.register(AttendanceTool())
    registry.register(AcademicsTool())
    registry.register(DirectoryTool())
    return registry


#: One registry for the process. Tools are stateless — they receive their
#: session through ToolExecutionContext — so rebuilding one per request would
#: only re-run the constructors.
_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = create_default_registry()
    return _registry
