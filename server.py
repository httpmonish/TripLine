"""
Tripline MCP Server — Phase 0.5

Exposes:
  - hello_tool          : safe echo, no side effects
  - echo_marker         : writes a named in-memory marker (observable, harmless)
  - clear_markers       : resets all in-memory markers
  - list_markers        : returns current in-memory marker state
  - read_file           : read a file from ./fixtures only (S2 parameter test)

Security notes:
  - read_file is sandboxed to the ./fixtures directory.
    Any attempt to read outside (path traversal, absolute paths) returns an error.
    ArmorIQ enforces at tool level; Tripline enforces at parameter level here.
  - TransportSecuritySettings is built from TRIPLINE_ALLOWED_HOSTS env var so that
    the same binary can run both locally and behind a Cloudflare Quick Tunnel.
    Without the env var, DNS rebinding protection is disabled for local development.
    With the env var, only listed hostnames are allowed (fixes the 421 error when
    behind a tunnel).

All in-memory state lives only in this process's memory.
No shell, no secrets, no external network calls from tools.
"""

from __future__ import annotations

import os
import pathlib
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

mcp = MCPServer("tripline-mcp")

# In-memory marker store: used by authorized/unauthorized tests to prove
# non-execution without touching the filesystem.
_markers: dict[str, bool] = {}

# In-memory execution counters for Phase 1 proof
_execution_counters: dict[str, int] = {
    "hello_tool": 0,
    "read_project_info": 0,
    "perform_test_action": 0,
}

# Fixtures directory — read_file is sandboxed to this path.
_FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


@mcp.tool()
def hello_tool() -> str:
    """Return a safe test message. Deterministic. No side effects."""
    _execution_counters["hello_tool"] = _execution_counters.get("hello_tool", 0) + 1
    return "Hello from Tripline MCP!"


@mcp.tool()
def read_project_info() -> str:
    """Return fixed/mock project information. Harmless."""
    _execution_counters["read_project_info"] = _execution_counters.get("read_project_info", 0) + 1
    return '{"project": "Tripline", "role": "evidence_layer", "status": "active"}'


@mcp.tool()
def perform_test_action() -> str:
    """Harmless but observable action. Increments counter."""
    _execution_counters["perform_test_action"] = _execution_counters.get("perform_test_action", 0) + 1
    return "test_action_performed"


@mcp.tool()
def get_execution_counters() -> str:
    """Return JSON string of execution counters."""
    import json
    return json.dumps(_execution_counters)


@mcp.tool()
def reset_execution_counters() -> str:
    """Reset all execution counters to 0."""
    for k in _execution_counters:
        _execution_counters[k] = 0
    return "counters_reset"


@mcp.tool()
def echo_marker(name: str) -> str:
    """
    Set a named in-memory marker and return confirmation.
    Harmless: no filesystem, no network, process-local only.
    Used by authorized/unauthorized execution tests.
    """
    _markers[name] = True
    return f"marker_set:{name}"


@mcp.tool()
def clear_markers() -> str:
    """Reset all in-memory markers. Used between test runs."""
    _markers.clear()
    return "markers_cleared"


@mcp.tool()
def list_markers() -> str:
    """Return current marker state. Used to verify non-execution."""
    return str(list(_markers.keys()))


@mcp.tool()
def read_file(path: str) -> str:
    """Read a file from the repository."""
    return repo_mod.read_file(path)



import importlib.util
import pathlib

def load_tool_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

issues_mod = load_tool_module("issues_tool", str(pathlib.Path(__file__).parent / "mcp" / "issues_mcp" / "tool.py"))
repo_mod = load_tool_module("repo_tool", str(pathlib.Path(__file__).parent / "mcp" / "repo_mcp" / "tool.py"))
sandbox_mod = load_tool_module("sandbox_tool", str(pathlib.Path(__file__).parent / "mcp" / "sandbox_mcp" / "tool.py"))

@mcp.tool()
def list_issues() -> str:
    """List all open issues."""
    return issues_mod.list_issues()

@mcp.tool()
def read_issue(issue_id: str) -> str:
    """Read full details of a specific issue."""
    return issues_mod.read_issue(issue_id)

@mcp.tool()
def comment_issue(issue_id: str, text: str) -> str:
    """Add a comment to an issue."""
    return issues_mod.comment_issue(issue_id, text)

@mcp.tool()
def list_dir(path: str = ".") -> str:
    """List directory contents in the repository."""
    return repo_mod.list_dir(path)

@mcp.tool()
def write_patch(path: str, content: str) -> str:
    """Write/overwrite a file in the repository (simplified patch)."""
    return repo_mod.write_patch(path, content)

@mcp.tool()
def run_tests(test_selector: str) -> str:
    """Run pytest with the given selector (e.g. 'test_issue_1'). Executed in sandbox with NO network."""
    return sandbox_mod.run_tests(test_selector)


def _build_transport_security() -> TransportSecuritySettings | None:
    """
    Build TransportSecuritySettings from environment.

    TRIPLINE_ALLOWED_HOSTS (comma-separated): set when running behind a Cloudflare
    Quick Tunnel. Example:
        export TRIPLINE_ALLOWED_HOSTS="facts-gmbh-recipient-willow.trycloudflare.com,127.0.0.1:*,localhost:*"

    When the env var is absent, return None — the MCP SDK will auto-enable DNS
    rebinding protection with only localhost/127.0.0.1 allowed (local-only mode).

    Root cause of the 421 error: the old server.py hard-coded a specific Cloudflare
    tunnel hostname in allowed_hosts, which expired. The fix is to inject the
    hostname at startup via env var rather than baking it into source.
    """
    raw = os.environ.get("TRIPLINE_ALLOWED_HOSTS", "").strip()
    if not raw:
        # No env var → None → MCP SDK uses its localhost-only default.
        # This is correct for local development (no tunnel).
        return None

    hosts = [h.strip() for h in raw.split(",") if h.strip()]
    origins = [
        f"https://{h}" if not h.startswith(("http://", "https://")) else h
        for h in hosts
        if not (h.endswith(":*") and h.startswith(("127.", "localhost", "[::1]")))
    ]
    # Always include localhost variants
    hosts += ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    origins += ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(dict.fromkeys(hosts)),
        allowed_origins=list(dict.fromkeys(origins)),
    )


import importlib.util
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

def _load_proof():
    spec = importlib.util.spec_from_file_location("proof", str(pathlib.Path(__file__).parent / "mcp" / "common" / "proof.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _load_witness():
    spec = importlib.util.spec_from_file_location("witness", str(pathlib.Path(__file__).parent / "mcp" / "common" / "witness.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class DecisionProofMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.proof_mod = _load_proof()
        self.witness_mod = _load_witness()

    async def dispatch(self, request, call_next):
        if request.method == "POST" and request.url.path == "/mcp":
            body_bytes = await request.body()
            import json
            try:
                msg = json.loads(body_bytes)
            except Exception:
                msg = None
            if isinstance(msg, dict) and msg.get("method") == "tools/call":
                params = msg.get("params", {})
                tool_name = params.get("name", "")
                proof_header = request.headers.get("x-tripline-decision-proof")
                trace_id_hdr = request.headers.get("x-tripline-trace-id")
                if trace_id_hdr:
                    try:
                        from canary.state import set_current_trace
                        set_current_trace(trace_id_hdr)
                    except Exception:
                        pass
                tool_args = params.get("arguments", {})
                key = self.witness_mod.get_witness_key()
                
                is_valid = False
                fail_reason = "MISSING_DECISION_PROOF"
                for mcp_cand in ("tripline-mcp", "repo-mcp", "issues-mcp", "sandbox-mcp"):
                    args_hash = self.witness_mod.compute_args_hash(mcp_cand, tool_name, tool_args)
                    v, r = self.proof_mod.verify_decision_proof(proof_header, args_hash, key, max_age=60.0)
                    if v:
                        is_valid = True
                        break
                    else:
                        fail_reason = r
                if not is_valid:
                    return JSONResponse(status_code=403, content={"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32000, "message": f"MCP Bypass Rejected: {fail_reason}"}})
        return await call_next(request)

def create_app():
    transport_security = _build_transport_security()
    starlette_app = mcp.streamable_http_app(
        transport_security=transport_security,
        json_response=True,
        stateless_http=True,
        host="127.0.0.1",
    )
    starlette_app.add_middleware(DecisionProofMiddleware)
    return starlette_app

if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Tripline MCP Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()

    # Create fixtures directory with a sample file so read_file tests work
    _FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    (_FIXTURES_DIR / "ok.txt").write_text("Tripline fixture file — safe read target.\n")

    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port)

