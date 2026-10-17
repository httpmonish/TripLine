"""
agent/security_receipts.py — Verifiable Security Receipts for REA Operations (Phase 7)

Generates cryptographically signed, immutable audit receipts for every protected REA
investigation step. Strictly distinguishes:
1. Model proposal
2. ArmorIQ policy check
3. TripLine target boundary / path confinement
4. MCP tool dispatch attempt
5. Tool execution outcome
6. ArmorIQ post-execution audit report
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import hmac
import json
import pathlib
from typing import Any, Dict, List, Optional

from agent.safety import redact_secrets

import os

def get_receipt_hmac_key() -> bytes:
    """
    Retrieves the HMAC secret key.
    Resolution order:
      1. Environment variable TRIPLINE_RECEIPT_SECRET_KEY
      2. .tripline/witness_key.txt (matches the repository witness signing standard)
      3. Secure default fixed key for deterministic offline testing
    """
    env_key = os.environ.get("TRIPLINE_RECEIPT_SECRET_KEY", "")
    if env_key:
        return env_key.encode("utf-8")
    key_path = pathlib.Path(__file__).resolve().parent.parent / ".tripline" / "witness_key.txt"
    if key_path.exists():
        try:
            return key_path.read_bytes().strip()
        except Exception:
            pass
    return b"tripline_receipt_secret_key_fixed"

RECEIPT_HMAC_KEY = get_receipt_hmac_key()


@dataclasses.dataclass
class REASecurityReceipt:
    receipt_id: str
    run_id: str
    timestamp_utc: str
    target_id: Optional[str]
    operation: str
    normalized_arguments: Dict[str, Any]
    policy_check_status: str  # CHECKED, SKIPPED, ERROR
    authorization_decision: str  # ALLOW, DENY, UNAVAILABLE, NONE
    authorization_reason: Optional[str]
    matched_policy: Optional[str]
    dispatch_attempted: bool
    dispatch_status: str  # EXECUTED, BLOCKED, FAILED, NONE
    tool_result_status: str  # SUCCESS, ERROR, NONE
    report_status: str  # REPORTED, FAILED, NONE
    evidence_refs: List[str]
    error_code: Optional[str]
    failure_stage: str  # NONE, AUTHORIZATION, TRIPLINE_CONFINEMENT, DISPATCH, TOOL_EXECUTION, REPORTING
    verification_status: str  # LIVE_VERIFIED, TEST_SIMULATED, UNVERIFIED
    hmac_sha256: str = ""

    def canonical_bytes(self) -> bytes:
        data = {
            "receipt_id": self.receipt_id,
            "run_id": self.run_id,
            "timestamp_utc": self.timestamp_utc,
            "target_id": self.target_id,
            "operation": self.operation,
            "normalized_arguments": self.normalized_arguments,
            "policy_check_status": self.policy_check_status,
            "authorization_decision": self.authorization_decision,
            "authorization_reason": self.authorization_reason,
            "matched_policy": self.matched_policy,
            "dispatch_attempted": self.dispatch_attempted,
            "dispatch_status": self.dispatch_status,
            "tool_result_status": self.tool_result_status,
            "report_status": self.report_status,
            "evidence_refs": self.evidence_refs,
            "error_code": self.error_code,
            "failure_stage": self.failure_stage,
            "verification_status": self.verification_status,
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def sign(self, secret_key: bytes = RECEIPT_HMAC_KEY) -> None:
        self.hmac_sha256 = hmac.new(secret_key, self.canonical_bytes(), hashlib.sha256).hexdigest()

    def verify_signature(self, secret_key: bytes = RECEIPT_HMAC_KEY) -> bool:
        expected = hmac.new(secret_key, self.canonical_bytes(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.hmac_sha256, expected)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "run_id": self.run_id,
            "timestamp_utc": self.timestamp_utc,
            "target_id": self.target_id,
            "operation": self.operation,
            "normalized_arguments": self.normalized_arguments,
            "policy_check_status": self.policy_check_status,
            "authorization_decision": self.authorization_decision,
            "authorization_reason": self.authorization_reason,
            "matched_policy": self.matched_policy,
            "dispatch_attempted": self.dispatch_attempted,
            "dispatch_status": self.dispatch_status,
            "tool_result_status": self.tool_result_status,
            "report_status": self.report_status,
            "evidence_refs": self.evidence_refs,
            "error_code": self.error_code,
            "failure_stage": self.failure_stage,
            "verification_status": self.verification_status,
            "hmac_sha256": self.hmac_sha256,
        }


def create_security_receipt(
    run_id: str,
    operation: str,
    tool_args: Dict[str, Any],
    target_id: Optional[str] = None,
    auth_decision: str = "ALLOW",
    auth_reason: Optional[str] = None,
    matched_policy: Optional[str] = None,
    dispatch_attempted: bool = True,
    dispatch_status: str = "EXECUTED",
    tool_result_status: str = "SUCCESS",
    report_status: str = "REPORTED",
    evidence_refs: Optional[List[str]] = None,
    error_code: Optional[str] = None,
    failure_stage: str = "NONE",
    verification_status: str = "LIVE_VERIFIED",
) -> REASecurityReceipt:
    """
    Constructs and cryptographically signs a REASecurityReceipt.
    """
    clean_args = redact_secrets(tool_args)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt_id = f"RCP-REA-{hashlib.sha256(f'{run_id}-{operation}-{ts}'.encode()).hexdigest()[:12]}"

    receipt = REASecurityReceipt(
        receipt_id=receipt_id,
        run_id=run_id,
        timestamp_utc=ts,
        target_id=target_id,
        operation=operation,
        normalized_arguments=clean_args,
        policy_check_status="CHECKED" if auth_decision in ("ALLOW", "DENY") else "ERROR",
        authorization_decision=auth_decision,
        authorization_reason=auth_reason,
        matched_policy=matched_policy,
        dispatch_attempted=dispatch_attempted,
        dispatch_status=dispatch_status,
        tool_result_status=tool_result_status,
        report_status=report_status,
        evidence_refs=evidence_refs or [],
        error_code=error_code,
        failure_stage=failure_stage,
        verification_status=verification_status,
    )
    receipt.sign()
    return receipt
