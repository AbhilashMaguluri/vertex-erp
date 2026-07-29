"""section study year

Adds `sections.year` (1..4) — the study-year level (First..Fourth Year) that
the Academic Configuration hierarchy groups sections under. Nullable at the
DB level so existing rows don't need a backfill; the API requires it for all
newly created sections (see SectionCreate).

Revision ID: a7c4e8f92d1b
Revises: f3a9c7d21b44
Create Date: 2026-07-25 21:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a7c4e8f92d1b'
down_revision: Union[str, None] = 'f3a9c7d21b44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sections', sa.Column('year', sa.Integer(), nullable=True))
    op.create_check_constraint('ck_sections_year_range', 'sections', 'year IS NULL OR (year >= 1 AND year <= 4)')


def downgrade() -> None:
    op.drop_constraint('ck_sections_year_range', 'sections', type_='check')
    op.drop_column('sections', 'year')
