"""student gender & photo

Adds the two Student attributes the counsellor dashboard and the Assigned
Students table need and that had no column yet:

  * `gender`    — powers the dashboard's gender distribution tiles; also part
                  of the student-maintained Personal Information module.
  * `photo_url` — the avatar shown in the caseload table and the 360 header.
                  Stores a path/URL only; upload handling is not part of this
                  change, so it stays NULL until a file pipeline is added.

Both nullable — existing rows predate them and both are student-maintained.

Revision ID: c8e2a1b46d03
Revises: b5d1f0c37a92
Create Date: 2026-07-26 09:45:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c8e2a1b46d03'
down_revision: Union[str, None] = 'b5d1f0c37a92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('students', sa.Column('gender', sa.String(length=20), nullable=True))
    op.add_column('students', sa.Column('photo_url', sa.String(length=500), nullable=True))
    op.create_index('ix_students_gender', 'students', ['gender'])
    op.create_check_constraint(
        'ck_students_gender',
        'students',
        "gender IS NULL OR gender IN ('MALE', 'FEMALE', 'OTHER')",
    )


def downgrade() -> None:
    op.drop_constraint('ck_students_gender', 'students', type_='check')
    op.drop_index('ix_students_gender', table_name='students')
    op.drop_column('students', 'photo_url')
    op.drop_column('students', 'gender')
