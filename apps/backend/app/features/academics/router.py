from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.permissions import require_permission
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.academics.schemas import (
    BulkMarksCreate,
    MarksResponse,
    SGPACalculationResponse,
    BacklogResponse,
)
from app.features.academics.service import AcademicsService

router = APIRouter(tags=["Academic Management & Marks"])


@router.post("/marks", response_model=List[MarksResponse], status_code=status.HTTP_201_CREATED)
async def record_bulk_marks(
    data: BulkMarksCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("marks.create")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AcademicsService(db)
    return await service.record_bulk_marks(data, str(current_user.id))


@router.get("/academics/student/{student_id}/backlogs", response_model=List[BacklogResponse])
async def get_student_backlogs(
    student_id: str,
    _: bool = Depends(require_permission("academics.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AcademicsService(db)
    return await service.get_student_backlogs(student_id)


@router.post("/academics/student/{student_id}/gpa/calculate", response_model=SGPACalculationResponse)
async def calculate_sgpa(
    student_id: str,
    semester_id: str = Query(...),
    _: bool = Depends(require_permission("academics.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = AcademicsService(db)
    return await service.calculate_sgpa(student_id, semester_id)
