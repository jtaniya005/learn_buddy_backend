from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    # Firebase UID
    id = Column(String, primary_key=True, index=True)

    # Core identity — one of email or phone will be set depending on
    # how the student signed up (password / Google / phone OTP).
    name = Column(String, nullable=False, default="Student")
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=True)

    # Set at registration, editable later from Settings / Edit profile
    student_class = Column(Integer, nullable=False, default=10)  # 10 or 12
    avatar_index = Column(Integer, nullable=False, default=0)
    weak_subjects = Column(JSON, nullable=False, default=list)
    daily_goal_minutes = Column(Integer, nullable=False, default=30)
    stream = Column(String, nullable=True)

    # Settings screen
    dark_mode = Column(Boolean, nullable=False, default=False)
    language = Column(String, nullable=False, default="en")  # 'en' | 'hi'
    buddy_tone = Column(String, nullable=False, default="friendly")  # friendly | strict | motivational
    daily_reminder_on = Column(Boolean, nullable=False, default=True)
    reminder_time = Column(String, nullable=False, default="19:00")
    streak_alert_on = Column(Boolean, nullable=False, default=True)

    # Maintained by the (future) progress module, exposed here for quick reads
    streak_days = Column(Integer, nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
