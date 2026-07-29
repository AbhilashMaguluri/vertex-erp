"""office import module

Creates:
  - import_batches
  - import_batch_records
Adds:
  - users.username (unique, nullable) — the roll number / short staff handle
    that Office Import provisions and that login accepts alongside the email.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-07-26 21:00:00.000000+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('username', sa.String(64), nullable=True))
    # Unique but nullable: every account predating Office Import keeps a NULL
    # username, and Postgres does not consider two NULLs equal.
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    op.create_table(
        'import_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('stored_path', sa.String(500), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.String(30), server_default='ANALYZED', nullable=False),
        sa.Column(
            'imported_by_user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('detection_json', postgresql.JSONB(), nullable=True),
        sa.Column('configuration_json', postgresql.JSONB(), nullable=True),
        sa.Column('summary_json', postgresql.JSONB(), nullable=True),
        sa.Column('credentials_json', postgresql.JSONB(), nullable=True),
        sa.Column('credentials_purged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_rows', sa.Integer(), server_default='0', nullable=False),
        sa.Column('students_detected', sa.Integer(), server_default='0', nullable=False),
        sa.Column('counsellors_detected', sa.Integer(), server_default='0', nullable=False),
        sa.Column('students_created', sa.Integer(), server_default='0', nullable=False),
        sa.Column('students_skipped', sa.Integer(), server_default='0', nullable=False),
        sa.Column('counsellors_created', sa.Integer(), server_default='0', nullable=False),
        sa.Column('counsellors_reused', sa.Integer(), server_default='0', nullable=False),
        sa.Column('assignments_created', sa.Integer(), server_default='0', nullable=False),
        sa.Column('failed_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('warning_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_import_batches_status', 'import_batches', ['status'])
    op.create_index('ix_import_batches_imported_by_user_id', 'import_batches', ['imported_by_user_id'])

    op.create_table(
        'import_batch_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'batch_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('import_batches.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('record_type', sa.String(20), nullable=False),
        sa.Column('identifier', sa.String(120), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('source_row_number', sa.Integer(), nullable=True),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_import_batch_records_batch_id', 'import_batch_records', ['batch_id'])
    op.create_index('ix_import_batch_records_record_type', 'import_batch_records', ['record_type'])
    op.create_index('ix_import_batch_records_identifier', 'import_batch_records', ['identifier'])
    op.create_index('ix_import_batch_records_status', 'import_batch_records', ['status'])


def downgrade() -> None:
    op.drop_index('ix_import_batch_records_status', table_name='import_batch_records')
    op.drop_index('ix_import_batch_records_identifier', table_name='import_batch_records')
    op.drop_index('ix_import_batch_records_record_type', table_name='import_batch_records')
    op.drop_index('ix_import_batch_records_batch_id', table_name='import_batch_records')
    op.drop_table('import_batch_records')

    op.drop_index('ix_import_batches_imported_by_user_id', table_name='import_batches')
    op.drop_index('ix_import_batches_status', table_name='import_batches')
    op.drop_table('import_batches')

    op.drop_index('ix_users_username', table_name='users')
    op.drop_column('users', 'username')
