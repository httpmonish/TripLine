"""
test_mcp.py — Smoke test for MCP server connectivity.

Replaces the old version that used result.structured_content (deprecated in MCP 2.x).
MCP 2.x returns result.content — a list of TextContent/ImageContent objects.

Usage:
    source .venv313/bin/activate
    python server.py &
    python test_mcp.py
"""

import asyncio

from mcp import Client


async def main():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        tools = await client.list_tools()

        print("Available tools:")
        for tool in tools.tools:
            print(f"  - {tool.name}: {tool.description or '(no description)'}")

        result = await client.call_tool("hello_tool", {})

        print("\nhello_tool result:")
        for content in result.content:
            print(f"  {content.text}")


if __name__ == "__main__":
    asyncio.run(main())
