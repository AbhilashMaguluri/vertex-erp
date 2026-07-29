"""Typed response models so the frontend can render rich content."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel


class ResponseType(str, Enum):
    """Discriminator for the frontend response renderer."""

    TEXT = "text"
    MARKDOWN = "markdown"
    TABLE = "table"
    CARD = "card"
    LIST = "list"
    ERROR = "error"
    LOADING = "loading"
    ACTION = "action"


class VertexResponse(BaseModel):
    """A structured response from Vertex (used in non-streaming or as the
    final envelope after a stream completes)."""

    type: ResponseType = ResponseType.MARKDOWN
    content: str
    metadata: Dict = {}
    ui_action: Optional[Dict] = None
