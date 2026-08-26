import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.db.database import engine, SessionLocal
from app.models.user import User

def main():
    print(f"Connecting to: {os.getenv('DATABASE_URL', 'not set')[:50]}...")
    try:
        with engine.connect() as conn:
            if engine.url.drivername == "sqlite":
                version = conn.execute(text("SELECT sqlite_version();")).scalar()
            else:
                version = conn.execute(text("SELECT version();")).scalar()
        print("Connected successfully.")
        print(f"DB version: {version}")

        db = SessionLocal()
        try:
            count = db.query(User).count()
            print(f"Users table reachable — {count} user(s) currently.")
        finally:
            db.close()

    except Exception as e:
        print(f"Connection FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
