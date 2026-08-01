"""Vertex AI router — the single HTTP entry point.

    POST /api/vertex/message

SSE event types:
    {"type":"token","content":"…"}     streamed response text
    {"type":"action","action":{…}}     UI action for the client to execute
    {"type":"replace","content":"…"}   discard what was streamed, show this
    {"type":"done"}                    stream complete
    {"type":"error","content":"…"}     stream failed

Two things this endpoint does differently from the rest of the API:

*Optional authentication.* Vertex answers guests too, so a missing or expired
token downgrades to guest mode instead of returning 401. What the token does
NOT do is come from the request body — identity is resolved here, server-side,
and the body's claims about who the user is are ignored entirely.

*Its own database session.* A dependency-injected session is torn down when
the response object is returned, which for a StreamingResponse is before the
body has been produced. The session is therefore opened inside the generator
and closed when the stream ends.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.core.vertex import ACTION_MARKER, REPLACE_MARKER, VertexCore
from app.ai.models.request import VertexRequest
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vertex", tags=["Vertex AI"])


async def _resolve_caller(raw_request: Request, db: AsyncSession) -> Optional[object]:
    """Authenticate from the Authorization header, or return None for a guest.

    Deliberately quiet: an anonymous or expired session is the normal state for
    a chat panel on the login page, not an error worth surfacing.
    """
    header = raw_request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None

    try:
        from app.core.security import decode_jwt_token
        from app.features.auth.repository import AuthRepository

        payload = decode_jwt_token(header.split(" ", 1)[1])
        user_id = payload.get("sub")
        if not user_id:
            return None

        user = await AuthRepository(db).get_user_by_id(user_id)
        if user is None or not user.is_active:
            return None

        # Mirrors get_current_active_user: an account still on its temporary
        # password cannot act through Vertex either.
        if user.force_password_change:
            return None

        return user

    except Exception as exc:
        logger.debug("Vertex caller resolution failed, continuing as guest: %s", exc)
        return None


@router.post("/message")
async def vertex_message(request: VertexRequest, raw_request: Request):
    """Accept a message and stream the agent's response as Server-Sent Events."""
    request_id = getattr(raw_request.state, "request_id", "unknown")

    async def event_stream():
        async with AsyncSessionLocal() as db:
            try:
                user = await _resolve_caller(raw_request, db)
                logger.info(
                    "Vertex request [%s]: %d message(s), caller=%s",
                    request_id,
                    len(request.messages),
                    str(user.id) if user else "guest",
                )

                core = VertexCore(db=db, auth_user=user)
                async for chunk in core.process(request):
                    yield _to_sse(chunk)

                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            except Exception as exc:
                logger.exception("Vertex stream failed [%s]: %s", request_id, exc)
                payload = json.dumps({
                    "type": "error",
                    "content": (
                        "Something went wrong while generating that response. "
                        "Please try again."
                    ),
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


def _to_sse(chunk: str) -> str:
    """Convert a pipeline chunk into an SSE frame.

    The pipeline wraps structured events in markers so the whole stream stays a
    single string generator; everything else is response text.
    """
    for marker in (ACTION_MARKER, REPLACE_MARKER):
        if chunk.startswith(marker) and chunk.endswith(marker):
            return f"data: {chunk[len(marker):-len(marker)]}\n\n"

    payload = json.dumps({"type": "token", "content": chunk})
    return f"data: {payload}\n\n"
