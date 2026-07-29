from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# Department Schemas
class DepartmentCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    hod_user_id: Optional[str] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    hod_user_id: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: UUID | str
    code: str
    name: str
    description: Optional[str] = None
    hod_user_id: UUID | str | None = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Section Schemas
class SectionCreate(BaseModel):
    department_id: str
    name: str = Field(..., min_length=1, max_length=20)
    year: int = Field(..., ge=1, le=4)
    batch_year: int = Field(..., ge=2000, le=2100)


class SectionUpdate(BaseModel):
    department_id: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=20)
    year: Optional[int] = Field(None, ge=1, le=4)
    batch_year: Optional[int] = Field(None, ge=2000, le=2100)


class SectionResponse(BaseModel):
    id: UUID | str
    department_id: UUID | str
    name: str
    year: Optional[int] = None
    batch_year: int
    created_at: datetime

    class Config:
        from_attributes = True


def _validate_academic_year_code(value: Optional[str]) -> Optional[str]:
    if value is not None and len(value) < 4:
        raise ValueError("Academic Year Code must be at least 4 characters.")
    return value


# Academic Year Schemas
# `name` deliberately has no Field(min_length=...) constraint — that would
# short-circuit with Pydantic's generic message before the field_validator
# below runs, hiding the friendlier "Academic Year Code must be at least 4
# characters." message from ever reaching the client.
class AcademicYearCreate(BaseModel):
    name: str = Field(..., max_length=50)
    start_date: date
    end_date: date
    is_current: bool = False

    _validate_name = field_validator("name")(_validate_academic_year_code)


class AcademicYearUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None

    _validate_name = field_validator("name")(_validate_academic_year_code)


class AcademicYearResponse(BaseModel):
    id: UUID | str
    name: str
    start_date: date
    end_date: date
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Semester Schemas
# Semesters are a fixed, institution-wide catalog (1-1 .. 4-2) seeded once —
# there is intentionally no Create/Update schema; see app/scripts/seed.py.
class SemesterResponse(BaseModel):
    id: UUID | str
    academic_year_id: Optional[UUID | str] = None
    number: int
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Subject Schemas
class SubjectCreate(BaseModel):
    department_id: str
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=150)
    credits: int = Field(3, ge=1, le=10)
    max_mid_marks: int = Field(30, ge=0)
    max_internal_marks: int = Field(20, ge=0)
    max_external_marks: int = Field(50, ge=0)


class SubjectUpdate(BaseModel):
    department_id: Optional[str] = None
    code: Optional[str] = Field(None, min_length=2, max_length=20)
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    credits: Optional[int] = Field(None, ge=1, le=10)
    max_mid_marks: Optional[int] = Field(None, ge=0)
    max_internal_marks: Optional[int] = Field(None, ge=0)
    max_external_marks: Optional[int] = Field(None, ge=0)


class SubjectResponse(BaseModel):
    id: UUID | str
    department_id: UUID | str
    code: str
    name: str
    credits: int
    max_mid_marks: int
    max_internal_marks: int
    max_external_marks: int
    created_at: datetime

    class Config:
        from_attributes = True
