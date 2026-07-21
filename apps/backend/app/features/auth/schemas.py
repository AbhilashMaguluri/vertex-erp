from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 900


class UserProfileResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool
    department_id: Optional[str] = None
    roles: List[str]
    permissions: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None
    department_id: Optional[str] = None
    roles: List[str]


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    department_id: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


class ActiveSessionResponse(BaseModel):
    id: str
    created_at: datetime
    expires_at: datetime
    is_current: bool = False
