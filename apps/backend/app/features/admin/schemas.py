from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


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
    id: str
    code: str
    name: str
    description: Optional[str] = None
    hod_user_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Section Schemas
class SectionCreate(BaseModel):
    department_id: str
    name: str = Field(..., min_length=1, max_length=20)
    batch_year: int = Field(..., ge=2000, le=2100)


class SectionResponse(BaseModel):
    id: str
    department_id: str
    name: str
    batch_year: int
    created_at: datetime

    class Config:
        from_attributes = True


# Academic Year Schemas
class AcademicYearCreate(BaseModel):
    name: str = Field(..., min_length=4, max_length=50)
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicYearResponse(BaseModel):
    id: str
    name: str
    start_date: date
    end_date: date
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Semester Schemas
class SemesterCreate(BaseModel):
    academic_year_id: str
    number: int = Field(..., ge=1, le=8)
    name: str = Field(..., min_length=2, max_length=50)
    start_date: date
    end_date: date
    is_current: bool = False


class SemesterResponse(BaseModel):
    id: str
    academic_year_id: str
    number: int
    name: str
    start_date: date
    end_date: date
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


class SubjectResponse(BaseModel):
    id: str
    department_id: str
    code: str
    name: str
    credits: int
    max_mid_marks: int
    max_internal_marks: int
    max_external_marks: int
    created_at: datetime

    class Config:
        from_attributes = True
