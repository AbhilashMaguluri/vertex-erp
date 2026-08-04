"""Department Access Policy — reusable backend policy for strict department-level data isolation.

Ensures that Department Administrators (DEPARTMENT_ADMIN) can only access and modify
resources belonging to their explicitly assigned department (User.department_id).
Super Administrators and Institution Admins retain institution-wide access.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.sql import Select

from app.core.enums import UserRole
from app.core.exceptions import ForbiddenError


class DepartmentAccessPolicy:
    """Policy for checking and enforcing department data boundaries."""

    @staticmethod
    def is_department_admin(user: Any) -> bool:
        """Return True if user holds the DEPARTMENT_ADMIN role."""
        if not user or not hasattr(user, "roles"):
            return False
        role_names = {r.name.upper() for r in user.roles}
        return UserRole.DEPARTMENT_ADMIN.value in role_names

    @staticmethod
    def get_user_department_id(user: Any) -> Optional[str]:
        """Extract the assigned department UUID for a user."""
        if not user:
            return None
        return getattr(user, "department_id", None)

    @staticmethod
    def apply_department_filter(query: Select, model: Any, user: Any) -> Select:
        """Apply department filtering to a SQLAlchemy Select query if user is a DEPARTMENT_ADMIN."""
        if DepartmentAccessPolicy.is_department_admin(user):
            dept_id = DepartmentAccessPolicy.get_user_department_id(user)
            if dept_id:
                if hasattr(model, "department_id"):
                    return query.where(model.department_id == dept_id)
                elif hasattr(model, "student") and hasattr(model.student, "department_id"):
                    # Joining student model if applicable
                    return query.where(model.student.has(department_id=dept_id))
        return query

    @staticmethod
    def validate_department_access(resource_department_id: Optional[str], user: Any) -> None:
        """Raise 403 ForbiddenError if a DEPARTMENT_ADMIN attempts to access another department's resource."""
        if DepartmentAccessPolicy.is_department_admin(user):
            user_dept_id = DepartmentAccessPolicy.get_user_department_id(user)
            if user_dept_id and resource_department_id and str(resource_department_id) != str(user_dept_id):
                raise ForbiddenError("Access denied: Resource belongs to a different department.")
