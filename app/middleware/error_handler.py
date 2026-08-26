"""
Turns unhandled exceptions into a consistent JSON shape instead of a
raw 500 with a stack trace leaking to the client. FastAPI's own
HTTPException handling (used everywhere in the endpoints) is untouched
— this only catches what falls through.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        print(f"[error] Unhandled exception on {request.url.path}: {exc!r}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Something went wrong. Please try again."},
        )
