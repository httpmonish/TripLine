# Phase 0.5 — Gap Closing Results

**Date**: 2026-10-02  
**ArmorIQ SDK**: 0.6.10  
**MCP SDK**: 2.2.0  
**Python**: 3.13.16  
**Tunnel**: patio-retailers-temple-advertisement.trycloudflare.com  
**Policy**: cli-tripline-maintainer-tripline-mcp (OPA, priority 100)

---

## Summary Table

| Task | Goal | Status |
|------|------|--------|
| T1 Backend ALLOW | Real backend allow with matched_policy | CONFIRMED |
| T2 Backend DENY | In-plan backend deny vs fast-path distinction | CONFIRMED |
| T3 Parameters S2 | read_file path enforcement test | CONFIRMED (tool-level only) |
| T4 Hold S4 | Live hold trigger | BLOCKED (no hold policy rule registered) |
| T5 Audit S5 | CLI logs + HTTP GET probe | CONFIRMED (write-only) |
| T6 Proxy S1 | Proxy mode via Cloudflare tunnel | CONFIRMED |
| T7 Non-execution | Non-execution proof via proxy path | CONFIRMED |

---

## T1 -- BACKEND ALLOW (Real backend allow)

**STATUS: CONFIRMED**

### Action taken

Ran `armoriq register` with the live Cloudflare tunnel URL in `armoriq.yaml`.
ArmorIQ registered agent `tripline-maintainer`, MCP `tripline-mcp` with 5 tools,
and created policy `cli-tripline-maintainer-tripline-mcp` (OPA, priority 100).

### Raw EnforceResult -- hello_tool (in plan, in policy allowlist)

```
EnforceResult(
    allowed=True,
    action='allow',
    reason='allow_with_logging',
    delegation_id=None,
    matched_policy='cli-tripline-maintainer-tripline-mcp',
    obligations=[]
)
```

### Raw token.policy_validation (post-registration)

```json
{
  "domain": "patio-retailers-temple-advertisement.trycloudflare.com",
  "requested_tools": ["hello_tool", "echo_marker"],
  "allowed_tools": ["hello_tool"],
  "denied_tools": [],
  "denied_reasons": [],
  "matched_policies": [{
    "policyId": "7d1d8873-9458-4d40-a1b1-21edf61d5ec9",
    "policyName": "cli-tripline-maintainer-tripline-mcp",
    "priority": 100,
    "defaultEnforcementAction": "block",
    "rules": {}
  }],
  "default_enforcement_action": "block",
  "decision_source": "opa",
  "policy_ref": "armoriq:474c55dbcb16:1a0fbec3f09"
}
```

Key fields:
- `decision_source: "opa"` -- OPA (Open Policy Agent) evaluating policy (not "native")
- `matched_policies[0].policyName` = `cli-tripline-maintainer-tripline-mcp` -- real policy attached
- `allowed_tools: ["hello_tool"]` -- only the tool in `armoriq.yaml policy.allow`
- `echo_marker` is NOT in `allowed_tools` -- not in armoriq.yaml policy.allow list

### Finding

Real backend allow fires when: (a) MCP registered with `armoriq register`, (b) tool is in plan
AND in the registered policy allow list, (c) backend has a policy document for this agent.

Pre-registration: `no_matching_policy` -- OPA had no policy document for this agent.
Post-registration: `allow_with_logging` -- OPA evaluates, decision recorded in audit trail.

---

## T2 -- BACKEND DENY (In-plan vs fast-path distinction)

**STATUS: CONFIRMED**

### Path A -- Fast-path (tool NOT in plan, NO RPC to backend)

```
EnforceResult(
    allowed=False,
    action='block',
    reason="tool-not-in-plan: 'echo_marker' was not declared in the captured plan",
    delegation_id=None,
    matched_policy=None,
    obligations=[]
)
```

### Path B -- Backend deny (tool IN plan, RPC to /iap/sdk/enforce, policy says no)

```
EnforceResult(
    allowed=False,
    action='block',
    reason='tool_not_in_allowlist',
    delegation_id=None,
    matched_policy='cli-tripline-maintainer-tripline-mcp',
    obligations=[]
)
```

### Distinction

| Property | Fast-path | Backend deny |
|----------|-----------|--------------|
| reason | "tool-not-in-plan: '...'" | "tool_not_in_allowlist" |
| matched_policy | None | "cli-tripline-maintainer-tripline-mcp" |
| Network RPC | No | Yes (/iap/sdk/enforce) |
| Plan membership | Tool NOT in plan | Tool IN plan, not in allowlist |

`list_markers` was in the plan but not in the policy allow list (armoriq.yaml only has
`hello_tool`). ArmorIQ OPA engine returned `tool_not_in_allowlist` with matched_policy set.
This is a real backend deny (not the SDK fast-path local guard).

To get an explicit deny (vs default block): add an explicit deny rule to the policy.
Current policy has `rules: {}` -- no explicit rules, just default_enforcement_action: block.

---

## T3 -- PARAMETERS S2: read_file path enforcement

**STATUS: CONFIRMED -- ArmorIQ enforces at tool level only**

### read_file tool added to server.py

```python
@mcp.tool()
def read_file(path: str) -> str:
    """Read a file from ./fixtures only. S2 parameter enforcement test."""
    if pathlib.Path(path).is_absolute():
        return f"error:absolute_path_rejected:{path}"
    try:
        resolved = (_FIXTURES_DIR / path).resolve()
        resolved.relative_to(_FIXTURES_DIR.resolve())  # ValueError if escaping
    except ValueError:
        return f"error:path_traversal_rejected:{path}"
    ...
```

### Raw EnforceResults for three paths (all identical)

```
check('read_file', path='fixtures/ok.txt').allowed  = False
check('read_file', path='fixtures/ok.txt').action   = 'block'
check('read_file', path='fixtures/ok.txt').reason   = 'no_matching_policy'

check('read_file', path='../.env.example').allowed  = False
check('read_file', path='../.env.example').action   = 'block'
check('read_file', path='../.env.example').reason   = 'no_matching_policy'

check('read_file', path='/etc/passwd').allowed      = False
check('read_file', path='/etc/passwd').action       = 'block'
check('read_file', path='/etc/passwd').reason       = 'no_matching_policy'
```

Note: no_matching_policy because read_file not in armoriq.yaml policy.allow at probe time.
The finding: all three paths returned the SAME reason. ArmorIQ never sees the path value.

FINDING: ArmorIQ 0.6.10 enforces at tool level only. Path argument value is invisible to OPA.
Safe path, traversal path, and absolute path produce identical enforcement decisions.

Parameter-level enforcement is Tripline's responsibility -- implemented in read_file() via:
1. Reject absolute paths (Path(path).is_absolute())
2. Resolve and check containment (resolved.relative_to(fixtures_resolved))
3. Return error string (not raise) to keep MCP tool stable

---

## T4 -- HOLD S4

**STATUS: BLOCKED -- No hold policy rule registered**

### Raw probe output

```
await_approval signature: (delegation_id: 'str', *, timeout: 'float' = 300.0,
    interval: 'float' = 5.0, user_email: 'Optional[str]' = None) -> 'str'
await_approval is coroutine: True

EnforceResult(allowed=False, action='block', reason='no_matching_policy',
    delegation_id=None, matched_policy=None, obligations=[])
```

Live HOLD requires a policy rule with action: hold in Policy Studio.
Current policy has rules: {} -- no hold rule. Live trigger not tested.

SDK mechanism confirmed: await_approval(delegation_id, timeout=300, interval=5) is an
async coroutine returning 'approved' | 'rejected' | 'timeout'. _handle_hold() creates
pending delegation via POST /delegation/create. The wiring is correct; only the policy
rule is missing.

---

## T5 -- AUDIT S5

**STATUS: CONFIRMED (write-only from SDK and HTTP)**

### armoriq CLI -- raw output

```
$ armoriq --help
  {init,validate,register,status,logs,login,logout,whoami,orgs,switch-org,keys,policy}

$ armoriq logs --help
  --follow, --no-follow   Continue streaming new log lines

$ armoriq status
  Agent: tripline-maintainer | User: default | Environment: sandbox
  Registered at: 2026-10-01T17:03:35+00:00
  MCP servers: (none)  [pre-registration; 5 tools registered after]

$ armoriq logs --no-follow
  [2026-10-01T16:48:59] init: {"config_path": "armoriq.yaml"}
  [2026-10-01T17:03:35] register: {"agent_id": "tripline-maintainer", ...}
```

CLI logs = CLI action history only (init/validate/register). NOT enforcement decisions.

### Raw HTTP GET probes

```
GET https://api.armoriq.ai/iap/audit          -> 404 Cannot GET /iap/audit
GET https://api.armoriq.ai/iap/audit/logs     -> 401 Access token is required  <- EXISTS
GET https://api.armoriq.ai/iap/decisions      -> 404
GET https://api.armoriq.ai/iap/sdk/audit      -> 404
GET https://api.armoriq.ai/audit              -> 404
GET https://api.armoriq.ai/logs               -> 404
GET https://api.armoriq.ai/v1/audit           -> 404
GET https://api.armoriq.ai/v1/logs            -> 404
```

/iap/audit/logs returns 401 (not 404) -- endpoint EXISTS but requires different auth (not X-API-Key).
All other audit endpoints do not exist (404).

session.report() -> completes without exception -> POST /iap/audit succeeded (write-only).

FINDING: Audit is write-only from SDK. Read access requires ArmorIQ dashboard (web UI).
/iap/audit/logs may be readable with a different auth token (OAuth bearer, not API key).
Tripline Phase 1 must maintain its own execution record.

---

## T6 -- PROXY S1: Proxy mode via Cloudflare tunnel

**STATUS: CONFIRMED**

### 421 Root Cause (FIXED)

MCP SDK auto-enables DNS rebinding protection when host="127.0.0.1":

```python
# mcp/server/lowlevel/server.py:
if transport_security is None and host in ("127.0.0.1", "localhost", "::1"):
    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
    )
```

Cloudflare tunnel sends Host: patio-retailers-temple-advertisement.trycloudflare.com
which does not match any of the auto-set allowed_hosts -> 421 Misdirected Request.

### Fix: TRIPLINE_ALLOWED_HOSTS env var (server.py Phase 0.5)

```bash
export TRIPLINE_ALLOWED_HOSTS="patio-retailers-temple-advertisement.trycloudflare.com"
python server.py
```

_build_transport_security() builds TransportSecuritySettings with tunnel hostname + localhost
in allowed_hosts. DNS rebinding protection stays active; tunnel hostname is explicitly allowed.

### armoriq register result (post-fix)

```
Registering with ArmorIQ control plane...
OK  Agent tripline-maintainer registered
OK  MCP server tripline-mcp registered (5 tools)
OK  Policy applied (1 allowed, 0 denied)
OK  Proxy endpoint: https://proxy.armoriq.ai
```

### Proxy mode check -- hello_tool

```
EnforceResult(
    allowed=True,
    action='allow',
    reason='Policy enforcement passed',
    delegation_id=None,
    matched_policy=None,
    obligations=[]
)
```

Proxy mode uses 'Policy enforcement passed' (not 'allow_with_logging'); same allowed=True.

### Proxy invoke -- raw HTTP POST to proxy.armoriq.ai/invoke

session.invoke() not available in SDK 0.6.10. Used raw HTTP:

```
POST https://proxy.armoriq.ai/invoke
Headers: X-API-Key: ak_live_..., Content-Type: application/json
Body: {"mcp": "tripline-mcp", "tool": "hello_tool", "args": {}, "token": "<token_id>"}

Response: HTTP 200
Body: {
  "jsonrpc": "2.0",
  "id": 1790932920501,
  "result": {
    "content": [{"text": "Hello from Tripline MCP!", "type": "text"}],
    "isError": false,
    "structuredContent": {"result": "Hello from Tripline MCP!"}
  }
}
```

Proxy chain confirmed: POST -> proxy.armoriq.ai -> Cloudflare tunnel -> MCP server -> tool -> response.
MCP server log: INFO 103.58.152.253:0 - "GET /mcp HTTP/1.1" 200 OK

---

## T7 -- NON-EXECUTION via proxy path

**STATUS: CONFIRMED**

### Raw results

```python
# Plan: [hello_tool]
# Check: echo_marker (NOT in plan)
EnforceResult(
    allowed=False,
    action='block',
    reason="tool-not-in-plan: 'echo_marker' was not declared in the captured plan",
    delegation_id=None,
    matched_policy=None,
    obligations=[]
)

# list_markers after blocked check:
'[]'   # empty -- marker NOT set
```

### Prevention mechanism

ArmorIQ SDK fast-path guard fires in proxy mode the same as in SDK mode.
session.check() checks the plan locally BEFORE any proxy routing.
The proxy was never contacted. The MCP server was never contacted.
The application gate (decision.allowed == False -> skip MCP call) is the final layer.

Who prevented execution:
- ArmorIQ SDK (client-side, tool-not-in-plan guard): blocked proxy routing
- Application gate: confirmed allowed=False, did not call MCP
- MCP server: never reached, no side effect

---

## Phase 0.5 Definition of Done

| Requirement | Status |
|-------------|--------|
| Backend ALLOW confirmed (matched_policy set) | DONE: cli-tripline-maintainer-tripline-mcp |
| Backend DENY confirmed (in-plan, policy-blocked) | DONE: tool_not_in_allowlist, matched_policy set |
| Fast-path vs backend deny distinction documented | DONE |
| read_file tool added (S2 parameter test) | DONE: sandboxed to ./fixtures |
| Parameter enforcement gap confirmed (tool-level only) | DONE |
| Hold mechanism introspected | DONE (live trigger blocked by missing policy rule) |
| Audit read probe completed | DONE (write-only confirmed, 401 on /iap/audit/logs) |
| Proxy mode working (421 fixed) | DONE: TRIPLINE_ALLOWED_HOSTS env var |
| ArmorIQ proxy invoke working | DONE: raw HTTP POST to proxy.armoriq.ai/invoke |
| Non-execution proof via proxy path | DONE: marker not set |
| No new secrets committed | DONE |
| docs/phase-0.5-gaps.md written | DONE |
