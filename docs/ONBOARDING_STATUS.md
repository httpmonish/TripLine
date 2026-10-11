# ArmorIQ Platform Onboarding & Invocation Status

**Project**: Tripline  
**Hackathon**: ArmorIQ "Flow State 2026" (10–17 Oct 2026)  
**Date**: 2026-10-11  
**Audit Phase**: Phase 8 Gap Closure  

---

## 1. Onboarding Status Matrix

| Component | Status | Evidence / Finding | Action Required |
|---|---|---|---|
| **Agent Registered** (`tripline-maintainer`) | **UNVERIFIED** | Phase 0 bootstrap recorded agent ID `40a9572d-8282-4757-a31d-9c2288a9dfeb`. Currently, API key returns HTTP 401 Unauthorized (`Invalid or expired API key`). Authoritative confirmation requires platform dashboard screenshot. | Owner screenshot of `platform.armoriq.ai` Agents tab saved to `docs/evidence/phase8/agent_dashboard.png`. |
| **MCP Registered** (`tripline-mcp`) | **UNVERIFIED** | Phase 0 recorded server ID `75cf4e64-b422-4763-bc00-9d6aa5d67a4b` pointing to a Cloudflare tunnel URL (`https://patio-retailers-...trycloudflare.com/mcp`). Localhost cannot be onboarded without an active public HTTPS tunnel. | Owner screenshot of `platform.armoriq.ai` MCP Servers tab saved to `docs/evidence/phase8/mcp_dashboard.png`. Note: Local runs bypass proxy and use direct execution post-check. |
| **Policies Present** (`cli-tripline-maintainer-tripline-mcp`) | **UNVERIFIED** | Phase 0 recorded policy ref `armoriq:eb0e6079680f:1a1251b073c`. Currently blocked from live API query due to HTTP 401 key expiration. | Owner screenshot of `platform.armoriq.ai` Policies tab saved to `docs/evidence/phase8/policy_dashboard.png`. |
| **API Key Active** | **UNVERIFIED (401 Expired)** | Live POST to `https://api.armoriq.ai/iap/sdk/bootstrap` returns HTTP 401 `{"message":"Invalid or expired API key"}` for both `.env` and `~/.armoriq/credentials.json`. | Owner must generate or rotate API key in `platform.armoriq.ai` Settings -> API Keys. |
| **Invocation Path** | **VERIFIED** | Architecture: **Enforce-check then direct call**. ArmorIQ authorizes every action via `session.check()` (`mode="sdk"`) before Tripline's local MCP executes the tool call. | Documented plainly in `README.md` and `docs/SUBMISSION.md`. Alternative (proxy mode) documented as limitation. |

---

## 2. Invocation Path Architecture & Limitations

### Verified Path: SDK Pre-Enforcement Check
1. The agent loop initializes an ArmorIQ SDK session: `session = aiq_client.start_session(SessionOptions(mode="sdk", default_mcp_name="tripline-mcp"))`.
2. Before any tool call executes, the agent invokes `decision = session.check(tool_name, tool_args)`.
3. The SDK transmits an outbound HTTP POST to `https://api.armoriq.ai/iap/sdk/enforce`.
4. If ArmorIQ returns `action: block` (`decision.allowed == False`), Tripline records an incident receipt and halts execution without touching the MCP server.
5. If ArmorIQ returns `action: allow`, Tripline validates downstream layers (Path Jail, Egress Gateway, Decision Proof) before executing the MCP tool directly.

### Documented Limitation: Direct Call vs. Proxy Invoke
* **Platform Proxy Mode (`mode="proxy"`)**: In proxy mode, tool calls are routed through `https://proxy.armoriq.ai`, which forwards to a public HTTPS endpoint for the MCP server.
* **Why Tripline Uses SDK Mode**:
  1. A localhost MCP server cannot receive requests from ArmorIQ's cloud proxy without maintaining a continuous public HTTPS tunnel (e.g. Cloudflare Quick Tunnel / ngrok).
  2. Transient tunnel teardowns cause HTTP 502 / 421 transport errors during automated test suites.
  3. SDK mode provides authoritative cloud OPA policy enforcement at `api.armoriq.ai` without requiring external inbound network ingress to the developer's laptop.

---

## 3. Owner Action Checklist (Dashboard Verification)

Please perform these steps in the `platform.armoriq.ai` web console:

1. **Rotate/Generate API Key**:
   - Navigate to **Settings** -> **API Keys**.
   - Create a fresh API key or inspect the existing key status.
   - Update `~/.armoriq/credentials.json` or `.env` with the active key (never commit to git).
2. **Capture Evidence Screenshots**:
   - Capture screenshot of **Agents** page showing `tripline-maintainer` -> save to `docs/evidence/phase8/agent_dashboard.png`.
   - Capture screenshot of **MCP Servers** page showing `tripline-mcp` -> save to `docs/evidence/phase8/mcp_dashboard.png`.
   - Capture screenshot of **Policies / Policy Studio** showing `cli-tripline-maintainer-tripline-mcp` -> save to `docs/evidence/phase8/policy_dashboard.png`.
   - Capture screenshot of **API Keys** page (ensure the secret key value is masked/hidden) -> save to `docs/evidence/phase8/apikey_dashboard.png`.
3. **Optional: Explicit Deny Policy**:
   - In Policy Studio, if an explicit deny rule for `delete_branch` is desired instead of allowlist omission (`tool_not_in_allowlist`), add an explicit DENY rule for `delete_branch`.
