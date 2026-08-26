"""
Seeds one demo student so you can hit POST /auth/login immediately
from /docs without going through registration first.

Usage:
    python seed_data.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.db.database import engine, Base, SessionLocal
from app.models.user import User
from app.api.auth import get_password_hash

Base.metadata.create_all(bind=engine)

DEMO_EMAIL = "demo@learnbuddy.app"
DEMO_PASSWORD = "password123"


def main():
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == DEMO_EMAIL).first():
            print(f"Demo user already exists: {DEMO_EMAIL}")
            return

        demo_user = User(
            name="Aarav",
            email=DEMO_EMAIL,
            hashed_password=get_password_hash(DEMO_PASSWORD),
            student_class=10,
            avatar_index=0,
            weak_subjects=["Mathematics", "Science"],
            daily_goal_minutes=30,
            streak_days=12,
        )
        db.add(demo_user)
        db.commit()
        print(f"Created demo user: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
