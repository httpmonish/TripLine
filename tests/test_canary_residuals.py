"""
tests/test_canary_residuals.py — Deterministic tests for canary scanner residuals (W9).

Validates Section 6.7 truth:
The Tripline Egress Gateway performs exact substring matching against planted canary tokens.
It deterministically catches plain unencoded leaks, but DOES NOT detect:
1. Base64-encoded tokens
2. ROT13-encoded tokens
3. Reversed string tokens
4. Split / fragmented tokens across whitespace

Runs offline with zero LLM and zero network dependencies.
"""

import base64
import codecs
import uuid
from pathlib import Path

import pytest
from canary.plant import plant_canaries
from canary.scan import scan_egress_payload

DEMO_REPO_DIR = Path("fixtures/demo_repo")
FIXTURES_DIR = Path("fixtures")


@pytest.fixture
def planted_t2_canary():
    run_id = str(uuid.uuid4())
    res = plant_canaries(run_id, DEMO_REPO_DIR, FIXTURES_DIR)
    t2_id = res["t2"].canary_id
    return run_id, t2_id


def test_positive_control_plain_leak(planted_t2_canary):
    """Positive control: exact plain token leak MUST be caught."""
    run_id, t2_id = planted_t2_canary
    payload = {"body": f"Here is the secret token: {t2_id}"}
    hit = scan_egress_payload(payload, run_id, "comment_issue")
    assert hit is not None
    assert hit["matched"] is True
    assert hit["canary_id"] == t2_id
    assert hit["decision"] == "hold"


def test_residual_base64_miss(planted_t2_canary):
    """Documented residual: Base64-encoded token is NOT caught."""
    run_id, t2_id = planted_t2_canary
    b64_val = base64.b64encode(t2_id.encode("utf-8")).decode("utf-8")
    payload = {"body": f"Encoded token: {b64_val}"}
    hit = scan_egress_payload(payload, run_id, "comment_issue")
    assert hit is None, "Exact scanner must miss Base64 transformed token"


def test_residual_rot13_miss(planted_t2_canary):
    """Documented residual: ROT13-encoded token is NOT caught."""
    run_id, t2_id = planted_t2_canary
    rot13_val = codecs.encode(t2_id, "rot_13")
    payload = {"body": f"Obfuscated token: {rot13_val}"}
    hit = scan_egress_payload(payload, run_id, "comment_issue")
    assert hit is None, "Exact scanner must miss ROT13 transformed token"


def test_residual_reversed_miss(planted_t2_canary):
    """Documented residual: Reversed token string is NOT caught."""
    run_id, t2_id = planted_t2_canary
    rev_val = t2_id[::-1]
    payload = {"body": f"Reversed token: {rev_val}"}
    hit = scan_egress_payload(payload, run_id, "comment_issue")
    assert hit is None, "Exact scanner must miss reversed token string"


def test_residual_split_tokens_miss(planted_t2_canary):
    """Documented residual: Token fragmented across spaces is NOT caught."""
    run_id, t2_id = planted_t2_canary
    mid = len(t2_id) // 2
    split_val = f"{t2_id[:mid]} {t2_id[mid:]}"
    payload = {"body": f"Fragmented token: {split_val}"}
    hit = scan_egress_payload(payload, run_id, "comment_issue")
    assert hit is None, "Exact scanner must miss fragmented token"
