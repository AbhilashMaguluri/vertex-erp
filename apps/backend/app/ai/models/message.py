"""Chat message primitives used across the entire Vertex AI subsystem."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class MessageRole(str, Enum):
    """Roles a message participant can assume."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A single message in a Vertex conversation."""

    role: MessageRole
    content: str
    timestamp: Optional[float] = None
