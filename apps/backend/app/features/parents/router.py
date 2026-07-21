from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.core.permissions import require_permission
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.parents.schemas import (
    ParentCommunicationCreateRequest,
    ParentCommunicationResponse,
)
from app.features.parents.service import ParentService

router = APIRouter(prefix="/parent-communication", tags=["Parent Communication"])


@router.post("", response_model=ParentCommunicationResponse, status_code=status.HTTP_201_CREATED)
async def log_parent_communication(
    data: ParentCommunicationCreateRequest,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("parent_communication.create")),
    db: AsyncSession = Depends(get_async_db),
):
    service = ParentService(db)
    return await service.log_communication(data, str(current_user.id))


@router.get("/student/{student_id}", response_model=List[ParentCommunicationResponse])
async def get_student_parent_communications(
    student_id: str,
    _: bool = Depends(require_permission("parent_communication.read")),
    db: AsyncSession = Depends(get_async_db),
):
    service = ParentService(db)
    return await service.get_student_communications(student_id)
