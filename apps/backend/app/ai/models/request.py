"""Vertex request model — the single payload shape for POST /api/vertex/message."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel

from app.ai.models.context import VertexContext
from app.ai.models.message import ChatMessage


class VertexRequest(BaseModel):
    """Everything Vertex needs to generate a response.

    The *messages* list contains the full conversation including the current
    user message (always the last element).  The *context* carries user
    identity, current page, and mode.  *metadata* is a forward-looking
    extension point (model preference, temperature, etc.).
    """

    messages: List[ChatMessage]
    context: VertexContext = VertexContext()
    metadata: Dict = {}
