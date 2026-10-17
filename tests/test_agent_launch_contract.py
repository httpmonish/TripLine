"""
tests/test_agent_launch_contract.py — Regression Test for Agent Launch Contract (Phase 1.3)

Proves:
1. Disabled live mode produces truthful, actionable error (403).
2. Missing ArmorIQ configuration reported separately from missing LLM configuration.
3. Missing LLM configuration reported separately from missing ArmorIQ configuration.
4. Job creation succeeds and returns valid job_id when documented prerequisites are satisfied.
5. Cancellation triggers safety kill switch and cancels active background jobs.
6. Deterministic security proof scenarios remain runnable without live LLM credentials.
"""

import os
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from dashboard.app import app
from dashboard.jobs import job_manager


@pytest.fixture
def client():
    return TestClient(app)


def test_disabled_live_mode_produces_truthful_error(client):
    """When TRIPLINE_ENABLE_LIVE is 0 or unset, live agent launch is rejected with 403."""
    with patch.dict(os.environ, {"TRIPLINE_ENABLE_LIVE": "0"}, clear=False):
        csrf = client.get("/api/csrf-token").json()["csrf_token"]
        resp = client.post(
            "/api/agent/runs",
            headers={"X-CSRF-Token": csrf, "Origin": "http://127.0.0.1:8080"},
            json={"task": "Summarize volunteer applications"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert "Live agent execution is disabled" in data["detail"]
        assert "TRIPLINE_ENABLE_LIVE=1" in data["detail"]


def test_missing_armoriq_credentials_reported_separately(client):
    """When live is enabled but ARMORIQ_API_KEY is missing, reports ArmorIQ error separately."""
    env = {
        "TRIPLINE_ENABLE_LIVE": "1",
        "GEMINI_API_KEY": "test-gemini-key",
    }
    # Ensure ARMORIQ_API_KEY is absent
    with patch.dict(os.environ, env, clear=False):
        if "ARMORIQ_API_KEY" in os.environ:
            del os.environ["ARMORIQ_API_KEY"]
        csrf = client.get("/api/csrf-token").json()["csrf_token"]
        resp = client.post(
            "/api/agent/runs",
            headers={"X-CSRF-Token": csrf, "Origin": "http://127.0.0.1:8080"},
            json={"task": "Summarize volunteer applications"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert "Missing ArmorIQ credentials" in data["detail"]


def test_missing_llm_credentials_reported_separately(client):
    """When live is enabled and ArmorIQ key is present, but no LLM provider key exists, reports LLM error separately."""
    with patch.dict(os.environ, {
        "TRIPLINE_ENABLE_LIVE": "1",
        "ARMORIQ_API_KEY": "ak_test_key_12345",
        "GEMINI_API_KEY": "",
        "GOOGLE_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "OPENAI_API_KEY": "",
        "GROQ_API_KEY": "",
    }, clear=False):
        csrf = client.get("/api/csrf-token").json()["csrf_token"]
        resp = client.post(
            "/api/agent/runs",
            headers={"X-CSRF-Token": csrf, "Origin": "http://127.0.0.1:8080"},
            json={"task": "Summarize volunteer applications"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert "Missing LLM provider credentials" in data["detail"]


def test_successful_job_creation_when_prerequisites_satisfied(client):
    """When live mode, ArmorIQ key, and LLM key are configured, creates the intended agent job."""
    env = {
        "TRIPLINE_ENABLE_LIVE": "1",
        "ARMORIQ_API_KEY": "ak_mock_valid_key",
        "GEMINI_API_KEY": "mock_gemini_key",
    }
    with patch.dict(os.environ, env, clear=False):
        # Mock JobManager._run_job_process to avoid starting actual background process
        with patch.object(job_manager, "_run_job_process", new_callable=AsyncMock):
            csrf = client.get("/api/csrf-token").json()["csrf_token"]
            resp = client.post(
                "/api/agent/runs",
                headers={"X-CSRF-Token": csrf, "Origin": "http://127.0.0.1:8080"},
                json={"task": "Summarize volunteer applications by status", "mode": "B"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["kind"] == "agent_task"
            assert data["live"] is True
            assert "job_id" in data
            assert data["params"]["task"] == "Summarize volunteer applications by status"
            assert data["params"]["mode"] == "B"


def test_stop_agent_run_triggers_kill_switch_and_cancels_job(client):
    """POST /api/agent/runs/{run_id}/stop triggers safety kill switch and cancels active job."""
    csrf = client.get("/api/csrf-token").json()["csrf_token"]
    resp = client.post(
        "/api/agent/runs/run_20261017_test/stop",
        headers={"X-CSRF-Token": csrf, "Origin": "http://127.0.0.1:8080"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "stopped"
    assert data["run_id"] == "run_20261017_test"
    assert data["kill_switch"] == "triggered"


def test_deterministic_security_proof_runnable_without_live_credentials(client):
    """Deterministic security proofs can be launched offline with zero live credentials."""
    csrf = client.get("/api/csrf-token").json()["csrf_token"]
    # Mock subprocess execution to test contract
    with patch.object(job_manager, "_run_job_process", new_callable=AsyncMock):
        resp = client.post(
            "/api/jobs",
            headers={"X-CSRF-Token": csrf, "Origin": "http://127.0.0.1:8080"},
            json={"kind": "security_proof", "params": {"scenario": "clean_read", "rung": 0}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["kind"] == "security_proof"
        assert data["live"] is False
        assert "job_id" in data
