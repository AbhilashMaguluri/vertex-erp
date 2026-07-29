from typing import Optional
from pydantic import BaseModel


class SearchResultItem(BaseModel):
    type: str  # "student" | "user"
    id: str
    title: str
    subtitle: Optional[str] = None
    url: str
