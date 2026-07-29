"""student self-service profile

Creates the student-owned side of the data model:

  student_profiles      1:1 with students — personal, family, contact, career,
                        skills, portfolio links, preferences
  student_internships   \
  student_interviews     >  student-maintained collections
  student_achievements  /
  student_documents     uploaded file metadata

and MOVES the family/address columns off `students` into `student_profiles`.
That move is the point of this migration: afterwards, `students` holds only
institution-owned facts and every student-writable field lives in a table the
student owns. The data is copied before the columns are dropped, so no
existing family detail is lost.

Also adds notifications.category so the notification centre can group by
Academic / Counselling / Attendance / Parent Communication / Placement /
System; existing rows are backfilled from their type.

Revision ID: d4f7b2e91c56
Revises: c8e2a1b46d03
Create Date: 2026-07-26 10:15:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4f7b2e91c56'
down_revision: Union[str, None] = 'c8e2a1b46d03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Columns moving from students -> student_profiles, as (source, destination).
_MOVED_COLUMNS = [
    ("father_name", "father_name"),
    ("father_phone", "father_phone"),
    ("father_email", "father_email"),
    ("mother_name", "mother_name"),
    ("mother_phone", "mother_phone"),
    ("mother_email", "mother_email"),
    ("guardian_name", "guardian_name"),
    ("guardian_phone", "guardian_phone"),
    ("guardian_email", "guardian_email"),
    ("guardian_relation", "guardian_relation"),
]


def upgrade() -> None:
    # ---------------- student_documents (referenced by the others) ----------
    op.create_table(
        'student_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(length=40), nullable=False, server_default='OTHER'),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=120), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('uploaded_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_student_documents_student_id', 'student_documents', ['student_id'])
    op.create_index('ix_student_documents_document_type', 'student_documents', ['document_type'])

    # ---------------- student_profiles ----------------
    op.create_table(
        'student_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, unique=True),

        sa.Column('preferred_name', sa.String(length=100), nullable=True),
        sa.Column('blood_group', sa.String(length=10), nullable=True),
        sa.Column('aadhaar_number', sa.String(length=20), nullable=True),
        sa.Column('nationality', sa.String(length=60), nullable=True),
        sa.Column('category', sa.String(length=40), nullable=True),
        sa.Column('religion', sa.String(length=60), nullable=True),
        sa.Column('languages_known', postgresql.JSONB(), nullable=True),

        sa.Column('father_name', sa.String(length=100), nullable=True),
        sa.Column('father_occupation', sa.String(length=100), nullable=True),
        sa.Column('father_qualification', sa.String(length=100), nullable=True),
        sa.Column('father_phone', sa.String(length=20), nullable=True),
        sa.Column('father_email', sa.String(length=255), nullable=True),
        sa.Column('mother_name', sa.String(length=100), nullable=True),
        sa.Column('mother_occupation', sa.String(length=100), nullable=True),
        sa.Column('mother_qualification', sa.String(length=100), nullable=True),
        sa.Column('mother_phone', sa.String(length=20), nullable=True),
        sa.Column('mother_email', sa.String(length=255), nullable=True),
        sa.Column('guardian_name', sa.String(length=100), nullable=True),
        sa.Column('guardian_relation', sa.String(length=50), nullable=True),
        sa.Column('guardian_phone', sa.String(length=20), nullable=True),
        sa.Column('guardian_email', sa.String(length=255), nullable=True),
        sa.Column('guardian_address', sa.Text(), nullable=True),
        sa.Column('annual_family_income', sa.Numeric(14, 2), nullable=True),

        sa.Column('mobile_number', sa.String(length=20), nullable=True),
        sa.Column('alternate_phone', sa.String(length=20), nullable=True),
        sa.Column('personal_email', sa.String(length=255), nullable=True),
        sa.Column('permanent_address', sa.Text(), nullable=True),
        sa.Column('current_address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('pin_code', sa.String(length=12), nullable=True),
        sa.Column('emergency_contact_name', sa.String(length=100), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(length=20), nullable=True),
        sa.Column('emergency_contact_relation', sa.String(length=50), nullable=True),

        sa.Column('career_goal', sa.Text(), nullable=True),
        sa.Column('higher_studies_goal', sa.Text(), nullable=True),
        sa.Column('dream_company', sa.String(length=150), nullable=True),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('weaknesses', sa.Text(), nullable=True),
        sa.Column('areas_to_improve', sa.Text(), nullable=True),

        sa.Column('technical_skills', postgresql.JSONB(), nullable=True),
        sa.Column('programming_languages', postgresql.JSONB(), nullable=True),
        sa.Column('soft_skills', postgresql.JSONB(), nullable=True),
        sa.Column('hobbies', postgresql.JSONB(), nullable=True),
        sa.Column('interests', postgresql.JSONB(), nullable=True),

        sa.Column('linkedin_url', sa.String(length=500), nullable=True),
        sa.Column('github_url', sa.String(length=500), nullable=True),
        sa.Column('portfolio_url', sa.String(length=500), nullable=True),
        sa.Column('leetcode_url', sa.String(length=500), nullable=True),
        sa.Column('codechef_url', sa.String(length=500), nullable=True),
        sa.Column('hackerrank_url', sa.String(length=500), nullable=True),
        sa.Column('resume_url', sa.String(length=500), nullable=True),

        sa.Column('notification_preferences', postgresql.JSONB(), nullable=True),
        sa.Column('share_contact_with_counsellor', sa.Boolean(), nullable=False, server_default=sa.true()),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_student_profiles_student_id', 'student_profiles', ['student_id'])

    # ---------------- move family data across, then drop the old columns ----
    # One profile row per existing student, carrying the family details over.
    src = ", ".join(s for s, _ in _MOVED_COLUMNS)
    dst = ", ".join(d for _, d in _MOVED_COLUMNS)
    op.execute(
        f"""
        INSERT INTO student_profiles (id, student_id, {dst}, share_contact_with_counsellor, created_at)
        SELECT gen_random_uuid(), s.id, {src}, true, now()
        FROM students s
        """
    )
    for source, _ in _MOVED_COLUMNS:
        op.drop_column('students', source)
    # Dead columns: declared on the model but never read or written anywhere
    # in the codebase. Their replacements are permanent_address /
    # current_address and emergency_contact_name/phone on student_profiles.
    op.drop_column('students', 'address')
    op.drop_column('students', 'emergency_contact')

    # ---------------- collections ----------------
    op.create_table(
        'student_internships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company', sa.String(length=150), nullable=False),
        sa.Column('role', sa.String(length=150), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('duration', sa.String(length=60), nullable=True),
        sa.Column('stipend', sa.Numeric(12, 2), nullable=True),
        sa.Column('technologies', postgresql.JSONB(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='COMPLETED'),
        sa.Column('certificate_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('student_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_student_internships_student_id', 'student_internships', ['student_id'])

    op.create_table(
        'student_interviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company', sa.String(length=150), nullable=False),
        sa.Column('role', sa.String(length=150), nullable=False),
        sa.Column('interview_date', sa.Date(), nullable=True),
        sa.Column('interview_type', sa.String(length=40), nullable=True),
        sa.Column('round_name', sa.String(length=100), nullable=True),
        sa.Column('result', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('package_offered', sa.Numeric(12, 2), nullable=True),
        sa.Column('counsellor_observation', sa.Text(), nullable=True),
        sa.Column('counsellor_observed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('counsellor_observed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('offer_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('student_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_student_interviews_student_id', 'student_interviews', ['student_id'])
    op.create_index('ix_student_interviews_interview_date', 'student_interviews', ['interview_date'])
    op.create_index('ix_student_interviews_result', 'student_interviews', ['result'])

    op.create_table(
        'student_achievements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(length=40), nullable=False, server_default='OTHER'),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('issuer', sa.String(length=150), nullable=True),
        sa.Column('achieved_on', sa.Date(), nullable=True),
        sa.Column('position', sa.String(length=100), nullable=True),
        sa.Column('credential_url', sa.String(length=500), nullable=True),
        sa.Column('proof_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('student_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_student_achievements_student_id', 'student_achievements', ['student_id'])
    op.create_index('ix_student_achievements_category', 'student_achievements', ['category'])

    # ---------------- notification categories ----------------
    op.add_column('notifications', sa.Column('category', sa.String(length=40), nullable=False, server_default='SYSTEM'))
    op.create_index('ix_notifications_category', 'notifications', ['category'])
    op.execute(
        """
        UPDATE notifications SET category = CASE type
            WHEN 'ATTENDANCE_ALERT'    THEN 'ATTENDANCE'
            WHEN 'FOLLOW_UP_REMINDER'  THEN 'COUNSELLING'
            WHEN 'SESSION_CREATED'     THEN 'COUNSELLING'
            WHEN 'PARENT_MEETING'      THEN 'PARENT_COMMUNICATION'
            WHEN 'MARKS_PUBLISHED'     THEN 'ACADEMIC'
            WHEN 'INTERVIEW_REMINDER'  THEN 'PLACEMENT'
            ELSE 'SYSTEM'
        END
        """
    )


def downgrade() -> None:
    op.drop_index('ix_notifications_category', table_name='notifications')
    op.drop_column('notifications', 'category')

    op.drop_table('student_achievements')
    op.drop_table('student_interviews')
    op.drop_table('student_internships')

    # Restore the columns on students and copy the family data back before the
    # profile table (the only remaining copy) is dropped.
    op.add_column('students', sa.Column('emergency_contact', sa.String(length=20), nullable=True))
    op.add_column('students', sa.Column('address', sa.Text(), nullable=True))
    for source, _ in _MOVED_COLUMNS:
        length = 255 if source.endswith('email') else (20 if source.endswith('phone') else (50 if source.endswith('relation') else 100))
        op.add_column('students', sa.Column(source, sa.String(length=length), nullable=True))

    assignments = ", ".join(f"{s} = p.{d}" for s, d in _MOVED_COLUMNS)
    op.execute(
        f"""
        UPDATE students s SET {assignments}
        FROM student_profiles p
        WHERE p.student_id = s.id
        """
    )

    op.drop_table('student_profiles')
    op.drop_table('student_documents')
