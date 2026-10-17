# Phase 2 — Page Storyboard & Experience Flow

**Project:** TripLine  
**Branch:** `agent-v2` (`9b51028`)  
**Design Reference:** Palantir Multimodal Data Plane & Warp Speed visual design language  
**Author:** Enterprise Product Designer & Creative Frontend Engineer  
**Status:** Approved & Implemented  

---

## 1. Visual Storyboard: Homepage (`/`)

The homepage delivers a cinematic, highly orchestrated product experience across 9 distinct visual scenes.

```
+----------------------------------------------------------------------------------------------------+
| SCENE 1: GLOBAL HEADER & STATUS                                                                    |
| [TripLine Logo]   Overview   Architecture   Demo   Evidence   Docs         [Run Governed Demo]     |
+----------------------------------------------------------------------------------------------------+
| SCENE 2: EDITORIAL HERO & CAMERA INITIALIZATION                                                    |
|                                                                                                    |
|          AI agents. Governed actions. Verifiable proof.                                            |
|          TripLine adds independent containment and verifiable execution evidence                    |
|          to governed AI workflows.                                                                 |
|                                                                                                    |
|          [ Explore Architecture ]   [ Run Live Demo ]   [ Inspect Receipts ]                       |
|                                                                                                    |
|          +-------------------------------------------------------------------------------+         |
|          | LIVE METRICS: 24 Verified Receipts | 84 Witness Blocks | <0.4ms Inode Jail   |         |
|          +-------------------------------------------------------------------------------+         |
+----------------------------------------------------------------------------------------------------+
| SCENE 3: FOUR-PLANE CINEMATIC ARCHITECTURE (Graphite Canvas, Silver Linework, CSS 3D Perspective)  |
|                                                                                                    |
|         / Plane 1: Agent & Trusted Plan \    --> [Orchestrator] -> [Proposal]                      |
|        /=================================\                                                         |
|                                                                                                    |
|             / Plane 2: ArmorIQ Gate \        --> [Identity & Policy] -> [Mode B Check]             |
|            /=========================\                                                             |
|                                                                                                    |
|                 / Plane 3: TripLine MCP \    --> [Path Jail Inode] -> [Canary Inspection]          |
|                /=========================\                                                         |
|                                                                                                    |
|                     / Plane 4: Witness \     --> [Canonical JSON] -> [HMAC-SHA256 Receipt]         |
|                    /====================\                                                          |
|                                                                                                    |
|    [Node Inspector Drawer: Shows Active Boundary, Source Code Link, Ingress/Egress Schema]        |
+----------------------------------------------------------------------------------------------------+
| SCENE 4: GOVERNED AGENT DEMONSTRATION & PROOF RUNNER                                               |
|                                                                                                    |
|    Select Scenario: [ Adversarial Path Traversal (Attack DP-01) v ]                               |
|    Execution Mode: (•) Deterministic Proof Job    ( ) Live Agent Run    ( ) Recorded Replay        |
|                                                                                                    |
|    [ Execute Selected Scenario ]    Job ID: job-proof-20261017-01   Run ID: run-9912a             |
+----------------------------------------------------------------------------------------------------+
| SCENE 5: WHAT ACTUALLY HAPPENED (EXECUTION TIMELINE & STAGE VERDICTS)                             |
|                                                                                                    |
|    1. Proposed Action: tool="read_file", path="../../etc/passwd"                                  |
|    2. ArmorIQ Authorization: ALLOW (Scoped role read permission validated)                        |
|    3. TripLine Containment: DENY / BLOCKED (Path jail fstat detected escaping symlink/relative)   |
|    4. Tool Execution: NOT_DISPATCHED (Execution stopped at TripLine boundary)                     |
|    5. Receipt Emission: RCP-20261017-DP01 (Canonical hash generated)                             |
+----------------------------------------------------------------------------------------------------+
| SCENE 6: EVIDENCE & CRYPTOGRAPHIC VERIFICATION PANEL                                               |
|                                                                                                    |
|    Receipt: RCP-20261017-DP01                                                                      |
|    Hash: 8f9b2c4e1... (RFC 8785 Canonical JSON)                                                    |
|    Signature: Verified HMAC-SHA256 with witness block #84                                         |
|                                                                                                    |
|    [ Verify Authenticity with Backend ]        [ Run Server-Side Tamper Test ]                    |
|    Result: ✓ CRYPTOGRAPHICALLY VALID           Result: ✗ TAMPER DETECTED (Single-bit deviation)  |
+----------------------------------------------------------------------------------------------------+
| SCENE 7: DEFENSE-IN-DEPTH MATRIX (TripLine vs ArmorIQ Separation)                                 |
|                                                                                                    |
|    Clear technical attribution showing why upstream authorization needs runtime OS containment.   |
+----------------------------------------------------------------------------------------------------+
| SCENE 8: BENCHMARKS & VERIFIED BOUNDARIES                                                          |
|                                                                                                    |
|    100% containment on M2 test suite | <0.4ms latency overhead | Full disclosure of scope limitations|
+----------------------------------------------------------------------------------------------------+
| SCENE 9: ENTERPRISE CALL TO ACTION & FOOTER                                                        |
|                                                                                                    |
|    [ Open Agent Console ]    [ View Witness Explorer ]    [ Read Documentation ]                   |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Interactive State Progression Storyboard

### State 1: Cold / System Idle
* **Hero Visual:** Architecture in idle standby mode. Subtle breathing pulse on Plane 1 (Agent).
* **Metrics:** Live system counts fetched via `GET /api/status` and `GET /api/receipts`.
* **Node Inspector:** Closed or showing default architectural summary.

### State 2: Scenario Initiated
* **User Action:** User clicks `Execute Selected Scenario` or selects a scenario chip.
* **UI Feedback:**
  * Job status changes to `PROVISIONING` $\to$ `RUNNING`.
  * Real Job ID displayed (`job-xxxx`).
  * Architecture camera smoothly pans down to focus on Plane 1 $\to$ Plane 2 connector.
  * Event stream connects via SSE (`/api/jobs/{id}/events`).

### State 3: ArmorIQ Authorization Evaluation
* **Event Ingress:** Agent proposes an action (`readFile`, `execCommand`, `fetchUrl`).
* **Camera Focus:** Shifts dynamically to Plane 2 (ArmorIQ Authorization Plane).
* **Visual Cue:**
  * If `ALLOW`: Connector line illuminates in signal cyan (`#65BCE7`) passing through to Plane 3.
  * If `DENY`: Connector halts at Plane 2, flashing amber/red with reason: `Policy violation: Role unauthorized for targeted resource`.

### State 4: TripLine MCP Runtime Containment
* **Camera Focus:** Centers on Plane 3 (TripLine Containment Plane).
* **Path Jail / Canary Inspection:**
  * If valid within sandbox root: passes to dispatch module.
  * If path traversal attempted (`../../etc/passwd`): Path Jail triggers immediate containment (`TRIPLINE_DENY`), prevents process dispatch.
  * If egress canary detected: Egress proxy triggers `HOLD`.

### State 5: Witness Recording & Receipt Emission
* **Camera Focus:** Descends to Plane 4 (Witness Plane).
* **Action:**
  * RFC 8785 canonical JSON serializer normalizes the event record.
  * HMAC-SHA256 signature generated and recorded into the append-only witness chain.
  * Receipt card on the right-hand panel illuminates with the newly minted receipt ID.

### State 6: Proof Verification
* **User Action:** User clicks `Verify Authenticity with Backend`.
* **Backend Call:** `POST /api/receipts/{id}/verify`.
* **UI Feedback:** Instant confirmation badge with green shield icon, timestamp, and verification latency.
* **Tamper Simulation:** User clicks `Run Server-Side Tamper Test`. The server tests a 1-bit perturbed copy in memory, returning an authentic verification failure while leaving disk records intact.

---

## 3. Supporting Page Storyboards

### 3.1 `/agent` (Interactive Agent Operations Center)
* **Layout:** Dual-pane split view.
  * **Left Pane (40%):** Orchestrator status, Crew members (Orchestrator, Security Reader, Response Synthesizer), Scenario launcher, Job controls.
  * **Right Pane (60%):** Real-time execution log (SSE stream), Stage timeline, Proposed action inspector with JSON schema validation.

### 3.2 `/receipts` (Cryptographic Evidence Explorer)
* **Layout:** Filterable table + deep inspection drawer.
  * **Top Filter Bar:** Search by Receipt ID, filter by Verdict (`ALLOW`, `DENY`, `HOLD`), filter by Tool.
  * **Table View:** Receipt ID, Action, ArmorIQ Decision, TripLine Decision, Dispatch State, Hash, Timestamp, Actions.
  * **Detail Modal/Drawer:** Raw canonical JSON viewer, cryptographic signature validation strip, tamper demonstration controls.

### 3.3 `/witness` (Immutable HMAC Chain Explorer)
* **Layout:** Vertical blockchain-style block visualizer.
  * **Chain Summary:** Genesis hash, Current block height, Total events signed.
  * **Block Cards:** Block index, Parent hash, Block hash, Event count, Timestamp, Cryptographic signature.
  * **Global Action:** `Verify Full Chain Integrity` button triggering `POST /api/witness/verify`.

---

## 4. Design Guidelines & Visual Guardrails

1. **Restrained Color Hierarchy:**
   * 85% Neutral Canvas: Silver (`#F4F5F6`), Crisp White (`#FFFFFF`), Deep Graphite (`#20252B`), Slate Borders (`#CDD2D8`).
   * 10% Technical Backgrounds: Charcoal Diagram Base (`#181B20`), Translucent Wafers (`#24272B`/`#2D3136`).
   * 5% Signal Accents: Signal Cyan (`#65BCE7`), Valid Green (`#10B981`), Blocked Red (`#EF4444`), Warning Amber (`#F59E0B`).
2. **Typography Scale:**
   * Geist Sans for interface labels, headings, and explanations.
   * Geist Mono strictly reserved for hashes, IDs, timestamps, and JSON payloads.
3. **No Decorative Animations:** Every transition maps directly to a state change in the execution pipeline.
