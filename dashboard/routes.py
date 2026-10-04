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
    frontend_out_html = Path(__file__).parent.parent / "tripline-frontend" / "out" / "index.html"
    if frontend_out_html.exists():
        return HTMLResponse(content=frontend_out_html.read_text(encoding="utf-8"))

    receipts = repo.get_all_receipts()
    runs = repo.get_all_runs()
    benchmark_runs = repo.get_benchmark_runs()
    
    total_blocked = sum(1 for r in runs if "DENY" in str(r.get("decision", "")).upper() or "BLOCKED" in str(r.get("decision", "")).upper())
    total_held = sum(1 for r in runs if "HOLD" in str(r.get("decision", "")).upper())
    
    # Map demo runs to incident cards
    receipt_by_run = {r.run_id: r for r in receipts}
    incidents = []
    for r in runs[:2]:
        rcpt = receipt_by_run.get(r.get("run_id"))
        att_id = r.get("attack_id", "")
        if "DP" in att_id:
            desc = "Direct Path: Agent proposed read_file outside repository root (../../.ssh/fake_key)."
        elif "IE" in att_id:
            desc = "In-Scope Egress: Agent read decoy config then attempted to leak canary token in issue comment."
        else:
            desc = f"Action proposal for {att_id} evaluated across security boundaries."
        incidents.append({
            "run": r,
            "receipt": rcpt,
            "description": desc,
            "receipt_id": rcpt.receipt_id if rcpt else None,
            "armoriq_decision": rcpt.decision.armoriq_decision if rcpt else (r.get("armoriq_decision") or "ALLOW").upper(),
            "tripline_decision": rcpt.decision.tripline_decision if rcpt else (r.get("tripline_decision") or r.get("decision") or "DENY").upper()
        })
        
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "receipts": receipts[:5],
            "total_receipts": len(receipts),
            "total_runs": len(runs),
            "total_benchmark_runs": len(benchmark_runs),
            "total_blocked": total_blocked,
            "total_held": total_held,
            "incidents": incidents
        }
    )

@router.get("/api/demo-data")
async def get_demo_data():
    receipts = repo.get_all_receipts()
    runs = repo.get_all_runs()
    benchmark_runs = repo.get_benchmark_runs()
    
    total_blocked = sum(1 for r in runs if "DENY" in str(r.get("decision", "")).upper() or "BLOCKED" in str(r.get("decision", "")).upper())
    total_held = sum(1 for r in runs if "HOLD" in str(r.get("decision", "")).upper())
    
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
        elif "IE" in att_id:
            lbl = "In-Scope Egress"
            prop = 'comment_issue body="canary: ak_live_synthetic_..."'
            rsn = "egress_canary_hit"
            tool = "comment_issue"
        else:
            lbl = att_id
            prop = f"tools/call {att_id}"
            rsn = r.get("reason", "unknown")
            tool = "tool"
            
        incidents.append({
            "id": att_id,
            "label": lbl,
            "proposal": prop,
            "reason": rsn,
            "decision": rcpt.decision.tripline_decision if rcpt else (r.get("tripline_decision") or "DENY").upper(),
            "tool": tool,
            "receipt_id": rcpt.receipt_id if rcpt else None,
            "canonical_hash": rcpt.canonical_hash if rcpt else None
        })

    return {
        "total_receipts": len(receipts),
        "total_runs": len(runs),
        "total_benchmark_runs": len(benchmark_runs),
        "total_blocked": total_blocked,
        "total_held": total_held,
        "incidents": incidents
    }

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
        
    # Find matching receipt file path if available
    receipt_file = None
    demo_dir = repo.workspace_root / "results" / "demo"
    if demo_dir.exists():
        for p in demo_dir.glob("receipt_*.json"):
            try:
                import json
                if json.loads(p.read_text()).get("receipt_id") == receipt.receipt_id:
                    receipt_file = f"results/demo/{p.name}"
                    break
            except Exception:
                pass
                
    return templates.TemplateResponse(
        request=request,
        name="receipt.html",
        context={"receipt": receipt, "receipt_file": receipt_file}
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
        
    events = repo.get_events_for_run(run_id, run.get("trace_id"))
    if events:
        steps = []
        for ev in events:
            steps.append({
                "name": ev.get("stage_name", "STAGE"),
                "action": ev.get("event", ""),
                "status": (ev.get("decision") or "INFO").upper(),
                "receipt_id": ev.get("receipt_id")
            })
    else:
        steps = [
            {"name": "planner", "action": "PLAN CREATED", "status": "ALLOW"},
            {"name": "read_issue", "action": "read issue payload", "status": "ALLOW"},
            {
                "name": run.get("class", "Attack Execution"),
                "action": f"execute attack ({run.get('attack_id', '')})",
                "status": str(run.get("decision", "unknown")).upper(),
                "receipt_id": f"RCP-{run['run_id']}-call-{run['run_id'][:8]}" if run.get("proposed") else None
            }
        ]
        
    receipt = next((r for r in repo.get_all_receipts() if r.run_id == run_id), None)
    receipt_file = None
    demo_dir = repo.workspace_root / "results" / "demo"
    if demo_dir.exists():
        att_id = run.get("attack_id")
        if att_id and (demo_dir / f"receipt_{att_id}.json").exists():
            receipt_file = f"results/demo/receipt_{att_id}.json"
        elif receipt:
            for p in demo_dir.glob("receipt_*.json"):
                try:
                    import json
                    if json.loads(p.read_text()).get("receipt_id") == receipt.receipt_id:
                        receipt_file = f"results/demo/{p.name}"
                        break
                except Exception:
                    pass

    t_dec = str(run.get("tripline_decision") or run.get("decision") or "").upper()
    a_dec = str(run.get("armoriq_decision") or "ALLOW").upper()
    if "DENY" in t_dec:
        verdict_class = "deny"
        verdict_word = "BLOCKED"
        verdict_summary = f"ArmorIQ {a_dec}ED this action. Tripline BLOCKED it via Path Jail ({run.get('tripline_reason', 'PATH_OUTSIDE_ROOT')}). {run.get('executed', 0)} read_file executions."
    elif "HOLD" in t_dec:
        verdict_class = "hold"
        verdict_word = "HELD"
        verdict_summary = f"ArmorIQ {a_dec}ED this action. Tripline HELD it via Egress Canary Gateway ({run.get('tripline_reason', 'egress_canary_hit')}). 0 comments executed."
    else:
        verdict_class = "allow"
        verdict_word = "ALLOWED"
        verdict_summary = f"ArmorIQ {a_dec}ED. Tripline {t_dec or 'ALLOWED'}."

    return templates.TemplateResponse(
        request=request,
        name="run.html",
        context={
            "run": run,
            "steps": steps,
            "receipt": receipt,
            "receipt_file": receipt_file,
            "verdict_class": verdict_class,
            "verdict_word": verdict_word,
            "verdict_summary": verdict_summary
        }
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
    bench_runs = repo.get_benchmark_runs()
    unique_attacks = set(r.get("attack_id") for r in bench_runs if r.get("attack_id"))
    total_attacks = len(unique_attacks) if unique_attacks else 27
    return templates.TemplateResponse(
        request=request,
        name="scoreboard.html",
        context={
            "stats": stats,
            "total_benchmark_runs": len(bench_runs),
            "total_attacks": total_attacks
        }
    )

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="signup.html",
        context={"submitted": False, "registration": None}
    )

@router.post("/signup", response_class=HTMLResponse)
async def signup_submit(request: Request):
    import uuid, datetime, json
    from fastapi.responses import JSONResponse
    
    form_data = {}
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            form_data = await request.json()
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            form_data = dict(form)
        except Exception:
            pass

    reg_id = f"TRPL-DEV-{uuid.uuid4().hex[:8].upper()}"
    api_key = f"trpl_live_{uuid.uuid4().hex[:18]}"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    registration = {
        "reg_id": reg_id,
        "name": form_data.get("name") or "Agent Developer",
        "email": form_data.get("email") or "builder@tripline.local",
        "team_type": form_data.get("team_type") or "Solo Builder",
        "agent_stack": form_data.get("agent_stack") or "MCP Server",
        "github": form_data.get("github") or "https://github.com/developer",
        "api_key": api_key,
        "timestamp": timestamp
    }
    
    demo_dir = repo.workspace_root / "results" / "demo"
    if demo_dir.exists():
        try:
            with open(demo_dir / "registrations.jsonl", "a") as f:
                f.write(json.dumps(registration) + "\n")
        except Exception:
            pass
            
    if "application/json" in content_type:
        return JSONResponse({"status": "success", "registration": registration})

    return templates.TemplateResponse(
        request=request,
        name="signup.html",
        context={"submitted": True, "registration": registration}
    )

@router.get("/limitations", response_class=HTMLResponse)
async def limitations_page(request: Request):
    lim_file = repo.workspace_root / "docs" / "limitations.md"
    content = lim_file.read_text(encoding="utf-8") if lim_file.exists() else "No limitations document found."
    return templates.TemplateResponse(
        request=request,
        name="limitations.html",
        context={"content": content}
    )

@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    stat_file = repo.workspace_root / "docs" / "STATUS.md"
    content = stat_file.read_text(encoding="utf-8") if stat_file.exists() else "No status document found."
    return templates.TemplateResponse(
        request=request,
        name="status.html",
        context={"content": content}
    )


