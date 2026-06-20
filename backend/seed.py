#!/usr/bin/env python3
"""Seed the database with default data. Run with --reset to drop and recreate all tables."""
import sys
from database import SessionLocal
import models
from auth import hash_password

DEFAULT_USERS = [
    {"email": "peter@stepchallenge.local", "name": "Peter", "password": "peter123",
     "weekly_goal": 70000, "monthly_goal": 280000},
    {"email": "anine@stepchallenge.local", "name": "Anine", "password": "anine123",
     "weekly_goal": 70000, "monthly_goal": 280000},
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

        print("\nDatabase seeded successfully!")
        print("\nLogin credentials:")
        for u in DEFAULT_USERS:
            print(f"  {u['name']}: {u['email']} / {u['password']}")

    finally:
        db.close()


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    seed(reset=reset)
