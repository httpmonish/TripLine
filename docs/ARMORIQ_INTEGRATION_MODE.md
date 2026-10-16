# ArmorIQ Integration Mode Decision (Phase 11 P1)

**Date**: 2026-10-16  
**Auditor**: Tripline Phase 11 Agent  
**Decision**: **MODE B** (Direct Local MCP Execution with Synchronous ArmorIQ Authorization)

---

## 1. Analysis of Modes

### Mode A (Platform Proxy Mode)
- **Architecture**: `LLM Plan` → `ArmorIQ capture_plan` → `ArmorIQ get_intent_token` → `ArmorIQ invoke()` via `https://proxy.armoriq.ai` → Platform proxies request over public internet to Tripline MCP endpoint.
- **Prerequisites**:
  1. Tripline MCP registered in ArmorIQ platform dashboard.
  2. Publicly accessible MCP URL reachable by ArmorIQ proxy (e.g. Cloudflare tunnel or hosted deployment).
  3. Valid, active ArmorIQ API key authorized for the organization and agent.
- **Observed Status**:
  - Outbound probe to ArmorIQ backend returns HTTP 401: `"Invalid or expired API key"`.
  - Public Cloudflare tunnel from prior phase is inactive.
  - Tunnel creation requires explicit owner approval (`TUNNEL APPROVED`, Rule R5).
  - Mode A is **NOT** currently operational from this machine.

### Mode B (Local Direct Execution with ArmorIQ Authorization)
- **Architecture**: `Trusted Planner` → `Plan Captured` → `ArmorIQ Session Check / Enforce` → `Local Tripline MCP Execution` (Path Jail, Canary Gateway) → `Tripline Witness Chain & HMAC Receipts`.
- **Honest Disclosure Wording (Mandatory for UI & README)**:
  > **"ArmorIQ authorizes each action before Tripline's MCP executes it; calls are not proxied through the platform."**

---

## 2. Policy Enforcement & Attribution in Mode B
- **Authorization Boundary**: The agent queries ArmorIQ's policy evaluation before any tool invocation is dispatched to Tripline's local MCP.
- **Fail-Closed Behavior**: If ArmorIQ denies an action or raises `PolicyBlockedException`, Tripline does **not** call the MCP tool.
- **Tripline Security Layers**: For any action ArmorIQ permits, Tripline's independent security layers (Path Jail against path traversal, Egress Gateway against canary leak) inspect arguments and contain the action.
- **Receipts**: Every denied action produces a cryptographically signed HMAC receipt with full forensic attribution.
