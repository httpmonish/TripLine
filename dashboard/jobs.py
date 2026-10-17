"""
dashboard/jobs.py — Subprocess job runner with SSE streaming and security isolation.

Strictly allowlisted jobs only. Single-job concurrency control (409 Conflict).
Secret-redacted log persistence under results/ui_jobs/<id>/.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import os
import pathlib
import re
import sys
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from dashboard.security import sanitize_text

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
JOBS_DIR = REPO_ROOT / "results" / "ui_jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

JOB_KINDS: Dict[str, Dict[str, Any]] = {
    "scenario": {
        "live": False,  # default is offline rung 0
        "cost_estimate": "$0.00 (rung 0 deterministic)",
        "timeout": 60,
        "side_effects": "Generates scenario run log and receipts under results/phase3/scenario/",
        "cmd": [sys.executable, "scripts/run_phase3_scenario.py", "--rung", "0"],
    },
    "armoriq_proof": {
        "live": True,
        "cost_estimate": "$0.00 (platform quota)",
        "timeout": 30,
        "side_effects": "Queries ArmorIQ IAP token and policy enforcement",
        "cmd": [sys.executable, "scripts/armoriq_proof.py"],
    },
    "jail_burst": {
        "live": False,
        "cost_estimate": "$0.00",
        "timeout": 30,
        "side_effects": "Tests 8 path traversal probes against in-MCP path jail",
        "cmd": [sys.executable, "scripts/jail_burst.py"],
    },
    "verify_all": {
        "live": False,
        "cost_estimate": "$0.00",
        "timeout": 30,
        "side_effects": "Verifies all recorded receipts, witness chains, and sidecar links",
        "cmd": [sys.executable, "scripts/verify_links.py"],
    },
    "tamper_demo": {
        "live": False,
        "cost_estimate": "$0.00",
        "timeout": 30,
        "side_effects": "Runs cryptographic tamper detection on temp copies",
        "cmd": [sys.executable, "scripts/tamper_demo.py"],
    },
    "tests": {
        "live": False,
        "cost_estimate": "$0.00",
        "timeout": 60,
        "side_effects": "Executes repository test suite offline",
        "cmd": [sys.executable, "-m", "pytest", "tests/test_test_hygiene.py", "tests/test_phase4_dashboard.py", "-v"],
    },
    "audit": {
        "live": False,
        "cost_estimate": "$0.00",
        "timeout": 30,
        "side_effects": "Scans repository truth, forbidden wording, and secret hygiene",
        "cmd": [sys.executable, "scripts/repo_audit.py"],
    },
    "agent_v2": {
        "live": True,
        "cost_estimate": "$0.00 (Mode B local execution + session check)",
        "timeout": 120,
        "side_effects": "Executes 5-issue queue through Agent v2 pipeline, generating receipts under results/phase11/",
        "cmd": [sys.executable, "scripts/run_agent_v2.py", "--mode", "B"],
    },
    "rea_investigate": {
        "live": False,
        "cost_estimate": "$0.00 (offline deterministic)",
        "timeout": 90,
        "side_effects": "Executes controlled REA investigation against preapproved synthetic electron app",
        "cmd": [sys.executable, "scripts/rea_investigator.py", "--mode", "offline"],
    },
}


class JobRecord:
    def __init__(
        self,
        job_id: str,
        kind: str,
        params: Dict[str, Any],
        live: bool = False,
    ):
        self.job_id = job_id
        self.kind = kind
        self.params = params
        self.live = live
        self.status = "queued"
        self.started_at: Optional[str] = None
        self.finished_at: Optional[str] = None
        self.exit_code: Optional[int] = None
        self.lines: List[str] = []
        self._listeners: List[asyncio.Queue] = []
        self._proc: Optional[asyncio.subprocess.Process] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "kind": self.kind,
            "params": self.params,
            "live": self.live,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_code": self.exit_code,
            "output_preview": self.lines[-10:] if self.lines else [],
        }

    def save(self) -> None:
        j_dir = JOBS_DIR / self.job_id
        j_dir.mkdir(parents=True, exist_ok=True)
        meta_file = j_dir / "meta.json"
        meta_file.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        log_file = j_dir / "output.log"
        log_file.write_text("\n".join(self.lines) + ("\n" if self.lines else ""), encoding="utf-8")


class JobManager:
    def __init__(self):
        self.jobs: Dict[str, JobRecord] = {}
        self.running_job_id: Optional[str] = None
        self._load_persisted_jobs()

    def _load_persisted_jobs(self) -> None:
        if not JOBS_DIR.exists():
            return
        for d in sorted(JOBS_DIR.iterdir()):
            if d.is_dir() and (d / "meta.json").exists():
                try:
                    data = json.loads((d / "meta.json").read_text(encoding="utf-8"))
                    rec = JobRecord(
                        job_id=data["job_id"],
                        kind=data["kind"],
                        params=data.get("params", {}),
                        live=data.get("live", False),
                    )
                    rec.status = data.get("status", "completed")
                    rec.started_at = data.get("started_at")
                    rec.finished_at = data.get("finished_at")
                    rec.exit_code = data.get("exit_code")
                    if (d / "output.log").exists():
                        rec.lines = (d / "output.log").read_text(encoding="utf-8").splitlines()
                    self.jobs[rec.job_id] = rec
                except Exception:
                    pass

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        return self.jobs.get(job_id)

    def list_jobs(self) -> List[Dict[str, Any]]:
        return [j.to_dict() for j in sorted(self.jobs.values(), key=lambda x: x.started_at or "", reverse=True)]

    async def start_job(self, kind: str, params: Optional[Dict[str, Any]] = None, confirm_token: Optional[str] = None) -> JobRecord:
        if kind not in JOB_KINDS:
            raise ValueError(f"Disallowed job kind '{kind}'. Allowed kinds: {list(JOB_KINDS.keys())}")

        if self.running_job_id is not None:
            active = self.jobs.get(self.running_job_id)
            if active and active.status == "running":
                raise RuntimeError(f"Another job ({self.running_job_id}) is currently running")

        job_info = JOB_KINDS[kind]
        is_live = job_info["live"]

        # Check for live run gating
        if is_live:
            enable_live = os.environ.get("TRIPLINE_ENABLE_LIVE") == "1"
            has_armoriq = bool(os.environ.get("ARMORIQ_API_KEY"))
            if not enable_live or not has_armoriq:
                raise PermissionError("Live execution is disabled. Set TRIPLINE_ENABLE_LIVE=1 and export an active ARMORIQ_API_KEY.")
            if confirm_token != "CONFIRMED_LIVE_EXECUTION":
                raise PermissionError("Confirmation token required to launch live executions against real API endpoints.")

        job_id = f"job-{uuid.uuid4().hex[:12]}"
        record = JobRecord(job_id=job_id, kind=kind, params=params or {}, live=is_live)
        self.jobs[job_id] = record
        self.running_job_id = job_id

        # Launch async task
        asyncio.create_task(self._run_job_process(record, job_info))
        return record

    async def _run_job_process(self, record: JobRecord, job_info: Dict[str, Any]) -> None:
        record.status = "running"
        record.started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record.save()

        cmd = list(job_info["cmd"])
        # Support param customization if applicable
        if record.kind == "scenario" and "rung" in record.params:
            cmd = [sys.executable, "scripts/run_phase3_scenario.py", "--rung", str(record.params["rung"])]
        elif record.kind == "rea_investigate":
            target = record.params.get("target", "synthetic-electron-app")
            tool = record.params.get("tool", "analyze_electron_app")
            from agent.rea_adapter import APPROVED_TARGET_REGISTRY
            if target not in APPROVED_TARGET_REGISTRY:
                target = "synthetic-electron-app"
            allowed_tools = ["analyze_electron_app", "inspect_analysis_view", "trace_application_feature"]
            if tool not in allowed_tools:
                tool = "analyze_electron_app"
            cmd = [
                sys.executable,
                "scripts/rea_investigator.py",
                "--target", str(target),
                "--tool", str(tool),
                "--mode", "offline",
            ]

        # Environment whitelist
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": ".",
            "PYTHONUNBUFFERED": "1",
            "HOME": str(pathlib.Path.home()),
        }
        for k in ["ARMORIQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "TRIPLINE_ENABLE_LIVE"]:
            if k in os.environ:
                env[k] = os.environ[k]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(REPO_ROOT),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            record._proc = proc

            timeout = job_info.get("timeout", 60)
            loop = asyncio.get_event_loop()
            start_t = loop.time()

            while True:
                if loop.time() - start_t > timeout:
                    proc.kill()
                    record.lines.append("[TIMEOUT] Process exceeded maximum execution time.")
                    record.status = "failed"
                    break

                line_bytes = await proc.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
                sanitized = sanitize_text(line)
                record.lines.append(sanitized)
                
                # Push to active SSE subscribers
                for q in list(record._listeners):
                    await q.put(sanitized)

            exit_code = await proc.wait()
            record.exit_code = exit_code
            if record.status != "failed" and record.status != "cancelled":
                record.status = "completed" if exit_code == 0 else "failed"

        except asyncio.CancelledError:
            record.status = "cancelled"
            if record._proc:
                try:
                    record._proc.kill()
                except Exception:
                    pass
        except Exception as e:
            record.status = "failed"
            record.lines.append(f"[ERROR] Process execution failed: {sanitize_text(str(e))}")
        finally:
            record.finished_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            if self.running_job_id == record.job_id:
                self.running_job_id = None
            record.save()
            for q in list(record._listeners):
                await q.put(None)  # Sentinel for end-of-stream

    async def cancel_job(self, job_id: str) -> bool:
        rec = self.jobs.get(job_id)
        if not rec or rec.status != "running":
            return False
        rec.status = "cancelled"
        if rec._proc:
            try:
                rec._proc.terminate()
                await asyncio.sleep(0.5)
                if rec._proc.returncode is None:
                    rec._proc.kill()
            except Exception:
                pass
        rec.save()
        if self.running_job_id == job_id:
            self.running_job_id = None
        return True

    async def stream_job_events(self, job_id: str) -> AsyncGenerator[str, None]:
        rec = self.jobs.get(job_id)
        if not rec:
            yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
            return

        # First yield all already recorded lines
        for line in rec.lines:
            yield f"data: {json.dumps({'line': line, 'status': rec.status, 'job_id': job_id})}\n\n"

        if rec.status in ("completed", "failed", "cancelled"):
            yield f"data: {json.dumps({'status': rec.status, 'exit_code': rec.exit_code, 'job_id': job_id, 'done': True})}\n\n"
            return

        # Subscribe for live lines
        q: asyncio.Queue = asyncio.Queue()
        rec._listeners.append(q)
        try:
            while True:
                item = await q.get()
                if item is None:
                    break
                yield f"data: {json.dumps({'line': item, 'status': rec.status, 'job_id': job_id})}\n\n"
            yield f"data: {json.dumps({'status': rec.status, 'exit_code': rec.exit_code, 'job_id': job_id, 'done': True})}\n\n"
        finally:
            if q in rec._listeners:
                rec._listeners.remove(q)


job_manager = JobManager()
