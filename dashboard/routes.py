"""
dashboard/routes.py — Server-rendered routes for minimal truthful dashboard.

Strictly displays real data from results/ and docs/evidence/.
No simulation, no stubs, no fake data.
Includes server-side cryptographic receipt verification and tamper demo.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from dashboard.repositories import DashboardRepository
from receipts.verify import verify_receipt

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
# Enforce Jinja2 HTML auto-escaping
templates.env.autoescape = True

repo = DashboardRepository()
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index_view(request: Request):
    run_data = repo.get_latest_phase3_run()
    context = {
        "request": request,
        "active_page": "latest",
        "has_run": run_data is not None,
        "run_id": run_data["run_id"] if run_data else "none",
        "source_file": run_data["source_file"] if run_data else "none",
        "records": run_data["records"] if run_data else [],
        "model": run_data.get("model") if run_data else "none",
        "rung": run_data.get("rung", 0) if run_data else 0,
        "timestamp": run_data.get("timestamp") if run_data else "none",
    }
    return templates.TemplateResponse(request=request, name="index.html", context=context)


@router.get("/attribution", response_class=HTMLResponse)
async def attribution_view(request: Request):
    burst_results = repo.get_burst_results()
    context = {
        "active_page": "attribution",
        "burst_results": burst_results,
    }
    return templates.TemplateResponse(request=request, name="attribution.html", context=context)


@router.get("/receipts", response_class=HTMLResponse)
async def receipts_list_view(request: Request):
    receipts = repo.get_phase3_receipts()
    context = {
        "active_page": "receipts",
        "receipts": receipts,
    }
    return templates.TemplateResponse(request=request, name="receipts.html", context=context)


@router.get("/receipts/{identifier}", response_class=HTMLResponse)
async def receipt_detail_view(request: Request, identifier: str):
    # Parameter path traversal prevention
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", identifier) or ".." in identifier or "/" in identifier or "\\" in identifier:
        raise HTTPException(status_code=400, detail="Invalid receipt filename format")

    if identifier.endswith(".json"):
        rcpt_info = repo.get_phase3_receipt(identifier)
        if not rcpt_info:
            raise HTTPException(status_code=404, detail="Receipt file not found")

        context = {
            "active_page": "receipts",
            "filename": identifier,
            "receipt": rcpt_info["data"],
            "receipt_json": rcpt_info["json_str"],
            "armoriq_ref": rcpt_info["armoriq_ref"],
            "sidecar_link_hash": rcpt_info["sidecar_link_hash"],
        }
        return templates.TemplateResponse(request=request, name="receipt_detail.html", context=context)
    else:
        # Lookup by receipt_id
        receipt = repo.get_receipt(identifier)
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")

        import json
        raw_json = json.dumps(receipt.model_dump() if hasattr(receipt, "model_dump") else receipt.dict(), indent=2)
        return templates.TemplateResponse(
            request=request,
            name="receipt.html",
            context={"receipt": receipt, "raw_json": raw_json, "active_page": "receipts"}
        )


@router.get("/runs/{run_id}", response_class=HTMLResponse)
async def run_view(request: Request, run_id: str):
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", run_id) or ".." in run_id:
        raise HTTPException(status_code=400, detail="Invalid run_id")
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    events = repo.get_events_for_run(run_id)
    receipt = repo.get_receipt(run_id)
    return templates.TemplateResponse(
        request=request,
        name="run.html",
        context={"run": run, "events": events, "receipt": receipt}
    )


@router.get("/boundary", response_class=HTMLResponse)
async def boundary_view(request: Request):
    return templates.TemplateResponse(request=request, name="boundary.html", context={"active_page": "boundary"})


@router.get("/scoreboard", response_class=HTMLResponse)
async def scoreboard_view(request: Request):
    stats = repo.get_scoreboard_data()
    return templates.TemplateResponse(request=request, name="scoreboard.html", context={"stats": stats})


@router.post("/api/receipts/{filename}/verify")
async def verify_receipt_endpoint(filename: str):
    if not re.match(r"^[a-zA-Z0-9_\-\.]+\.json$", filename) or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid receipt filename")

    rcpt_info = repo.get_phase3_receipt(filename)
    if not rcpt_info:
        raise HTTPException(status_code=404, detail="Receipt not found")

    is_valid, reason = verify_receipt(rcpt_info["data"])
    return {
        "filename": filename,
        "status": "VERIFIED" if is_valid else "TAMPER_DETECTED",
        "reason": reason,
        "canonical_hash": rcpt_info["data"].get("canonical_hash"),
        "receipt_signature": rcpt_info["data"].get("receipt_signature"),
    }


@router.post("/api/receipts/{filename}/verify-tampered")
async def verify_tampered_receipt_endpoint(filename: str):
    if not re.match(r"^[a-zA-Z0-9_\-\.]+\.json$", filename) or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid receipt filename")

    rcpt_info = repo.get_phase3_receipt(filename)
    if not rcpt_info:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Make in-memory copy and tamper one byte in a covered field without touching original file
    import copy
    tampered_data = copy.deepcopy(rcpt_info["data"])
    if "decision" in tampered_data and isinstance(tampered_data["decision"], dict):
        cur_dec = tampered_data["decision"].get("tripline_decision", "DENY")
        tampered_data["decision"]["tripline_decision"] = "ALLOW" if cur_dec != "ALLOW" else "DENY"

    is_valid, reason = verify_receipt(tampered_data)
    return {
        "filename": filename,
        "status": "VERIFIED" if is_valid else "TAMPER_DETECTED",
        "reason": reason,
        "tampered_field": "decision.tripline_decision",
        "expected_canonical_hash": rcpt_info["data"].get("canonical_hash"),
        "recomputed_hash": reason.split("got ")[-1].rstrip(")") if "got " in reason else "mismatch",
    }


@router.get("/measured", response_class=HTMLResponse)
async def measured_view(request: Request):
    context = {
        "active_page": "measured",
    }
    return templates.TemplateResponse(request=request, name="measured.html", context=context)


@router.get("/about", response_class=HTMLResponse)
async def about_view(request: Request):
    context = {
        "active_page": "about",
    }
    return templates.TemplateResponse(request=request, name="about.html", context=context)
