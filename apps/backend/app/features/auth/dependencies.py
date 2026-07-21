from typing import List
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.core.security import decode_jwt_token
from app.features.auth.models import User
from app.features.auth.repository import AuthRepository


async def get_current_user_id(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or malformed Authorization header")
    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)
    sub = payload.get("sub")
    if not sub:
        raise AuthenticationError("Invalid token payload: missing subject")
    return sub


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    repo = AuthRepository(db)
    user = await repo.get_user_by_id(user_id)
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("User account is inactive")
    return user


async def get_current_user_permissions(
    user: User = Depends(get_current_user),
) -> List[str]:
    permissions = set()
    for role in user.roles:
        for perm in role.permissions:
            permissions.add(perm.name)
    return list(permissions)
