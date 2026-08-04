"""Resolver services for attendance import.

Resolves:
- Student existence by roll number.
- Existing attendance records for given student, subject, and date.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Dict, List, Optional

from app.features.attendance.models import AttendanceRecord
from app.features.attendance_import.repository import AttendanceImportRepository
from app.features.attendance_import.schemas import (
    NormalizedAttendanceEntry,
    ResolvedAttendanceEntry,
)
from app.features.students.models import Student

logger = logging.getLogger("app.attendance_import.resolvers")


class StudentResolver:
    """Resolve student accounts by roll number."""

    def __init__(self, repo: AttendanceImportRepository):
        self.repo = repo

    async def find_existing_students(
        self, roll_numbers: List[str],
    ) -> Dict[str, Student]:
        return await self.repo.get_students_by_rolls(roll_numbers)


class ExistingAttendanceResolver:
    """Resolve pre-existing attendance records."""

    def __init__(self, repo: AttendanceImportRepository):
        self.repo = repo

    async def find_existing_attendance(
        self,
        student_ids: List[str],
        subject_id: str,
        att_date: date,
    ) -> Dict[str, AttendanceRecord]:
        return await self.repo.get_existing_attendance(
            student_ids, subject_id, att_date,
        )
