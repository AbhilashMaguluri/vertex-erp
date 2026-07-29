"""Tool system — generic domain-based tools with action-level granularity.

Each tool represents a domain (ui, student, attendance, report, email).
Each tool exposes multiple actions via execute(action, params, context).
Tools register themselves with the ToolRegistry, and the Planner discovers
them automatically — never hardcoding tool names.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.ai.models.context import VertexContext


class ToolAction(BaseModel):
    """Metadata describing a single action a tool supports."""

    name: str
    description: str
    parameters: Dict = {}
    requires_auth: bool = False
    required_permissions: List[str] = []


class ToolResult(BaseModel):
    """Result of a tool execution."""

    success: bool
    data: Dict = {}
    message: str = ""
    ui_action: Optional[Dict] = None
    error: Optional[str] = None


class VertexTool(ABC):
    """Abstract base for domain-based tools."""

    name: str
    description: str
    domain: str

    @abstractmethod
    def get_actions(self) -> List[ToolAction]:
        """Return all actions this tool supports."""
        ...

    @abstractmethod
    async def execute(
        self, action: str, params: Dict, context: VertexContext
    ) -> ToolResult:
        """Execute an action with given params and context."""
        ...

    def supports_action(self, action: str) -> bool:
        """Check if this tool supports a specific action."""
        return any(a.name == action for a in self.get_actions())

    def get_action_meta(self, action: str) -> Optional[ToolAction]:
        """Get metadata for a specific action."""
        for a in self.get_actions():
            if a.name == action:
                return a
        return None

    def to_description_dict(self) -> Dict:
        """Return a dict suitable for LLM context."""
        return {
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "actions": [
                {"name": a.name, "description": a.description}
                for a in self.get_actions()
            ],
        }


class ToolRegistry:
    """Central registry for tool discovery — the Planner never hardcodes
    tool names, it queries the registry."""

    def __init__(self) -> None:
        self._tools: Dict[str, VertexTool] = {}

    def register(self, tool: VertexTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[VertexTool]:
        return self._tools.get(name)

    def find_by_domain(self, domain: str) -> List[VertexTool]:
        return [t for t in self._tools.values() if t.domain == domain]

    def find_by_action(self, action: str) -> List[VertexTool]:
        """Find all tools that support a given action name."""
        return [t for t in self._tools.values() if t.supports_action(action)]

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_all_descriptions(self) -> List[Dict]:
        """Return tool metadata for LLM context injection."""
        return [t.to_description_dict() for t in self._tools.values()]

    def validate_action(self, tool_name: str, action: str) -> bool:
        tool = self._tools.get(tool_name)
        return tool is not None and tool.supports_action(action)

    @property
    def has_tools(self) -> bool:
        return len(self._tools) > 0
