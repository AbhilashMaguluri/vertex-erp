"""Assessment Template Service.

Manages configurable assessment structures (Mid Written with questions A, B, C, D;
Open Book; Objective Test; Seminar; Assignment; Quiz; Lab Internal; Practical; Viva).
"""
from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.features.marks_import.models import AssessmentTemplate
from app.features.marks_import.schemas import (
    AssessmentComponentSchema,
    AssessmentTemplateCreate,
    AssessmentTemplateUpdate,
)

logger = logging.getLogger("app.marks_import.template_service")

# Default assessment structure templates
DEFAULT_TEMPLATES = [
    {
        "assessment_code": "MID_WRITTEN",
        "assessment_name": "Mid Written Exam",
        "total_max_marks": 30.0,
        "components": [
            {"key": "A", "label": "Question A", "max_marks": 6.0},
            {"key": "B", "label": "Question B", "max_marks": 6.0},
            {"key": "C", "label": "Question C", "max_marks": 6.0},
            {"key": "D", "label": "Question D", "max_marks": 12.0},
        ],
        "description": "Standard Mid Written Exam (30 Marks)",
    },
    {
        "assessment_code": "OPEN_BOOK",
        "assessment_name": "Open Book Exam",
        "total_max_marks": 20.0,
        "components": [],
        "description": "Open Book Exam (20 Marks)",
    },
    {
        "assessment_code": "OBJECTIVE_TEST",
        "assessment_name": "Objective Test",
        "total_max_marks": 20.0,
        "components": [],
        "description": "Objective / Multiple Choice Test (20 Marks)",
    },
    {
        "assessment_code": "SEMINAR",
        "assessment_name": "Seminar",
        "total_max_marks": 5.0,
        "components": [],
        "description": "Seminar Presentation (5 Marks)",
    },
    {
        "assessment_code": "ASSIGNMENT",
        "assessment_name": "Assignment",
        "total_max_marks": 10.0,
        "components": [],
        "description": "Assignment Submission (10 Marks)",
    },
    {
        "assessment_code": "QUIZ",
        "assessment_name": "Quiz",
        "total_max_marks": 10.0,
        "components": [],
        "description": "Class Quiz (10 Marks)",
    },
    {
        "assessment_code": "LAB_INTERNAL",
        "assessment_name": "Lab Internal",
        "total_max_marks": 70.0,
        "components": [],
        "description": "Laboratory Internal Evaluation (70 Marks)",
    },
    {
        "assessment_code": "PRACTICAL_EXAM",
        "assessment_name": "Practical Exam",
        "total_max_marks": 50.0,
        "components": [],
        "description": "Practical Examination (50 Marks)",
    },
    {
        "assessment_code": "VIVA",
        "assessment_name": "Viva Voce",
        "total_max_marks": 10.0,
        "components": [],
        "description": "Oral / Viva Evaluation (10 Marks)",
    },
]


class AssessmentTemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_template_by_id(self, template_id: str) -> AssessmentTemplate:
        result = await self.db.execute(
            select(AssessmentTemplate).where(AssessmentTemplate.id == template_id)
        )
        tmpl = result.scalar_one_or_none()
        if not tmpl:
            raise NotFoundError(f"Assessment template '{template_id}' not found.")
        return tmpl

    async def get_template_for_subject(
        self, subject_id: Optional[str], assessment_code: str,
    ) -> AssessmentTemplate:
        """Find subject-specific template first, fallback to global default template."""
        # Try subject-specific template
        if subject_id:
            query = select(AssessmentTemplate).where(
                AssessmentTemplate.subject_id == subject_id,
                AssessmentTemplate.assessment_code == assessment_code.upper(),
            )
            tmpl = (await self.db.execute(query)).scalar_one_or_none()
            if tmpl:
                return tmpl

        # Try global template (subject_id IS NULL)
        query = select(AssessmentTemplate).where(
            AssessmentTemplate.subject_id.is_(None),
            AssessmentTemplate.assessment_code == assessment_code.upper(),
        )
        tmpl = (await self.db.execute(query)).scalar_one_or_none()
        if tmpl:
            return tmpl

        # Seed fallback if default match exists
        default_def = next((d for d in DEFAULT_TEMPLATES if d["assessment_code"] == assessment_code.upper()), None)
        if default_def:
            tmpl = AssessmentTemplate(
                subject_id=subject_id,
                assessment_code=default_def["assessment_code"],
                assessment_name=default_def["assessment_name"],
                total_max_marks=default_def["total_max_marks"],
                components_json=default_def["components"],
                description=default_def["description"],
            )
            self.db.add(tmpl)
            await self.db.flush()
            return tmpl

        # Construct generic fallback template
        tmpl = AssessmentTemplate(
            subject_id=subject_id,
            assessment_code=assessment_code.upper(),
            assessment_name=assessment_code.replace("_", " ").title(),
            total_max_marks=30.0,
            components_json=[],
            description="Generic Assessment Template",
        )
        self.db.add(tmpl)
        await self.db.flush()
        return tmpl

    async def list_templates(
        self, subject_id: Optional[str] = None,
    ) -> List[AssessmentTemplate]:
        query = select(AssessmentTemplate)
        if subject_id:
            query = query.where(
                (AssessmentTemplate.subject_id == subject_id) | (AssessmentTemplate.subject_id.is_(None))
            )
        query = query.order_by(AssessmentTemplate.assessment_name)
        results = (await self.db.execute(query)).scalars().all()
        return list(results)

    async def create_template(
        self, data: AssessmentTemplateCreate,
    ) -> AssessmentTemplate:
        # Check existing
        query = select(AssessmentTemplate).where(
            AssessmentTemplate.assessment_code == data.assessment_code.upper(),
        )
        if data.subject_id:
            query = query.where(AssessmentTemplate.subject_id == data.subject_id)
        else:
            query = query.where(AssessmentTemplate.subject_id.is_(None))

        existing = (await self.db.execute(query)).scalar_one_or_none()
        if existing:
            raise ValidationError(
                f"Template for assessment code '{data.assessment_code}' already exists."
            )

        tmpl = AssessmentTemplate(
            subject_id=data.subject_id,
            assessment_code=data.assessment_code.upper(),
            assessment_name=data.assessment_name,
            total_max_marks=data.total_max_marks,
            components_json=[c.model_dump() for c in data.components],
            description=data.description,
        )
        self.db.add(tmpl)
        await self.db.flush()
        return tmpl

    async def update_template(
        self, template_id: str, data: AssessmentTemplateUpdate,
    ) -> AssessmentTemplate:
        tmpl = await self.get_template_by_id(template_id)
        if data.assessment_name is not None:
            tmpl.assessment_name = data.assessment_name
        if data.total_max_marks is not None:
            tmpl.total_max_marks = data.total_max_marks
        if data.components is not None:
            tmpl.components_json = [c.model_dump() for c in data.components]
        if data.description is not None:
            tmpl.description = data.description

        await self.db.flush()
        return tmpl
