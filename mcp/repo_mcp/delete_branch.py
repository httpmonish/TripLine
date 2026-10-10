"""
mcp/repo_mcp/delete_branch.py — Sandboxed destructive tool for Phase 2.

Implements Section 4.1 safeguards:
  1. Operates ONLY on throwaway sandbox git repo specified via TRIPLINE_SANDBOX_REPO.
     Refuses if unset, project repo, or missing .tripline_sandbox_marker.
  2. Strict branch name validation: regex ^[A-Za-z0-9._/-]{1,64}$, no leading '-', '..', whitespace.
  3. Refuses deletion of current branch and protected branches: main, master, develop, release/*.
  4. Non-shell argument list execution: ['git', '-C', sandbox, 'branch', '-D', '--', name].
  5. Deterministic witness event recording via WitnessRecorder('repo-mcp').
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import uuid
from typing import Any, Dict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MARKER_FILE_NAME = ".tripline_sandbox_marker"
BRANCH_REGEX = re.compile(r"^[A-Za-z0-9._/-]{1,64}$")
PROTECTED_BRANCHES = {"main", "master", "develop"}


def _load_witness():
    p = REPO_ROOT / "mcp" / "common" / "witness.py"
    spec = importlib.util.spec_from_file_location("witness", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


witness_mod = _load_witness()
recorder = witness_mod.WitnessRecorder("repo-mcp")
compute_args_hash = witness_mod.compute_args_hash


def _hash_result(result: Any) -> str:
    encoded = witness_mod.canonical_json(result).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_sandbox_path() -> tuple[pathlib.Path | None, str | None]:
    sandbox_env = os.environ.get("TRIPLINE_SANDBOX_REPO")
    if not sandbox_env or not sandbox_env.strip():
        return None, "TRIPLINE_SANDBOX_REPO environment variable is unset"

    sandbox_path = pathlib.Path(sandbox_env).resolve()
    if not sandbox_path.exists() or not sandbox_path.is_dir():
        return None, f"Sandbox directory does not exist: {sandbox_path}"

    if sandbox_path == REPO_ROOT.resolve():
        return None, "Sandbox path cannot be the project repository"

    marker = sandbox_path / MARKER_FILE_NAME
    if not marker.exists():
        return None, f"Sandbox directory lacks {MARKER_FILE_NAME} verification marker"

    git_dir = sandbox_path / ".git"
    if not git_dir.exists():
        return None, "Sandbox directory is not a git repository"

    return sandbox_path, None


def _validate_branch_name(name: str, sandbox_path: pathlib.Path) -> str | None:
    if not name or not isinstance(name, str):
        return "Branch name must be a non-empty string"

    if any(c.isspace() for c in name):
        return "Branch name contains forbidden whitespace"

    if name.startswith("-"):
        return "Branch name cannot start with '-' (option injection prevented)"

    if ".." in name:
        return "Branch name cannot contain '..' (traversal prevented)"

    if not BRANCH_REGEX.match(name):
        return "Branch name contains invalid characters or exceeds 64 characters"

    if name in PROTECTED_BRANCHES or name.startswith("release/"):
        return f"Branch '{name}' is protected and cannot be deleted"

    # Check current active branch in sandbox
    try:
        proc = subprocess.run(
            ["git", "-C", str(sandbox_path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        current_branch = proc.stdout.strip()
        if name == current_branch:
            return f"Cannot delete the currently checked-out branch '{current_branch}'"
    except Exception as e:
        return f"Failed to determine current branch: {e}"

    return None


def delete_branch(name: str) -> str:
    """
    Delete a git branch inside the throwaway sandbox repository.
    Gated by ArmorIQ and local DecisionProofMiddleware.
    """
    from canary.state import get_current_call, get_current_trace

    trace_id = get_current_trace() or None
    call_id = get_current_call() or f"call-{uuid.uuid4().hex[:8]}"

    args_hash = compute_args_hash("repo-mcp", "delete_branch", {"name": name})
    recorder.record_event(call_id, args_hash, "delete_branch", "received", trace_id=trace_id)

    # 1. Validate sandbox
    sandbox_path, err = _validate_sandbox_path()
    if err:
        recorder.record_event(call_id, args_hash, "delete_branch", "rejected_by_safeguard", trace_id=trace_id)
        res = json.dumps({"tool": "delete_branch", "name": name, "status": "error", "error": err})
        return res

    # 2. Validate branch name & protected branches
    err = _validate_branch_name(name, sandbox_path)
    if err:
        recorder.record_event(call_id, args_hash, "delete_branch", "rejected_by_safeguard", trace_id=trace_id)
        res = json.dumps({"tool": "delete_branch", "name": name, "status": "error", "error": err})
        return res

    # 3. Execute branch deletion
    recorder.record_event(call_id, args_hash, "delete_branch", "execution_started", trace_id=trace_id)

    cmd = ["git", "-C", str(sandbox_path), "branch", "-D", "--", name]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode == 0:
        res = json.dumps({"tool": "delete_branch", "name": name, "status": "deleted", "output": proc.stdout.strip()})
    else:
        err_msg = proc.stderr.strip() or proc.stdout.strip()
        res = json.dumps({"tool": "delete_branch", "name": name, "status": "not_found" if "not found" in err_msg.lower() else "error", "error": err_msg})

    recorder.record_event(call_id, args_hash, "delete_branch", "execution_completed", result_hash=_hash_result(res), trace_id=trace_id)
    return res
