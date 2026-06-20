"""fix Running Fast conversion_per_km from 1300 to 1400

Revision ID: 009
Revises: 008

Running Fast (12 km/h) at 278 steps/min: 278 * 60 / 12 = 1390 steps/km.
The seed value of 1300 was copy-pasted from the slower running variants.
"""
from alembic import op
import sqlalchemy as sa

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE conversion_rules
               SET conversion_per_km = 1400
             WHERE activity_type = 'Running, Fast (12 km/h)'
               AND conversion_per_km = 1300
        """)
    )
    # Recalculate any activities that used the distance-based path (no manual_steps)
    conn.execute(
        sa.text("""
            UPDATE activities
               SET step_equivalent_calculated = ROUND(distance_km * 1400)
             WHERE activity_type = 'Running, Fast (12 km/h)'
               AND manual_steps IS NULL
               AND distance_km IS NOT NULL
               AND distance_km > 0
        """)
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE conversion_rules
               SET conversion_per_km = 1300
             WHERE activity_type = 'Running, Fast (12 km/h)'
        """)
    )
