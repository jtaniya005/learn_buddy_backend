"""
Placeholder routes for every module in the SOW that isn't built yet.

Lets /docs show the full 37-endpoint API surface from day one (useful
for the Flutter side to start wiring against real paths), while making
it obvious in the code — and in a 501 response — exactly what's still
a stub.

As you build each module for real, delete its block here and give it
its own app/api/<module>.py, imported directly into main.py the same
way auth.py and users.py are. The AI module (chat/*) is intentionally
last — don't touch app/services/ai/ until you're ready for it.
"""
from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["Not built yet"])

NOT_BUILT = HTTPException(
    status.HTTP_501_NOT_IMPLEMENTED,
    "Not implemented yet — see app/api/_not_yet_built.py",
)

# --- Study Material ---
@router.get("/subjects")
def list_subjects():
    raise NOT_BUILT

@router.get("/subjects/{subject_id}/chapters")
def list_chapters(subject_id: str):
    raise NOT_BUILT

@router.get("/chapters/{chapter_id}")
def get_chapter(chapter_id: str):
    raise NOT_BUILT

@router.get("/chapters/{chapter_id}/topics")
def get_chapter_topics(chapter_id: str):
    raise NOT_BUILT


# --- Progress & Analytics ---
@router.get("/progress/summary")
def progress_summary():
    raise NOT_BUILT

@router.get("/progress/weekly-activity")
def progress_weekly_activity():
    raise NOT_BUILT

@router.get("/progress/subjects")
def progress_by_subject():
    raise NOT_BUILT

@router.get("/progress/weak-chapters")
def progress_weak_chapters():
    raise NOT_BUILT

@router.post("/progress/log-session")
def log_session():
    raise NOT_BUILT


# --- Career Guidance ---
@router.get("/careers")
def list_careers():
    raise NOT_BUILT

@router.get("/careers/{career_id}")
def get_career(career_id: str):
    raise NOT_BUILT

@router.get("/careers/{career_id}/roadmap")
def get_career_roadmap(career_id: str):
    raise NOT_BUILT

@router.get("/careers/{career_id}/skills")
def get_career_skills(career_id: str):
    raise NOT_BUILT

@router.get("/careers/{career_id}/exams")
def get_career_exams(career_id: str):
    raise NOT_BUILT

@router.post("/career-quiz/submit")
def submit_career_quiz():
    raise NOT_BUILT


# --- Notifications ---
@router.post("/notifications/register-device")
def register_device():
    raise NOT_BUILT

@router.put("/notifications/preferences")
def update_notification_prefs():
    raise NOT_BUILT


# --- AI Mentor (Buddy) — deliberately last. See app/services/ai/README.md ---
@router.post("/chat/message")
def send_message():
    raise NOT_BUILT

@router.get("/chat/history")
def chat_history():
    raise NOT_BUILT

@router.get("/chat/daily-checkin")
def daily_checkin():
    raise NOT_BUILT

@router.post("/chat/checkin-response")
def checkin_response():
    raise NOT_BUILT

@router.put("/chat/language")
def set_chat_language():
    raise NOT_BUILT
