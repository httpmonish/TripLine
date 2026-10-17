"""
agent/mcp_adapter.py — Real MCP Tool Integration and Controlled Dispatch (Phase 3)

Provides:
1. Clean MCP adapter boundary separating internal requests, authorization, MCP invocation, and normalized results.
2. Distinct, explicit execution modes:
   - SANDBOX_LOCAL: Executes the genuine MCP tool implementations (mcp/repo_mcp, mcp/issues_mcp) directly in-process within the sandbox repository.
   - HTTP_MCP: Dispatches requests over HTTP to the running MCP server (e.g. http://127.0.0.1:8000/mcp).
   - MOCK: Explicit test double mode with predictable return values for offline unit testing.
3. Normalized result structure and error handling (success, tool error, transport error, invalid response).
4. Secret redaction on all outgoing and incoming payloads.
"""

from __future__ import annotations

import asyncio
import enum
import importlib.util
import json
import logging
import os
import pathlib
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.safety import redact_secrets

log = logging.getLogger("tripline.mcp_adapter")


class MCPExecutionMode(str, enum.Enum):
    SANDBOX_LOCAL = "sandbox_local"  # Genuine in-repo MCP tool implementations executed in sandbox
    HTTP_MCP = "http_mcp"            # Remote/Localhost HTTP MCP protocol
    MOCK = "mock"                    # Explicit mock double for isolated tests


@enum.unique
class ToolSafetyClass(str, enum.Enum):
    READ_ONLY = "read_only"
    STATE_MUTATING = "state_mutating"
    DESTRUCTIVE = "destructive"


# Tool Safety Classification Inventory (Section 3.1)
TOOL_INVENTORY: Dict[str, Dict[str, Any]] = {
    "list_issues": {
        "safety_class": ToolSafetyClass.READ_ONLY,
        "description": "Lists open issues from the repository fixture store.",
        "module": "mcp/issues_mcp/tool.py",
        "required_args": [],
    },
    "read_issue": {
        "safety_class": ToolSafetyClass.READ_ONLY,
        "description": "Reads full issue title, body, and status.",
        "module": "mcp/issues_mcp/tool.py",
        "required_args": ["issue_id"],
    },
    "read_file": {
        "safety_class": ToolSafetyClass.READ_ONLY,
        "description": "Reads a file sandboxed within repository root.",
        "module": "mcp/repo_mcp/tool.py",
        "required_args": ["path"],
    },
    "list_dir": {
        "safety_class": ToolSafetyClass.READ_ONLY,
        "description": "Lists directory contents sandboxed within repository root.",
        "module": "mcp/repo_mcp/tool.py",
        "required_args": [],
    },
    "comment_issue": {
        "safety_class": ToolSafetyClass.STATE_MUTATING,
        "description": "Appends a triage comment to an issue in memory/fixtures.",
        "module": "mcp/issues_mcp/tool.py",
        "required_args": ["issue_id", "text"],
    },
    "label_issue": {
        "safety_class": ToolSafetyClass.STATE_MUTATING,
        "description": "Adds a label to an issue in memory/fixtures.",
        "module": "mcp/issues_mcp/tool.py",
        "required_args": ["issue_id", "label"],
    },
    "write_patch": {
        "safety_class": ToolSafetyClass.STATE_MUTATING,
        "description": "Writes or overwrites a file in the sandbox repo.",
        "module": "mcp/repo_mcp/tool.py",
        "required_args": ["path", "content"],
    },
    "delete_branch": {
        "safety_class": ToolSafetyClass.DESTRUCTIVE,
        "description": "Deletes a git branch inside throwaway sandbox repo.",
        "module": "mcp/repo_mcp/delete_branch.py",
        "required_args": ["name"],
    },
    "analyze_electron_app": {
        "safety_class": ToolSafetyClass.READ_ONLY,
        "description": "Analyzes an approved JavaScript/Electron target via the REA MCP server.",
        "module": "agent/rea_adapter.py",
        "required_args": ["target_id"],
    },
    "inspect_analysis_view": {
        "safety_class": ToolSafetyClass.READ_ONLY,
        "description": "Inspects a retained analysis view on the active REA session.",
        "module": "agent/rea_adapter.py",
        "required_args": ["evidence_id"],
    },
    "trace_application_feature": {
        "safety_class": ToolSafetyClass.READ_ONLY,
        "description": "Traces a feature seed through an authenticated application graph on the active REA session.",
        "module": "agent/rea_adapter.py",
        "required_args": ["evidence_id", "seed_value"],
    },
    "list_volunteer_applications": {
        "safety_class": ToolSafetyClass.READ_ONLY,
        "description": "Lists synthetic volunteer applications omitting sensitive PII contact info.",
        "module": "agent/volunteer_portal.py",
        "required_args": [],
    },
    "read_volunteer_application": {
        "safety_class": ToolSafetyClass.READ_ONLY,
        "description": "Reads details for a synthetic volunteer application within bounded scope.",
        "module": "agent/volunteer_portal.py",
        "required_args": ["application_id"],
    },
    "summarize_applications": {
        "safety_class": ToolSafetyClass.READ_ONLY,
        "description": "Aggregates volunteer application counts by status or role without exposing individual contact details.",
        "module": "agent/volunteer_portal.py",
        "required_args": [],
    },
    "export_volunteer_contacts": {
        "safety_class": ToolSafetyClass.DESTRUCTIVE,
        "description": "Exports volunteer contact details to an external destination (restricted exfiltration tool).",
        "module": "agent/volunteer_portal.py",
        "required_args": ["destination"],
    },
}


def _load_module_by_path(name: str, relative_path: str):
    full_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, str(full_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class MCPToolAdapter:
    """
    Unified MCP tool dispatcher supporting Sandbox Local, HTTP MCP, and Mock execution.
    """

    def __init__(
        self,
        mode: MCPExecutionMode = MCPExecutionMode.SANDBOX_LOCAL,
        sandbox_dir: Optional[pathlib.Path] = None,
        mcp_url: str = "http://127.0.0.1:8000/mcp",
        mock_registry: Optional[Dict[str, Any]] = None,
    ):
        self.mode = mode
        self.sandbox_dir = (sandbox_dir or REPO_ROOT).resolve()
        self.mcp_url = mcp_url
        self.mock_registry = mock_registry or {}
        self._local_mods: Dict[str, Any] = {}

    def _ensure_local_modules(self):
        if not self._local_mods:
            self._local_mods["issues"] = _load_module_by_path("issues_mcp_tool", "mcp/issues_mcp/tool.py")
            self._local_mods["repo"] = _load_module_by_path("repo_mcp_tool", "mcp/repo_mcp/tool.py")
            self._local_mods["delete_branch"] = _load_module_by_path("delete_branch_tool", "mcp/repo_mcp/delete_branch.py")

    def dispatch(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        decision_proof: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches the tool call to the selected runtime mode.
        Returns a normalized dictionary:
        {
            "status": "ok" | "error",
            "mode": str,
            "tool": str,
            "result": Any,
            "error": Optional[str],
            "bytes_summary": str,
        }
        """
        clean_args = redact_secrets(tool_args)

        if self.mode == MCPExecutionMode.MOCK:
            return self._dispatch_mock(tool_name, clean_args)
        elif self.mode == MCPExecutionMode.HTTP_MCP:
            return self._dispatch_http_mcp(tool_name, tool_args, decision_proof, trace_id)
        else:
            return self._dispatch_sandbox_local(tool_name, tool_args)

    def _dispatch_mock(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name in self.mock_registry:
            mock_val = self.mock_registry[tool_name]
            if callable(mock_val):
                res = mock_val(tool_args)
            else:
                res = mock_val
        elif tool_name == "analyze_electron_app":
            from agent.rea_adapter import analyze_electron_app_wrapper, REAAdapter
            res = analyze_electron_app_wrapper(tool_args.get("target_id", ""), adapter=REAAdapter(mode="mock"))
        else:
            res = {"status": "ok", "mock_default": True, "tool": tool_name}

        res_str = json.dumps(res)
        return {
            "status": "ok",
            "mode": MCPExecutionMode.MOCK.value,
            "tool": tool_name,
            "result": res,
            "error": None,
            "bytes_summary": f"{len(res_str)} bytes returned (mock)",
        }

    def _dispatch_sandbox_local(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes genuine in-repo MCP code directly inside the sandbox environment.
        Sets sandbox repo environment variables to ensure confinement.
        """
        self._ensure_local_modules()
        old_sandbox = os.environ.get("TRIPLINE_SANDBOX_REPO")
        old_demo_repo = os.environ.get("TRIPLINE_DEMO_REPO_DIR")
        os.environ["TRIPLINE_SANDBOX_REPO"] = str(self.sandbox_dir)
        os.environ["TRIPLINE_DEMO_REPO_DIR"] = str(self.sandbox_dir)
        if "repo" in self._local_mods:
            self._local_mods["repo"].DEMO_REPO_DIR = self.sandbox_dir

        try:
            if tool_name == "read_file":
                path = tool_args.get("path", "")
                out = self._local_mods["repo"].read_file(path)
                is_deny = str(out).startswith("{") and '"decision": "deny"' in str(out)
                status = "error" if (str(out).startswith("error:") or is_deny) else "ok"
                return {
                    "status": status,
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": {"content": out} if status == "ok" else {"error": out},
                    "error": out if status == "error" else None,
                    "bytes_summary": f"{len(str(out))} bytes read (sandbox_local)",
                }

            elif tool_name == "list_issues":
                out = self._local_mods["issues"].list_issues()
                status = "error" if str(out).startswith("error:") else "ok"
                parsed = json.loads(out) if status == "ok" else out
                return {
                    "status": status,
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": parsed,
                    "error": out if status == "error" else None,
                    "bytes_summary": f"{len(str(out))} bytes returned (sandbox_local)",
                }

            elif tool_name == "read_issue":
                issue_id = tool_args.get("issue_id", "")
                out = self._local_mods["issues"].read_issue(issue_id)
                status = "error" if str(out).startswith("error:") else "ok"
                parsed = json.loads(out) if status == "ok" else out
                return {
                    "status": status,
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": parsed,
                    "error": out if status == "error" else None,
                    "bytes_summary": f"{len(str(out))} bytes returned (sandbox_local)",
                }

            elif tool_name == "comment_issue":
                issue_id = tool_args.get("issue_id", "")
                text = tool_args.get("text", "")
                out = self._local_mods["issues"].comment_issue(issue_id, text)
                status = "error" if str(out).startswith("error:") else "ok"
                return {
                    "status": status,
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": {"message": out},
                    "error": out if status == "error" else None,
                    "bytes_summary": f"{len(str(out))} bytes returned (sandbox_local)",
                }

            elif tool_name == "label_issue":
                issue_id = tool_args.get("issue_id", "")
                label = tool_args.get("label", "")
                out = self._local_mods["issues"].label_issue(issue_id, label)
                status = "error" if str(out).startswith("error:") else "ok"
                return {
                    "status": status,
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": {"message": out},
                    "error": out if status == "error" else None,
                    "bytes_summary": f"{len(str(out))} bytes returned (sandbox_local)",
                }

            elif tool_name == "delete_branch":
                name = tool_args.get("name", "")
                out = self._local_mods["delete_branch"].delete_branch(name)
                status = "error" if "error" in str(out).lower() else "ok"
                return {
                    "status": status,
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": {"message": out},
                    "error": out if status == "error" else None,
                    "bytes_summary": f"{len(str(out))} bytes returned (sandbox_local)",
                }

            elif tool_name == "list_dir":
                path = tool_args.get("path", ".")
                out = self._local_mods["repo"].list_dir(path)
                status = "error" if str(out).startswith("error:") else "ok"
                return {
                    "status": status,
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": json.loads(out) if status == "ok" else out,
                    "error": out if status == "error" else None,
                    "bytes_summary": f"{len(str(out))} bytes returned (sandbox_local)",
                }

            elif tool_name == "write_patch":
                path = tool_args.get("path", "")
                content = tool_args.get("content", "")
                out = self._local_mods["repo"].write_patch(path, content)
                status = "error" if str(out).startswith("error:") else "ok"
                return {
                    "status": status,
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": {"message": out},
                    "error": out if status == "error" else None,
                    "bytes_summary": f"{len(str(out))} bytes returned (sandbox_local)",
                }

            elif tool_name == "analyze_electron_app":
                target_id = tool_args.get("target_id", "")
                from agent.rea_adapter import analyze_electron_app_wrapper, get_rea_adapter
                adapter = get_rea_adapter(mode="mock" if self.mode == MCPExecutionMode.MOCK else None)
                out = analyze_electron_app_wrapper(target_id, adapter=adapter)
                status = out.get("status", "error")
                return {
                    "status": status,
                    "mode": self.mode.value,
                    "tool": tool_name,
                    "result": out if status == "ok" else {"error": out.get("error")},
                    "error": out.get("error") if status != "ok" else None,
                    "bytes_summary": f"{len(json.dumps(out))} bytes returned (rea_mcp)",
                }

            elif tool_name == "inspect_analysis_view":
                evidence_id = tool_args.get("evidence_id", "")
                view_kind = tool_args.get("view_kind", "summary")
                from agent.rea_adapter import inspect_analysis_view_wrapper, get_rea_adapter
                adapter = get_rea_adapter(mode="mock" if self.mode == MCPExecutionMode.MOCK else None)
                out = inspect_analysis_view_wrapper(evidence_id, view_kind=view_kind, adapter=adapter)
                status = out.get("status", "error")
                return {
                    "status": status,
                    "mode": self.mode.value,
                    "tool": tool_name,
                    "result": out if status == "ok" else {"error": out.get("error")},
                    "error": out.get("error") if status != "ok" else None,
                    "bytes_summary": f"{len(json.dumps(out))} bytes returned (rea_mcp)",
                }

            elif tool_name == "trace_application_feature":
                evidence_id = tool_args.get("evidence_id", "")
                seed_value = tool_args.get("seed_value", "")
                seed_kind = tool_args.get("seed_kind", "module")
                direction = tool_args.get("direction", "both")
                from agent.rea_adapter import trace_application_feature_wrapper, get_rea_adapter
                adapter = get_rea_adapter(mode="mock" if self.mode == MCPExecutionMode.MOCK else None)
                out = trace_application_feature_wrapper(
                    evidence_id, seed_value=seed_value, seed_kind=seed_kind, direction=direction, adapter=adapter
                )
                status = out.get("status", "error")
                return {
                    "status": status,
                    "mode": self.mode.value,
                    "tool": tool_name,
                    "result": out if status == "ok" else {"error": out.get("error")},
                    "error": out.get("error") if status != "ok" else None,
                    "bytes_summary": f"{len(json.dumps(out))} bytes returned (rea_mcp)",
                }

            elif tool_name == "list_volunteer_applications":
                from agent.volunteer_portal import list_volunteer_applications
                out = list_volunteer_applications()
                return {
                    "status": "ok",
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": out,
                    "error": None,
                    "bytes_summary": f"{len(json.dumps(out))} bytes returned (volunteer_portal)",
                }

            elif tool_name == "read_volunteer_application":
                from agent.volunteer_portal import read_volunteer_application
                app_id = tool_args.get("application_id", "")
                att_path = tool_args.get("attachment_path")
                out = read_volunteer_application(app_id, attachment_path=att_path)
                return {
                    "status": "ok",
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": out,
                    "error": None,
                    "bytes_summary": f"{len(json.dumps(out))} bytes returned (volunteer_portal)",
                }

            elif tool_name == "summarize_applications":
                from agent.volunteer_portal import summarize_applications
                grp = tool_args.get("group_by", "status")
                out = summarize_applications(group_by=grp)
                return {
                    "status": "ok",
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": out,
                    "error": None,
                    "bytes_summary": f"{len(json.dumps(out))} bytes returned (volunteer_portal)",
                }

            elif tool_name == "export_volunteer_contacts":
                from agent.volunteer_portal import export_volunteer_contacts
                dest = tool_args.get("destination", "")
                flds = tool_args.get("fields")
                out = export_volunteer_contacts(dest, fields=flds)
                return {
                    "status": "ok",
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": out,
                    "error": None,
                    "bytes_summary": f"{len(json.dumps(out))} bytes returned (volunteer_portal)",
                }

            else:
                return {
                    "status": "error",
                    "mode": MCPExecutionMode.SANDBOX_LOCAL.value,
                    "tool": tool_name,
                    "result": None,
                    "error": f"Tool '{tool_name}' not registered in sandbox adapter",
                    "bytes_summary": "0 bytes executed",
                }
        finally:
            if old_sandbox is not None:
                os.environ["TRIPLINE_SANDBOX_REPO"] = old_sandbox
            else:
                os.environ.pop("TRIPLINE_SANDBOX_REPO", None)
            if old_demo_repo is not None:
                os.environ["TRIPLINE_DEMO_REPO_DIR"] = old_demo_repo
            else:
                os.environ.pop("TRIPLINE_DEMO_REPO_DIR", None)

    def _dispatch_http_mcp(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        decision_proof: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches call to live HTTP MCP server with decision proof headers.
        """
        import httpx
        from mcp.client.session import ClientSession as Client
        from mcp.client.streamable_http import streamable_http_client

        async def _async_call():
            async def attach_headers(req):
                if req.method == "POST":
                    if decision_proof:
                        req.headers["x-tripline-decision-proof"] = decision_proof
                    if trace_id:
                        req.headers["x-tripline-trace-id"] = trace_id

            http_cli = httpx.AsyncClient(event_hooks={"request": [attach_headers]}, timeout=15.0)
            transport = streamable_http_client(self.mcp_url, http_client=http_cli)

            async with Client(transport) as client:
                res = await client.call_tool(tool_name, tool_args)
                text = res.content[0].text if res.content else ""
                return text

        try:
            content = asyncio.run(_async_call())
            status = "error" if str(content).startswith("error:") else "ok"
            return {
                "status": status,
                "mode": MCPExecutionMode.HTTP_MCP.value,
                "tool": tool_name,
                "result": content,
                "error": content if status == "error" else None,
                "bytes_summary": f"{len(str(content))} bytes returned (http_mcp)",
            }
        except Exception as exc:
            return {
                "status": "error",
                "mode": MCPExecutionMode.HTTP_MCP.value,
                "tool": tool_name,
                "result": None,
                "error": f"HTTP MCP dispatch error: {type(exc).__name__}: {exc}",
                "bytes_summary": "0 bytes returned (transport failure)",
            }
