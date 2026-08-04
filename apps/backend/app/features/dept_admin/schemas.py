"""Pydantic schemas for the Department Administrator feature."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field


class CreateDeptAdminRequest(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    department_id: str = Field(..., description="Assigned Department UUID")
    phone: Optional[str] = None
    username: Optional[str] = None


class UpdateDeptAdminRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department_id: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class DeptAdminUserResponse(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str] = None
    department_id: Optional[str] = None
    department_code: Optional[str] = None
    department_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeptDashboardMetricsResponse(BaseModel):
    department_id: str
    department_code: str
    department_name: str
    total_students: int = 0
    faculty_count: int = 0
    counselor_count: int = 0
    attendance_percentage: float = 0.0
    pending_counseling_sessions: int = 0
    subject_count: int = 0
    section_count: int = 0
    recent_activity_count: int = 0
