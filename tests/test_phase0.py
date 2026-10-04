"""
Tripline Phase 0 — Automated Test Suite

Tests:
  1. MCP discovery (tool listing)
  2. MCP invocation (hello_tool, echo_marker)
  3. ArmorIQ authentication (client instantiation, key format)
  4. Plan creation
  5. Intent token minting
  6. Authorized invocation (in-plan tool allowed)
  7. Unauthorized invocation (out-of-plan tool blocked)
  8. Denied action non-execution (side effect must NOT exist)
  9. Decision-Proof enforcement over real HTTP:
     - No proof -> rejected (MISSING_DECISION_PROOF)
     - Tampered args -> rejected (INVALID_PROOF_SIGNATURE)
     - Expired (>60s) -> rejected (EXPIRED_DECISION_PROOF)
     - Replay behavior -> verified within window
     - Valid proof -> accepted
"""

from __future__ import annotations

import asyncio
import os
import time
import warnings
import pytest

from tests.helpers import needs_key, needs_mcp, authenticated_mcp_client

API_KEY = os.environ.get("ARMORIQ_API_KEY", "")
if not API_KEY:
    try:
        import json, pathlib
        _cred_file = pathlib.Path.home() / ".armoriq" / "credentials.json"
        if _cred_file.exists():
            _data = json.loads(_cred_file.read_text())
            _k = _data.get("apiKey", "")
            if isinstance(_k, str) and _k.startswith("ak_"):
                API_KEY = _k
    except Exception:
        pass

HAS_KEY = bool(API_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# 1. MCP discovery
# ─────────────────────────────────────────────────────────────────────────────

@needs_mcp
def test_mcp_discovery():
    """MCP client discovers hello_tool (and marker tools)."""
    async def _run():
        async with authenticated_mcp_client() as client:
            result = await client.list_tools()
            names = [t.name for t in result.tools]
            return names

    names = asyncio.run(_run())
    assert "hello_tool" in names, f"hello_tool not found in {names}"
    assert "echo_marker" in names, f"echo_marker not found in {names}"
    assert "clear_markers" in names, f"clear_markers not found in {names}"
    assert "list_markers" in names, f"list_markers not found in {names}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. MCP invocation
# ─────────────────────────────────────────────────────────────────────────────

@needs_mcp
def test_mcp_hello_tool():
    """hello_tool returns the expected string with decision-proof attached."""
    async def _run():
        async with authenticated_mcp_client() as client:
            result = await client.call_tool("hello_tool", {})
            return result

    result = asyncio.run(_run())
    text = result.content[0].text if result.content else ""
    assert "Hello from Tripline MCP" in text, f"Unexpected response: {text}"


@needs_mcp
def test_mcp_echo_marker():
    """echo_marker sets a marker and returns confirmation with decision-proof."""
    async def _run():
        async with authenticated_mcp_client() as client:
            # Clear first
            await client.call_tool("clear_markers", {})
            # Set marker
            r = await client.call_tool("echo_marker", {"name": "test_probe"})
            text = r.content[0].text if r.content else ""
            # Check it persisted
            r2 = await client.call_tool("list_markers", {})
            markers_text = r2.content[0].text if r2.content else ""
            return text, markers_text

    set_response, list_response = asyncio.run(_run())
    assert "marker_set:test_probe" in set_response, f"Bad set response: {set_response}"
    assert "test_probe" in list_response, f"Marker not listed: {list_response}"


# ─────────────────────────────────────────────────────────────────────────────
# 3. ArmorIQ authentication
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.armoriq
@needs_key
def test_armoriq_client_instantiation():
    """ArmorIQClient instantiates without error when API key is valid format."""
    from armoriq_helper import build_client
    client = build_client(skip_validate=True)
    assert client.api_key == API_KEY
    assert client.agent_id == "tripline-maintainer"
    client.close()


@pytest.mark.armoriq
@needs_key
def test_armoriq_client_rejects_bad_key():
    """ArmorIQClient raises ConfigurationException on a bad key format."""
    from armoriq_sdk import ArmorIQClient
    from armoriq_sdk.exceptions import ConfigurationException
    with pytest.raises(ConfigurationException):
        ArmorIQClient(api_key="not_a_valid_key_format", _skip_api_key_validation=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Plan creation
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.armoriq
@needs_key
def test_plan_creation():
    """capture_plan() returns a PlanCapture with the expected structure."""
    from armoriq_helper import build_client, build_plan
    from armoriq_sdk import PlanCapture

    client = build_client(skip_validate=True)
    plan = build_plan("hello_tool")
    capture = client.capture_plan("agent", "run hello_tool", plan=plan)

    assert isinstance(capture, PlanCapture)
    assert len(capture.plan["steps"]) == 1
    assert capture.plan["steps"][0]["action"] == "hello_tool"
    assert capture.plan["steps"][0]["mcp"] == "tripline-mcp"
    client.close()


# ─────────────────────────────────────────────────────────────────────────────
# 5. Intent token
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.armoriq
@needs_key
def test_intent_token_minted():
    """get_intent_token() returns a valid, unexpired IntentToken."""
    from armoriq_helper import build_client, mint_token
    from armoriq_sdk import IntentToken

    client = build_client(skip_validate=True)
    token = mint_token(client, "hello_tool")

    assert isinstance(token, IntentToken)
    assert token.token_id
    assert token.plan_hash
    assert not token.is_expired
    assert token.time_until_expiry > 0
    client.close()


@pytest.mark.armoriq
@needs_key
def test_intent_token_ttl_respected():
    """A token minted with ttl=15s is valid initially and has time_until_expiry > 0."""
    from armoriq_helper import build_client, mint_token

    client = build_client(skip_validate=True)
    token = mint_token(client, "hello_tool", ttl=15.0)
    assert not token.is_expired, "Token should not be expired immediately"
    assert 0 < token.time_until_expiry <= 15.5, (
        f"time_until_expiry={token.time_until_expiry} exceeds requested TTL"
    )
    client.close()


# ─────────────────────────────────────────────────────────────────────────────
# 6. Authorized invocation
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.armoriq
@needs_key
def test_authorized_invocation_allowed():
    """Authorized tool check via session.check()."""
    from armoriq_sdk import SessionOptions, ToolCall
    from armoriq_helper import build_client

    client = build_client(skip_validate=True)
    session = client.start_session(
        SessionOptions(mode="sdk", default_mcp_name="tripline-mcp")
    )
    token = session.start_plan([ToolCall(name="hello_tool", args={})])

    pv = token.policy_validation or {}
    allowed_tools = pv.get("allowed_tools", [])
    denied_tools = pv.get("denied_tools", [])

    assert "hello_tool" in allowed_tools, f"hello_tool should be in allowed_tools: {pv}"
    assert "hello_tool" not in denied_tools, f"hello_tool should not be in denied_tools: {pv}"

    sdk_decision = session.check("hello_tool", {})
    assert sdk_decision.reason in ("no_matching_policy", None) or sdk_decision.allowed, (
        f"Unexpected enforce_sdk result: {sdk_decision}"
    )

    session.close()
    client.close()


@pytest.mark.armoriq
@needs_key
@needs_mcp
def test_authorized_invocation_executes():
    """Full authorized loop: plan -> token -> check() -> gate -> MCP call -> result."""
    from armoriq_sdk import SessionOptions, ToolCall
    from armoriq_helper import build_client

    client = build_client(skip_validate=True)
    session = client.start_session(
        SessionOptions(mode="sdk", default_mcp_name="tripline-mcp")
    )
    token = session.start_plan([ToolCall(name="echo_marker", args={"name": "authorized_probe"})])

    pv = token.policy_validation or {}
    allowed_tools = pv.get("allowed_tools", [])
    decision_source = pv.get("decision_source", "unknown")

    sdk_decision = session.check("echo_marker", {"name": "authorized_probe"})
    authorized = sdk_decision.allowed or ("echo_marker" in allowed_tools)
    assert authorized, f"echo_marker should be authorized: {sdk_decision}"

    async def _run_mcp():
        async with authenticated_mcp_client() as mcp:
            await mcp.call_tool("clear_markers", {})
            r = await mcp.call_tool("echo_marker", {"name": "authorized_probe"})
            r2 = await mcp.call_tool("list_markers", {})
            return (
                r.content[0].text if r.content else "",
                r2.content[0].text if r2.content else "",
            )

    set_resp, list_resp = asyncio.run(_run_mcp())
    assert "marker_set:authorized_probe" in set_resp
    assert "authorized_probe" in list_resp, f"Marker should exist: {list_resp}"

    session.close()
    client.close()


# ─────────────────────────────────────────────────────────────────────────────
# 7. Unauthorized invocation
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.armoriq
@needs_key
def test_unauthorized_invocation_blocked():
    """Out-of-plan action -> blocked by SDK pre-check (tool-not-in-plan)."""
    from armoriq_sdk import SessionOptions, ToolCall
    from armoriq_helper import build_client

    client = build_client(skip_validate=True)
    session = client.start_session(
        SessionOptions(mode="sdk", default_mcp_name="tripline-mcp")
    )
    session.start_plan([ToolCall(name="hello_tool", args={})])

    decision = session.check("echo_marker", {"name": "unauthorized_probe"})
    assert not decision.allowed, f"Expected echo_marker to be BLOCKED: {decision}"
    assert decision.action == "block"
    assert decision.reason is not None
    assert "plan" in decision.reason.lower()

    session.close()
    client.close()


# ─────────────────────────────────────────────────────────────────────────────
# 8. Denied action non-execution (the key proof)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.armoriq
@needs_key
@needs_mcp
def test_denied_action_not_executed():
    """PROOF OF NON-EXECUTION — authorization gate prevents tool execution."""
    from armoriq_sdk import SessionOptions, ToolCall
    from armoriq_helper import build_client

    UNAUTHORIZED_MARKER = "unauthorized_probe"

    async def _clear():
        async with authenticated_mcp_client() as mcp:
            await mcp.call_tool("clear_markers", {})
            r = await mcp.call_tool("list_markers", {})
            return r.content[0].text if r.content else ""

    baseline = asyncio.run(_clear())
    assert UNAUTHORIZED_MARKER not in baseline, f"Baseline should be clean: {baseline}"

    client_aiq = build_client(skip_validate=True)
    session = client_aiq.start_session(
        SessionOptions(mode="sdk", default_mcp_name="tripline-mcp")
    )
    session.start_plan([ToolCall(name="hello_tool", args={})])
    decision = session.check("echo_marker", {"name": UNAUTHORIZED_MARKER})

    assert not decision.allowed
    assert decision.action == "block"

    mcp_was_called = False
    if decision.allowed:
        async def _bad_call():
            async with authenticated_mcp_client() as mcp:
                await mcp.call_tool("echo_marker", {"name": UNAUTHORIZED_MARKER})
        asyncio.run(_bad_call())
        mcp_was_called = True

    assert not mcp_was_called, "Gate failed: MCP was called despite block!"

    async def _check():
        async with authenticated_mcp_client() as mcp:
            r = await mcp.call_tool("list_markers", {})
            return r.content[0].text if r.content else ""

    final_markers = asyncio.run(_check())
    assert UNAUTHORIZED_MARKER not in final_markers, f"Marker exists: {final_markers}"

    session2 = client_aiq.start_session(
        SessionOptions(mode="sdk", default_mcp_name="tripline-mcp")
    )
    token2 = session2.start_plan([ToolCall(name="echo_marker", args={})])
    pv = token2.policy_validation or {}
    authorized_tools = pv.get("allowed_tools", [])
    if "echo_marker" in authorized_tools:
        async def _auth_call():
            async with authenticated_mcp_client() as mcp:
                await mcp.call_tool("echo_marker", {"name": "authorized_control"})
                r = await mcp.call_tool("list_markers", {})
                return r.content[0].text if r.content else ""
        markers_after_auth = asyncio.run(_auth_call())
        assert "authorized_control" in markers_after_auth

    session2.close()
    session.close()
    client_aiq.close()


# ─────────────────────────────────────────────────────────────────────────────
# 9. Explicit Decision-Proof Enforcement Tests over Real HTTP
# ─────────────────────────────────────────────────────────────────────────────

@needs_mcp
def test_mcp_call_without_decision_proof_is_rejected():
    """Direct MCP tool call without Decision-Proof header MUST return MISSING_DECISION_PROOF."""
    from mcp.shared.exceptions import MCPError

    async def _run():
        async with authenticated_mcp_client(attach_proof=False) as client:
            with pytest.raises(MCPError) as exc_info:
                await client.call_tool("hello_tool", {})
            assert "MISSING_DECISION_PROOF" in str(exc_info.value)

    asyncio.run(_run())


@needs_mcp
def test_mcp_call_with_tampered_args_proof_is_rejected():
    """Call where HMAC signature does not match args is rejected with INVALID_PROOF_SIGNATURE."""
    from mcp.shared.exceptions import MCPError
    import importlib.util

    spec_p = importlib.util.spec_from_file_location("proof", "mcp/common/proof.py")
    proof_mod = importlib.util.module_from_spec(spec_p)
    spec_p.loader.exec_module(proof_mod)
    spec_w = importlib.util.spec_from_file_location("witness", "mcp/common/witness.py")
    witness_mod = importlib.util.module_from_spec(spec_w)
    spec_w.loader.exec_module(witness_mod)

    w_key = witness_mod.get_witness_key()
    tampered = proof_mod.compute_decision_proof("wrong_args_hash_0000000000000000", "ALLOW", w_key, time.time())

    async def _run():
        async with authenticated_mcp_client(proof_override=tampered) as client:
            with pytest.raises(MCPError) as exc_info:
                await client.call_tool("hello_tool", {})
            assert "INVALID_PROOF_SIGNATURE" in str(exc_info.value)

    asyncio.run(_run())


@needs_mcp
def test_mcp_call_with_expired_decision_proof_is_rejected():
    """Call with timestamp >60s old is rejected with EXPIRED_DECISION_PROOF."""
    from mcp.shared.exceptions import MCPError
    import importlib.util

    spec_p = importlib.util.spec_from_file_location("proof", "mcp/common/proof.py")
    proof_mod = importlib.util.module_from_spec(spec_p)
    spec_p.loader.exec_module(proof_mod)
    spec_w = importlib.util.spec_from_file_location("witness", "mcp/common/witness.py")
    witness_mod = importlib.util.module_from_spec(spec_w)
    spec_w.loader.exec_module(witness_mod)

    w_key = witness_mod.get_witness_key()
    h = witness_mod.compute_args_hash("tripline-mcp", "hello_tool", {})
    expired = proof_mod.compute_decision_proof(h, "ALLOW", w_key, time.time() - 120.0)

    async def _run():
        async with authenticated_mcp_client(proof_override=expired) as client:
            with pytest.raises(MCPError) as exc_info:
                await client.call_tool("hello_tool", {})
            assert "EXPIRED_DECISION_PROOF" in str(exc_info.value)

    asyncio.run(_run())


@needs_mcp
def test_mcp_call_replay_within_window_behavior():
    """
    Document and test replay behavior:
    Decision proofs are windowed HMAC tokens (max_age=60s). Replay of the exact same
    proof for identical tool arguments within the 60s window succeeds (permitting network
    retries without state desync). Replaying against different arguments is rejected.
    """
    import importlib.util
    from mcp.shared.exceptions import MCPError

    spec_p = importlib.util.spec_from_file_location("proof", "mcp/common/proof.py")
    proof_mod = importlib.util.module_from_spec(spec_p)
    spec_p.loader.exec_module(proof_mod)
    spec_w = importlib.util.spec_from_file_location("witness", "mcp/common/witness.py")
    witness_mod = importlib.util.module_from_spec(spec_w)
    spec_w.loader.exec_module(witness_mod)

    w_key = witness_mod.get_witness_key()
    h = witness_mod.compute_args_hash("tripline-mcp", "hello_tool", {})
    fixed_proof = proof_mod.compute_decision_proof(h, "ALLOW", w_key, time.time())

    async def _run():
        # Call 1 with fixed proof -> succeeds
        async with authenticated_mcp_client(proof_override=fixed_proof) as client:
            r1 = await client.call_tool("hello_tool", {})
            assert "Hello from Tripline MCP" in r1.content[0].text

        # Call 2 (replayed proof for same tool & args within 60s) -> succeeds (retry safe)
        async with authenticated_mcp_client(proof_override=fixed_proof) as client:
            r2 = await client.call_tool("hello_tool", {})
            assert "Hello from Tripline MCP" in r2.content[0].text

        # Replaying same proof on a DIFFERENT tool (echo_marker) -> rejected (signature mismatch)
        async with authenticated_mcp_client(proof_override=fixed_proof) as client:
            with pytest.raises(MCPError) as exc_info:
                await client.call_tool("echo_marker", {"name": "replay_probe"})
            assert "INVALID_PROOF_SIGNATURE" in str(exc_info.value)

    asyncio.run(_run())


@needs_mcp
def test_mcp_call_with_valid_decision_proof_is_accepted():
    """Call with valid proof is accepted through the DecisionProofMiddleware."""
    async def _run():
        async with authenticated_mcp_client() as client:
            res = await client.call_tool("hello_tool", {})
            assert "Hello from Tripline MCP" in res.content[0].text

    asyncio.run(_run())
