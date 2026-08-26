from pydantic import BaseModel
from typing import List, Optional


class UserOut(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    student_class: int
    avatar_index: int
    weak_subjects: List[str]
    daily_goal_minutes: int
    streak_days: int
    stream: Optional[str] = None

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    avatar_index: Optional[int] = None
    student_class: Optional[int] = None
    weak_subjects: Optional[List[str]] = None
    daily_goal_minutes: Optional[int] = None
    stream: Optional[str] = None


class UserSettingsUpdate(BaseModel):
    dark_mode: Optional[bool] = None
    language: Optional[str] = None
    buddy_tone: Optional[str] = None
    daily_goal_minutes: Optional[int] = None
    daily_reminder_on: Optional[bool] = None
    reminder_time: Optional[str] = None
    streak_alert_on: Optional[bool] = None
