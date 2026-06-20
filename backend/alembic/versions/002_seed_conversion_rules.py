"""seed conversion rules

Revision ID: 002
Revises: 001
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

_RULES = [
    # Aerobics & Dance
    ("Aerobic Class",                   163.0,  0.0),
    ("Aerobic Dancing",                 127.0,  0.0),
    ("Aerobics, Low Impact",            125.0,  0.0),
    ("Aerobics, Step",                  153.0,  0.0),
    ("Ballet Dancing",                  120.0,  0.0),
    ("Dancing",                         121.0,  0.0),
    # Ball & Racket Sports
    ("Badminton, Recreational",         134.0,  0.0),
    ("Badminton, Competitive",          160.0,  0.0),
    ("Baseball",                        121.0,  0.0),
    ("Basketball, Recreational",        100.0,  0.0),
    ("Basketball, Game",                130.0,  0.0),
    ("Cricket",                          80.0,  0.0),
    ("Football",                        180.0,  0.0),
    ("Handball, Recreational",          130.0,  0.0),
    ("Handball, Competitive",           230.0,  0.0),
    ("Hockey",                          189.0,  0.0),
    ("Kickball",                        200.0,  0.0),
    ("Lacrosse",                        190.0,  0.0),
    ("Netball",                         170.0,  0.0),
    ("Racquetball, Casual",             143.0,  0.0),
    ("Racquetball, Competitive",        180.0,  0.0),
    ("Rugby",                           190.0,  0.0),
    ("Soccer, Recreational",            151.0,  0.0),
    ("Soccer, Competitive",             181.0,  0.0),
    ("Softball",                        152.0,  0.0),
    ("Squash",                          190.0,  0.0),
    ("Table Tennis",                    121.0,  0.0),
    ("Tennis",                          174.0,  0.0),
    ("Volleyball",                      110.0,  0.0),
    # Boxing & Martial Arts
    ("Boxing, Non-Competitive",         121.0,  0.0),
    ("Boxing, Competitive",             180.0,  0.0),
    ("Kickboxing",                      210.0,  0.0),
    ("Martial Arts",                    201.0,  0.0),
    ("Punching Bag",                    181.0,  0.0),
    ("Tae Bo",                          190.0,  0.0),
    ("Wrestling",                       170.0,  0.0),
    # Cycling
    ("Cycling, Easy (16 km/h)",          132.0,  500.0),
    ("Cycling, Moderate (19 km/h)",     174.0,  550.0),
    ("Cycling, Vigorous (24 km/h)",     211.0,  530.0),
    # Fitness Classes & Gym
    ("Calisthenics",                    106.0,  0.0),
    ("Cheerleading",                    100.0,  0.0),
    ("Circuit Training",                179.0,  0.0),
    ("Elliptical Trainer",              210.0,  0.0),
    ("Gymnastics",                      110.0,  0.0),
    ("Pilates",                          95.0,  0.0),
    ("Spinning",                        220.0,  0.0),
    ("Stair Climbing",                  135.0,  0.0),
    ("Stretching",                       76.0,  0.0),
    ("Trampoline",                       90.0,  0.0),
    ("Weight Lifting",                  117.0,  0.0),
    ("Yoga",                             67.0,  0.0),
    # Home & Yard
    ("Gardening",                        96.0,  0.0),
    ("Housework, Light",                 75.0,  0.0),
    ("Vacuuming",                        87.0,  0.0),
    ("Washing Car",                     100.0,  0.0),
    ("Yard Work",                       100.0,  0.0),
    # Jumping
    ("Jumping Rope, Moderate",          169.0,  0.0),
    ("Jumping Rope, Fast",              210.0,  0.0),
    # Leisure & Light Sports
    ("Billiards / Pool",                 77.0,  0.0),
    ("Bowling",                          87.0,  0.0),
    ("Fencing",                         152.0,  0.0),
    ("Frisbee",                          84.0,  0.0),
    ("Golf, Carrying Clubs",            116.0,  0.0),
    ("Golf, Powered Cart",               40.0,  0.0),
    ("Miniature Golf",                   91.0,  0.0),
    ("Skateboarding",                   102.0,  0.0),
    ("Skeeball",                         52.0,  0.0),
    ("Surfing",                         130.0,  0.0),
    ("Tai Chi",                          81.0,  0.0),
    # Manual Steps
    ("Manual Steps",                      0.0,  0.0),
    # Outdoor & Water Sports
    ("Canoeing",                         99.0,  0.0),
    ("Hiking",                          171.0,  2900.0),
    ("Horseback Riding",                120.0,  0.0),
    ("Kayaking",                        152.0,  1800.0),
    ("Rock Climbing",                   211.0,  0.0),
    ("Rowing",                          161.0,  1900.0),
    ("Sailing",                          91.0,  0.0),
    ("Swimming",                        196.0,  5900.0),
    ("Water Aerobics",                  105.0,  0.0),
    ("Water Polo",                      200.0,  0.0),
    ("Water Skiing",                    145.0,  0.0),
    # Running & Jogging
    ("Jogging",                         168.0,  1400.0),
    ("Running, Easy (8 km/h)",           178.0,  1300.0),
    ("Running, Moderate (10 km/h)",     222.0,  1300.0),
    ("Running, Fast (12 km/h)",         278.0,  1300.0),
    # Skating
    ("Ice Skating, Recreational",       144.0,  0.0),
    ("Ice Skating, Moderate",           122.0,  0.0),
    ("Rollerblading",                   173.0,  0.0),
    # Snow Sports
    ("Skiing, Downhill",                121.0,  0.0),
    ("Skiing, Cross-Country",           157.0,  0.0),
    ("Sledding",                        166.0,  0.0),
    ("Snow Shoveling",                  133.0,  0.0),
    ("Snowboarding",                    182.0,  0.0),
    ("Snowshoeing",                     180.0,  0.0),
    # Walking
    ("Walking, Slow (3 km/h)",            76.0,  1425.0),
    ("Walking, Moderate",                95.0,  1200.0),
    ("Walking, Fast (6 km/h)",          152.0,  1425.0),
    # Wheelchair
    ("Wheeling, Leisurely",              70.0,  0.0),
    ("Wheeling, Fast",                  137.0,  0.0),
]

# Original 7 built-in activity types that were replaced by the expanded list above.
_OLD_NAMES = (
    "Walking", "Running", "Hiking", "Cycling", "Climbing", "Strength", "Manual Steps",
)


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    # Remove old built-in rules whose names were replaced (Manual Steps is re-inserted below).
    conn.execute(
        sa.text("DELETE FROM conversion_rules WHERE activity_type = ANY(:names)"),
        {"names": list(_OLD_NAMES)},
    )

    # Insert new rules; skip any that the user already added with the same name.
    conn.execute(
        sa.text("""
            INSERT INTO conversion_rules
                (activity_type, conversion_per_minute, conversion_per_km, is_default, updated_at)
            VALUES
                (:activity_type, :conversion_per_minute, :conversion_per_km, TRUE, :updated_at)
            ON CONFLICT (activity_type) DO NOTHING
        """),
        [
            {
                "activity_type": name,
                "conversion_per_minute": per_min,
                "conversion_per_km": per_km,
                "updated_at": now,
            }
            for name, per_min, per_km in _RULES
        ],
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM conversion_rules WHERE is_default = TRUE"))
