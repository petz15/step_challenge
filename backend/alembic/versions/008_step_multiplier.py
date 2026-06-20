"""add step_multiplier to conversion_rules

Revision ID: 008
Revises: 007
"""
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'conversion_rules',
        sa.Column('step_multiplier', sa.Float(), nullable=False, server_default='1.0'),
    )


def downgrade() -> None:
    op.drop_column('conversion_rules', 'step_multiplier')
