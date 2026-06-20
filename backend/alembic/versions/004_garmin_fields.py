"""add garmin fields

Revision ID: 004
Revises: 003
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('garmin_email', sa.String(), nullable=True))
    op.add_column('users', sa.Column('garmin_password_enc', sa.Text(), nullable=True))
    op.add_column('activities', sa.Column('garmin_activity_id', sa.String(), nullable=True))
    op.create_index('ix_activities_garmin_activity_id', 'activities', ['garmin_activity_id'])


def downgrade() -> None:
    op.drop_index('ix_activities_garmin_activity_id', table_name='activities')
    op.drop_column('activities', 'garmin_activity_id')
    op.drop_column('users', 'garmin_password_enc')
    op.drop_column('users', 'garmin_email')
