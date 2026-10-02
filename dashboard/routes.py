from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from dashboard.repositories import DashboardRepository

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
repo = DashboardRepository()

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    receipts = repo.get_all_receipts()
    runs = repo.get_all_runs()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "receipts": receipts[:5],
            "total_receipts": len(receipts),
            "total_runs": len(runs)
        }
    )

@router.get("/receipts", response_class=HTMLResponse)
async def list_receipts(request: Request):
    receipts = repo.get_all_receipts()
    return templates.TemplateResponse(
        request=request,
        name="receipts.html",
        context={"receipts": receipts}
    )

@router.get("/receipts/{receipt_id}", response_class=HTMLResponse)
async def view_receipt(request: Request, receipt_id: str):
    receipt = repo.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return templates.TemplateResponse(
        request=request,
        name="receipt.html",
        context={"receipt": receipt}
    )

@router.get("/runs", response_class=HTMLResponse)
async def list_runs(request: Request):
    runs = repo.get_all_runs()
    return templates.TemplateResponse(
        request=request,
        name="runs.html",
        context={"runs": runs}
    )

@router.get("/runs/{run_id}", response_class=HTMLResponse)
async def view_run(request: Request, run_id: str):
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    steps = [
        {"name": "planner", "action": "PLAN CREATED", "status": "ALLOW"},
        {"name": "read_issue", "action": "read issue payload", "status": "ALLOW"},
        {
            "name": run.get("class", "unknown"),
            "action": "execute attack vector",
            "status": run.get("decision", "unknown").upper(),
            "receipt_id": f"RCP-{run['run_id']}-call-{run['run_id'][:8]}" if run.get("proposed") else None
        }
    ]
        
    return templates.TemplateResponse(
        request=request,
        name="run.html",
        context={"run": run, "steps": steps}
    )

@router.get("/boundary", response_class=HTMLResponse)
async def view_boundary(request: Request):
    runs = repo.get_all_runs()
    matrix = {}
    for r in runs:
        if r.get("mode") != "M2":
            continue
        if r.get("class") == "benign":
            continue
            
        c = r.get("class", "unknown")
        if c not in matrix:
            matrix[c] = {"armoriq": False, "tripline": False, "neither": False}
            
        arm = r.get("arm")
        decision = (r.get("decision") or "").lower()
        if arm == "C":
            if decision == "hold" or "jail" in (r.get("reason") or "").lower() or "path" in (r.get("reason") or "").lower():
                matrix[c]["tripline"] = True
            elif decision == "denied":
                matrix[c]["armoriq"] = True
            elif decision == "allowed":
                matrix[c]["neither"] = True

    return templates.TemplateResponse(
        request=request,
        name="boundary.html",
        context={"matrix": matrix}
    )

@router.get("/scoreboard", response_class=HTMLResponse)
async def view_scoreboard(request: Request):
    stats = repo.get_scoreboard_data()
    return templates.TemplateResponse(
        request=request,
        name="scoreboard.html",
        context={"stats": stats}
    )
