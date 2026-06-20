#!/usr/bin/env python3
"""Seed the database with default data. Run with --reset to drop and recreate all tables."""
import sys
import random
from datetime import date, timedelta
from database import engine, SessionLocal, Base
import models
from auth import hash_password

DEFAULT_CONVERSION_RULES = [
    {"activity_type": "Walking",      "conversion_per_minute": 1.0,  "conversion_per_km": 1250.0},
    {"activity_type": "Running",      "conversion_per_minute": 2.5,  "conversion_per_km": 1500.0},
    {"activity_type": "Hiking",       "conversion_per_minute": 50.0, "conversion_per_km": 2000.0},
    {"activity_type": "Cycling",      "conversion_per_minute": 30.0, "conversion_per_km": 500.0},
    {"activity_type": "Climbing",     "conversion_per_minute": 40.0, "conversion_per_km": 0.0},
    {"activity_type": "Strength",     "conversion_per_minute": 20.0, "conversion_per_km": 0.0},
    {"activity_type": "Manual Steps", "conversion_per_minute": 0.0,  "conversion_per_km": 0.0},
]

DEFAULT_USERS = [
    {"email": "peter@stepchallenge.local", "name": "Peter", "password": "peter123",
     "weekly_goal": 70000, "monthly_goal": 280000},
    {"email": "gf@stepchallenge.local", "name": "Anine", "password": "anine123",
     "weekly_goal": 70000, "monthly_goal": 280000},
]

SAMPLE_ACTIVITIES = [
    ("Walking", 45, None, None),
    ("Running", 30, None, None),
    ("Hiking", 90, None, None),
    ("Cycling", 60, None, None),
    ("Strength", 45, None, None),
    ("Walking", None, 5.0, None),
    ("Running", None, 8.0, None),
    ("Manual Steps", None, None, 8000),
]


def seed(reset: bool = False):
    if reset:
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("Recreating tables via Alembic...")
        from alembic.config import Config
        from alembic import command as alembic_cmd
        import os
        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
        alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "alembic"))
        alembic_cmd.upgrade(alembic_cfg, "head")

    db = SessionLocal()
    try:
        # Conversion rules
        existing_rules = db.query(models.ConversionRule).count()
        if existing_rules == 0:
            print("Seeding conversion rules...")
            for rule_data in DEFAULT_CONVERSION_RULES:
                db.add(models.ConversionRule(**rule_data, is_default=True))
            db.commit()

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
                    # 1-2 random activities per day
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
