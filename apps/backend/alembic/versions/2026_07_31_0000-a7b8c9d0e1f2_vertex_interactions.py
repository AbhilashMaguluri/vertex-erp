"""vertex agent interaction evaluations

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-31 00:00:00.000000

Creates vertex_interactions: one row per request handled by the Vertex agent,
holding the evaluation scorecard and stage timings for that request.

No foreign keys by design — telemetry must not block deletions elsewhere in
the schema, so user_id is a bare UUID column.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'vertex_interactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', sa.String(64), nullable=False),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mode', sa.String(30), nullable=False, server_default='guest'),

        sa.Column('user_message', sa.Text(), nullable=True),
        sa.Column('goal_type', sa.String(30), nullable=True),
        sa.Column('goal_target', sa.String(40), nullable=True),
        sa.Column('goal_statement', sa.String(300), nullable=True),
        sa.Column('intent_category', sa.String(40), nullable=True),
        sa.Column('intent_confidence', sa.Float(), nullable=False, server_default='0'),
        sa.Column('plan_action', sa.String(30), nullable=True),
        sa.Column('ownership_owner', sa.String(30), nullable=True),
        sa.Column('ownership_route', sa.String(40), nullable=True),
        sa.Column('tool_name', sa.String(60), nullable=True),
        sa.Column('tool_action', sa.String(60), nullable=True),

        sa.Column('goal_achieved', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('correct_tool_used', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('permission_validation_passed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('input_guardrails_passed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('output_guardrails_passed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('hallucination_risk', sa.Float(), nullable=False, server_default='0'),
        sa.Column('response_format_valid', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('execution_success', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('fallback_used', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('overall_score', sa.Float(), nullable=False, server_default='1'),

        sa.Column('tool_error', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=False, server_default='0'),
        sa.Column('response_length', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('eval_results', postgresql.JSONB(), nullable=True),
        sa.Column('timings', postgresql.JSONB(), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index('ix_vertex_interactions_request_id', 'vertex_interactions', ['request_id'])
    op.create_index('ix_vertex_interactions_session_id', 'vertex_interactions', ['session_id'])
    op.create_index('ix_vertex_interactions_user_id', 'vertex_interactions', ['user_id'])
    op.create_index('ix_vertex_interactions_mode', 'vertex_interactions', ['mode'])
    op.create_index('ix_vertex_interactions_goal_type', 'vertex_interactions', ['goal_type'])
    op.create_index('ix_vertex_interactions_intent_category', 'vertex_interactions', ['intent_category'])
    op.create_index('ix_vertex_interactions_plan_action', 'vertex_interactions', ['plan_action'])
    op.create_index('ix_vertex_interactions_tool_name', 'vertex_interactions', ['tool_name'])
    op.create_index('ix_vertex_interactions_overall_score', 'vertex_interactions', ['overall_score'])
    op.create_index('ix_vertex_interactions_created_at', 'vertex_interactions', ['created_at'])
    op.create_index(
        'ix_vertex_interactions_created_score',
        'vertex_interactions',
        ['created_at', 'overall_score'],
    )


def downgrade() -> None:
    op.drop_index('ix_vertex_interactions_created_score', table_name='vertex_interactions')
    op.drop_index('ix_vertex_interactions_created_at', table_name='vertex_interactions')
    op.drop_index('ix_vertex_interactions_overall_score', table_name='vertex_interactions')
    op.drop_index('ix_vertex_interactions_tool_name', table_name='vertex_interactions')
    op.drop_index('ix_vertex_interactions_plan_action', table_name='vertex_interactions')
    op.drop_index('ix_vertex_interactions_intent_category', table_name='vertex_interactions')
    op.drop_index('ix_vertex_interactions_goal_type', table_name='vertex_interactions')
    op.drop_index('ix_vertex_interactions_mode', table_name='vertex_interactions')
    op.drop_index('ix_vertex_interactions_user_id', table_name='vertex_interactions')
    op.drop_index('ix_vertex_interactions_session_id', table_name='vertex_interactions')
    op.drop_index('ix_vertex_interactions_request_id', table_name='vertex_interactions')
    op.drop_table('vertex_interactions')
