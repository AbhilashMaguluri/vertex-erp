from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, model_validator


class LoginRequest(BaseModel):
    # Kept named `email` for wire compatibility, but it accepts either the
    # email address or the short username Office Import issues — a student
    # signs in with the roll number printed on their credential slip. Typed as
    # a plain string rather than EmailStr for exactly that reason.
    email: str = Field(..., min_length=1, max_length=255, description="Email address or username")
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class UserSummary(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    full_name: str
    roles: List[str]
    permissions: List[str]
    department_id: Optional[str] = None
    force_password_change: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserSummary


class UserProfileResponse(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    force_password_change: bool
    department_id: Optional[str] = None
    roles: List[str]
    permissions: List[str]
    last_login_at: Optional[datetime] = None
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


class SessionResponse(BaseModel):
    id: str
    created_at: datetime
    expires_at: datetime
    remember_me: bool
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    is_current: bool = False

    class Config:
        from_attributes = True


class StudentProvisionDetails(BaseModel):
    """Extra fields required only when an Admin creates a STUDENT account."""

    roll_number: str = Field(..., min_length=1, max_length=30)
    registration_number: str = Field(..., min_length=1, max_length=50)
    date_of_birth: date
    batch_year: int = Field(..., ge=2000, le=2100)
    section_id: str
    semester_id: str


class UserCreateRequest(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None
    department_id: Optional[str] = None
    role: str
    student_details: Optional[StudentProvisionDetails] = None
    # Optional override for the auto-generated default password (STUDENT
    # accounts default to "<RollNumber>@vvit.net" — see AdminService.create_user_by_admin).
    password: Optional[str] = Field(None, min_length=6, max_length=128)

    @model_validator(mode="after")
    def validate_student_fields(self) -> "UserCreateRequest":
        if self.role.upper() == "STUDENT":
            if not self.department_id:
                raise ValueError("department_id is required when role is STUDENT")
            if not self.student_details:
                raise ValueError("student_details is required when role is STUDENT")
        return self


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    department_id: Optional[str] = None
    role: Optional[str] = None


class AdminCreateUserResponse(BaseModel):
    user: UserProfileResponse
    temporary_password: str
    email_sent: bool


class AdminResetPasswordResponse(BaseModel):
    temporary_password: str
    email_sent: bool


class UserListItemResponse(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    full_name: str
    roles: List[str]
    department_id: Optional[str] = None
    is_active: bool
    force_password_change: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AssignCounsellorRequest(BaseModel):
    student_id: str
    counsellor_id: str
    semester_id: str


