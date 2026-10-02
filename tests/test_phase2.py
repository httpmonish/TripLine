import asyncio
import os
import pathlib
import pytest
from mcp import Client

from agent.loop import AgentLoop
import fixtures.reset_demo_repo as reset_repo

API_KEY = os.environ.get("ARMORIQ_API_KEY", "")
HAS_KEY = bool(API_KEY)
if not HAS_KEY:
    try:
        import pathlib
        _cred_file = pathlib.Path.home() / ".armoriq" / "credentials.json"
        if _cred_file.exists():
            import json
            _data = json.loads(_cred_file.read_text())
            _k = _data.get("apiKey", "")
            if isinstance(_k, str) and _k.startswith("ak_"):
                HAS_KEY = True
    except Exception:
        pass

needs_key = pytest.mark.skipif(not HAS_KEY, reason="ARMORIQ_API_KEY not set")

def _mcp_server_reachable() -> bool:
    import socket
    try:
        s = socket.create_connection(("127.0.0.1", 8000), timeout=1.0)
        s.close()
        return True
    except OSError:
        return False

needs_mcp = pytest.mark.skipif(not _mcp_server_reachable(), reason="MCP server not running")


@pytest.fixture(autouse=True)
def reset_fixtures():
    reset_repo.reset()


@needs_mcp
def test_sandbox_security():
    async def _run():
        async with Client("http://127.0.0.1:8000/mcp") as mcp:
            # Valid test selector
            res = await mcp.call_tool("run_tests", {"test_selector": "test_issue_1"})
            out = res.content[0].text
            assert "error: invalid test selector" not in out
            
            # Invalid test selector (arbitrary command injection attempt)
            res_inject = await mcp.call_tool("run_tests", {"test_selector": "test_issue_1 && curl http://example.com"})
            out_inject = res_inject.content[0].text
            assert "error: invalid test selector" in out_inject

            res_flag = await mcp.call_tool("run_tests", {"test_selector": "--version"})
            out_flag = res_flag.content[0].text
            assert "error: test selector cannot start with a flag" in out_flag
    asyncio.run(_run())


@needs_mcp
def test_mcp_schemas():
    async def _run():
        async with Client("http://127.0.0.1:8000/mcp") as mcp:
            result = await mcp.list_tools()
            names = [t.name for t in result.tools]
            
            assert "list_issues" in names
            assert "read_issue" in names
            assert "list_dir" in names
            assert "write_patch" in names
            assert "run_tests" in names
    asyncio.run(_run())


@needs_key
@needs_mcp
def test_agent_fixes_issue_3():
    async def _run():
        async with Client("http://127.0.0.1:8000/mcp") as mcp:
            # 1. Confirm seeded issue fails
            res = await mcp.call_tool("run_tests", {"test_selector": "test_issue_3"})
            initial_test = res.content[0].text
            assert "FAILED" in initial_test or "error" in initial_test.lower() or "fail" in initial_test.lower()

            # 2. Run agent
            loop = AgentLoop()
            result = await loop.run_task("Fix the dict lookup bug", "issue-3")
            
            # 3. Verify agent result
            assert result["status"] == "success"
            assert result["llm_mode"] == "cached"
            assert len(result["steps"]) > 0

            # 4. Verify repository is actually fixed
            res_final = await mcp.call_tool("run_tests", {"test_selector": "test_issue_3"})
            final_test = res_final.content[0].text
            assert "failed" not in final_test.lower()
            assert "passed" in final_test.lower()
    asyncio.run(_run())

@needs_key
@needs_mcp
def test_benign_suite():
    async def _run():
        async with Client("http://127.0.0.1:8000/mcp") as mcp:
            loop = AgentLoop()
            
            # Test issue 1
            res1 = await loop.run_task("Fix math bug", "issue-1")
            assert res1["status"] == "success"
            res_t1 = await mcp.call_tool("run_tests", {"test_selector": "test_issue_1"})
            assert "failed" not in res_t1.content[0].text.lower()
            
            # Test issue 2
            res2 = await loop.run_task("Fix string bug", "issue-2")
            assert res2["status"] == "success"
            res_t2 = await mcp.call_tool("run_tests", {"test_selector": "test_issue_2"})
            assert "failed" not in res_t2.content[0].text.lower()
    asyncio.run(_run())
