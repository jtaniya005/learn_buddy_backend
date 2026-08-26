# Learn Buddy — Backend

FastAPI backend for the Learn Buddy app, structured to match your
other project (plain `Settings` class, `bcrypt` directly, SQLite
fallback in `db/database.py`, table creation in `main.py`). Uses
**Supabase Postgres** as the database.

**Auth and Profile/Settings are fully working** end-to-end. Every
other module from the SOW is stubbed (`501`) so the full API surface
is visible in `/docs` from day one.

## What's actually built

| Module | Status |
|---|---|
| Auth (register, login, Google, phone OTP, logout, refresh) | Working |
| Profile & Settings | Working |
| Study Material | Stub (`501`) |
| Progress & Analytics | Stub (`501`) |
| Career Guidance | Stub (`501`) |
| Notifications | Stub (`501`) |
| AI Mentor (Buddy) | Not started — see `app/services/ai/README.md` |

## How "unique ID per user" works

Every account — however the student signs up (email/password, Google,
or phone OTP) — gets one row in the `users` table with an integer
primary key (`id`). That ID is inside every JWT (`sub` claim), so on
every request `get_current_user` (in `app/dependencies/auth_deps.py`)
uses it to look up **that exact student's** row and return their
profile — class, avatar, weak subjects, streak, settings.

1. `POST /auth/register` (or `/auth/google`, `/auth/phone/verify-otp`)
   creates the `users` row, returns an access + refresh token.
2. App stores the access token, sends it as `Authorization: Bearer <token>`
   on every request after that.
3. `GET /user/profile` looks up the row by the ID inside that token
   and returns everything needed to personalize the Home screen.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Edit `.env`:
- `DATABASE_URL` — already filled in with your Supabase project's
  pooler host (`aws-1-ap-south-1.pooler.supabase.com`). Replace
  `[YOUR-PASSWORD]` with your actual database password (the one you
  set when creating the Supabase project, not your Supabase account
  password).
- `JWT_SECRET_KEY` — generate one with:
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```

If `DATABASE_URL` is ever unreachable (project paused, wrong
password, no internet), `app/db/database.py` automatically falls back
to a local `sql_app.db` SQLite file — so the app still runs for local
development even if Supabase is temporarily unavailable. You'll see a
warning printed when that happens.

### Create the tables and try it

```bash
python check_db.py     # confirms Supabase is reachable
python seed_data.py    # optional — adds demo@learnbuddy.app for quick testing
uvicorn app.main:app --reload
```

Tables are also created automatically on every app startup
(`Base.metadata.create_all` in `main.py`), so you don't strictly need
a separate migration step to get started. Use `migrate_db.py` later,
when you need to ALTER an existing table (add/rename a column) rather
than just create a new one.

Visit `http://localhost:8000/docs`. Try `POST /auth/login` with
`demo@learnbuddy.app` / `password123`, copy the `access_token`, click
"Authorize", paste it in, then call `GET /user/profile` — you'll get
that exact demo student back.

### Google Sign-In (optional for now)

`/auth/google` needs a Firebase service account JSON. Download one
from Firebase Console -> Project Settings -> Service Accounts, save it
as `firebase-service-account.json` in the project root, and point
`FIREBASE_CREDENTIALS_PATH` at it. Until you do this, every other
endpoint still works fine — the app just logs a warning on startup.

### Supabase Storage (optional for now)

`app/services/supabase_storage.py` is ready for avatar/content
uploads whenever you need them — set `SUPABASE_KEY` in `.env` to your
project's `service_role` key (Project Settings -> API) to enable it.

### Marksheet OCR Extraction

The marksheet extraction flow (`POST /students/me/marksheet/extract`) uses Tesseract OCR and OpenCV instead of a vision LLM. This avoids per-request API costs, but note that this approach is less forgiving than an LLM. It relies on exact text parsing, so reviewing the parsed subjects/marks before saving matters more.

**System Dependencies (Not installable via pip)**:
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`


## Project layout

```
app/
  core/
    config.py          plain Settings class, reads from .env
    security.py         (kept empty — hashing/JWT live in api/auth.py)
  constants/
    app_constants.py    shared fixed values (valid classes, buddy tones, ...)
  db/
    database.py         engine + SQLite fallback, SessionLocal, Base, get_db
    base.py              (kept empty, matching your other project)
  models/
    user.py              User + RefreshToken
  schemas/
    auth.py, user.py     Pydantic request/response models
  dependencies/
    auth_deps.py         get_current_user, get_current_user_optional
  middleware/
    logging.py            logs every request's method/path/status/duration
    error_handler.py      turns unhandled exceptions into clean JSON
  api/
    auth.py               built — register/login/google/phone-otp/refresh/logout
    users.py               built — profile/settings
    _not_yet_built.py       stubs for every other module
  services/
    otp_service.py          phone OTP (in-memory — swap for Redis + real SMS before prod)
    google_auth_service.py  Firebase ID token verification
    supabase_storage.py     file uploads (avatars etc.) — optional, disabled until SUPABASE_KEY is set
    ai/                      empty on purpose, see README.md inside
check_db.py          verify Supabase connectivity
migrate_db.py        create tables + a place to add ALTER TABLE patches
seed_data.py         seed one demo user for local testing
```

## Building the next module

Follow the same pattern as `auth.py`/`users.py`:
1. Add a SQLAlchemy model in `app/models/`, add it to `app/models/__init__.py`.
2. Add Pydantic schemas in `app/schemas/`.
3. Write the real endpoints in `app/api/<module>.py`.
4. Import and `include_router(...)` it in `app/main.py` (same pattern
   as `auth_router`/`users_router`).
5. Delete that module's block from `_not_yet_built.py`.
6. Restart the app — `create_all` picks up the new table automatically.

Suggested order (matches dependency order, not just the SOW list):
**Study Material -> Progress -> Career Guidance -> Notifications -> AI Mentor**
(Progress and AI both need Study Material's chapter IDs to exist first.)
