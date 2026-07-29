import pytest
from app.features.students.profile_schemas import (
    StudentSelfProfileResponse,
    ReadOnlyAcademicIdentity,
    ProfileCompletion,
    CertificationCreate,
    SkillCreate,
)


def test_academic_identity_schema():
    identity = ReadOnlyAcademicIdentity(
        student_id="123e4567-e89b-12d3-a456-426614174000",
        roll_number="210101",
        registration_number="REG2021001",
        full_name="John Doe",
        college_email="john@college.edu",
        department_name="Computer Science & Engineering",
        batch_year=2025,
        status="ACTIVE",
        risk_level="NONE",
    )
    assert identity.roll_number == "210101"
    assert identity.department_name == "Computer Science & Engineering"


def test_certification_schema():
    cert = CertificationCreate(
        name="AWS Certified Solutions Architect",
        issuing_organization="Amazon Web Services",
    )
    assert cert.name == "AWS Certified Solutions Architect"
    assert cert.issuing_organization == "Amazon Web Services"


def test_skill_schema():
    skill = SkillCreate(
        skill_name="Python",
        skill_type="TECHNICAL",
        proficiency_level="ADVANCED",
    )
    assert skill.skill_name == "Python"
    assert skill.proficiency_level == "ADVANCED"
