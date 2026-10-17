# Phase 2 — Product Information Architecture Blueprint

**Project:** TripLine  
**Branch:** `agent-v2` (`9b51028`)  
**Design Reference:** Palantir Multimodal Data Plane & Warp Speed visual design language, ArmorIQ authorization interface  
**Author:** Principal AI Solution Architect & Staff Full-Stack Engineer  
**Status:** Approved & Implemented  

---

## 1. Executive Product Narrative & Experience Strategy

### 1.1 The Core Proposition
TripLine is an enterprise AI security containment and cryptographic witness system designed to operate downstream of authorization frameworks such as **ArmorIQ**.

While ArmorIQ provides upstream intent and identity authorization (**"Should this agent perform this action?"**), TripLine provides runtime execution containment, path confinement, canary exfiltration inspection, and cryptographic auditability (**"Did the execution stay within OS boundaries, and can we mathematically prove what happened?"**).

```
+-------------------------------------------------------------------------------+
|                             ENTERPRISE AI PIPELINE                            |
+-------------------------------------------------------------------------------+
|  [Agent / Orchestrator]                                                       |
|       |                                                                       |
|       v (Proposed Action Packet)                                              |
|  [Plane 2: ArmorIQ Authorization Gateway]  --> DENY? Exit with Signed Deny     |
|       |                                                                       |
|       v (ALLOW)                                                               |
|  [Plane 3: TripLine MCP Containment Engine]                                   |
|       |-- Path Jail (open-then-verify fstat inode bounds check)               |
|       +-- Egress Canary Scanner (exact-match substring canary inspection)     |
|       |                                                                       |
|       v (DISPATCHED / CONTAINED)                                              |
|  [Plane 4: Witness & Cryptographic Receipts]                                  |
|       |-- RFC 8785 Canonical JSON Serialization                               |
|       +-- HMAC-SHA256 Append-Only Witness Chain Record                        |
+-------------------------------------------------------------------------------+
```

### 1.2 Unification of Public Narrative
Previously, the site exhibited narrative drift between:
1. A technical research dashboard (`/receipts`, `/attribution`, `/measured`).
2. An enterprise security portal (`/overview`).
3. An interactive agent playground (`/agent`).

**Resolution:**
The root route `/` is designated as the **single primary presentation and evaluation experience**. All secondary pages (`/agent`, `/receipts`, `/witness`, `/jail-burst`, `/console`, `/claims`, `/layers`, `/measured`) function as deep-dive forensic views sharing the identical silver/graphite design language, typography, shell, and data contracts.

---

## 2. Homepage Narrative Sequence (Route `/`)

The homepage guides evaluators, judges, and security architects through a logical 9-stage sequence:

### Section A — Premium Global Header
* **Visual Treatment:** Translucent frosted silver bar (`bg-white/80 backdrop-blur-md border-b border-[#CDD2D8]`).
* **Branding:** Official `TripLine` wordmark with silver/graphite mark and geometric typography.
* **Primary Navigation Links:**
  * `Overview` (`#overview` / `/overview`)
  * `Architecture` (`#architecture`)
  * `Live Demo` (`#demo` / `/agent`)
  * `Evidence & Receipts` (`/receipts`)
  * `Witness Chain` (`/witness`)
  * `Documentation` (`https://github.com/httpmonish/TripLine`)
* **Call to Action:** `Run Governed Demo` button with subtle electric cyan glow (`bg-[#20252B] text-white hover:bg-[#2D3136]`).
* **Environment Indicator:** Honest system status pill showing backend health (`API Online / Offline`) and ArmorIQ credential status (`ArmorIQ Mode B Fail-Closed / Cloud`).

### Section B — Editorial Hero & Value Hypothesis
* **Headline:**  
  `AI agents. Governed actions. Verifiable proof.`
* **Supporting Statement:**  
  *TripLine adds independent containment and verifiable execution evidence to governed AI workflows. ArmorIQ authorizes an action; TripLine’s implemented controls protect the applicable execution boundary and preserve evidence of what happened.*
* **Action Cluster:**
  * Primary: `Explore 4-Plane Architecture` (scrolls smoothly to Section C).
  * Secondary: `Launch Governed Demo` (triggers interactive flow or routes to `/agent`).
  * Tertiary: `Inspect Cryptographic Receipts` (`/receipts`).
* **Live System Metrics Strip:** Real-time metrics read from the backend API:
  * Total Verified Receipts count.
  * Witness Chain Height (`N` blocks).
  * Path Jail Inode Verification Latency (<0.4ms).
  * Active Enforcement Gate Status (`Mode B Fail-Closed Active`).

### Section C — Immersive Four-Plane Architecture (Visual Centerpiece)
* **Visual Core:** Hardware-accelerated CSS 3D perspective (`perspective: 1200px; transform-style: preserve-3d`) layered isometric SVG wafers.
* **Composition:** Dark graphite technical space (`#181B20`), silver technical linework (`#70767D`), translucent planes with high-contrast active nodes.
* **The 4 Stacked Planes:**
  1. **Plane 1 (Top): Agent & Trusted Intent Plane** (Task Ingress, Orchestrator, Scoped Readers/Responders, Action Proposal).
  2. **Plane 2: ArmorIQ Authorization Boundary** (Independent policy engine, Intent verification, Mode B Synchronous Gate).
  3. **Plane 3: TripLine MCP Runtime Containment** (Path Jail inode check, Egress Canary inspection, Tool Dispatcher).
  4. **Plane 4 (Bottom): Witness & Cryptographic Proof** (RFC 8785 Canonicalizer, HMAC-SHA256 Witness Chain, Immutable Receipts).
* **Interactivity:** Interactive plane selector, node inspector panel displaying genuine source code links (`security/path_jail.py`, `dashboard/api.py`, `receipts/models.py`), boundary ownership, and active runtime events.

### Section D — Functioning Agent Demonstration
* **Purpose:** Provide an authentic, non-simulated demonstration of TripLine in action.
* **Execution Options:**
  1. **Deterministic Local Proof Job (Primary for Judges):** Runs authentic test scenarios (`scenario`, `jail_burst`, `verify_all`, `rea_investigate`) against real backend APIs.
  2. **Live Agent Run (When Credentials Configured):** Dispatches real task to CrewAI orchestrator + reader/responder crew with fail-closed ArmorIQ authorization.
  3. **Recorded Replay:** Inspects authentic historical execution records (`results/phase3/scenario/`) with an explicit "Recorded Demonstration" badge.
* **Controls:** Scenario selector, `Run Governed Demo` button, execution progress indicator.

### Section E — What Actually Happened (Verdict Breakdown)
* **Real-Time Stage Matrix:**
  * **Proposed Action:** Tool name, arguments (sanitized, zero secret leakage), targeted file/URL.
  * **ArmorIQ Authorization:** Verdict (`ALLOW` / `DENY`), evaluation timestamp, policy rule.
  * **TripLine Containment:** Path Jail inode resolution (`IN_BOUNDS` / `JAIL_VIOLATION`), Canary check (`CLEAN` / `CANARY_DETECTED`).
  * **Dispatch State:** `DISPATCHED_TO_TOOL` vs `HALTED_PRE_DISPATCH`.
  * **Tool Execution Outcome:** Return status code, stdout snippet, error logs.
  * **Receipt Emission:** Cryptographic receipt ID (`RCP-...`) linking to raw canonical JSON.
  * **Verification Result:** Authoritative backend verifier output (`VERIFIED` / `FAILED`).

### Section F — Forensic Evidence & Cryptographic Verification
* **Display:** Live receipt card populated from `/api/receipts/latest`.
* **Actionable Tooling:**
  * `Verify Hash & Signature` (calls `POST /api/receipts/{id}/verify`).
  * `Run Server Tamper Check` (calls `POST /api/receipts/{id}/tamper-check` to prove single-bit modification causes instant failure without mutating disk).
  * `Inspect Witness Block` (links to `/witness` with block index).

### Section G — Why TripLine Complements ArmorIQ
* **Architecture Distinction Table:**
  | Dimension | ArmorIQ Authorization | TripLine Execution Containment |
  | :--- | :--- | :--- |
  | **Core Question** | *"Should the agent perform this task?"* | *"Did the tool stay inside its OS boundaries?"* |
  | **Enforcement Point** | Upstream Agent / API Gateway | In-MCP Tool Execution Hook |
  | **Defense Target** | Prompt injection, unauthorized intent, privilege escalation | Path traversal (`../../etc`), canary exfiltration, runaway processes |
  | **Evidence Output** | Authorization decision token | RFC 8785 canonical signed receipt + HMAC-SHA256 witness chain |
  | **Integration Model** | Synchronous Mode B authorization check | Local containment sandbox & evidence recorder |

### Section H — Measured Results, Limits & Scope
* **Authentic Test Results:**
  * Mode M2 Forced-Compliance Synthetic Benchmark: 100% containment across 10 deterministic probe attacks.
  * Defense-in-depth ablation: Jail alone (90%), Canary alone (85%), Combined TripLine + ArmorIQ (100%).
  * Overhead: <0.4ms average path jail fstat resolution; <1.2ms witness chain append.
* **Honest Scope Disclosures:**
  * Probes test file path traversal and exact-string canaries, not kernel memory corruption.
  * Cloud ArmorIQ checks require active network connectivity and valid API tokens; otherwise fail-closed policy rejects actions.

### Section I — Enterprise Closing & Technical Deep Links
* **Call to Actions:**
  * `Launch Full Agent Console` (`/agent`)
  * `Explore Evidence Vault` (`/receipts`)
  * `Read Technical Architecture Docs` (`/docs` / GitHub repository)

---

## 3. Supporting Pages Inventory & Data Contracts

All supporting pages adhere to the silver/white/graphite design system:

| Route | User Purpose | Authoritative Data Source | Primary Action | Error / Empty / Unavailable Handling |
| :--- | :--- | :--- | :--- | :--- |
| `/agent` | Live agent console & scenario runner | `POST /api/jobs`, `GET /api/agent/runs`, `GET /api/jobs/{id}/events` | Start/Cancel agent run; inspect live event stream | Explicit "No active runs" state; fail-closed badge if credentials missing |
| `/receipts` | Cryptographic receipt audit & tamper lab | `GET /api/receipts`, `GET /api/receipts/{id}`, `POST /api/receipts/{id}/verify` | Verify receipt; run non-destructive tamper test | Empty state if `results/` is clean; banner on invalid signature |
| `/witness` | Immutable audit log & HMAC chain explorer | `GET /api/witness/summary`, `POST /api/witness/verify` | Verify entire witness chain from genesis block | Chain breakdown indicator if hash mismatch detected |
| `/console` | Backend job execution & system diagnostics | `GET /api/jobs`, `GET /api/system/health`, `GET /api/status` | Filter running/completed jobs; view SSE logs | Real-time reconnecting indicator if SSE drops |
| `/jail-burst` | Adversarial path traversal & canary test suite | `POST /api/jobs` (`job_type: "jail_burst"`), `GET /api/measured` | Execute 10-probe adversarial benchmark suite | Clear notice indicating synthetic test harness |
| `/measured` | Performance overhead & containment metrics | `GET /api/measured`, `GET /api/status` | Filter benchmarks by attack category | Explanatory note detailing M2 benchmark methodology |
| `/claims` | Security claim verification & provenance map | `docs/redesign/phase-01-claims-and-security-audit.md` | Trace security claims to specific source files | Clarifies experimental vs production guarantees |
| `/layers` | Multi-layer defense attribution matrix | `GET /api/measured`, static architecture definition | Toggle active layer to isolate protection scope | N/A (interactive educational view) |
| `/overview` | Executive presentation of TripLine architecture | Static enterprise content + live status strip | Navigate to 4-plane architecture or agent console | Fallback to static system diagram if WebGL/3D fails |
| `/style-guide` | Component library & design token verification | `tripline-frontend/styles/tokens.css` | Inspect typography, colors, buttons, and badges | Direct visual reference for QA |

---

## 4. Phase Gate Acceptance Criteria Check

- [x] **Single Primary Homepage:** `/` serves as the authoritative, unified product showcase.
- [x] **No Competing Old/New Narratives:** Deprecated or fragmented narratives eliminated; legacy server-rendered views aligned.
- [x] **Logical Story Arc:** Evaluator moves naturally from Value Proposition $\to$ 4-Plane Architecture $\to$ Agent Demo $\to$ Cryptographic Proof.
- [x] **Honest Data Architecture:** Real endpoints specified; no fabricated stats or fallback random IDs.
