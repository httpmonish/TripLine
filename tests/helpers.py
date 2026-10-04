"""
helpers.py — shared test utilities for the Tripline test suite.

Imported by test_phase0 through test_phase6 to avoid duplicating
marker definitions and key-detection logic.

Design:
- `needs_mcp` is a pytest.mark.skipif that checks for the MCP_TEST_PORT env var
  set by conftest's session fixture, OR falls back to checking port 8000.
  This means it evaluates to "reachable" when the conftest has already started
  the server, fixing the "20 skipped because server not running at collection
  time" regression.
- `needs_key` checks for ARMORIQ_API_KEY or ~/.armoriq/credentials.json.
  Tests marked @needs_key are also marked @pytest.mark.armoriq so they can be
  run separately via `make test-armoriq`.
"""

from __future__ import annotations

import json
import os
import pathlib
import socket

import pytest


# ── ArmorIQ key detection ────────────────────────────────────────────────────

def _detect_armoriq_key() -> bool:
    key = os.environ.get("ARMORIQ_API_KEY", "")
    if key and key.startswith("ak_"):
        return True
    try:
        cred = pathlib.Path.home() / ".armoriq" / "credentials.json"
        if cred.exists():
            data = json.loads(cred.read_text())
            k = data.get("apiKey", "")
            if isinstance(k, str) and k.startswith("ak_"):
                return True
    except Exception:
        pass
    return False


HAS_KEY: bool = _detect_armoriq_key()

needs_key = pytest.mark.skipif(
    not HAS_KEY,
    reason="ARMORIQ_API_KEY not set and no ~/.armoriq/credentials.json — use make test-armoriq",
)


# ── MCP server reachability ──────────────────────────────────────────────────

def _mcp_server_reachable() -> bool:
    """
    Check whether the MCP server is up.

    Prefers MCP_TEST_PORT env var (set by conftest's mcp_server_session fixture)
    so this returns True when called after conftest has started the server,
    even at collection time in subsequent modules.
    """
    port = int(os.environ.get("MCP_TEST_PORT", "8000"))
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=1.0)
        s.close()
        return True
    except OSError:
        return False


needs_mcp = pytest.mark.skipif(
    not _mcp_server_reachable(),
    reason="MCP server not running — conftest should start it automatically",
)


def mcp_url() -> str:
    """Return the MCP server URL based on MCP_TEST_PORT (or fallback 8000)."""
    port = int(os.environ.get("MCP_TEST_PORT", "8000"))
    return f"http://127.0.0.1:{port}/mcp"


# ── Decision-Proof Test Client ──────────────────────────────────────────────
from contextlib import asynccontextmanager
import importlib.util
import time
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


@asynccontextmanager
async def authenticated_mcp_client(
    url: str | None = None,
    attach_proof: bool = True,
    proof_override: str | None = None,
    decision: str = "ALLOW",
    mcp_name: str = "tripline-mcp",
    trace_id: str | None = None,
):
    """
    Async context manager yielding an MCP Client that automatically signs
    tools/call requests with a valid Decision-Proof header (identical to Tripline's gateway).

    Supports:
    - attach_proof=False: sends calls without proof to test MISSING_DECISION_PROOF rejection.
    - proof_override: sends an explicit header (e.g. expired, tampered) to test verification failure.
    - trace_id: threads trace_id header across MCP boundaries.
    """
    if url is None:
        url = mcp_url()

    spec_w = importlib.util.spec_from_file_location("witness", "mcp/common/witness.py")
    witness_mod = importlib.util.module_from_spec(spec_w)
    spec_w.loader.exec_module(witness_mod)

    spec_p = importlib.util.spec_from_file_location("proof", "mcp/common/proof.py")
    proof_mod = importlib.util.module_from_spec(spec_p)
    spec_p.loader.exec_module(proof_mod)

    async def attach_decision_proof(req):
        if req.method == "POST":
            if trace_id:
                req.headers["x-tripline-trace-id"] = trace_id
            try:
                body = json.loads(req.content)
                if isinstance(body, dict) and body.get("method") == "tools/call":
                    if proof_override is not None:
                        req.headers["x-tripline-decision-proof"] = proof_override
                    elif attach_proof:
                        params = body.get("params", {})
                        tool = params.get("name", "")
                        args = params.get("arguments", {})
                        w_key = witness_mod.get_witness_key()
                        h = witness_mod.compute_args_hash(mcp_name, tool, args)
                        p = proof_mod.compute_decision_proof(h, decision, w_key, time.time())
                        req.headers["x-tripline-decision-proof"] = p
            except Exception:
                pass

    http_cli = httpx2.AsyncClient(event_hooks={"request": [attach_decision_proof]})
    transport = streamable_http_client(url, http_client=http_cli)
    async with Client(transport) as client:
        yield client

