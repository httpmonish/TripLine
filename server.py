	from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

mcp = MCPServer("tripline-mcp")


@mcp.tool()
def hello_tool() -> str:
    """Return a safe test message."""
    return "Hello from Tripline MCP!"


security = TransportSecuritySettings(
    allowed_hosts=[
        "nirvana-turn-function-participate.trycloudflare.com",
        "nirvana-turn-function-participate.trycloudflare.com:*",
    ],
    allowed_origins=[
        "https://nirvana-turn-function-participate.trycloudflare.com",
    ],
)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        json_response=True,
        stateless_http=True,
        transport_security=security,
    )

