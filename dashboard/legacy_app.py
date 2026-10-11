"""
dashboard/legacy_app.py — Legacy Jinja2 Evidence Viewer Application.

Preserved for historical reference and backward compatibility on port 8081.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dashboard.routes import router as legacy_router

app = FastAPI(title="Tripline Legacy Evidence Viewer")
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.include_router(legacy_router)
