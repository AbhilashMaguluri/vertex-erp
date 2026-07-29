"""fixed semester catalog

Semesters stop being a per-academic-year, admin-creatable entity and become
a fixed, institution-wide catalog of 8 rows (1-1 .. 4-2) that every batch
reuses year after year. This migration:

  - relaxes semesters.academic_year_id / start_date / end_date to nullable
    (a fixed semester isn't scoped to one calendar year or a concrete date
    range the way the old per-year model assumed)
  - re-points the academic_year_id FK at ON DELETE SET NULL instead of
    CASCADE, since deleting an academic year must no longer delete the
    shared semester catalog
  - adds a uniqueness constraint on `number` (1..8), since there is now
    exactly one row per program semester
  - seeds the 8 fixed rows

Revision ID: f3a9c7d21b44
Revises: e9ecd609fe81
Create Date: 2026-07-25 20:45:00.000000+00:00

"""
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f3a9c7d21b44'
down_revision: Union[str, None] = 'e9ecd609fe81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FIXED_SEMESTERS = [
    (1, "1-1"), (2, "1-2"),
    (3, "2-1"), (4, "2-2"),
    (5, "3-1"), (6, "3-2"),
    (7, "4-1"), (8, "4-2"),
]


def upgrade() -> None:
    op.alter_column('semesters', 'academic_year_id', existing_type=sa.UUID(), nullable=True)
    op.alter_column('semesters', 'start_date', existing_type=sa.Date(), nullable=True)
    op.alter_column('semesters', 'end_date', existing_type=sa.Date(), nullable=True)

    op.drop_constraint('semesters_academic_year_id_fkey', 'semesters', type_='foreignkey')
    op.create_foreign_key(
        None, 'semesters', 'academic_years', ['academic_year_id'], ['id'], ondelete='SET NULL'
    )
    op.create_unique_constraint('uq_semesters_number', 'semesters', ['number'])

    semesters_table = sa.table(
        'semesters',
        sa.column('id', sa.UUID()),
        sa.column('academic_year_id', sa.UUID()),
        sa.column('number', sa.Integer()),
        sa.column('name', sa.String()),
        sa.column('start_date', sa.Date()),
        sa.column('end_date', sa.Date()),
        sa.column('is_current', sa.Boolean()),
        sa.column('version', sa.Integer()),
        sa.column('created_at', sa.DateTime(timezone=True)),
    )
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        semesters_table,
        [
            {
                "id": str(uuid.uuid4()),
                "academic_year_id": None,
                "number": number,
                "name": name,
                "start_date": None,
                "end_date": None,
                "is_current": False,
                "version": 1,
                "created_at": now,
            }
            for number, name in FIXED_SEMESTERS
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM semesters WHERE number BETWEEN 1 AND 8 AND academic_year_id IS NULL")

    op.drop_constraint('uq_semesters_number', 'semesters', type_='unique')
    op.drop_constraint('semesters_academic_year_id_fkey', 'semesters', type_='foreignkey')
    op.create_foreign_key(
        None, 'semesters', 'academic_years', ['academic_year_id'], ['id'], ondelete='CASCADE'
    )

    op.alter_column('semesters', 'end_date', existing_type=sa.Date(), nullable=False)
    op.alter_column('semesters', 'start_date', existing_type=sa.Date(), nullable=False)
    op.alter_column('semesters', 'academic_year_id', existing_type=sa.UUID(), nullable=False)
