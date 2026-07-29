"""Vertex AI router — the single HTTP entry point for all Vertex interactions.

Endpoint:  ``POST /api/vertex/message``

SSE event types:
    data: {"type":"token","content":"Hello"}\n\n    — streamed LLM token
    data: {"type":"action","action":{...}}\n\n     — UI action for frontend
    data: {"type":"done"}\n\n                       — stream complete
    data: {"type":"error","content":"..."}\n\n      — error
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.ai.core.vertex import VertexCore
from app.ai.models.request import VertexRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vertex", tags=["Vertex AI"])

_ACTION_MARKER = "__SSE_ACTION__"


@router.post("/message")
async def vertex_message(request: VertexRequest, raw_request: Request):
    """Accept a message to Vertex and stream the response as Server-Sent Events."""

    async def event_stream():
        core = VertexCore()
        try:
            async for token in core.process(request):
                # Check if this token contains an embedded action event
                if token.startswith(_ACTION_MARKER) and token.endswith(_ACTION_MARKER):
                    # Extract the action JSON from between the markers
                    action_json = token[len(_ACTION_MARKER):-len(_ACTION_MARKER)]
                    yield f"data: {action_json}\n\n"
                else:
                    payload = json.dumps({"type": "token", "content": token})
                    yield f"data: {payload}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            logger.exception("Stream error in /api/vertex/message")
            payload = json.dumps({
                "type": "error",
                "content": "An error occurred while generating the response. Please try again.",
            })
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
