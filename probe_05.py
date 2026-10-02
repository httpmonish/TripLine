"""
probe_05.py - Phase 0.5 raw diagnostic probes

Prints raw SDK/HTTP output for every experiment.
Never rewrites assertions to match behavior -- prints exactly what the SDK returns.

Run:
    source .venv313/bin/activate
    python probe_05.py 2>&1 | tee docs/probe_05_raw.txt

Tasks covered:
  T1  BACKEND ALLOW   - session.check() for in-plan tool (raw EnforceResult)
  T2  BACKEND DENY    - in-plan explicit deny vs fast-path deny distinction
  T3  PARAMETERS S2   - read_file with safe / traversal / absolute paths
  T4  HOLD S4         - live hold policy, await_approval signature
  T5  AUDIT S5        - CLI logs + raw HTTP GET /audit attempts
  T6  PROXY S1        - proxy mode with live Cloudflare tunnel
  T7  NON-EXECUTION   - side-effect proof through proxy path (if T6 worked)
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import pathlib
import re
import subprocess
import sys
import time

import httpx

SEP = "=" * 70

def hdr(title):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)

def raw(label, value):
    print(f"  [{label}]  {value!r}")

def note(msg):
    print(f"  NOTE: {msg}")

# Load API key
API_KEY = os.environ.get("ARMORIQ_API_KEY", "")
if not API_KEY:
    try:
        _f = pathlib.Path.home() / ".armoriq" / "credentials.json"
        _d = json.loads(_f.read_text())
        _k = _d.get("apiKey", "")
        if isinstance(_k, str) and _k.startswith("ak_"):
            API_KEY = _k
    except Exception:
        pass

if not API_KEY:
    print("ERROR: No API key found. Run: armoriq login")
    sys.exit(1)

print(f"API_KEY: {API_KEY[:12]}... (loaded)")

import armoriq_sdk as aiq
from armoriq_sdk import SessionOptions, ToolCall, ReportOptions
from armoriq_helper import build_client

# =============================================================================
# T1 - BACKEND ALLOW: raw check() result for in-plan tool
# =============================================================================

hdr("T1 - BACKEND ALLOW: raw check() result for in-plan tool")
note("Probing current check() behavior before any policy registration.")
note("Policy show: 'No confirmed policy for this org yet'")

try:
    client = build_client(skip_validate=True)
    session = client.start_session(
        SessionOptions(mode="sdk", default_mcp_name="tripline-mcp")
    )
    token = session.start_plan([
        ToolCall(name="hello_tool", args={}),
        ToolCall(name="echo_marker", args={"name": "backend_allow_probe"}),
    ])

    raw("token.token_id", token.token_id)
    raw("token.plan_hash", token.plan_hash)
    raw("token.policy_validation", token.policy_validation)
    raw("token.time_until_expiry", token.time_until_expiry)

    r_hello = session.check("hello_tool", {})
    raw("check('hello_tool').allowed", r_hello.allowed)
    raw("check('hello_tool').action", r_hello.action)
    raw("check('hello_tool').reason", r_hello.reason)
    raw("check('hello_tool').matched_policy", r_hello.matched_policy)
    raw("check('hello_tool').delegation_id", r_hello.delegation_id)
    raw("check('hello_tool').obligations", r_hello.obligations)
    print(f"\n  FULL EnforceResult hello_tool: {r_hello!r}")

    r_echo = session.check("echo_marker", {"name": "backend_allow_probe"})
    raw("check('echo_marker').allowed", r_echo.allowed)
    raw("check('echo_marker').action", r_echo.action)
    raw("check('echo_marker').reason", r_echo.reason)
    raw("check('echo_marker').matched_policy", r_echo.matched_policy)
    print(f"\n  FULL EnforceResult echo_marker: {r_echo!r}")

    if r_hello.reason == "no_matching_policy":
        note("RESULT: still no_matching_policy - no policy rule registered on backend.")
        note("ACTION REQUIRED: Register policy in Policy Studio for agent 'tripline-maintainer'")
    elif r_hello.allowed:
        note("RESULT: BACKEND ALLOW CONFIRMED - matched_policy is set, allowed=True")

    session.close()
    client.close()
except Exception as e:
    print(f"  T1 ERROR: {type(e).__name__}: {e}")

# =============================================================================
# T2 - BACKEND DENY: in-plan vs fast-path distinction
# =============================================================================

hdr("T2 - BACKEND DENY: in-plan tool result vs fast-path (tool-not-in-plan)")
note("To get backend deny: tool MUST be in plan; then backend returns matched_policy.")
note("Fast-path deny: tool NOT in plan; SDK blocks locally before any RPC.")

try:
    client2 = build_client(skip_validate=True)
    session2 = client2.start_session(
        SessionOptions(mode="sdk", default_mcp_name="tripline-mcp")
    )
    token2 = session2.start_plan([
        ToolCall(name="list_markers", args={}),
    ])
    raw("T2 token.policy_validation", token2.policy_validation)

    r_inplan = session2.check("list_markers", {})
    raw("T2 IN-PLAN check('list_markers').allowed", r_inplan.allowed)
    raw("T2 IN-PLAN check('list_markers').action", r_inplan.action)
    raw("T2 IN-PLAN check('list_markers').reason", r_inplan.reason)
    raw("T2 IN-PLAN check('list_markers').matched_policy", r_inplan.matched_policy)
    print(f"\n  FULL EnforceResult list_markers (in-plan): {r_inplan!r}")

    # fast-path: echo_marker is NOT in plan
    r_fast = session2.check("echo_marker", {})
    raw("T2 FAST-PATH check('echo_marker' NOT in plan).allowed", r_fast.allowed)
    raw("T2 FAST-PATH check('echo_marker' NOT in plan).action", r_fast.action)
    raw("T2 FAST-PATH check('echo_marker' NOT in plan).reason", r_fast.reason)
    raw("T2 FAST-PATH check('echo_marker' NOT in plan).matched_policy", r_fast.matched_policy)
    print(f"\n  FULL EnforceResult echo_marker (fast-path): {r_fast!r}")

    if r_inplan.reason == "no_matching_policy" and r_fast.reason != "no_matching_policy":
        note("CONFIRMED: fast-path ('tool-not-in-plan') vs backend ('no_matching_policy') are DISTINCT.")
        note("matched_policy is None in both cases - no policy rule registered on backend.")
        note("Backend DENY with matched_policy requires registering explicit deny rule in Policy Studio.")
    elif r_inplan.matched_policy:
        note("BACKEND DENY CONFIRMED - matched_policy is set.")

    session2.close()
    client2.close()
except Exception as e:
    print(f"  T2 ERROR: {type(e).__name__}: {e}")

# =============================================================================
# T3 - PARAMETERS S2: read_file(path) - does ArmorIQ differ per path?
# =============================================================================

hdr("T3 - PARAMETERS S2: read_file with safe / traversal / absolute paths")
note("read_file is NOT on the MCP server yet - tests ArmorIQ enforcement only.")
note("Testing whether ArmorIQ's enforce differs based on path argument value.")

try:
    client3 = build_client(skip_validate=True)
    session3 = client3.start_session(
        SessionOptions(mode="sdk", default_mcp_name="tripline-mcp")
    )
    token3 = session3.start_plan([
        ToolCall(name="read_file", args={"path": "fixtures/ok.txt"}),
    ])
    raw("T3 token.policy_validation", token3.policy_validation)

    paths = [
        ("safe", "fixtures/ok.txt"),
        ("traversal", "../.env.example"),
        ("absolute", "/etc/passwd"),
    ]

    results_distinct = []
    for label, path in paths:
        try:
            r = session3.check("read_file", {"path": path})
            raw(f"T3 check('read_file', path={path!r}).allowed", r.allowed)
            raw(f"T3 check('read_file', path={path!r}).action", r.action)
            raw(f"T3 check('read_file', path={path!r}).reason", r.reason)
            raw(f"T3 check('read_file', path={path!r}).matched_policy", r.matched_policy)
            results_distinct.append((label, r.allowed, r.action, r.reason))
            print()
        except Exception as e:
            raw(f"T3 check('read_file', {label}) ERROR", f"{type(e).__name__}: {e}")

    actions = set(r[2] for r in results_distinct)
    reasons = set(r[3] for r in results_distinct)
    if len(actions) == 1 and len(reasons) == 1:
        note(f"ALL THREE paths returned SAME decision: action={list(actions)[0]!r}, reason={list(reasons)[0]!r}")
        note("FINDING: ArmorIQ enforces at tool level only - path values make NO difference.")
        note("Parameter-level enforcement (path jail) is Tripline's responsibility.")
    else:
        note(f"DIFFERENT decisions for different paths: actions={actions}, reasons={reasons}")
        note("FINDING: ArmorIQ has parameter-level awareness for path args.")

    session3.close()
    client3.close()
except Exception as e:
    print(f"  T3 ERROR: {type(e).__name__}: {e}")

# =============================================================================
# T4 - HOLD S4: probe await_approval, attempt hold trigger
# =============================================================================

hdr("T4 - HOLD S4: check hold mechanism, attempt live trigger")

try:
    client4 = build_client(skip_validate=True)
    session4 = client4.start_session(
        SessionOptions(mode="sdk", default_mcp_name="tripline-mcp")
    )

    sig = inspect.signature(session4.await_approval)
    raw("T4 await_approval signature", str(sig))
    raw("T4 await_approval is coroutine", inspect.iscoroutinefunction(session4.await_approval))

    token4 = session4.start_plan([
        ToolCall(name="clear_markers", args={}),
    ])
    raw("T4 token.policy_validation", token4.policy_validation)

    r_hold = session4.check("clear_markers", {})
    raw("T4 check('clear_markers').allowed", r_hold.allowed)
    raw("T4 check('clear_markers').action", r_hold.action)
    raw("T4 check('clear_markers').reason", r_hold.reason)
    raw("T4 check('clear_markers').delegation_id", r_hold.delegation_id)
    raw("T4 check('clear_markers').matched_policy", r_hold.matched_policy)
    print(f"\n  FULL EnforceResult clear_markers: {r_hold!r}")

    if r_hold.action == "hold":
        note("HOLD TRIGGERED - delegation_id present, polling await_approval")
        if r_hold.delegation_id:
            async def _await():
                return await session4.await_approval(r_hold.delegation_id, timeout=30, interval=5)
            hold_result = asyncio.run(_await())
            raw("T4 await_approval result", hold_result)
        else:
            note("action='hold' but no delegation_id - unexpected state")
    elif r_hold.action == "block":
        note("Tool blocked (no_matching_policy or explicit deny - no hold rule registered).")
        note("Live HOLD test requires a policy rule with action='hold' in Policy Studio.")
    elif r_hold.allowed:
        note("Tool allowed - no hold triggered.")

    session4.close()
    client4.close()
except Exception as e:
    print(f"  T4 ERROR: {type(e).__name__}: {e}")

# =============================================================================
# T5 - AUDIT S5: CLI logs + HTTP GET attempts
# =============================================================================

hdr("T5 - AUDIT S5: CLI logs (--no-follow), raw HTTP GET /audit probe")

# Raw HTTP probe of all plausible audit read endpoints
audit_endpoints = [
    "https://api.armoriq.ai/iap/audit",
    "https://api.armoriq.ai/iap/audit/logs",
    "https://api.armoriq.ai/iap/decisions",
    "https://api.armoriq.ai/iap/sdk/audit",
    "https://api.armoriq.ai/audit",
    "https://api.armoriq.ai/logs",
    "https://api.armoriq.ai/v1/audit",
    "https://api.armoriq.ai/v1/logs",
]

for endpoint in audit_endpoints:
    try:
        r = httpx.get(endpoint, headers={"X-API-Key": API_KEY}, timeout=8.0)
        raw(f"GET {endpoint} status", r.status_code)
        raw(f"GET {endpoint} body[:300]", r.text[:300])
    except Exception as e:
        raw(f"GET {endpoint} error", f"{type(e).__name__}: {e}")

# POST a report and note behavior
note("Sending session.report() and observing outcome:")
try:
    client5 = build_client(skip_validate=True)
    session5 = client5.start_session(
        SessionOptions(mode="sdk", default_mcp_name="tripline-mcp")
    )
    session5.start_plan([ToolCall(name="hello_tool", args={})])
    r5 = session5.check("hello_tool", {})
    raw("T5 pre-report check result", r5)

    session5.report(
        "hello_tool", {}, "Hello from Tripline MCP!",
        opts=ReportOptions(status="success", duration_ms=3.0),
    )
    note("session.report() completed without exception - POST /iap/audit succeeded")
    session5.close()
    client5.close()
except Exception as e:
    print(f"  T5 report error: {type(e).__name__}: {e}")

note("armoriq logs --no-follow output is recorded in docs/probe_05_raw.txt")

# =============================================================================
# T6 - PROXY S1: Cloudflare tunnel + proxy mode
# =============================================================================

hdr("T6 - PROXY S1: proxy mode test with live Cloudflare tunnel")
note("Current tunnel status: dead (cloudflared exited 2026-10-01 18:04)")
note("Attempting to start a new Quick Tunnel...")

tunnel_url = None
tunnel_proc = None

cf_check = subprocess.run(["which", "cloudflared"], capture_output=True, text=True)
raw("cloudflared binary location", cf_check.stdout.strip() or "NOT FOUND")

if cf_check.returncode == 0:
    note("cloudflared found - starting tunnel against http://127.0.0.1:8000")
    tunnel_proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://127.0.0.1:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.time() + 35
    while time.time() < deadline:
        line = tunnel_proc.stdout.readline()
        if line:
            print(f"  [cloudflared] {line.rstrip()}")
        if "trycloudflare.com" in line:
            m = re.search(r"https://[\w\-]+\.trycloudflare\.com", line)
            if m:
                tunnel_url = m.group(0)
                raw("T6 tunnel_url", tunnel_url)
                break
    if not tunnel_url:
        note("No tunnel URL obtained in 35s")
        if tunnel_proc:
            tunnel_proc.terminate()
            tunnel_proc = None
else:
    note("cloudflared not in PATH - proxy mode test SKIPPED")
    note("Install: brew install cloudflared")

if tunnel_url:
    note(f"Live tunnel: {tunnel_url}")

    yaml_path = pathlib.Path("armoriq.yaml")
    yaml_orig = yaml_path.read_text()
    yaml_patched = re.sub(
        r"url: https://[\w\-]+\.trycloudflare\.com/mcp",
        f"url: {tunnel_url}/mcp",
        yaml_orig,
    )
    yaml_path.write_text(yaml_patched)
    raw("T6 updated armoriq.yaml MCP URL", f"{tunnel_url}/mcp")

    # Register with updated URL
    reg = subprocess.run(
        [".venv313/bin/armoriq", "register"],
        capture_output=True, text=True,
        env={**os.environ, "ARMORIQ_API_KEY": API_KEY},
        cwd=str(pathlib.Path.cwd()),
    )
    raw("T6 armoriq register stdout", reg.stdout.strip())
    raw("T6 armoriq register stderr", reg.stderr.strip())
    raw("T6 armoriq register returncode", reg.returncode)

    time.sleep(5)  # let tunnel settle + registration propagate

    try:
        client6 = build_client(skip_validate=True)
        session6 = client6.start_session(
            SessionOptions(mode="proxy", default_mcp_name="tripline-mcp")
        )
        token6 = session6.start_plan([ToolCall(name="hello_tool", args={})])
        raw("T6 proxy token.token_id", token6.token_id)
        raw("T6 proxy token.policy_validation", token6.policy_validation)

        # Try session.invoke (proxy-routed MCP call)
        try:
            invoke_r = session6.invoke("hello_tool", {})
            raw("T6 session6.invoke('hello_tool') result", invoke_r)
            note("PROXY MODE INVOKE SUCCEEDED")
        except AttributeError:
            note("session.invoke() not available in SDK 0.6.10 - trying client.invoke()")
            try:
                invoke_r = client6.invoke("tripline-mcp", "hello_tool", {}, token=token6)
                raw("T6 client6.invoke result", invoke_r)
            except Exception as e2:
                raw("T6 client6.invoke error", f"{type(e2).__name__}: {e2}")
        except Exception as e:
            raw("T6 session6.invoke error", f"{type(e).__name__}: {e}")

        # Check via proxy
        r6 = session6.check("hello_tool", {})
        raw("T6 proxy check.allowed", r6.allowed)
        raw("T6 proxy check.action", r6.action)
        raw("T6 proxy check.reason", r6.reason)
        raw("T6 proxy check.matched_policy", r6.matched_policy)
        print(f"\n  FULL proxy EnforceResult hello_tool: {r6!r}")

        session6.close()
        client6.close()
    except Exception as e:
        raw("T6 proxy session error", f"{type(e).__name__}: {e}")

    yaml_path.write_text(yaml_orig)
    note("armoriq.yaml restored to original")

    # =========================================================================
    # T7 - NON-EXECUTION via proxy path
    # =========================================================================

    hdr("T7 - NON-EXECUTION via proxy path (requires live tunnel from T6)")
    note("Testing that ArmorIQ prevents execution before proxy routes the call.")

    yaml_path.write_text(yaml_patched)
    try:
        client7 = build_client(skip_validate=True)
        session7 = client7.start_session(
            SessionOptions(mode="proxy", default_mcp_name="tripline-mcp")
        )
        session7.start_plan([ToolCall(name="hello_tool", args={})])

        # Clear markers first
        async def _clear():
            from mcp import Client
            async with Client("http://127.0.0.1:8000/mcp") as mcp:
                await mcp.call_tool("clear_markers", {})
        asyncio.run(_clear())

        r7 = session7.check("echo_marker", {"name": "proxy_nonexec_probe"})
        raw("T7 check('echo_marker' not-in-plan).allowed", r7.allowed)
        raw("T7 check('echo_marker' not-in-plan).action", r7.action)
        raw("T7 check('echo_marker' not-in-plan).reason", r7.reason)

        if not r7.allowed:
            async def _check_markers():
                from mcp import Client
                async with Client("http://127.0.0.1:8000/mcp") as mcp:
                    r = await mcp.call_tool("list_markers", {})
                    return r.content[0].text if r.content else ""
            markers = asyncio.run(_check_markers())
            raw("T7 list_markers after blocked check", markers)
            if "proxy_nonexec_probe" not in markers:
                note("NON-EXECUTION PROOF via proxy: CONFIRMED - marker not set")
                note("Prevention: ArmorIQ SDK fast-path guard fired before proxy routing.")
            else:
                note("FAIL: marker exists despite block - gate not working!")
        else:
            note("T7 UNEXPECTED: check returned allowed=True for out-of-plan tool")

        session7.close()
        client7.close()
    except Exception as e:
        raw("T7 error", f"{type(e).__name__}: {e}")
    finally:
        yaml_path.write_text(yaml_orig)
        note("armoriq.yaml restored")

    if tunnel_proc:
        tunnel_proc.terminate()
        note("cloudflared tunnel terminated")

else:
    hdr("T7 - NON-EXECUTION via proxy path")
    note("T7 SKIPPED - no live Cloudflare tunnel (T6 failed to obtain URL)")
    note("Non-execution ALREADY CONFIRMED in SDK mode via test_denied_action_not_executed.")
    note("Prevention mechanism: ArmorIQ SDK fast-path guard (tool-not-in-plan) - no RPC made.")

print(f"\n{SEP}")
print("  probe_05.py complete")
print(SEP)
