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

# Fixtures directory — read_file is sandboxed to this path.
_FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


@mcp.tool()
def hello_tool() -> str:
    """Return a safe test message. Deterministic. No side effects."""
    return "Hello from Tripline MCP!"


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
    """
    Read a file from the ./fixtures directory only.

    S2 (parameter enforcement) test tool: Tripline enforces the path constraint
    here at the application layer. ArmorIQ enforces only at the tool level (it
    cannot see path parameter values). This demonstrates the parameter-level gap
    documented in Phase 0.5 / S2.

    Returns the file contents, or an error string if the path is outside ./fixtures,
    is absolute, or the file does not exist. Never raises an exception.
    """
    _FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # Reject absolute paths immediately
    if pathlib.Path(path).is_absolute():
        return f"error:absolute_path_rejected:{path}"

    # Resolve relative to fixtures and check it stays inside
    try:
        resolved = (_FIXTURES_DIR / path).resolve()
        fixtures_resolved = _FIXTURES_DIR.resolve()
        resolved.relative_to(fixtures_resolved)  # raises ValueError if escaping
    except ValueError:
        return f"error:path_traversal_rejected:{path}"
    except Exception as e:
        return f"error:path_resolution_failed:{e}"

    if not resolved.exists():
        return f"error:file_not_found:{path}"

    try:
        return resolved.read_text(errors="replace")
    except Exception as e:
        return f"error:read_failed:{e}"


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


if __name__ == "__main__":
    transport_security = _build_transport_security()

    # Create fixtures directory with a sample file so read_file tests work
    _FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    (_FIXTURES_DIR / "ok.txt").write_text("Tripline fixture file — safe read target.\n")

    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        json_response=True,
        stateless_http=True,
        transport_security=transport_security,
        # transport_security=None  → SDK auto-sets localhost-only host allowlist.
        # transport_security=<settings>  → uses TRIPLINE_ALLOWED_HOSTS env var.
        # To run behind a Cloudflare tunnel:
        #   export TRIPLINE_ALLOWED_HOSTS="your-tunnel-name.trycloudflare.com"
        #   python server.py
    )
