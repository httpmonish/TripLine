"""
dashboard/app.py — Minimal Truthful FastAPI Application (Phase 4).

Enforces security headers, strictly read-only views, and local static assets.
"""

from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

from dashboard.api import api_router
from dashboard.routes import router

app = FastAPI(
    title="Tripline Evidence Dashboard",
    description="Minimal read-only viewer for real agent execution receipts and defense layers.",
    docs_url=None,   # Disable Swagger docs in production viewer
    redoc_url=None,  # Disable ReDoc in production viewer
)

# Security Headers Middleware (Section 5.4)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(api_router)
app.include_router(router)
