"""Tool system — the only way Vertex changes anything.

Two rules hold the design together:

1. The LLM never manipulates application state. The Planner decides, a tool
   executes, and the model is told what happened afterwards.
2. Every action declares the permissions it needs. The permission validator
   reads that declaration; a tool that forgets to declare one is treated as
   requiring authentication rather than as public.

Tools reach the database through :class:`ToolExecutionContext`, which carries
the request-scoped session. Nothing here opens its own session.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.ai.models.context import VertexContext
from app.ai.models.ownership import DataOwner


class ToolAction(BaseModel):
    """Metadata describing a single action a tool supports."""

    name: str
    description: str
    parameters: Dict = Field(default_factory=dict)

    requires_auth: bool = False
    required_permissions: List[str] = Field(default_factory=list)

    #: Who owns the data this action touches. Used by the permission validator
    #: to apply ownership rules on top of raw permission checks.
    owner: DataOwner = DataOwner.APPLICATION

    #: True when the action changes stored state, as opposed to reading it or
    #: driving the UI. Mutating actions are held to the stricter checks.
    mutates_state: bool = False

    #: True when the effect is hard to undo and the user should confirm first.
    requires_confirmation: bool = False


class ToolResult(BaseModel):
    """Result of a tool execution."""

    success: bool
    data: Dict = Field(default_factory=dict)
    message: str = ""
    ui_action: Optional[Dict] = None
    error: Optional[str] = None

    #: True when ``data`` holds real records read from the ERP. The output
    #: guardrail uses this to decide whether concrete figures in the response
    #: are grounded or fabricated.
    is_erp_data: bool = False

    @property
    def failed(self) -> bool:
        return not self.success


class ToolExecutionContext(BaseModel):
    """Everything a tool needs to run, assembled by the pipeline."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vertex: VertexContext

    #: Request-scoped AsyncSession, or None when the pipeline runs without a
    #: database (guest traffic, tests). Tools that need it must check.
    db: Optional[object] = None

    #: The authenticated ``User`` ORM object. Needed by feature services that
    #: scope their own results from it (global search, caseload filtering) —
    #: passing it through means Vertex reuses their scoping instead of
    #: reimplementing it.
    auth_user: Optional[object] = None

    request_id: str = ""

    @property
    def user_id(self) -> Optional[str]:
        return self.vertex.user.id

    @property
    def student_id(self) -> Optional[str]:
        """The student record this request acts on.

        Prefers the caller's own record, falling back to the one open in their
        workspace. Never read from the message.
        """
        return self.vertex.user.student_id or self.vertex.workspace.student_id


class VertexTool(ABC):
    """Abstract base for domain-based tools."""

    name: str
    description: str
    domain: str

    @abstractmethod
    def get_actions(self) -> List[ToolAction]:
        """Return every action this tool supports."""
        ...  # pragma: no cover

    @abstractmethod
    async def execute(
        self, action: str, params: Dict, context: ToolExecutionContext
    ) -> ToolResult:
        """Run an action. Must not raise — return a failed ToolResult instead."""
        ...  # pragma: no cover

    def supports_action(self, action: str) -> bool:
        return any(a.name == action for a in self.get_actions())

    def get_action_meta(self, action: str) -> Optional[ToolAction]:
        for candidate in self.get_actions():
            if candidate.name == action:
                return candidate
        return None

    def to_description_dict(self) -> Dict:
        """Shape used when describing capabilities to the LLM."""
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
    """Central registry for discovery.

    The Planner asks for a capability by domain or action name; it never
    hardcodes a tool. Adding a tool is a registration, not a planner edit.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, VertexTool] = {}

    def register(self, tool: VertexTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: Optional[str]) -> Optional[VertexTool]:
        return self._tools.get(name) if name else None

    def find_by_domain(self, domain: str) -> List[VertexTool]:
        return [t for t in self._tools.values() if t.domain == domain]

    def find_by_action(self, action: str) -> List[VertexTool]:
        return [t for t in self._tools.values() if t.supports_action(action)]

    def resolve(self, domain: str, action: str) -> Optional[VertexTool]:
        """First tool in ``domain`` that supports ``action``.

        The lookup the Planner actually performs — asking for a capability
        rather than a name, so a replacement tool is picked up automatically.
        """
        for tool in self.find_by_domain(domain):
            if tool.supports_action(action):
                return tool
        return None

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_all_descriptions(self) -> List[Dict]:
        return [t.to_description_dict() for t in self._tools.values()]

    def validate_action(self, tool_name: str, action: str) -> bool:
        tool = self._tools.get(tool_name)
        return tool is not None and tool.supports_action(action)

    @property
    def has_tools(self) -> bool:
        return bool(self._tools)
