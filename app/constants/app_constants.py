"""
Central place for fixed values shared across models/schemas/services —
avoids magic numbers/strings scattered across the codebase.
"""

VALID_CLASSES = (10, 12)

AVATAR_COUNT = 8  # must match avatarOptions.length in the Flutter app

SUBJECT_NAMES = ("Mathematics", "Science", "Social Science", "English")

BUDDY_TONES = ("friendly", "strict", "motivational")

APP_LANGUAGES = ("en", "hi")

DEFAULT_DAILY_GOAL_MINUTES = 30
MIN_DAILY_GOAL_MINUTES = 10
MAX_DAILY_GOAL_MINUTES = 180
