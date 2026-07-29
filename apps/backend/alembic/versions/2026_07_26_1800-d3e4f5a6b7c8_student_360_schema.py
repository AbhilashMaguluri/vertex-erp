"""student 360 schema expansion

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-07-26 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd3e4f5a6b7c8'
down_revision = 'c2d3e4f5a6b7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to student_profiles
    op.add_column('student_profiles', sa.Column('hostel_type', sa.String(30), server_default='DAY_SCHOLAR', nullable=True))
    op.add_column('student_profiles', sa.Column('hostel_name', sa.String(100), nullable=True))
    op.add_column('student_profiles', sa.Column('hostel_block', sa.String(50), nullable=True))
    op.add_column('student_profiles', sa.Column('hostel_floor', sa.String(30), nullable=True))
    op.add_column('student_profiles', sa.Column('hostel_room_number', sa.String(30), nullable=True))
    op.add_column('student_profiles', sa.Column('preferred_communication_method', sa.String(50), server_default='WhatsApp', nullable=True))
    op.add_column('student_profiles', sa.Column('preferred_call_time', sa.String(100), server_default='Evening 5:00 PM - 7:00 PM', nullable=True))
    op.add_column('student_profiles', sa.Column('assigned_mentor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('student_profiles', sa.Column('faculty_advisor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('student_profiles', sa.Column('admission_number', sa.String(50), nullable=True))
    op.add_column('student_profiles', sa.Column('admission_date', sa.Date(), nullable=True))
    op.add_column('student_profiles', sa.Column('placement_status', sa.String(50), server_default='SEEKING', nullable=True))
    op.add_column('student_profiles', sa.Column('scholarship_status', sa.String(100), nullable=True))

    # Add columns to student_documents
    op.add_column('student_documents', sa.Column('storage_key', sa.String(500), nullable=True))
    op.add_column('student_documents', sa.Column('file_url', sa.String(1000), nullable=True))
    op.add_column('student_documents', sa.Column('version', sa.Integer(), server_default='1', nullable=False))
    op.add_column('student_documents', sa.Column('verification_status', sa.String(30), server_default='PENDING', nullable=False))
    op.add_column('student_documents', sa.Column('verified_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('student_documents', sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('student_documents', sa.Column('rejection_reason', sa.Text(), nullable=True))

    # Create relational tables
    op.create_table(
        'student_certifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('issuing_organization', sa.String(150), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('credential_id', sa.String(100), nullable=True),
        sa.Column('credential_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'student_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('skill_name', sa.String(100), nullable=False),
        sa.Column('skill_type', sa.String(40), server_default='TECHNICAL', nullable=False),
        sa.Column('proficiency_level', sa.String(30), server_default='INTERMEDIATE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'student_research_papers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('journal_conference_name', sa.String(200), nullable=False),
        sa.Column('publication_date', sa.Date(), nullable=True),
        sa.Column('doi_or_url', sa.String(500), nullable=True),
        sa.Column('authors_list', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(40), server_default='PUBLISHED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'student_competitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_name', sa.String(200), nullable=False),
        sa.Column('organizer', sa.String(150), nullable=True),
        sa.Column('event_date', sa.Date(), nullable=True),
        sa.Column('position_rank', sa.String(100), nullable=True),
        sa.Column('project_title', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'student_clubs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('club_name', sa.String(150), nullable=False),
        sa.Column('role', sa.String(80), server_default='MEMBER', nullable=False),
        sa.Column('joined_date', sa.Date(), nullable=True),
        sa.Column('active_status', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'student_assignment_histories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('change_type', sa.String(50), nullable=False),
        sa.Column('previous_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('changed_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'student_profile_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source', sa.String(30), server_default='STUDENT', nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('device_info', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('student_profile_audit_logs')
    op.drop_table('student_assignment_histories')
    op.drop_table('student_clubs')
    op.drop_table('student_competitions')
    op.drop_table('student_research_papers')
    op.drop_table('student_skills')
    op.drop_table('student_certifications')
