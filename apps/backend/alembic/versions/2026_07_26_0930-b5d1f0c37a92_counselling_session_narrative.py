"""counselling session narrative fields

Splits the single free-text `observations` blob into the structured record a
counselling session actually produces:

  * `recommendations`      — what the counsellor advised
  * `student_commitments`  — what the student agreed to do
  * `confidential_notes`   — counsellor/admin-only narrative, NEVER serialised
                             into a student-facing response (see
                             CounsellingService._to_response)

All three are nullable so the existing session rows remain valid without a
backfill; `observations` stays required and unchanged.

Revision ID: b5d1f0c37a92
Revises: a7c4e8f92d1b
Create Date: 2026-07-26 09:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b5d1f0c37a92'
down_revision: Union[str, None] = 'a7c4e8f92d1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('counselling_sessions', sa.Column('recommendations', sa.Text(), nullable=True))
    op.add_column('counselling_sessions', sa.Column('student_commitments', sa.Text(), nullable=True))
    op.add_column('counselling_sessions', sa.Column('confidential_notes', sa.Text(), nullable=True))

    # The caseload list and the Student 360 counselling tab both sort a single
    # student's sessions newest-first; the plain student_id index alone leaves
    # that as a sort on every read.
    op.create_index(
        'ix_counselling_sessions_student_id_session_date',
        'counselling_sessions',
        ['student_id', sa.text('session_date DESC')],
    )


def downgrade() -> None:
    op.drop_index('ix_counselling_sessions_student_id_session_date', table_name='counselling_sessions')
    op.drop_column('counselling_sessions', 'confidential_notes')
    op.drop_column('counselling_sessions', 'student_commitments')
    op.drop_column('counselling_sessions', 'recommendations')
