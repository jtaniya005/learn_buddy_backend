import firebase_admin
from firebase_admin import credentials
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import engine, Base, SessionLocal
from app.models.user import User

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api._not_yet_built import router as stub_router
from app.api.students import router as students_router

from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.error_handler import register_error_handlers

# Create tables that don't exist yet. Only ever ADDS tables — won't
# alter a column on an existing table if you change a model later.
# Use migrate_db.py for ad-hoc ALTER TABLE changes as the schema grows.
Base.metadata.create_all(bind=engine)

# Firebase Admin — used by /auth/google (ID token verification) and,
# later, push notifications. Safe to skip in local dev if the file
# doesn't exist yet; Google sign-in just won't work until it does.
try:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
except Exception:
    print("[warn] Firebase not initialized — check FIREBASE_CREDENTIALS_PATH")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend for Learn Buddy — personalized learning app for Class 10 & 12.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",  # Allow any localhost port for Flutter Web
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
register_error_handlers(app)

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(students_router, prefix=settings.API_V1_STR)
app.include_router(stub_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}
