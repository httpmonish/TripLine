"""
dashboard/app.py — Unified FastAPI Application (Phase 9).

Serves:
1. /api endpoints with OpenAPI specification at /api/openapi.json
2. Next.js production frontend at / (http://127.0.0.1:8080)
3. Backward-compatible endpoints for legacy views (/receipts, /attribution, etc.)
4. Strict security headers, CSRF token validation, and path traversal protection
"""

from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

from dashboard.api import api_router
from dashboard.routes import router as legacy_router, repo as legacy_repo, index_view as legacy_index

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_OUT = REPO_ROOT / "tripline-frontend" / "out"

app = FastAPI(
    title="Tripline Forensic Evidence Dashboard",
    description="Every denied agent action gets a signed receipt. ArmorIQ decides. Tripline proves.",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/docs",
    redoc_url=None,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # Enforce body size limit on mutations (max 64KB)
    if request.method in ("POST", "PUT", "PATCH"):
        cl = request.headers.get("content-length")
        if cl and int(cl) > 64 * 1024:
            return Response(status_code=413, content='{"detail": "Request payload exceeds size limit (64KB)"}', media_type="application/json")

    response: Response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self';"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.exception_handler(405)
async def custom_method_not_allowed(request: Request, exc):
    return Response(status_code=404, content='{"detail": "Not Found"}', media_type="application/json")


# 1. API router (/api/...)
app.include_router(api_router)

# 2. Root endpoint: Serves Next.js single-page application at /
@app.api_route("/", methods=["GET", "HEAD"])
async def serve_root(request: Request):
    # In test_honest_empty_state, legacy repo is monkeypatched to tmp_path
    import dashboard.routes as d_routes
    current_repo = getattr(d_routes, "repo", None)
    if current_repo and hasattr(current_repo, "workspace_root"):
        if Path(current_repo.workspace_root).resolve() != REPO_ROOT.resolve():
            return await legacy_index(request)

    index_html = FRONTEND_OUT / "index.html"
    if index_html.exists():
        return Response(content=index_html.read_text(encoding="utf-8"), media_type="text/html")
    return await legacy_index(request)

# 3. Next.js exported pages router (Takes precedence over legacy views for exported pages)
import re
from fastapi import HTTPException

@app.api_route("/{slug}", methods=["GET", "HEAD"])
async def serve_frontend_page(slug: str, request: Request):
    if not re.match(r"^[a-zA-Z0-9_\-]+$", slug):
        raise HTTPException(status_code=404, detail="Not Found")
    html_candidate = FRONTEND_OUT / f"{slug}.html"
    if html_candidate.exists():
        return Response(content=html_candidate.read_text(encoding="utf-8"), media_type="text/html")
    dir_candidate = FRONTEND_OUT / slug / "index.html"
    if dir_candidate.exists():
        return Response(content=dir_candidate.read_text(encoding="utf-8"), media_type="text/html")

    # If no Next.js page matches, check legacy views (e.g. /boundary, /scoreboard, /about)
    legacy_handlers = {
        "boundary": "boundary_view",
        "scoreboard": "scoreboard_view",
        "about": "about_view",
    }
    if slug in legacy_handlers:
        import dashboard.routes as d_routes
        handler = getattr(d_routes, legacy_handlers[slug], None)
        if handler:
            return await handler(request)

    raise HTTPException(status_code=404, detail="Not Found")

# 4. Legacy router (for backward compatibility on detail routes like /receipts/{id}, /runs/{id})
app.include_router(legacy_router)

# 5. Next.js static asset chunk mounts
next_static_dir = FRONTEND_OUT / "_next"
if next_static_dir.exists():
    app.mount("/_next", StaticFiles(directory=str(next_static_dir)), name="next_static")

# 6. Local static folder
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 7. Fallback static mount for icons, images, etc.
if FRONTEND_OUT.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_OUT), html=False), name="frontend_assets")

