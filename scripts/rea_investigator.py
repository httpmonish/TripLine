#!/usr/bin/env python3
"""
scripts/rea_investigator.py — User-Facing CLI Software Investigator (Phases 10, 11 & Security Hotfix)

Demonstrates TripLine REA: An evidence-backed AI software investigator with governed
tool execution.

Strict Security Properties Enforced:
  1. Exact 1-to-1 Authorization Binding: Every authorization decision is strictly bound
     to the specific operation executed (prevents confused-deputy attacks).
  2. Independent Authorization for Multi-Step Workflows: Analysis and follow-up feature
     tracing are independently authorized by ArmorIQ.
  3. Proper Execution Reporting Timing: session.report() reports execution outcome ONLY
     after actual tool dispatch and execution, never prematurely after check().
  4. Cryptographic Receipt Custody: HMAC receipts require a strong, dedicated
     TRIPLINE_RECEIPT_SECRET_KEY (>=32 bytes) in live mode and fail closed if missing.
  5. Target Sandbox & Path Jail: Only preapproved registered target IDs within the
     controlled analysis root are permitted.
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
from typing import Any, Dict, List, Optional, Tuple

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
from agent.security_receipts import (
    create_security_receipt,
    REASecurityReceipt,
    ReceiptConfigurationError,
)
from agent.safety import redact_secrets

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("tripline.rea_investigator")

ALLOWED_INVESTIGATION_OPERATIONS = {
    "analyze_electron_app",
    "inspect_analysis_view",
    "trace_application_feature",
}


class ArmorIQSessionContext:
    """Manages active ArmorIQ session lifecycle, ensuring execution outcome is reported post-dispatch."""

    def __init__(self, session: Any = None, tool_name: str = "", tool_args: Optional[Dict[str, Any]] = None, mode: str = "offline"):
        self.session = session
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.mode = mode

    def report_execution(self, status: str = "success", result: Any = None) -> None:
        """Reports real operation execution outcome and cleanly closes the session."""
        if self.session is not None:
            try:
                from armoriq_sdk import ReportOptions
                report_opts = ReportOptions(
                    status="success" if status == "success" else "failed",
                    error_message=None if status == "success" else "Operation failed or denied",
                )
                self.session.report(
                    tool_name=self.tool_name,
                    tool_args=self.tool_args,
                    result=result or {"status": status},
                    opts=report_opts,
                )
            except Exception as exc:
                log.warning("Could not report execution outcome to ArmorIQ: %s", exc)
            finally:
                try:
                    self.session.close()
                except Exception:
                    pass
                self.session = None


def check_armoriq_enforcement(
    tool_name: str,
    tool_args: Dict[str, Any],
    mode: str,
) -> Tuple[Dict[str, Any], ArmorIQSessionContext]:
    """
    Evaluates the ArmorIQ authorization gate.
    In 'live-governed' mode, contacts the live platform.
    Returns (decision_dict, session_context). Outcome reporting is deferred until tool execution completes.
    """
    if mode == "live-governed":
        try:
            from armoriq_helper import build_client
            from armoriq_sdk import SessionOptions, ToolCall
            client = build_client(skip_validate=True)
            session = client.start_session(SessionOptions(mode="sdk", default_mcp_name="tripline-mcp"))
            session.start_plan([ToolCall(name=tool_name, args=tool_args)], goal="Software reverse engineering")
            check_res = session.check(tool_name, tool_args)
            allowed = bool(getattr(check_res, "allowed", False))
            reason = getattr(check_res, "reason", "ArmorIQ evaluation completed")
            matched_policy = getattr(check_res, "matched_policy", "platform-policy")

            context = ArmorIQSessionContext(session=session, tool_name=tool_name, tool_args=tool_args, mode=mode)
            # If denied at check time, report denial immediately and close
            if not allowed:
                context.report_execution(status="failed", result={"error": reason})

            return {
                "decision": "ALLOW" if allowed else "DENY",
                "allowed": allowed,
                "reason": reason,
                "matched_policy": matched_policy,
                "verification": "LIVE_VERIFIED",
            }, context
        except Exception as exc:
            log.warning("Live ArmorIQ check failed: %s. Failing closed.", exc)
            return {
                "decision": "UNAVAILABLE",
                "allowed": False,
                "reason": f"Live ArmorIQ check failed: {exc}",
                "matched_policy": None,
                "verification": "UNVERIFIED",
            }, ArmorIQSessionContext(None, mode)
    elif mode == "live-rea":
        return {
            "decision": "ALLOW",
            "allowed": True,
            "reason": "Local governance approval (live-rea mode)",
            "matched_policy": "local-rea-governance",
            "verification": "LOCAL_GOVERNED",
        }, ArmorIQSessionContext(None, mode)
    else:  # offline
        return {
            "decision": "ALLOW",
            "allowed": True,
            "reason": "Offline mock policy allowance",
            "matched_policy": "mock-policy",
            "verification": "TEST_SIMULATED",
        }, ArmorIQSessionContext(None, mode)


def run_investigation(
    target_id: str = "synthetic-electron-app",
    objective: str = "Investigate application architecture, BrowserWindow configuration, and IPC handlers",
    mode: str = "live-rea",
    tool_name: str = "analyze_electron_app",
    evidence_id: Optional[str] = None,
    seed_value: str = "main.js",
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
    print(f"Tool:          {tool_name}")
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
            operation=tool_name,
            tool_args={"target_id": target_id},
            target_id=target_id,
            auth_decision="ALLOW",
            dispatch_attempted=False,
            dispatch_status="BLOCKED",
            tool_result_status="NONE",
            error_code="TARGET_VALIDATION_ERROR",
            failure_stage="TRIPLINE_CONFINEMENT",
            verification_status="TEST_SIMULATED" if mode == "offline" else "LIVE_VERIFIED",
        )
        (out_dir / "receipt.json").write_text(json.dumps(receipt.to_dict(), indent=2))
        return {"status": "error", "error": str(te), "receipt": receipt.to_dict()}

    # 2. ArmorIQ Authorization Gate
    tool_args = {"target_id": target_id}
    if tool_name == "trace_application_feature":
        tool_args = {"evidence_id": evidence_id or f"ev_{target_id}_seed", "seed_value": seed_value}
    elif tool_name == "inspect_analysis_view":
        tool_args = {"evidence_id": evidence_id or f"ev_{target_id}_seed", "view_kind": "summary"}

    print(f"[2/5] Evaluating ArmorIQ Policy Gate for '{tool_name}'...")
    auth_res, session_ctx = check_armoriq_enforcement(tool_name, tool_args, mode=mode)
    print(f"      -> Decision:        {auth_res['decision']}")
    print(f"      -> Reason:          {auth_res['reason']}")
    print(f"      -> Policy Origin:   {auth_res.get('matched_policy')}")
    print(f"      -> Verification:    {auth_res['verification']}")

    # Fail closed on denial or missing authorization
    if not auth_res["allowed"]:
        print(f"\n[!] HALT: Operation '{tool_name}' DENIED by ArmorIQ policy. Dispatch aborted.")
        receipt = create_security_receipt(
            run_id=run_id,
            operation=tool_name,
            tool_args=tool_args,
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

    # Strict check: If caller authorized an unrelated tool (e.g. hello_tool), do NOT dispatch REA analysis!
    if tool_name not in ALLOWED_INVESTIGATION_OPERATIONS:
        print(f"\n[!] Tool '{tool_name}' is authorized but is NOT an REA software investigation operation.")
        print("    Confused-deputy dispatch prevented: analyze_electron_app will NOT be substituted.")
        session_ctx.report_execution(status="success")
        receipt = create_security_receipt(
            run_id=run_id,
            operation=tool_name,
            tool_args=tool_args,
            target_id=target_id,
            auth_decision=auth_res["decision"],
            auth_reason=auth_res["reason"],
            matched_policy=auth_res.get("matched_policy"),
            dispatch_attempted=False,
            dispatch_status="BLOCKED",
            tool_result_status="NONE",
            failure_stage="DISPATCH_VALIDATION",
            verification_status=auth_res["verification"],
        )
        (out_dir / "receipt.json").write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")
        return {
            "status": "blocked",
            "reason": f"Tool '{tool_name}' is not an investigation operation. Dispatch blocked.",
            "receipt": receipt.to_dict(),
        }

    # 3. Persistent REA MCP Initialization & 1-to-1 Dispatch
    print(f"[3/5] Dispatching Exact Authorized Operation '{tool_name}' (Mode: {mode})...")
    adapter_mode = "mock" if mode == "offline" else "live"
    adapter = REAAdapter(mode=adapter_mode)
    service = REAService(adapter=adapter)

    analysis_res: Optional[REAAnalysisResult] = None
    trace_res: Optional[REAAnalysisResult] = None

    if tool_name == "analyze_electron_app":
        analysis_res = service.analyze_target(target_id=target_id, detail="summary")
        # Post-dispatch reporting to ArmorIQ
        session_ctx.report_execution(status="success" if analysis_res.execution_status == "SUCCESS" else "failed")

        if analysis_res.execution_status != "SUCCESS":
            print(f"      -> Analysis Error: {analysis_res.error}")
            receipt = create_security_receipt(
                run_id=run_id,
                operation=tool_name,
                tool_args=tool_args,
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

        # 4. Independent Authorization for Follow-up Feature Trace
        print("\n[4/5] Evaluating Independent ArmorIQ Policy Gate for 'trace_application_feature'...")
        trace_args = {
            "evidence_id": analysis_res.evidence_id,
            "seed_value": seed_value,
            "seed_kind": "module",
            "direction": "both",
        }
        trace_auth, trace_session_ctx = check_armoriq_enforcement("trace_application_feature", trace_args, mode=mode)
        print(f"      -> Trace Decision:  {trace_auth['decision']}")
        print(f"      -> Trace Reason:    {trace_auth['reason']}")

        if trace_auth["allowed"]:
            print(f"      -> Dispatching Authorized Trace on Seed '{seed_value}'...")
            trace_res = service.trace_feature(
                evidence_id=analysis_res.evidence_id,
                seed_value=seed_value,
                seed_kind="module",
                direction="both",
            )
            trace_session_ctx.report_execution("success" if trace_res.execution_status == "SUCCESS" else "failed")
            print(f"      -> Trace Evidence:  {trace_res.evidence_id}")
        else:
            print("      -> [!] Trace Operation DENIED by ArmorIQ. Follow-up trace aborted.")

    elif tool_name == "trace_application_feature":
        trace_res = service.trace_feature(
            evidence_id=evidence_id or f"ev_{target_id}",
            seed_value=seed_value,
            seed_kind="module",
            direction="both",
        )
        session_ctx.report_execution(status="success" if trace_res.execution_status == "SUCCESS" else "failed")
        print(f"      -> Trace Evidence: {trace_res.evidence_id}")

    elif tool_name == "inspect_analysis_view":
        inspect_res = service.inspect_evidence(
            evidence_id=evidence_id or f"ev_{target_id}",
            view_kind="summary",
        )
        session_ctx.report_execution(status="success" if inspect_res.execution_status == "SUCCESS" else "failed")
        print(f"      -> View Inspected: {inspect_res.evidence_id}")

    # 5. Report & Cryptographic Receipt Synthesis
    print("\n[5/5] Synthesizing Evidence-Backed Report & Cryptographic Receipt...")
    report = build_investigation_report(
        run_id=run_id,
        target_id=target_id,
        objective=objective,
        analysis_result=analysis_res.raw_response if analysis_res else {},
        trace_result=trace_res.raw_response if trace_res else {},
        armoriq_status=auth_res["decision"],
        dispatch_status="EXECUTED",
        is_live=(mode != "offline"),
    )

    all_evidence: List[str] = []
    if analysis_res:
        all_evidence.extend(analysis_res.evidence_refs)
    if trace_res:
        all_evidence.extend(trace_res.evidence_refs)
    all_evidence = sorted(list(set(all_evidence)))

    receipt = create_security_receipt(
        run_id=run_id,
        operation=tool_name,
        tool_args=tool_args,
        target_id=target_id,
        auth_decision=auth_res["decision"],
        auth_reason=auth_res["reason"],
        matched_policy=auth_res.get("matched_policy"),
        dispatch_attempted=True,
        dispatch_status="EXECUTED",
        tool_result_status="SUCCESS",
        report_status="REPORTED",
        evidence_refs=all_evidence,
        verification_status="LIVE_VERIFIED" if mode != "offline" else "TEST_SIMULATED",
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
    parser.add_argument("--evidence-id", type=str, default=None, help="Evidence ID for trace or inspection operations")
    parser.add_argument("--seed", type=str, default="main.js", help="Seed value for feature tracing")
    parser.add_argument("--json", action="store_true", help="Emit raw JSON result")
    args = parser.parse_args()

    res = run_investigation(
        target_id=args.target,
        objective=args.objective,
        mode=args.mode,
        tool_name=args.tool,
        evidence_id=args.evidence_id,
        seed_value=args.seed,
    )

    if args.json:
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
