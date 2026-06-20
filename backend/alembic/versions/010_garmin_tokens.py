"""store garmin oauth session tokens

Revision ID: 010
Revises: 009

After a successful login (including MFA), we persist the garth OAuth tokens
so subsequent syncs reuse them without re-authentication.
"""
from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('garmin_tokens_enc', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'garmin_tokens_enc')
