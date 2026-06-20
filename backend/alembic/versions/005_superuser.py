"""add superuser flag

Revision ID: 005
Revises: 004
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'))
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE users SET is_superuser = TRUE WHERE email = 'peter@stepchallenge.local'")
    )


def downgrade() -> None:
    op.drop_column('users', 'is_superuser')
