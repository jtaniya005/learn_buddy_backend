import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = "Learn Buddy API"
    API_V1_STR: str = "/api/v1"

    # Database (Supabase Postgres)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

    # Supabase credentials (for storage — avatars, future content uploads)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")  # Use service_role key for admin actions
    SUPABASE_BUCKET: str = os.getenv("SUPABASE_BUCKET", "avatars")

    # Firebase (Google sign-in ID token verification)
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-service-account.json")

    # AI — unused until the AI module starts, safe to leave blank
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

    # OCR Config
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "")

settings = Settings()
