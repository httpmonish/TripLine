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

Key Management & Security:
- Live receipt signing requires a dedicated, cryptographically strong secret configured via
  the TRIPLINE_RECEIPT_SECRET_KEY environment variable (minimum 32 bytes).
- Live signing NEVER falls back to committed files, witness keys, or hardcoded strings.
- In live mode (LIVE_VERIFIED), missing or weak keys raise ReceiptConfigurationError and fail closed.
- Offline tests use explicit test keys via TEST_SIMULATED mode or parameter injection.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import hmac
import json
import os
import pathlib
from typing import Any, Dict, List, Optional

from agent.safety import redact_secrets


class ReceiptConfigurationError(RuntimeError):
    """Raised when the receipt signing secret is missing, insecure, or invalid."""
    pass


# Deterministic test-only key used exclusively when verification_status == "TEST_SIMULATED"
# and no live key is configured.
TEST_SIMULATED_HMAC_KEY = b"tripline_test_deterministic_hmac_secret_key_32_bytes_min!"


_DOTENV_LOADED = False

def _ensure_dotenv_loaded() -> None:
    global _DOTENV_LOADED
    if not _DOTENV_LOADED:
        _DOTENV_LOADED = True
        try:
            from dotenv import load_dotenv
            repo_root = pathlib.Path(__file__).resolve().parent.parent
            load_dotenv(repo_root / ".env")
        except ImportError:
            pass

_ensure_dotenv_loaded()


def get_live_receipt_hmac_key(required: bool = True) -> bytes:
    """
    Retrieves and validates the live receipt HMAC secret key from TRIPLINE_RECEIPT_SECRET_KEY.
    Strictly enforces:
      1. Key MUST come from TRIPLINE_RECEIPT_SECRET_KEY environment variable.
      2. Key MUST be at least 32 characters/bytes in length.
      3. No fallback to committed files or fixed production strings.
    """
    key_str = os.environ.get("TRIPLINE_RECEIPT_SECRET_KEY", "").strip()
    if not key_str:
        if required:
            raise ReceiptConfigurationError(
                "Missing required live signing secret: TRIPLINE_RECEIPT_SECRET_KEY is not set. "
                "Live mode strictly fails closed to prevent unverified receipt generation."
            )
        return b""

    key_bytes = key_str.encode("utf-8")
    if len(key_bytes) < 32:
        raise ReceiptConfigurationError(
            f"Configured TRIPLINE_RECEIPT_SECRET_KEY is too short ({len(key_bytes)} bytes). "
            "Minimum required length is 32 bytes for cryptographic authenticity."
        )
    return key_bytes


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

    def _resolve_key(self, explicit_key: Optional[bytes] = None) -> bytes:
        if explicit_key is not None:
            if len(explicit_key) < 32:
                raise ReceiptConfigurationError(
                    f"Provided secret_key is too short ({len(explicit_key)} bytes). Minimum 32 bytes required."
                )
            return explicit_key

        if self.verification_status == "TEST_SIMULATED":
            live_key = get_live_receipt_hmac_key(required=False)
            return live_key if (live_key and len(live_key) >= 32) else TEST_SIMULATED_HMAC_KEY

        # For LIVE_VERIFIED or any production status, fail closed if key is missing or weak
        return get_live_receipt_hmac_key(required=True)

    def sign(self, secret_key: Optional[bytes] = None) -> None:
        key = self._resolve_key(secret_key)
        self.hmac_sha256 = hmac.new(key, self.canonical_bytes(), hashlib.sha256).hexdigest()

    def verify_signature(self, secret_key: Optional[bytes] = None) -> bool:
        if not self.hmac_sha256:
            return False
        key = self._resolve_key(secret_key)
        expected = hmac.new(key, self.canonical_bytes(), hashlib.sha256).hexdigest()
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
    signing_key: Optional[bytes] = None,
) -> REASecurityReceipt:
    """
    Constructs and cryptographically signs a REASecurityReceipt.
    In live mode (LIVE_VERIFIED), strictly requires a valid TRIPLINE_RECEIPT_SECRET_KEY
    or explicit signing_key (>=32 bytes), failing closed with ReceiptConfigurationError.
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
    receipt.sign(secret_key=signing_key)
    return receipt
