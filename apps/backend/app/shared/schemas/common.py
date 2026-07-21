from typing import Any, List, Optional
from pydantic import BaseModel


class UserBasicInfo(BaseModel):
    id: str
    name: str
    email: str

    class Config:
        from_attributes = True


class ApiErrorDetail(BaseModel):
    field: Optional[str] = None
    code: Optional[str] = None
    message: str


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    details: Optional[List[ApiErrorDetail]] = None


class ApiErrorResponseModel(BaseModel):
    error: ErrorEnvelope


class SuccessResponse(BaseModel):
    message: str
    data: Optional[Any] = None
