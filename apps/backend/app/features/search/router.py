from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.search.schemas import SearchResultItem
from app.features.search.service import SearchService

router = APIRouter(prefix="/search", tags=["Global Search"])


@router.get("", response_model=List[SearchResultItem])
async def search(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = SearchService(db)
    return await service.search(q, current_user)
