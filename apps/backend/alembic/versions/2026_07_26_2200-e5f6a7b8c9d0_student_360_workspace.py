"""student 360 workspace — personal, health, extracurricular & ERP academic fields

Revision ID: e5f6a7b8c9d0
Revises: e4f5a6b7c8d9
Create Date: 2026-07-26 22:00:00.000000

Adds the profile fields the Student 360 workspace needs and that no earlier
revision created: mother tongue / self introduction, the support-areas
vocabulary, the structured skill lists, extracurricular participation, health
information, the permanent-address block, two extra coding profiles, and the
ERP-owned academic facts (admission type, ABC id, entrance ranks, scholarship,
credits required).

`programming_languages`, `technical_skills`, `soft_skills`, `hobbies` and
`interests` are NOT re-created here — revision d4f7b2e91c56 already created
them on student_profiles. They were missing from the ORM model, not from the
database; the fix for that is in profile_models.py.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'e4f5a6b7c8d9'
branch_labels = None
depends_on = None


# (column name, type) pairs — all nullable, all additive.
_NEW_COLUMNS = [
    # Personal
    ('mother_tongue', sa.String(60)),
    ('self_introduction', sa.Text()),
    ('support_areas', postgresql.JSONB()),
    ('support_areas_other', sa.String(255)),

    # Contact — current address gains a district; permanent address becomes a
    # block of its own instead of a single free-text field.
    ('district', sa.String(100)),
    ('permanent_city', sa.String(100)),
    ('permanent_district', sa.String(100)),
    ('permanent_state', sa.String(100)),
    ('permanent_pin_code', sa.String(12)),

    # Skills
    ('tools_technologies', postgresql.JSONB()),
    ('other_skills', postgresql.JSONB()),

    # Extracurricular
    ('extracurricular_activities', postgresql.JSONB()),
    ('extracurricular_other', sa.String(255)),
    ('extracurricular_achievements', sa.Text()),

    # Health
    ('medical_conditions', sa.Text()),
    ('allergies', sa.Text()),
    ('disability', sa.Text()),
    ('current_medications', sa.Text()),
    ('health_notes', sa.Text()),

    # Portfolio
    ('codeforces_url', sa.String(500)),
    ('other_coding_url', sa.String(500)),

    # ERP-owned academic record
    ('abc_id', sa.String(30)),
    ('admission_type', sa.String(30)),
    ('joining_year', sa.Integer()),
    ('academic_year', sa.String(20)),
    ('ssc_percentage', sa.Numeric(5, 2)),
    ('intermediate_percentage', sa.Numeric(5, 2)),
    ('eamcet_rank', sa.Integer()),
    ('jee_rank', sa.Integer()),
    ('scholarship_name', sa.String(150)),
    ('fee_reimbursement_status', sa.String(60)),
    ('total_credits_required', sa.Integer()),
]


def upgrade() -> None:
    for name, type_ in _NEW_COLUMNS:
        op.add_column('student_profiles', sa.Column(name, type_, nullable=True))

    # NOT NULL with a default: every existing row means "permanent address is
    # recorded separately", which is the safe reading of an unset flag.
    op.add_column(
        'student_profiles',
        sa.Column(
            'permanent_same_as_current',
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('student_profiles', 'permanent_same_as_current')
    for name, _ in reversed(_NEW_COLUMNS):
        op.drop_column('student_profiles', name)
