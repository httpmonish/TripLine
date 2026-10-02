"""
armoriq_helper.py — Phase 0 ArmorIQ SDK helpers

Provides thin wrappers around armoriq_sdk 0.6.10 that the spike scripts
and tests import.  Nothing here calls MCP over the network; it uses the
SDK's local/sdk enforcement mode only.

Architecture decision: SDK mode (mode="sdk"), not proxy mode.
Proxy mode routes through https://proxy.armoriq.ai, which caused:
  - HTTP 502 (proxy couldn't reach the Cloudflare Quick Tunnel)
  - HTTP 421 (TransportSecuritySettings rejected the proxy's Host header)

SDK mode hits the ArmorIQ backend directly for:
  - /iap/sdk/token      (mint intent token)
  - /iap/sdk/enforce    (check policy)
  - /iap/audit          (report execution)

The MCP tool itself is called locally by the test harness, not routed
through the proxy.  This is the correct architecture for a solo-dev
hackathon project.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import armoriq_sdk as aiq

log = logging.getLogger(__name__)


def build_client(*, skip_validate: bool = False) -> aiq.ArmorIQClient:
    """
    Build an ArmorIQClient.

    Key resolution order (mirrors ArmorIQClient.__init__):
      1. ARMORIQ_API_KEY environment variable
      2. ~/.armoriq/credentials.json (written by `armoriq login`)
      3. EnvironmentError if neither is present

    skip_validate=True prevents a proxy /health round-trip at init time,
    which is useful in tests where the proxy may be unavailable.
    """
    api_key = os.environ.get("ARMORIQ_API_KEY", "")
    if not api_key:
        # Try the CLI credential store (same path the SDK constructor reads)
        try:
            from armoriq_sdk.credentials import load_credentials
            creds = load_credentials()
            if creds:
                api_key = creds.apiKey
        except Exception:
            pass
    if not api_key:
        raise EnvironmentError(
            "ARMORIQ_API_KEY not set and ~/.armoriq/credentials.json not found. "
            "Run: export ARMORIQ_API_KEY=ak_... or: armoriq login"
        )

    return aiq.ArmorIQClient(
        api_key=api_key,
        agent_id="tripline-maintainer",
        user_id="default",
        _skip_api_key_validation=skip_validate,
    )


def build_plan(tool_name: str, mcp_id: str = "tripline-mcp") -> dict[str, Any]:
    """
    Build the minimal ArmorIQ plan dict for a single tool call.

    The plan format expected by capture_plan():
        { "steps": [ { "mcp": <id>, "action": <tool_name> } ] }
    """
    return {"steps": [{"mcp": mcp_id, "action": tool_name}]}


def mint_token(
    client: aiq.ArmorIQClient,
    tool_name: str,
    mcp_id: str = "tripline-mcp",
    ttl: float = 300.0,
) -> aiq.IntentToken:
    """
    Capture a plan and mint a signed intent token for one tool call.

    Returns the IntentToken; callers decide what to do with it.
    """
    plan = build_plan(tool_name, mcp_id)
    capture = client.capture_plan(
        llm="tripline-maintainer",
        prompt=f"Execute {tool_name}",
        plan=plan,
    )
    token = client.get_intent_token(capture, validity_seconds=ttl)
    log.info(
        "Token minted: id=%s plan_hash=%.16s expires_in=%.0fs",
        token.token_id,
        token.plan_hash,
        token.time_until_expiry,
    )
    return token


def start_session_sdk(
    client: aiq.ArmorIQClient,
    tool_name: str,
    mcp_id: str = "tripline-mcp",
    ttl: int = 300,
) -> tuple[aiq.ArmorIQSession, aiq.IntentToken]:
    """
    Open an SDK-mode session and start a plan for a single tool.

    Returns (session, token).  Call session.check(tool_name, {}) to enforce.
    Call session.close() when done.
    """
    from armoriq_sdk import SessionOptions, ToolCall

    session = client.start_session(
        SessionOptions(
            mode="sdk",
            default_mcp_name=mcp_id,
            validity_seconds=ttl,
        )
    )
    token = session.start_plan([ToolCall(name=tool_name, args={})])
    return session, token


def enforce(
    session: aiq.ArmorIQSession,
    tool_name: str,
    args: dict[str, Any] | None = None,
) -> aiq.EnforceResult:
    """
    Run mode-aware enforcement for tool_name inside session.
    Returns EnforceResult with .allowed, .action, .reason.
    """
    return session.check(tool_name, args or {})
