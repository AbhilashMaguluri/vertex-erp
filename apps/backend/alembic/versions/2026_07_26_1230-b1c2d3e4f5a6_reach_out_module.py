"""reach out module tables

Creates:
  - counsellor_contact_profiles
  - schedule_exceptions
  - student_communication_privacies
  - appointment_requests
  - communication_timeline_logs
  - counsellor_favorite_students
  - communication_templates
  - institutional_channel_policies
  - campus_emergency_contacts

Revision ID: b1c2d3e4f5a6
Revises: d4f7b2e91c56
Create Date: 2026-07-26 12:30:00.000000+00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'd4f7b2e91c56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. counsellor_contact_profiles
    op.create_table(
        'counsellor_contact_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('counsellor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('photo_url', sa.String(500), nullable=True),
        sa.Column('designation', sa.String(100), server_default='Student Counsellor', nullable=False),
        sa.Column('department_name', sa.String(150), server_default='Artificial Intelligence & Data Science', nullable=False),
        sa.Column('years_experience', sa.Integer(), server_default='8', nullable=False),
        sa.Column('specializations', postgresql.JSONB(), nullable=True),
        sa.Column('languages_spoken', postgresql.JSONB(), nullable=True),
        sa.Column('about_me', sa.Text(), nullable=True),
        sa.Column('research_interests', sa.Text(), nullable=True),
        sa.Column('building', sa.String(100), server_default='Block B', nullable=False),
        sa.Column('floor', sa.String(50), server_default='3rd Floor', nullable=False),
        sa.Column('cabin_number', sa.String(50), server_default='Room 302', nullable=False),
        sa.Column('office_phone', sa.String(30), nullable=True),
        sa.Column('emergency_alternate_phone', sa.String(30), nullable=True),
        sa.Column('office_image_url', sa.String(500), nullable=True),
        sa.Column('maps_url', sa.String(1000), nullable=True),
        sa.Column('office_status', sa.String(30), server_default='AVAILABLE', nullable=False),
        sa.Column('status_message', sa.String(255), nullable=True),
        sa.Column('structured_schedule', postgresql.JSONB(), nullable=True),
        sa.Column('channel_preferences', postgresql.JSONB(), nullable=True),
        sa.Column('whatsapp_number', sa.String(50), nullable=True),
        sa.Column('linkedin_url', sa.String(500), nullable=True),
        sa.Column('teams_url', sa.String(500), nullable=True),
        sa.Column('google_meet_url', sa.String(500), nullable=True),
        sa.Column('zoom_url', sa.String(500), nullable=True),
        sa.Column('telegram_url', sa.String(500), nullable=True),
        sa.Column('college_email', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. schedule_exceptions
    op.create_table(
        'schedule_exceptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('counsellor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('exception_type', sa.String(40), server_default='SPECIAL_HOURS', nullable=False),
        sa.Column('title', sa.String(150), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('custom_hours', postgresql.JSONB(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 3. student_communication_privacies
    op.create_table(
        'student_communication_privacies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('share_phone', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('share_personal_email', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('share_linkedin', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('share_github', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('share_portfolio', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('share_leetcode', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('share_codechef', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('share_hackerrank', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('preferred_parent_contact', sa.String(30), server_default='FATHER', nullable=False),
        sa.Column('best_time_to_call', sa.String(100), nullable=True),
        sa.Column('preferred_language', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 4. appointment_requests
    op.create_table(
        'appointment_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('counsellor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('request_type', sa.String(50), server_default='APPOINTMENT', nullable=False),
        sa.Column('preferred_date', sa.Date(), nullable=False),
        sa.Column('preferred_time_slot', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(30), server_default='PENDING', nullable=False),
        sa.Column('rescheduled_date', sa.Date(), nullable=True),
        sa.Column('rescheduled_slot', sa.String(50), nullable=True),
        sa.Column('counsellor_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 5. communication_timeline_logs
    op.create_table(
        'communication_timeline_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('counsellor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(40), nullable=False),
        sa.Column('direction', sa.String(40), server_default='COUNSELLOR_TO_STUDENT', nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('sentiment', sa.String(30), server_default='POSITIVE', nullable=False),
        sa.Column('action_outcome', sa.String(50), server_default='RESOLVED', nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('follow_up_date', sa.Date(), nullable=True),
        sa.Column('attachments', postgresql.JSONB(), nullable=True),
        sa.Column('ai_summary', postgresql.JSONB(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 6. counsellor_favorite_students
    op.create_table(
        'counsellor_favorite_students',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('counsellor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('counsellor_id', 'student_id', name='uq_counsellor_favorite_student'),
    )

    # 7. communication_templates
    op.create_table(
        'communication_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(150), nullable=False),
        sa.Column('category', sa.String(50), server_default='GENERAL', nullable=False),
        sa.Column('channel', sa.String(40), server_default='WHATSAPP', nullable=False),
        sa.Column('subject_template', sa.String(255), nullable=True),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('is_system', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 8. institutional_channel_policies
    op.create_table(
        'institutional_channel_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('whatsapp_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('linkedin_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('telegram_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('teams_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('google_meet_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('zoom_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('phone_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('email_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 9. campus_emergency_contacts
    op.create_table(
        'campus_emergency_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('category', sa.String(50), server_default='GENERAL', nullable=False),
        sa.Column('phone', sa.String(30), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('location', sa.String(150), nullable=True),
        sa.Column('is_24_7', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('campus_emergency_contacts')
    op.drop_table('institutional_channel_policies')
    op.drop_table('communication_templates')
    op.drop_table('counsellor_favorite_students')
    op.drop_table('communication_timeline_logs')
    op.drop_table('appointment_requests')
    op.drop_table('student_communication_privacies')
    op.drop_table('schedule_exceptions')
    op.drop_table('counsellor_contact_profiles')
