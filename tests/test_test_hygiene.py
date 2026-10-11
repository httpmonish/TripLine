"""
tests/test_test_hygiene.py — Test suite integrity & working tree immutability.

Assures Phase 9 requirement:
Tracked evidence (.tripline/witness/*, fixtures/.ssh/fake_key, results/demo/events.jsonl)
must NEVER be modified, deleted, or left dirty by tests or harnesses.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_tracked_evidence_immutable():
    """Verify that all tracked evidence files under .tripline/, fixtures/, and results/ are clean."""
    res = subprocess.run(
        ["git", "status", "--porcelain", ".tripline/", "fixtures/", "results/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    dirty_lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    assert not dirty_lines, f"Tracked evidence was modified during execution: {dirty_lines}"


def test_tracked_witness_logs_exist():
    """Verify that committed witness log chains exist and are non-empty."""
    witness_dir = REPO_ROOT / ".tripline" / "witness"
    assert witness_dir.exists(), "Witness directory missing"
    logs = list(witness_dir.glob("*.jsonl"))
    assert len(logs) >= 3, f"Expected at least 3 witness logs, found {len(logs)}"
    for log_path in logs:
        assert log_path.stat().st_size > 0, f"Witness log {log_path.name} is empty"


def test_fake_key_is_synthetic_banner():
    """Verify fixtures/.ssh/fake_key contains synthetic fixture header."""
    fake_key = REPO_ROOT / "fixtures" / ".ssh" / "fake_key"
    assert fake_key.exists(), "fixtures/.ssh/fake_key missing"
    content = fake_key.read_text(encoding="utf-8")
    assert "FAKE_KEY_MATERIAL_ONLY" in content, "fake_key missing synthetic banner"
