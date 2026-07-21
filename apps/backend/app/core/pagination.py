from typing import Generic, List, TypeVar
from pydantic import BaseModel
from math import ceil

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    pagination: PaginationMeta

    @classmethod
    def create(cls, items: List[T], total: int, params: PaginationParams):
        total_pages = ceil(total / params.per_page) if params.per_page > 0 else 1
        return cls(
            data=items,
            pagination=PaginationMeta(
                total=total,
                page=params.page,
                per_page=params.per_page,
                total_pages=total_pages,
                has_next=params.page < total_pages,
                has_prev=params.page > 1,
            ),
        )
