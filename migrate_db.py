"""
Ad-hoc schema patches — run after changing a model, when create_all
(which only ADDS missing tables, never alters existing ones) isn't
enough. Add an ALTER TABLE block here each time you add/rename a
column on an existing table, matching the pattern below.

Usage:
    python migrate_db.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.db.database import engine, Base
import app.models  # noqa: F401 — registers all models on Base.metadata


def run_safe(conn, sql: str, description: str):
    try:
        conn.execute(text(sql))
        conn.commit()
        print(f"OK: {description}")
    except Exception as e:
        print(f"Skipped ({description}): {e}")


def main():
    print("Creating any missing tables...")
    Base.metadata.create_all(bind=engine)
    print(f"Tables tracked: {list(Base.metadata.tables.keys())}")

    # Example of the pattern to follow for future column additions —
    # commented out since nothing needs patching yet:
    #
    with engine.connect() as conn:
        run_safe(
            conn,
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS stream VARCHAR",
            "add users.stream",
        )

    print("Done.")


if __name__ == "__main__":
    main()
