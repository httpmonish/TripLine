# Tripline Hackathon Submission Package

**Competition**: ArmorIQ "Flow State 2026" Hackathon (10–17 Oct 2026)  
**Target Submission Date**: 16 Oct 2026 (Hard Close: 17 Oct 2026 23:59 Asia/Calcutta, UTC+05:30)

---

## 1. Project Header & Tagline
* **Project Name**: Tripline
* **Tagline (< 80 chars)**: *Blocked isn't evidence. Every denied action gets a receipt.* (62 characters)

---

## 2. Short Descriptions (3 Lengths)

### A. ~50 Words (Elevator Pitch)
Tripline is a verifiable forensic evidence layer for autonomous AI agents integrated with ArmorIQ. While ArmorIQ authorizes tool actions upstream, Tripline’s in-MCP boundary jail and egress canary gateway contain malicious arguments downstream. Every denied action produces an HMAC-signed incident receipt, proving that blocked actions produced zero side effects.

### B. ~100 Words (Executive Summary)
Autonomous AI agents require defense-in-depth: authorization of an action does not authorize every downstream use of its data. Tripline bridges policy enforcement and forensic verification. Integrated with the ArmorIQ platform, Tripline captures the agent loop across three distinct defense layers: upstream tool authorization (ArmorIQ), in-MCP filesystem boundary containment (Tripline Path Jail), and outbound canary exfiltration prevention (Tripline Egress Gateway). When an attack occurs, Tripline doesn't just block it—it records an HMAC-chained witness log and mints a tamper-detectable cryptographic incident receipt proving that the prohibited action never executed.

### C. ~200 Words (Full Overview)
In high-stakes agentic workflows, an empty error message or a "blocked" log line is insufficient evidence. Security teams need attributable, tamper-detectable proof of what an agent attempted, which layer intercepted it, and whether side effects occurred. Tripline introduces an orthogonal defense-in-depth and forensic evidence architecture for autonomous agents operating through MCP.

Working with ArmorIQ's real platform enforcement (`/iap/sdk/enforce`), Tripline defends across three architectural boundaries. When an adversarial instruction attempts out-of-scope operations like `delete_branch`, ArmorIQ intercepts the call upstream (not on the agent's allowlist). When an agent attempts directory traversal escapes like reading `~/.ssh/fake_key`, Tripline's in-MCP Path Jail traps the inode boundary. When an agent attempts to exfiltrate planted secrets through issue comments, Tripline's Egress Gateway quarantines the payload.

Crucially, Tripline proves what happened: every security event appends to an HMAC-chained witness log and mints an HMAC-SHA256 Canonical JSON Incident Receipt covering the tool call, argument hash, layer decision, and execution count (0). Any post-hoc modification triggers deterministic tamper detection. Tested across real scenario runs and deterministic test harnesses across a 5-issue queue, Tripline ensures that "ArmorIQ decides, and Tripline proves."

---

## 3. Problem & Solution Overview

### The Problem (3 Sentences)
Existing AI agent security gateways operate as black-box firewalls that drop unauthorized prompts or return generic denial errors. However, authorization of an initial tool call does not prevent an agent from using authorized tools with malicious parameters, such as directory traversal or secret exfiltration. Furthermore, a simple "blocked" log entry fails to provide cryptographic proof to auditors that the prohibited action produced zero side effects.

### What Tripline Does (5 Core Capabilities)
* **Action-Level Boundary Enforcement**: Connects directly to the ArmorIQ platform to enforce strict tool allowlists on every MCP call.
* **In-MCP Filesystem Jail**: Intercepts path arguments at the file descriptor level (`fstat` inode check) to block path traversal outside the repository root.
* **Egress Canary Gateway**: Traps planted canary tokens (`TRPL-TRA-...`) in outbound comment payloads before network dispatch.
* **Zero-Execution Proof**: Asserts and seals execution counts (`0 executed`) in the MCP witness chain whenever an action is blocked.
* **Cryptographic Incident Receipts**: Emits Canonical JSON SHA-256 receipts signed with HMAC-SHA256, enabling independent offline verification and tamper detection.

### How ArmorIQ is Used
ArmorIQ serves as the upstream authorization layer (Layer 1). On every proposed tool call, the agent loop calls the ArmorIQ SDK (`/iap/sdk/enforce`) with the active session token and proposed tool. ArmorIQ evaluates the agent role against platform policy `cli-tripline-maintainer-tripline-mcp`. If unauthorized (e.g., `delete_branch`), ArmorIQ returns an immediate `block` decision (`reason: tool_not_in_allowlist`), preventing the request from ever reaching the MCP server.

### What Tripline Adds
Tripline provides downstream parameter containment and cryptographic evidence:
1. **Defense-in-Depth**: Catches traversal attacks and data exfiltration on tools that ArmorIQ legitimately authorizes (e.g., `read_file` and `comment_issue`).
2. **Cryptographic Receipts**: Transforms denial logs into verifiable HMAC-signed receipts.

---

## 4. Proof of ArmorIQ Blocking an Action

Captured directly from live evaluation against `https://api.armoriq.ai/iap/sdk/enforce`:
```json
{
  "tool": "delete_branch",
  "decision": "DENY",
  "allowed": false,
  "action": "block",
  "reason": "tool_not_in_allowlist",
  "matched_policy": "cli-tripline-maintainer-tripline-mcp",
  "trace_id": "06ff60f0-7696-4922-a98f-d60528e62249",
  "token_id": "3fb28b396c8f45dbaae5aefa8f01be4a",
  "policy_ref": "armoriq:eb0e6079680f:1a1255d239e",
  "endpoint": "https://api.armoriq.ai/iap/sdk/enforce"
}
```
* **Evidence File**: `results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json`
* **Audit Screenshot**: `[SCREENSHOT PENDING — human to capture on platform.armoriq.ai]`

---

## 5. Built With
* **Language & Frameworks**: Python 3.13.16, FastMCP / Model Context Protocol (v1.25.0), FastAPI (v0.115.11), Starlette, Jinja2.
* **Security & Auth**: `armoriq_sdk` (v0.6.10), HMAC-SHA256, Canonical JSON SHA-256.
* **Test & Verification**: `pytest` (v9.1.1), `pytest-asyncio`, Uvicorn.
* **Evaluated LLM**: Anthropic Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`).

---

## 6. Challenges and What Is Honest
* **Model Refusal vs. Layer Exercise**: Modern frontier LLMs refuse overt attack instructions (we observed a 40% refusal rate). To ensure guardrails are deterministically tested, we built both live agent scenarios and automated probe sweeps (`scripts/jail_burst.py`).
* **The Honest Residual**: Tripline's egress gateway checks exact canary substrings. It does not detect Base64-encoded, reversed, or split tokens.
* **Small Sample Sizes**: Measured runs use N=15 (k=5 per cell); we claim no broad statistical significance beyond this test suite. Historical 86-run benchmarks used Mode M2 forced-compliance synthetic stubs.

---

## 7. Submission Disclosures
* **Pre-Existing Code (Rule 5)**: Pre-build-week foundation (29,785 lines across 18 directories) was disclosed and approved. In-window development produced 5,079 added lines (14.57% net growth). See `docs/IN_WINDOW_LEDGER.md`.
* **Sandbox Only (Rule 7)**: All operations ran in disposable local sandboxes. `~/.ssh/fake_key` is a synthetic fixture; no real keys or credentials were used.
* **AI Assistance**: Built with AI coding assistance ([OWNER TO CONFIRM TOOLS]).

---

## 8. Submission Links
* **Repository URL**: `https://github.com/httpmonish/TripLine.git`
* **Demo Video (≤ 90 seconds)**: `[PHASE 6 LINK PENDING]`
* **Contact Email**: `[OWNER TO ADD]`
