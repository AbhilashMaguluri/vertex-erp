from typing import Callable, List, Optional
from fastapi import Depends
from app.core.exceptions import ForbiddenError


class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, current_user_permissions: List[str]) -> bool:
        if self.required_permission not in current_user_permissions:
            raise ForbiddenError(f"Missing required permission: '{self.required_permission}'")
        return True


def require_permission(permission: str) -> Callable:
    """FastAPI dependency for checking permission."""
    def dependency(user_permissions: List[str] = Depends(get_current_permissions_dependency)):
        checker = PermissionChecker(permission)
        checker(user_permissions)
        return True
    return dependency


def get_current_permissions_dependency():
    """Stub dependency replaced in actual auth dependencies module."""
    pass
