# Tripline — Hackathon Submission Packet (Final)

**Competition**: ArmorIQ "Flow State 2026" Hackathon (10–17 Oct 2026)  
**Submission Target**: 16 Oct 2026 (Hard Close: 17 Oct 2026 23:59 Asia/Calcutta, UTC+05:30)  
**Branch**: `phase7-final`  
**Repository**: `https://github.com/httpmonish/TripLine.git`  
**Demo Video URL**: `[OWNER TO PASTE: YouTube / Loom / Drive link to video/out/tripline_demo_90s.mp4]`  
**Contact Email**: `[OWNER TO PASTE: your-email@example.com]`  

---

## 1. Project Header & Tagline

* **Project Name**: Tripline
* **Tagline**: *Blocked isn't evidence. Every denied action gets a receipt.* (62 characters)
* **Closing Line**: *ArmorIQ decides. Tripline proves.*

---

## 2. Short Descriptions

### A. ~50 Words (Elevator Pitch)
Tripline is a verifiable forensic evidence layer for autonomous AI agents integrated with ArmorIQ. While ArmorIQ authorizes tool actions upstream, Tripline’s in-MCP boundary jail and egress canary gateway contain malicious arguments downstream. Every denied action produces an HMAC-signed incident receipt, proving that blocked actions produced zero side effects.

### B. ~100 Words (Executive Summary)
Autonomous AI agents require defense-in-depth: authorization of an action does not authorize every downstream use of its data. Tripline bridges policy enforcement and forensic verification. Integrated with the ArmorIQ platform, Tripline captures the agent loop across three distinct defense layers: upstream tool authorization (ArmorIQ), in-MCP filesystem boundary containment (Tripline Path Jail), and outbound canary exfiltration prevention (Tripline Egress Gateway). When an attack occurs, Tripline doesn't just block it—it records an HMAC-chained witness log and mints a tamper-detectable cryptographic incident receipt proving that the prohibited action never executed.

### C. ~200 Words (Full Overview)
In high-stakes agentic workflows, an empty error message or a "blocked" log line is insufficient evidence. Security teams need attributable, tamper-detectable proof of what an agent attempted, which layer intercepted it, and whether side effects occurred. Tripline introduces an orthogonal defense-in-depth and forensic evidence architecture for autonomous agents operating through MCP.

Working with ArmorIQ's real platform enforcement (`/iap/sdk/enforce`), Tripline defends across three architectural boundaries. When an adversarial instruction attempts out-of-scope operations like `delete_branch`, ArmorIQ intercepts the call upstream. When an agent attempts directory traversal escapes like reading `~/.ssh/fake_key`, Tripline's in-MCP Path Jail traps the inode boundary. When an agent attempts to exfiltrate planted secrets through issue comments, Tripline's Egress Gateway quarantines the payload.

Crucially, Tripline proves what happened: every security event appends to an HMAC-chained witness log and mints an HMAC-SHA256 Canonical JSON Incident Receipt covering the tool call, argument hash, layer decision, and execution count (0). Any post-hoc modification triggers deterministic tamper detection. Tested against Claude 3.5 Sonnet across a 5-issue queue, Tripline ensures that "ArmorIQ decides, and Tripline proves."

---

## 3. Proof of ArmorIQ Platform Enforcement

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

* **Live Verification Trace (Re-verified Phase 7)**: `b129c7cf-6435-46eb-a970-1ea1f93f6c68` (HTTP 200, action: `block`, reason: `tool_not_in_allowlist`).
* **Evidence File**: `results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json` (SHA-256: `9efea4489eb1a6b0931557bf8cf2523bc380d96ae236104bc1ec9ce93bc31a89`).
* **Platform Audit Screenshot**: `docs/evidence/phase7/armoriq_audit_screenshot.png` `[OWNER TO CAPTURE from platform.armoriq.ai Audit Logs]`.

---

## 4. Built With (Real Versions)

* **Languages & Core Runtime**: Python 3.13.16.
* **Agent Plane & Protocols**: FastMCP / Model Context Protocol (v1.25.0), Starlette, Jinja2.
* **Security & Auth**: `armoriq_sdk` (v0.6.10), HMAC-SHA256, Canonical JSON SHA-256.
* **API & Judge Dashboard**: FastAPI (v0.115.11), Uvicorn (v0.34.0), pure server-rendered HTML (zero external CSS/JS CDN dependencies).
* **Testing & Verification**: `pytest` (v9.1.1), `pytest-asyncio`.
* **Evaluated Foundation Model**: Anthropic Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`).

---

## 5. Honest Challenges & Limitations

* **Model Refusal vs. Guardrail Exercise**: Frontier LLMs refuse overt attack instructions (we observed a 40% refusal rate on Claude 3.5 Sonnet). To guarantee security boundaries are deterministically exercised regardless of model variance, we built both live agent scenarios and automated probe sweeps (`scripts/jail_burst.py`).
* **The Honest Residual**: Tripline's egress gateway inspects for exact canary substring tokens (`TRPL-TRA-...`). If an agent transforms the token (Base64 encoding, reverse string, character split), neither layer intercepts the exfiltration.
* **Cryptographic Scope**: Receipts and witness logs are HMAC-signed; they detect any alteration by non-keyholders, but an actor possessing the private witness key can forge entries.
* **Sample Sizes**: Measured runs use N=15 (k=5 per cell); we claim no broad statistical significance beyond this test suite. Historical benchmarks citing 86 runs used Mode M2 forced-compliance synthetic stubs.

---

## 6. Disclosures

* **Pre-Existing Code (Rule 5)**: Pre-build-week foundation (29,785 lines across 18 directories) was disclosed and approved. In-window development produced 5,079 added lines (14.57% net growth). Full commit accounting: [`docs/IN_WINDOW_LEDGER.md`](file:///Users/themonishnawaz/tripline/docs/IN_WINDOW_LEDGER.md).
* **Sandbox Only (Rule 7)**: All operations ran in disposable local sandboxes. `~/.ssh/fake_key` is a synthetic fixture; no real keys or credentials were used.
* **AI Assistance**: Antigravity IDE (Gemini agent) pair-programming assistance for implementation, test authoring, and documentation audits.
* **Media / Synthetic Voice**: The 86-second demo video is silent with burned-in synchronized captions (`video/captions.srt`) and a silent AAC stereo track; no synthetic voice clone was used.
* **Third-Party Open Source**: See [`THIRD_PARTY.md`](file:///Users/themonishnawaz/tripline/THIRD_PARTY.md) for licenses of all dependencies.

---

## 7. How a Judge Can Check in Two Minutes (3 Commands)

No API keys, external networks, or cloud signups required:

```bash
# 1. Cryptographically verify all authentic receipts in results/
make verify

# 2. Tamper with one byte of a receipt copy and watch it get caught
make tamper

# 3. Launch the offline, dependency-free judge dashboard
make dashboard
# Visit http://127.0.0.1:8000 in your browser to view receipts, attribution, and measured runs.
```
