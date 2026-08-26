from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Attempt to connect to primary DATABASE_URL, fallback to SQLite if paused/unreachable
try:
    if settings.DATABASE_URL.startswith("sqlite"):
        engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(settings.DATABASE_URL)
        # Test DB connection
        with engine.connect() as conn:
            pass
except Exception as e:
    print(f"\n[Warning]: Could not connect to primary DATABASE_URL ({e}).")
    print("[Fallback]: Falling back to local SQLite database (sql_app.db) for development.\n")
    engine = create_engine("sqlite:///./sql_app.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
