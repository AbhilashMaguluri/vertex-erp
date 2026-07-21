from typing import AsyncGenerator, Optional
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.core.security import decode_jwt_token
from app.shared.utils.idempotency import get_idempotent_response


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_db():
        yield session


async def get_current_token_payload(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")
    token = auth_header.split(" ")[1]
    return decode_jwt_token(token)


async def check_idempotency(idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")):
    if idempotency_key:
        cached = get_idempotent_response(idempotency_key)
        if cached:
            return cached
    return None
