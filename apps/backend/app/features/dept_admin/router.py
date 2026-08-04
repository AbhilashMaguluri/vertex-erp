"""FastAPI router for Department Administrator endpoints."""
from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit_log
from app.core.enums import AuditAction
from app.core.exceptions import ForbiddenError, ValidationError
from app.core.permissions import require_permission
from app.database import get_async_db
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.dept_admin.schemas import (
    CreateDeptAdminRequest,
    DeptAdminUserResponse,
    DeptDashboardMetricsResponse,
    UpdateDeptAdminRequest,
)
from app.features.dept_admin.service import DeptAdminService

router = APIRouter(tags=["Department Administrator Management"])


# --------------------------------------------------------------------------
# Super Admin Endpoints — Manage Department Admins
# --------------------------------------------------------------------------

@router.get("/admin/dept-admins", response_model=List[DeptAdminUserResponse])
async def list_department_administrators(
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Super Admin: List all Department Administrators across departments."""
    return await DeptAdminService(db).list_dept_admins()


@router.post("/admin/dept-admins", response_model=DeptAdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_department_administrator(
    data: CreateDeptAdminRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Super Admin: Create a new Department Administrator and assign to a department."""
    service = DeptAdminService(db)
    res, temp_password = await service.create_dept_admin(data, str(current_user.id))

    await record_audit_log(
        db, user=current_user, action=AuditAction.CREATE.value,
        entity_type="User", entity_id=res.id,
        changes={"role": "DEPARTMENT_ADMIN", "department_id": data.department_id, "email": data.email},
        request=request,
    )
    await db.commit()
    return res


@router.put("/admin/dept-admins/{user_id}", response_model=DeptAdminUserResponse)
async def update_department_administrator(
    user_id: str,
    data: UpdateDeptAdminRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Super Admin: Update Department Administrator profile or assigned department."""
    service = DeptAdminService(db)
    res = await service.update_dept_admin(user_id, data)

    await record_audit_log(
        db, user=current_user, action=AuditAction.UPDATE.value,
        entity_type="User", entity_id=user_id,
        changes=data.model_dump(exclude_unset=True),
        request=request,
    )
    await db.commit()
    return res


@router.post("/admin/dept-admins/{user_id}/reset-password")
async def reset_department_admin_password(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("user.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Super Admin: Reset password for a Department Administrator."""
    service = DeptAdminService(db)
    new_password = await service.reset_password(user_id)

    await record_audit_log(
        db, user=current_user, action=AuditAction.PASSWORD_RESET.value,
        entity_type="User", entity_id=user_id,
        changes={"reset_by": current_user.email},
        request=request,
    )
    await db.commit()
    return {"message": "Password reset successfully.", "temporary_password": new_password}


# --------------------------------------------------------------------------
# Department Admin Dashboard Endpoint
# --------------------------------------------------------------------------

@router.get("/dept-admin/dashboard", response_model=DeptDashboardMetricsResponse)
async def get_department_admin_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get metrics strictly scoped to the authenticated Department Admin's assigned department."""
    if not current_user.department_id:
        raise ValidationError("User is not assigned to any academic department.")

    return await DeptAdminService(db).get_dept_dashboard_metrics(current_user.department_id)
