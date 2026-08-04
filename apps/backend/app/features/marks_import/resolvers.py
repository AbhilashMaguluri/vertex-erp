"""Resolver services for marks import."""
from __future__ import annotations

from typing import Dict, List

from app.features.academics.models import Mark
from app.features.marks_import.repository import MarksImportRepository
from app.features.students.models import Student


class StudentResolver:
    """Resolve student accounts by roll number."""

    def __init__(self, repo: MarksImportRepository):
        self.repo = repo

    async def find_existing_students(
        self, roll_numbers: List[str],
    ) -> Dict[str, Student]:
        return await self.repo.get_students_by_rolls(roll_numbers)


class ExistingMarksResolver:
    """Resolve pre-existing marks records."""

    def __init__(self, repo: MarksImportRepository):
        self.repo = repo

    async def find_existing_marks(
        self,
        student_ids: List[str],
        subject_id: str,
        semester_id: str,
        assessment_code: str,
    ) -> Dict[str, Mark]:
        return await self.repo.get_existing_marks(
            student_ids, subject_id, semester_id, assessment_code,
        )
