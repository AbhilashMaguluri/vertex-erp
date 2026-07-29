from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.permissions import require_permission
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.core.scoping import ensure_student_record_access
from app.features.students.repository import StudentRepository
from app.features.academics.schemas import (
    BulkMarksCreate,
    MarksResponse,
    SGPACalculationResponse,
    BacklogResponse,
    StudentAcademicRecordResponse,
)
from app.features.academics.service import AcademicsService

router = APIRouter(tags=["Academic Management & Marks"])


@router.get("/academics/student/{student_id}/record", response_model=StudentAcademicRecordResponse)
async def get_student_academic_record(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("academics.read")),
    db: AsyncSession = Depends(get_async_db),
):
    """Semester-wise transcript. Counsellors are scoped to assigned students;
    a student may only read their own record."""
    await ensure_student_record_access(current_user, student_id, StudentRepository(db))
    service = AcademicsService(db)
    return await service.get_student_academic_record(student_id)


@router.post("/marks", response_model=List[MarksResponse], status_code=status.HTTP_201_CREATED)
async def record_bulk_marks(
    data: BulkMarksCreate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AcademicsService(db)
    return await service.record_bulk_marks(data, str(current_user.id))


@router.get("/academics/student/{student_id}/backlogs", response_model=List[BacklogResponse])
async def get_student_backlogs(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("academics.read")),
    db: AsyncSession = Depends(get_async_db),
):
    await ensure_student_record_access(current_user, student_id, StudentRepository(db))
    service = AcademicsService(db)
    return await service.get_student_backlogs(student_id)


@router.post("/academics/student/{student_id}/gpa/calculate", response_model=SGPACalculationResponse)
async def calculate_sgpa(
    student_id: str,
    semester_id: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("academics.read")),
    db: AsyncSession = Depends(get_async_db),
):
    await ensure_student_record_access(current_user, student_id, StudentRepository(db))
    service = AcademicsService(db)
    return await service.calculate_sgpa(student_id, semester_id)
