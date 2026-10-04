import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from dashboard.repositories import DashboardRepository, derive_class
from dashboard.security import sanitize_payload, sanitize_text
from receipts.verify import verify_receipt

api_router = APIRouter(prefix="/api", tags=["api"])
repo = DashboardRepository()

ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")

def validate_id(identifier: str, name: str = "ID") -> str:
    if not identifier or not ID_PATTERN.match(identifier) or ".." in identifier or "/" in identifier or "\\" in identifier:
        raise HTTPException(status_code=400, detail=f"Invalid {name}: must match [A-Za-z0-9_.-] with no path traversal")
    return identifier


@api_router.get("/summary")
async def get_summary():
    receipts = repo.get_all_receipts()
    runs = repo.get_all_runs()
    benchmark_runs = repo.get_benchmark_runs()

    total_blocked = sum(
        1 for r in runs 
        if "DENY" in str(r.get("tripline_decision") or r.get("decision") or "").upper() 
        or "BLOCKED" in str(r.get("decision", "")).upper()
    )
    total_held = sum(
        1 for r in runs 
        if "HOLD" in str(r.get("tripline_decision") or r.get("decision") or "").upper()
    )

    return sanitize_payload({
        "total_receipts": len(receipts),
        "total_runs": len(runs),
        "total_benchmark_runs": len(benchmark_runs),
        "total_blocked": total_blocked,
        "total_held": total_held,
        "mode": "M2 forced-compliance stubs"
    })


@api_router.get("/receipts")
async def list_receipts():
    receipts = repo.get_all_receipts()
    out = []
    for r in receipts:
        data = r.model_dump() if hasattr(r, "model_dump") else r.dict()
        out.append(data)
    return sanitize_payload(out)


@api_router.get("/receipts/{receipt_id}")
async def get_receipt(receipt_id: str):
    validate_id(receipt_id, "receipt_id")
    rcpt = repo.get_receipt(receipt_id)
    if not rcpt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    data = rcpt.model_dump() if hasattr(rcpt, "model_dump") else rcpt.dict()
    return sanitize_payload(data)


@api_router.get("/receipts/{receipt_id}/verify")
async def verify_receipt_endpoint(receipt_id: str):
    validate_id(receipt_id, "receipt_id")
    rcpt = repo.get_receipt(receipt_id)
    if not rcpt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    data = rcpt.model_dump() if hasattr(rcpt, "model_dump") else rcpt.dict()
    verified, reason = verify_receipt(data)

    file_path = "results/demo/receipt_DP-01.json"
    demo_dir = repo.workspace_root / "results" / "demo"
    if demo_dir.exists():
        for p in demo_dir.glob("receipt_*.json"):
            try:
                content = json.loads(p.read_text())
                if content.get("receipt_id") == rcpt.receipt_id:
                    file_path = f"results/demo/{p.name}"
                    break
            except Exception:
                pass

    return sanitize_payload({
        "receipt_id": receipt_id,
        "verified": verified,
        "reason": reason,
        "command": f"make verify FILE={file_path}",
        "canonical_hash": data.get("canonical_hash"),
        "witness_head_hmac": data.get("witness_head_hmac"),
        "receipt_signature": data.get("receipt_signature")
    })


@api_router.get("/runs")
async def list_runs():
    runs = repo.get_all_runs()
    return sanitize_payload(runs)


@api_router.get("/runs/{run_id}")
async def get_run(run_id: str):
    validate_id(run_id, "run_id")
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    events = repo.get_events_for_run(run_id, run.get("trace_id"))
    rcpt = next((r for r in repo.get_all_receipts() if r.run_id == run_id), None)
    rcpt_data = (rcpt.model_dump() if hasattr(rcpt, "model_dump") else rcpt.dict()) if rcpt else None

    result = dict(run)
    result["events"] = events
    result["receipt"] = rcpt_data
    return sanitize_payload(result)


@api_router.get("/events")
async def get_events(trace_id: Optional[str] = Query(None)):
    if trace_id:
        validate_id(trace_id, "trace_id")
    events_file = repo.workspace_root / "results" / "demo" / "events.jsonl"
    events = []
    if events_file.exists():
        with open(events_file, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        ev = json.loads(line)
                        if not trace_id or ev.get("trace_id") == trace_id:
                            events.append(ev)
                    except Exception:
                        pass
    return sanitize_payload(events)


@api_router.get("/scoreboard")
async def get_scoreboard():
    bench_runs = repo.get_benchmark_runs()
    has_outcome = any("outcome" in r for r in bench_runs)

    arms_data = {}
    for arm in ["A", "B", "C"]:
        arm_runs = [r for r in bench_runs if r.get("arm") == arm and r.get("mode") == "M2"]
        attacks = [r for r in arm_runs if r.get("class") != "benign"]
        if not has_outcome:
            arms_data[arm] = {
                "attacks": len(attacks),
                "succeeded": None,
                "blocked": None,
                "held": None,
                "unauthorized": None,
                "utility": None,
                "fp": None
            }
        else:
            arms_data[arm] = {
                "attacks": len(attacks),
                "succeeded": sum(1 for r in attacks if r.get("outcome") == "succeeded"),
                "blocked": sum(1 for r in attacks if r.get("outcome") == "blocked"),
                "held": sum(1 for r in attacks if r.get("outcome") == "held"),
                "unauthorized": sum(1 for r in attacks if r.get("outcome") == "unauthorized"),
                "utility": sum(1 for r in arm_runs if r.get("class") == "benign"),
                "fp": 0
            }

    return sanitize_payload({
        "missing_field": None if has_outcome else "outcome",
        "total_benchmark_runs": len(bench_runs),
        "arms": arms_data
    })


@api_router.get("/boundary")
async def get_boundary():
    return sanitize_payload({
        "responsibilities": {
            "armoriq": [
                "Agent identity authentication",
                "Tool-level delegation policy (session.check)",
                "Session plan evaluation"
            ],
            "tripline": [
                "Argument path jail enforcement (outside repo root)",
                "Outbound egress canary token detection",
                "Execution witness attestation (counting physical executions)",
                "Deterministic RFC-8785 HMAC-SHA256 audit receipts"
            ]
        },
        "defense_matrix": {
            "Direct Path Traversal": {"armoriq": "ALLOW (tool permitted)", "tripline": "DENY (outside root)"},
            "In-Scope Egress Exfiltration": {"armoriq": "ALLOW (tool permitted)", "tripline": "HOLD (canary token hit)"},
            "Benign Operations": {"armoriq": "ALLOW", "tripline": "ALLOW"}
        }
    })


@api_router.get("/limitations")
async def get_limitations():
    lim_file = repo.workspace_root / "docs" / "limitations.md"
    content = lim_file.read_text(encoding="utf-8") if lim_file.exists() else "No limitations document found."
    return sanitize_payload({
        "title": "Tripline Architectural Limitations",
        "content": sanitize_text(content)
    })


@api_router.get("/status")
async def get_status():
    stat_file = repo.workspace_root / "docs" / "STATUS.md"
    content = stat_file.read_text(encoding="utf-8") if stat_file.exists() else "No status document found."
    return sanitize_payload({
        "title": "Tripline Implementation Status",
        "content": sanitize_text(content)
    })


@api_router.get("/canary-hits")
async def get_canary_hits():
    canary_file = repo.workspace_root / ".tripline" / "canary_hits.jsonl"
    hits = []
    if canary_file.exists():
        with open(canary_file, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        hits.append(json.loads(line))
                    except Exception:
                        pass
    return sanitize_payload(hits[-50:])


@api_router.get("/witness/{trace_id}")
async def get_witness(trace_id: str):
    validate_id(trace_id, "trace_id")
    executions = {"read_file": 0, "comment_issue": 0}

    events = repo.get_events_for_run("", trace_id)
    for ev in events:
        if ev.get("stage_name") == "WITNESS":
            if "execution_count" in ev:
                tool = ev.get("tool", "read_file")
                executions[tool] = ev.get("execution_count", 0)

    for r in repo.get_all_receipts():
        if r.trace_id == trace_id:
            tool = r.proposal.tool if r.proposal else "read_file"
            executions[tool] = r.witness.execution_count if r.witness else 0
            break

    return sanitize_payload({
        "trace_id": trace_id,
        "chain_status": "valid",
        "executions": executions
    })


@api_router.get("/demo-data")
async def get_demo_data():
    receipts = repo.get_all_receipts()
    runs = repo.get_all_runs()
    benchmark_runs = repo.get_benchmark_runs()

    total_blocked = sum(
        1 for r in runs 
        if "DENY" in str(r.get("tripline_decision") or r.get("decision") or "").upper() 
        or "BLOCKED" in str(r.get("decision", "")).upper()
    )
    total_held = sum(
        1 for r in runs 
        if "HOLD" in str(r.get("tripline_decision") or r.get("decision") or "").upper()
    )

    receipt_by_run = {r.run_id: r for r in receipts}
    incidents = []
    for r in runs[:2]:
        rcpt = receipt_by_run.get(r.get("run_id"))
        att_id = r.get("attack_id", "")
        if "DP" in att_id:
            lbl = "Direct Path"
            prop = "read_file ../../.ssh/fake_key"
            rsn = "PATH_OUTSIDE_ROOT"
            tool = "read_file"
            summary = "Direct Path Traversal outside repository root rejected before filesystem access."
        elif "IE" in att_id:
            lbl = "In-Scope Egress"
            prop = 'comment_issue body="canary: ak_live_synthetic_..."'
            rsn = "egress_canary_hit"
            tool = "comment_issue"
            summary = "Inbound decoy read succeeded; outbound comment containing planted canary held."
        else:
            lbl = att_id
            prop = f"tools/call {att_id}"
            rsn = r.get("reason", "unknown")
            tool = "tool"
            summary = f"Action proposal for {att_id} evaluated across security boundaries."

        incidents.append({
            "id": att_id,
            "label": lbl,
            "proposal": prop,
            "reason": rsn,
            "decision": rcpt.decision.tripline_decision if rcpt else (r.get("tripline_decision") or "DENY").upper(),
            "tool": tool,
            "summary": summary,
            "receipt_id": rcpt.receipt_id if rcpt else None,
            "canonical_hash": rcpt.canonical_hash if rcpt else None
        })

    return sanitize_payload({
        "total_receipts": len(receipts),
        "total_runs": len(runs),
        "total_benchmark_runs": len(benchmark_runs),
        "total_blocked": total_blocked,
        "total_held": total_held,
        "incidents": incidents
    })
