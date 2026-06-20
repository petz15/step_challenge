"""add health_metrics table

Revision ID: 006
Revises: 005
"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'health_metrics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('metric_type', sa.String(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('source', sa.String(), nullable=False, server_default='garmin_api'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_health_metrics_user_date', 'health_metrics', ['user_id', 'date'])
    op.create_unique_constraint(
        'uq_health_metrics_user_date_type',
        'health_metrics',
        ['user_id', 'date', 'metric_type'],
    )


def downgrade() -> None:
    op.drop_table('health_metrics')
