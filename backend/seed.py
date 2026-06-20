#!/usr/bin/env python3
"""Seed the database with default data. Run with --reset to drop and recreate all tables."""
import sys
import random
from datetime import date, timedelta
from database import SessionLocal
import models
from auth import hash_password

DEFAULT_USERS = [
    {"email": "peter@stepchallenge.local", "name": "Peter", "password": "peter123",
     "weekly_goal": 70000, "monthly_goal": 280000},
    {"email": "anine@stepchallenge.local", "name": "Anine", "password": "anine123",
     "weekly_goal": 70000, "monthly_goal": 280000},
]

SAMPLE_ACTIVITIES = [
    ("Walking, Moderate",              45,  None, None),
    ("Running, Moderate (10 min/mile)", 30,  None, None),
    ("Hiking",                          90,  None, None),
    ("Cycling, Easy (10 mph)",          60,  None, None),
    ("Weight Lifting",                  45,  None, None),
    ("Walking, Moderate",             None,   5.0, None),
    ("Running, Easy (12 min/mile)",   None,   8.0, None),
    ("Manual Steps",                  None,  None, 8000),
]


def seed(reset: bool = False):
    if reset:
        from alembic.config import Config
        from alembic import command as alembic_cmd
        from database import engine, Base
        import os
        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
        alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "alembic"))
        print("Resetting Alembic version stamp...")
        alembic_cmd.stamp(alembic_cfg, "base")
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("Recreating tables via Alembic...")
        alembic_cmd.upgrade(alembic_cfg, "head")

    db = SessionLocal()
    try:
        # Users
        existing_users = db.query(models.User).count()
        if existing_users == 0:
            print("Seeding users...")
            for u in DEFAULT_USERS:
                user = models.User(
                    email=u["email"],
                    name=u["name"],
                    password_hash=hash_password(u["password"]),
                    weekly_goal=u["weekly_goal"],
                    monthly_goal=u["monthly_goal"],
                )
                db.add(user)
            db.commit()

        # Sample activities (last 30 days)
        existing_activities = db.query(models.Activity).count()
        if existing_activities == 0:
            print("Seeding sample activities...")
            users = db.query(models.User).all()
            rules = {r.activity_type: r for r in db.query(models.ConversionRule).all()}
            today = date.today()

            for user in users:
                for i in range(30):
                    day = today - timedelta(days=i)
                    for _ in range(random.randint(1, 2)):
                        act_type, dur, dist, manual = random.choice(SAMPLE_ACTIVITIES)
                        rule = rules.get(act_type)
                        if manual:
                            steps = manual + random.randint(-500, 500)
                        elif dur and rule:
                            steps = int(round(dur * rule.conversion_per_minute * random.uniform(0.8, 1.2)))
                        elif dist and rule:
                            steps = int(round(dist * rule.conversion_per_km * random.uniform(0.8, 1.2)))
                        else:
                            steps = 0

                        db.add(models.Activity(
                            user_id=user.id,
                            activity_type=act_type,
                            duration_minutes=dur,
                            distance_km=dist,
                            manual_steps=manual,
                            step_equivalent_calculated=max(0, steps),
                            date=day,
                            source="manual",
                        ))
            db.commit()
            print(f"Seeded sample activities for {len(users)} users over 30 days")

        print("\nDatabase seeded successfully!")
        print("\nLogin credentials:")
        for u in DEFAULT_USERS:
            print(f"  {u['name']}: {u['email']} / {u['password']}")

    finally:
        db.close()


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    seed(reset=reset)
