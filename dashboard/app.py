from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
from dashboard.routes import router

app = FastAPI(title="Tripline Dashboard")

workspace_root = Path(__file__).parent.parent
frontend_out = workspace_root / "tripline-frontend" / "out"

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

if frontend_out.exists():
    next_static = frontend_out / "_next"
    if next_static.exists():
        app.mount("/_next", StaticFiles(directory=str(next_static)), name="next_static")

# Serve public root icons from frontend_out
@app.get("/icon-light-32x32.png")
@app.get("/icon-dark-32x32.png")
@app.get("/icon.svg")
@app.get("/apple-icon.png")
async def get_icon(path: str = None):
    from fastapi import Request
    # Handled via individual route decorators
    pass

for icon_name in ["icon-light-32x32.png", "icon-dark-32x32.png", "icon.svg", "apple-icon.png"]:
    icon_file = frontend_out / icon_name
    if icon_file.exists():
        def make_endpoint(f):
            return lambda: FileResponse(str(f))
        app.add_api_route(f"/{icon_name}", make_endpoint(icon_file), methods=["GET"])

app.include_router(router)
