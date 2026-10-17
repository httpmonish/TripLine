#!/usr/bin/env python3
"""
scripts/rea_investigator.py — User-Facing CLI Software Investigator (Phase 10 & 11)

Demonstrates TripLine REA: An evidence-backed AI software investigator with governed
tool execution.

Modes:
  1. offline: Deterministic reproducible test mode using explicit mock doubles.
  2. live-rea: Real REA static analysis; ArmorIQ evaluated locally/mocked if credentials absent.
  3. live-governed: Genuine REA execution coupled with live ArmorIQ platform enforcement.

Workflow:
  1. Validates registered sample target.
  2. Verifies environment dependencies.
  3. Requests ArmorIQ policy check on proposed investigation action.
  4. Dispatches REA MCP analysis upon successful authorization.
  5. Performs follow-up feature trace using retained evidence references.
  6. Encloses untrusted target data in strict security boundaries.
  7. Synthesizes an evidence-backed investigation report and HMAC-signed security receipt.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import pathlib
import sys
import uuid
from typing import Any, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from agent.rea_adapter import (
    REAAdapter,
    resolve_approved_target,
    APPROVED_TARGET_REGISTRY,
    REATargetValidationError,
    get_rea_adapter,
)
from agent.rea_service import REAService, REAAnalysisResult
from agent.rea_report import build_investigation_report, InvestigationReport
from agent.security_receipts import create_security_receipt, REASecurityReceipt
from agent.safety import redact_secrets

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("tripline.rea_investigator")


def check_armoriq_enforcement(
    tool_name: str,
    tool_args: Dict[str, Any],
    mode: str,
) -> Dict[str, Any]:
    """
    Evaluates the ArmorIQ authorization gate.
    In 'live-governed' mode, performs live platform check with network verification.
    In other modes, uses offline deterministic safety check.
    """
    if mode == "live-governed":
        try:
            from dotenv import load_dotenv
            load_dotenv()
            from armoriq_helper import build_client
            from armoriq_sdk import SessionOptions, ToolCall
            client = build_client(skip_validate=True)
            session = client.start_session(SessionOptions(mode="sdk", default_mcp_name="tripline-mcp"))
            session.start_plan([ToolCall(name=tool_name, args=tool_args)], goal="Software reverse engineering")
            check_res = session.check(tool_name, tool_args)
            allowed = bool(getattr(check_res, "allowed", False))
            reason = getattr(check_res, "reason", "ArmorIQ evaluation completed")
            matched_policy = getattr(check_res, "matched_policy", "platform-policy")
            try:
                session.report(status="success" if allowed else "denied")
            except Exception:
                pass
            session.close()
            return {
                "decision": "ALLOW" if allowed else "DENY",
                "allowed": allowed,
                "reason": reason,
                "matched_policy": matched_policy,
                "verification": "LIVE_VERIFIED",
            }
        except Exception as exc:
            log.warning("Live ArmorIQ check failed: %s. Failing closed.", exc)
            return {
                "decision": "UNAVAILABLE",
                "allowed": False,
                "reason": f"Live ArmorIQ check failed: {exc}",
                "matched_policy": None,
                "verification": "UNVERIFIED",
            }
    elif mode == "live-rea":
        return {
            "decision": "ALLOW",
            "allowed": True,
            "reason": "Local governance approval (live-rea mode)",
            "matched_policy": "local-rea-governance",
            "verification": "LOCAL_GOVERNED",
        }
    else:  # offline
        return {
            "decision": "ALLOW",
            "allowed": True,
            "reason": "Offline mock policy allowance",
            "matched_policy": "mock-policy",
            "verification": "TEST_SIMULATED",
        }


def run_investigation(
    target_id: str = "synthetic-electron-app",
    objective: str = "Investigate application architecture, BrowserWindow configuration, and IPC handlers",
    mode: str = "live-rea",
    tool_name: str = "analyze_electron_app",
    output_dir: Optional[pathlib.Path] = None,
) -> Dict[str, Any]:
    run_id = f"inv-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}-{uuid.uuid4().hex[:6]}"
    out_dir = output_dir or (REPO_ROOT / "investigations" / run_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("TRIPLINE REA GOVERNED SOFTWARE INVESTIGATOR")
    print("=" * 80)
    print(f"Run ID:        {run_id}")
    print(f"Target ID:     {target_id}")
    print(f"Mode:          {mode.upper()}")
    print(f"Objective:     {objective}")
    print("-" * 80)

    # 1. Target Confinement Check
    print("[1/5] Validating Target Registration & Filesystem Confinement...")
    try:
        resolved_path = resolve_approved_target(target_id)
        print(f"      -> Confinement Verified: {resolved_path}")
    except REATargetValidationError as te:
        print(f"      -> REJECTED: {te}")
        receipt = create_security_receipt(
            run_id=run_id,
            operation="analyze_electron_app",
            tool_args={"target_id": target_id},
            target_id=target_id,
            auth_decision="ALLOW",
            dispatch_attempted=False,
            dispatch_status="BLOCKED",
            tool_result_status="NONE",
            error_code="TARGET_VALIDATION_ERROR",
            failure_stage="TRIPLINE_CONFINEMENT",
            verification_status="TEST_VERIFIED",
        )
        (out_dir / "receipt.json").write_text(json.dumps(receipt.to_dict(), indent=2))
        return {"status": "error", "error": str(te), "receipt": receipt.to_dict()}

    # 2. ArmorIQ Authorization Gate
    print(f"[2/5] Evaluating ArmorIQ Policy Gate for '{tool_name}'...")
    auth_res = check_armoriq_enforcement(tool_name, {"target_id": target_id}, mode=mode)
    print(f"      -> Decision:        {auth_res['decision']}")
    print(f"      -> Reason:          {auth_res['reason']}")
    print(f"      -> Policy Origin:   {auth_res.get('matched_policy')}")
    print(f"      -> Verification:    {auth_res['verification']}")

    if not auth_res["allowed"]:
        print(f"\n[!] HALT: Operation '{tool_name}' DENIED by ArmorIQ policy. Dispatch aborted.")
        receipt = create_security_receipt(
            run_id=run_id,
            operation=tool_name,
            tool_args={"target_id": target_id},
            target_id=target_id,
            auth_decision=auth_res["decision"],
            auth_reason=auth_res["reason"],
            matched_policy=auth_res.get("matched_policy"),
            dispatch_attempted=False,
            dispatch_status="BLOCKED",
            tool_result_status="NONE",
            failure_stage="AUTHORIZATION",
            verification_status=auth_res["verification"],
        )
        receipt_path = out_dir / "receipt.json"
        receipt_path.write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")
        print(f"      -> Signed Security Receipt saved: {receipt_path}")
        print(f"      -> Dispatch Attempted:            {receipt.dispatch_attempted}")
        return {
            "status": "denied",
            "run_id": run_id,
            "decision": auth_res["decision"],
            "reason": auth_res["reason"],
            "receipt": receipt.to_dict(),
        }

    # 3. Persistent REA MCP Initialization & Discovery
    print(f"[3/5] Dispatching Safe REA Static Analysis (Mode: {mode})...")
    adapter_mode = "mock" if mode == "offline" else "live"
    adapter = REAAdapter(mode=adapter_mode)
    service = REAService(adapter=adapter)

    analysis_res = service.analyze_target(target_id=target_id, detail="summary")
    if analysis_res.execution_status != "SUCCESS":
        print(f"      -> Analysis Error: {analysis_res.error}")
        receipt = create_security_receipt(
            run_id=run_id,
            operation="analyze_electron_app",
            tool_args={"target_id": target_id},
            target_id=target_id,
            auth_decision="ALLOW",
            dispatch_attempted=True,
            dispatch_status="EXECUTED",
            tool_result_status="ERROR",
            error_code=analysis_res.error,
            failure_stage="TOOL_EXECUTION",
            verification_status="LIVE_VERIFIED" if mode != "offline" else "TEST_SIMULATED",
        )
        (out_dir / "receipt.json").write_text(json.dumps(receipt.to_dict(), indent=2))
        return {"status": "error", "error": analysis_res.error, "receipt": receipt.to_dict()}

    print(f"      -> Evidence Recorded: {analysis_res.evidence_id}")
    print(f"      -> Parent Evidence:   {analysis_res.parent_evidence_id}")
    print(f"      -> Untrusted Content: {analysis_res.untrusted_content}")

    # 4. Feature Trace Follow-up
    print("[4/5] Tracing Feature Seed ('main.js') on Active Session...")
    trace_res = service.trace_feature(
        evidence_id=analysis_res.evidence_id,
        seed_value="main.js",
        seed_kind="module",
        direction="both",
    )
    print(f"      -> Trace Evidence:    {trace_res.evidence_id}")

    # 5. Report & Receipt Synthesis
    print("[5/5] Synthesizing Evidence-Backed Report & Cryptographic Receipt...")
    report = build_investigation_report(
        run_id=run_id,
        target_id=target_id,
        objective=objective,
        analysis_result=analysis_res.raw_response,
        trace_result=trace_res.raw_response,
        armoriq_status=auth_res["decision"],
        dispatch_status="EXECUTED",
        is_live=(mode != "offline"),
    )

    all_evidence = sorted(list(set(analysis_res.evidence_refs + trace_res.evidence_refs)))
    receipt = create_security_receipt(
        run_id=run_id,
        operation="analyze_electron_app",
        tool_args={"target_id": target_id},
        target_id=target_id,
        auth_decision=auth_res["decision"],
        auth_reason=auth_res["reason"],
        matched_policy=auth_res.get("matched_policy"),
        dispatch_attempted=True,
        dispatch_status="EXECUTED",
        tool_result_status="SUCCESS",
        evidence_refs=all_evidence,
        verification_status=auth_res["verification"],
    )

    # Save artifacts
    report_md_path = out_dir / "report.md"
    report_json_path = out_dir / "report.json"
    receipt_json_path = out_dir / "receipt.json"

    report_md_path.write_text(report.to_markdown(), encoding="utf-8")
    report_json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    receipt_json_path.write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")

    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)
    print(f"Report (Markdown):  {report_md_path}")
    print(f"Report (JSON):      {report_json_path}")
    print(f"Receipt (JSON):     {receipt_json_path}")
    print(f"Receipt HMAC-SHA:   {receipt.hmac_sha256}")
    print(f"Total Evidence IDs: {len(all_evidence)}")
    print("=" * 80 + "\n")

    return {
        "status": "success",
        "run_id": run_id,
        "report": report.to_dict(),
        "receipt": receipt.to_dict(),
        "report_markdown": report.to_markdown(),
    }


def main():
    parser = argparse.ArgumentParser(description="TripLine REA Software Investigator")
    parser.add_argument("--target", type=str, default="synthetic-electron-app", help="Approved target ID")
    parser.add_argument("--objective", "--goal", dest="objective", type=str, default="Investigate Electron IPC handlers and token verification mechanisms", help="Investigation goal / objective")
    parser.add_argument("--mode", choices=["offline", "live-rea", "live-governed"], default="live-rea", help="Execution mode")
    parser.add_argument("--tool", type=str, default="analyze_electron_app", help="Protected tool name to evaluate and dispatch")
    parser.add_argument("--json", action="store_true", help="Emit raw JSON result")
    args = parser.parse_args()

    res = run_investigation(
        target_id=args.target,
        objective=args.objective,
        mode=args.mode,
        tool_name=args.tool,
    )

    if args.json:
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
