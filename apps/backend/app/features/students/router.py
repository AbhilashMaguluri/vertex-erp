from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.permissions import require_permission
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.students.schemas import (
    StudentProfileResponse,
    Student360Response,
    RiskFlagUpdateRequest,
)
from app.features.students.service import StudentService

router = APIRouter(prefix="/students", tags=["Student Workspace"])


@router.get("/{student_id}/workspace", response_model=Student360Response)
async def get_student_360_workspace(
    student_id: str,
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    return await service.get_student_360_workspace(student_id)


@router.get("/{student_id}", response_model=StudentProfileResponse)
async def get_student_profile(
    student_id: str,
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    return await service.get_student_profile(student_id)


@router.patch("/{student_id}/risk", response_model=StudentProfileResponse)
async def update_student_risk_flag(
    student_id: str,
    data: RiskFlagUpdateRequest,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("student.risk.update")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentService(db)
    return await service.update_risk_flag(student_id, data, str(current_user.id))
