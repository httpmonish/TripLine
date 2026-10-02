"""
Tripline MCP Server — Phase 0 Foundation

Exposes:
  - hello_tool          : safe echo, no side effects
  - echo_marker         : writes a named in-memory marker (observable, harmless)
  - clear_markers       : resets all in-memory markers

No filesystem, no shell, no secrets, no external network.
All state lives only in this process's memory.
"""

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

mcp = MCPServer("tripline-mcp")

# In-memory marker store: used by authorized/unauthorized tests to prove
# non-execution without touching the filesystem.
_markers: dict[str, bool] = {}


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


# Only enforce host restrictions when using a real Cloudflare tunnel.
# For local-only (127.0.0.1) operation, omit TransportSecuritySettings
# so the 421 "Invalid Host header" does NOT occur.

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        json_response=True,
        stateless_http=True,
        # No transport_security when running locally — the 421 was caused by
        # allowed_hosts not including 'localhost' / '127.0.0.1'.
    )
