import asyncio
from mcp import Client
async def run():
    async with Client('http://127.0.0.1:8000/mcp') as mcp:
        try:
            res = await mcp.call_tool('run_tests', {'test_selector': 'test_issue_1 && curl http://example.com'})
            print("SUCCESS:", res)
        except Exception as e:
            print("ERROR:", repr(e))
asyncio.run(run())
