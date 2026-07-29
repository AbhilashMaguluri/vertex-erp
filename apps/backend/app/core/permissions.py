from typing import Callable
from fastapi import Depends
from app.core.exceptions import ForbiddenError
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User


def require_permission(permission: str) -> Callable:
    """FastAPI dependency: 403s unless the authenticated user holds `permission`."""

    async def dependency(user: User = Depends(get_current_active_user)) -> User:
        permissions = {p.name for role in user.roles for p in role.permissions}
        if permission not in permissions:
            raise ForbiddenError(f"Missing required permission: '{permission}'")
        return user

    return dependency


def require_role(*roles: str) -> Callable:
    """FastAPI dependency: 403s unless the authenticated user holds one of `roles`."""

    allowed = {r.upper() for r in roles}

    async def dependency(user: User = Depends(get_current_active_user)) -> User:
        user_roles = {r.name for r in user.roles}
        if not user_roles & allowed:
            raise ForbiddenError(f"Requires one of the following roles: {', '.join(sorted(allowed))}")
        return user

    return dependency
