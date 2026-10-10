"""
agent/triage_loop.py — Real Autonomous LLM Core Loop for Tripline Phase 1

Implements Section 4.3 of the Phase 1 specification:
  - The real LLM selects the tools and arguments dynamically based on triage needs.
  - Every tool invocation runs through live ArmorIQ enforcement (/iap/sdk/enforce).
  - Every allowed tool executes via the live MCP server with an HMAC Decision Proof.
  - Every step records raw provider tool-call JSON, ArmorIQ policy references,
    and trace correlation into agent/logs/<run_id>.jsonl.
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
from typing import Any, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from armoriq_helper import build_client
from armoriq_sdk import SessionOptions, ToolCall
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


async def execute_mcp_call(
    mcp_url: str,
    tool_name: str,
    tool_args: Dict[str, Any],
    decision_proof: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Tuple[bool, str]:
    """Calls the MCP server via streamable_http_client with decision proof."""
    import httpx2
    from mcp.client.session import ClientSession as Client
    from mcp.client.streamable_http import streamable_http_client

    async def attach_proof_hook(req):
        if req.method == "POST":
            if decision_proof:
                req.headers["x-tripline-decision-proof"] = decision_proof
            if trace_id:
                req.headers["x-tripline-trace-id"] = trace_id

    http_cli = httpx2.AsyncClient(event_hooks={"request": [attach_proof_hook]}, timeout=30.0)
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
    max_steps: int = 25,
) -> Dict[str, Any]:
    """Runs the real LLM triage agent loop synchronously."""
    witness_mod, proof_mod = _load_proof_modules()

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

    # Initialize live ArmorIQ client and session
    aiq_client = build_client(skip_validate=True)
    session = aiq_client.start_session(SessionOptions(mode="sdk", default_mcp_name="tripline-mcp"))

    # Start plan declaring all authorized triage tools
    triage_tools = ["list_issues", "read_issue", "read_file", "comment_issue", "hello_tool"]
    token = session.start_plan([ToolCall(name=t, args={}) for t in triage_tools])

    pv = getattr(token, "policy_validation", {}) or {}
    policy_ref = pv.get("policy_ref", "unknown")
    matched_policies = pv.get("matched_policies", [])
    primary_policy = matched_policies[0].get("policyName") if matched_policies else "unknown"

    conversation_history: List[Dict[str, Any]] = [
        {
            "role": "user",
            "content": "Please triage the open repository issues. List the issues, read their details, inspect any mentioned files, and add triage comments with findings and labels.",
        }
    ]

    summary = {
        "run_id": run_id,
        "provider": llm_client.provider,
        "model": llm_client.model,
        "policy_ref": policy_ref,
        "token_id": token.token_id,
        "tools_called": [],
        "allow_count": 0,
        "deny_count": 0,
        "trace_ids": [],
        "step_count": 0,
        "status": "in_progress",
    }

    step_idx = 0
    w_key = witness_mod.get_witness_key()

    try:
        while step_idx < max_steps:
            step_idx += 1
            timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

            # 1. Real LLM model call
            model_text, tool_calls, raw_provider_resp = llm_client.generate(
                conversation_history, system_prompt, temperature=0.2
            )

            if not tool_calls:
                # Model concluded its triage turn
                summary["final_response"] = model_text
                summary["status"] = "completed"
                break

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["arguments"]
                raw_tool_call_json = tc.get("raw", {})
                summary["tools_called"].append(tool_name)

                # 2. Real ArmorIQ Platform Policy Check
                decision = session.check(tool_name, tool_args)
                is_allowed = decision.allowed
                matched_policy = decision.matched_policy or primary_policy
                trace_id = f"trace-{run_id}-{step_idx}"
                summary["trace_ids"].append(trace_id)

                proof_status = "NONE"
                mcp_success = False
                mcp_output = ""

                if is_allowed:
                    summary["allow_count"] += 1
                    # 3. Mint local Decision Proof for MCP execution
                    args_hash = witness_mod.compute_args_hash("tripline-mcp", tool_name, tool_args)
                    proof = proof_mod.compute_decision_proof(args_hash, "ALLOW", w_key, time.time())
                    proof_status = "MINTED_AND_ATTACHED"

                    # 4. Call live MCP server
                    mcp_success, mcp_output = asyncio.run(
                        execute_mcp_call(
                            mcp_url=mcp_url,
                            tool_name=tool_name,
                            tool_args=tool_args,
                            decision_proof=proof,
                            trace_id=trace_id,
                        )
                    )

                    # 5. Report execution to ArmorIQ
                    try:
                        session.report(status="success" if mcp_success else "error")
                    except Exception:
                        pass
                else:
                    summary["deny_count"] += 1
                    proof_status = "BLOCKED_BY_ARMORIQ"
                    mcp_output = f"ArmorIQ Policy Blocked: {decision.reason}"

                # 6. Log step to JSONL
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
                    "token_id": token.token_id,
                    "policy_ref": policy_ref,
                    "mcp_success": mcp_success,
                    "mcp_output_summary": mcp_output[:250],
                    "proof_status": proof_status,
                }

                with open(log_file, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")

                # 7. Append tool result to conversation history
                conversation_history.append({
                    "role": "model" if llm_client.provider == "gemini" else "assistant",
                    "content": f"Tool call {tool_name} with args {tool_args}",
                })
                conversation_history.append({
                    "role": "tool" if llm_client.provider != "gemini" else "user",
                    "content": mcp_output,
                })

            summary["step_count"] = step_idx
    finally:
        session.close()

    return summary
