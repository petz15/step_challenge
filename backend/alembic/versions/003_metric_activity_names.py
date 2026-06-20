"""rename activity types to metric units

Revision ID: 003
Revises: 002
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

_RENAMES = [
    ("Cycling, Easy (10 mph)",          "Cycling, Easy (16 km/h)"),
    ("Cycling, Moderate (12 mph)",      "Cycling, Moderate (19 km/h)"),
    ("Cycling, Vigorous (15 mph)",      "Cycling, Vigorous (24 km/h)"),
    ("Running, Easy (12 min/mile)",     "Running, Easy (8 km/h)"),
    ("Running, Moderate (10 min/mile)", "Running, Moderate (10 km/h)"),
    ("Running, Fast (8 min/mile)",      "Running, Fast (12 km/h)"),
    ("Walking, Slow (2 mph)",           "Walking, Slow (3 km/h)"),
    ("Walking, Fast (4 mph)",           "Walking, Fast (6 km/h)"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for old, new in _RENAMES:
        conn.execute(
            sa.text("UPDATE conversion_rules SET activity_type = :new WHERE activity_type = :old"),
            {"old": old, "new": new},
        )
        conn.execute(
            sa.text("UPDATE activities SET activity_type = :new WHERE activity_type = :old"),
            {"old": old, "new": new},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for old, new in _RENAMES:
        conn.execute(
            sa.text("UPDATE conversion_rules SET activity_type = :old WHERE activity_type = :new"),
            {"old": old, "new": new},
        )
        conn.execute(
            sa.text("UPDATE activities SET activity_type = :old WHERE activity_type = :new"),
            {"old": old, "new": new},
        )
