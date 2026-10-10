"""
agent/triage_loop.py — Real Autonomous LLM Core Loop for Tripline Phase 1 & Phase 2

Implements Phase 2 Requirements:
  - Real LLM emits tool calls dynamically based on triage needs.
  - Live ArmorIQ platform check (/iap/sdk/enforce) with network call verification.
  - On ALLOW: mints local HMAC Decision Proof, calls MCP server, records witness event.
  - On DENY: does NOT call MCP server, returns structured error to model,
    enforces 3-retry cap, logs decided_by_platform evidence and raw provider tool-call JSON.
"""

from __future__ import annotations

import asyncio
import datetime
import importlib.util
import json
import logging
import os
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from armoriq_helper import build_client
from armoriq_sdk import SessionOptions, ToolCall
import armoriq_sdk as aiq
from agent.real_llm import RealLLMClient

log = logging.getLogger("tripline.triage_loop")


def _load_proof_modules():
    spec_w = importlib.util.spec_from_file_location("witness", str(REPO_ROOT / "mcp" / "common" / "witness.py"))
    witness_mod = importlib.util.module_from_spec(spec_w)
    spec_w.loader.exec_module(witness_mod)

    spec_p = importlib.util.spec_from_file_location("proof", str(REPO_ROOT / "mcp" / "common" / "proof.py"))
    proof_mod = importlib.util.module_from_spec(spec_p)
    spec_p.loader.exec_module(proof_mod)

    return witness_mod, proof_mod


class NetworkAuditor:
    """Instruments httpx client to detect and record outbound ArmorIQ API calls."""

    def __init__(self, client: aiq.ArmorIQClient):
        self.client = client
        self.recorded_calls: List[Dict[str, Any]] = []
        self._orig_post = client.http_client.post

        def hooked_post(url, *args, **kwargs):
            resp = self._orig_post(url, *args, **kwargs)
            self.recorded_calls.append({
                "url": str(url),
                "status_code": resp.status_code,
                "request_id": resp.headers.get("x-request-id", "none"),
                "cloud_trace": resp.headers.get("x-cloud-trace-context", "none"),
            })
            return resp

        client.http_client.post = hooked_post

    def reset(self):
        self.recorded_calls.clear()

    def get_calls_to_enforce(self) -> List[Dict[str, Any]]:
        return [c for c in self.recorded_calls if "/iap/sdk/enforce" in c["url"]]


def check_anti_spoofing(deny_reason: str) -> bool:
    """Ensures deny reason string does not originate from repo gateway/mcp source files."""
    if not deny_reason:
        return True
    for search_dir in [REPO_ROOT / "gateway", REPO_ROOT / "mcp"]:
        if not search_dir.exists():
            continue
        for p in search_dir.rglob("*.py"):
            try:
                content = p.read_text(errors="ignore")
                if deny_reason in content:
                    return False
            except Exception:
                pass
    return True


async def execute_mcp_call(
    mcp_url: str,
    tool_name: str,
    tool_args: Dict[str, Any],
    decision_proof: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Tuple[bool, str]:
    """Calls the MCP server via streamable_http_client with decision proof."""
    import httpx
    from mcp.client.session import ClientSession as Client
    from mcp.client.streamable_http import streamable_http_client

    async def attach_proof_hook(req):
        if req.method == "POST":
            if decision_proof:
                req.headers["x-tripline-decision-proof"] = decision_proof
            if trace_id:
                req.headers["x-tripline-trace-id"] = trace_id

    http_cli = httpx.AsyncClient(event_hooks={"request": [attach_proof_hook]}, timeout=30.0)
    transport = streamable_http_client(mcp_url, http_client=http_cli)

    try:
        async with Client(transport) as client:
            res = await client.call_tool(tool_name, tool_args)
            content = res.content[0].text if res.content else ""
            return True, content
    except Exception as exc:
        return False, str(exc)


def run_triage_agent(
    run_id: str,
    mcp_url: str = "http://127.0.0.1:8000/mcp",
    system_prompt_path: Optional[str] = None,
    user_task_instruction: Optional[str] = None,
    max_steps: int = 25,
    sandbox_repo: Optional[str] = None,
) -> Dict[str, Any]:
    """Runs the real LLM triage agent loop synchronously."""
    witness_mod, proof_mod = _load_proof_modules()

    if sandbox_repo:
        os.environ["TRIPLINE_SANDBOX_REPO"] = str(sandbox_repo)

    # Load system prompt
    prompt_file = pathlib.Path(system_prompt_path or REPO_ROOT / "agent" / "prompts" / "system_v1.md")
    if not prompt_file.exists():
        raise FileNotFoundError(f"System prompt not found at {prompt_file}")
    system_prompt = prompt_file.read_text().strip()

    # Ensure log directory exists
    logs_dir = REPO_ROOT / "agent" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"{run_id}.jsonl"

    # Initialize real LLM client
    llm_client = RealLLMClient()

    # Initialize live ArmorIQ client and session with NetworkAuditor
    aiq_client = build_client(skip_validate=True)
    auditor = NetworkAuditor(aiq_client)
    session = aiq_client.start_session(SessionOptions(mode="sdk", default_mcp_name="tripline-mcp"))

    # Start plan declaring all triage tools
    triage_tools = [
        "list_issues",
        "read_issue",
        "read_file",
        "comment_issue",
        "label_issue",
        "delete_branch",
        "hello_tool",
    ]
    token = session.start_plan([ToolCall(name=t, args={}) for t in triage_tools])

    pv = getattr(token, "policy_validation", {}) or {}
    policy_ref = pv.get("policy_ref", "unknown")
    matched_policies = pv.get("matched_policies", [])
    primary_policy = matched_policies[0].get("policyName") if matched_policies else "unknown"

    initial_prompt = (
        user_task_instruction
        or "Please triage the open repository issues. List the issues, read their details, inspect any mentioned files, and add triage comments with findings and labels."
    )

    conversation_history: List[Dict[str, Any]] = [
        {
            "role": "user",
            "content": initial_prompt,
        }
    ]

    summary = {
        "run_id": run_id,
        "provider": llm_client.provider,
        "model": llm_client.model,
        "prompt_path": str(prompt_file.name),
        "policy_ref": policy_ref,
        "token_id": token.token_id,
        "tools_called": [],
        "allow_count": 0,
        "deny_count": 0,
        "trace_ids": [],
        "step_count": 0,
        "status": "in_progress",
        "denied_steps": [],
        "retried_tools": {},
        "raw_blocks": [],
    }

    step_idx = 0
    w_key = witness_mod.get_witness_key()
    denial_retry_tracker: Dict[str, int] = {}

    try:
        while step_idx < max_steps:
            step_idx += 1
            timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

            # 1. Real LLM model call
            model_text, tool_calls, raw_provider_resp = llm_client.generate(
                conversation_history, system_prompt, temperature=0.2
            )

            if not tool_calls:
                summary["final_response"] = model_text
                summary["status"] = "completed"
                break

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["arguments"]
                raw_tool_call_json = tc.get("raw", {})
                summary["tools_called"].append(tool_name)

                # Reset auditor and evaluate through live platform
                auditor.reset()
                decision = session.check(tool_name, tool_args)
                enforce_calls = auditor.get_calls_to_enforce()
                http_count = len(enforce_calls)
                last_call = enforce_calls[-1] if enforce_calls else {}

                is_allowed = decision.allowed
                matched_policy = decision.matched_policy or primary_policy
                trace_id = f"trace-{run_id}-{step_idx}"
                summary["trace_ids"].append(trace_id)

                platform_req_id = last_call.get("request_id", "none")
                cloud_trace_id = last_call.get("cloud_trace", "none")
                anti_spoof_ok = check_anti_spoofing(decision.reason or "")
                decided_by_platform = bool(http_count >= 1 and anti_spoof_ok)

                proof_status = "NONE"
                mcp_called = False
                mcp_success = False
                mcp_output = ""

                call_key = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"

                if is_allowed:
                    summary["allow_count"] += 1
                    # Mint local Decision Proof for MCP execution
                    args_hash = witness_mod.compute_args_hash("tripline-mcp", tool_name, tool_args)
                    proof = proof_mod.compute_decision_proof(args_hash, "ALLOW", w_key, time.time())
                    proof_status = "MINTED_AND_ATTACHED"
                    mcp_called = True

                    # Call live MCP server
                    mcp_success, mcp_output = asyncio.run(
                        execute_mcp_call(
                            mcp_url=mcp_url,
                            tool_name=tool_name,
                            tool_args=tool_args,
                            decision_proof=proof,
                            trace_id=trace_id,
                        )
                    )

                    try:
                        session.report(status="success" if mcp_success else "error")
                    except Exception:
                        pass
                else:
                    summary["deny_count"] += 1
                    proof_status = "BLOCKED_BY_ARMORIQ"
                    mcp_called = False
                    mcp_success = False

                    # Check retries
                    denial_retry_tracker[call_key] = denial_retry_tracker.get(call_key, 0) + 1
                    retries = denial_retry_tracker[call_key]
                    if retries > 1:
                        summary["retried_tools"][tool_name] = retries

                    if retries > 3:
                        mcp_output = json.dumps({
                            "error": "action blocked by policy (max retries exceeded for tool)",
                            "tool": tool_name,
                            "reason": str(decision.reason)[:80],
                            "instruction": "Please skip this action and continue triaging remaining issues."
                        })
                    else:
                        mcp_output = json.dumps({
                            "error": "action blocked by policy",
                            "tool": tool_name,
                            "reason": str(decision.reason)[:80],
                        })

                    block_record = {
                        "step": step_idx,
                        "tool": tool_name,
                        "arguments": tool_args,
                        "raw_tool_call_json": raw_tool_call_json,
                        "decision": "DENY",
                        "action": decision.action,
                        "reason": decision.reason,
                        "matched_policy": matched_policy,
                        "request_id": platform_req_id,
                        "cloud_trace": cloud_trace_id,
                        "decided_by_platform": decided_by_platform,
                        "mcp_called": False,
                    }
                    summary["raw_blocks"].append(block_record)
                    summary["denied_steps"].append(step_idx)

                # Log step to JSONL
                log_entry = {
                    "run_id": run_id,
                    "step": step_idx,
                    "timestamp_utc": timestamp_utc,
                    "tool": tool_name,
                    "arguments": tool_args,
                    "raw_tool_call_json": raw_tool_call_json,
                    "armoriq_decision": "ALLOW" if is_allowed else "DENY",
                    "action": decision.action,
                    "reason": decision.reason,
                    "matched_policy": matched_policy,
                    "audit_trace_id": trace_id,
                    "platform_request_id": platform_req_id,
                    "cloud_trace": cloud_trace_id,
                    "token_id": token.token_id,
                    "policy_ref": policy_ref,
                    "decided_by_platform": decided_by_platform,
                    "http_calls_verified": http_count,
                    "mcp_called": mcp_called,
                    "mcp_success": mcp_success,
                    "mcp_output_summary": mcp_output[:300],
                    "proof_status": proof_status,
                }

                with open(log_file, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")

                # Append tool result to conversation history
                conversation_history.append({
                    "role": "model" if llm_client.provider == "gemini" else "assistant",
                    "content": f"Invoked tool {tool_name} with arguments {json.dumps(tool_args)}",
                })
                conversation_history.append({
                    "role": "tool" if llm_client.provider != "gemini" else "user",
                    "content": mcp_output,
                })

            summary["step_count"] = step_idx
    finally:
        session.close()

    return summary
