from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.permissions import require_permission
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.attendance.schemas import (
    BulkAttendanceCreate,
    AttendanceRecordResponse,
    StudentAttendanceSummaryResponse,
    CorrectionRequestCreate,
    CorrectionResponse,
)
from app.features.attendance.service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["Attendance Management"])


@router.post("", response_model=List[AttendanceRecordResponse], status_code=status.HTTP_201_CREATED)
async def record_bulk_attendance(
    data: BulkAttendanceCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attendance.create")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AttendanceService(db)
    return await service.record_bulk_attendance(data, str(current_user.id))


@router.get("/student/{student_id}", response_model=StudentAttendanceSummaryResponse)
async def get_student_attendance_summary(
    student_id: str,
    _: bool = Depends(require_permission("attendance.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AttendanceService(db)
    return await service.get_student_attendance_summary(student_id)


@router.post("/corrections", response_model=CorrectionResponse, status_code=status.HTTP_201_CREATED)
async def request_correction(
    data: CorrectionRequestCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attendance.correction.create")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AttendanceService(db)
    return await service.request_correction(data, str(current_user.id))


@router.patch("/corrections/{correction_id}", response_model=CorrectionResponse)
async def approve_correction(
    correction_id: str,
    is_approved: bool = Query(True),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attendance.correction.approve")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AttendanceService(db)
    return await service.approve_correction(correction_id, is_approved, str(current_user.id))
