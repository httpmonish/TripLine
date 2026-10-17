# Phase 5 — Four-Plane Architecture Specification

**Project:** TripLine  
**Branch:** `agent-v2` (`9b51028`)  
**Component:** `tripline-frontend/components/diagrams/FourPlaneArchitecture.tsx`  
**Author:** 3D/Web Animation Architect & Principal AI Solution Architect  
**Status:** Approved & Implemented  

---

## 1. Architectural Geometry & Spatial Composition

The visual signature of TripLine is a dimensional, multi-layered isometric system composed of **four physical wafers (planes)** stacked in 3D perspective space:

```
                          PLANE 1: AGENT & TRUSTED PLAN
           [Task Ingress] -----> [Crew Orchestrator] -----> [REA Intent Model]
                                      |
                                      v (Proposed Action Packet)
                   ===============================================
                       PLANE 2: ARMORIQ AUTHORIZATION BOUNDARY
           [Independent Policy Engine]  --> DENY: Terminate with Signed Upstream Receipt
                                      |
                                      v (ALLOW)
                   ===============================================
                     PLANE 3: TRIPLINE MCP RUNTIME CONTAINMENT
           [Path Jail: open-then-verify fstat]  --> [Egress Canary Gateway]
                                      |
                                      v (CLEAN & IN-BOUNDS)
                                 [Tool Dispatcher]
                   ===============================================
                      PLANE 4: WITNESS & CRYPTOGRAPHIC PROOF
           [RFC 8785 Canonical JSON]  --> [HMAC-SHA256 Append-Only Witness Chain]
```

### 1.1 CSS 3D Perspective Architecture
* **Stacking Technique:** Built using hardware-accelerated CSS 3D transforms (`perspective: 1400px; transform-style: preserve-3d; transform: rotateX(24deg) rotateZ(-4deg)`).
* **Zero Three.js / WebGL Dependencies:** Eliminates React 19 compatibility failures, bundle bloat (saving >600KB), and SSR canvas hydration flashes.
* **Retina Typography:** Every label, hash, and boundary badge is native DOM/SVG, rendering with sub-pixel sharpness across high-DPI displays.
* **Responsive 2D Fallback:** Instant toggle to planar 2D orthogonal mode for mobile screens, reduced motion preferences, or lower-power devices.

---

## 2. Four Planes Specification & Boundary Ownership

### Plane 1: Agent & Trusted Plan
* **System Owner:** Upstream Agent / CrewAI Orchestrator.
* **Nodes:**
  1. `Task Ingress`: Ingestion of untrusted external prompts, issue bodies, or webhook triggers.
  2. `Crew Orchestrator`: Administrative scoping of reader and responder sub-agents.
  3. `REA Intent Model`: Synthesis of structured action packets before OS execution.
* **Integrity Guarantee:** Plan metadata reflects authentic run structures; zero fake Merkle hashes.

### Plane 2: ArmorIQ Authorization Boundary
* **System Owner:** ArmorIQ Intent Authorization Proxy (IAP).
* **Nodes:**
  1. `ArmorIQ Policy Gate`: Evaluates intent tokens and role authorizations.
* **Enforcement Distinction:** When an action is denied at Plane 2 (e.g. `delete_branch`), execution halts immediately. Plane 3 (TripLine Containment) is marked **`NONE (NOT REACHED)`** and never illuminates downstream tools.

### Plane 3: TripLine MCP Runtime Containment
* **System Owner:** TripLine Runtime Execution Boundary.
* **Nodes:**
  1. `TripLine Path Jail`: Resolves file descriptors using `os.open(O_NOFOLLOW)` and `fstat` inode bounds checking to trap `../../` traversal, symlink escapes, and null-byte injection.
  2. `Egress Canary Gateway`: Inspects outbound parameters for seeded canary tokens; places exfiltration attempts in a non-dispatched `HOLD` state.
  3. `Protected Dispatcher`: Sandboxed tool execution.

### Plane 4: Witness & Cryptographic Proof
* **System Owner:** TripLine Forensic Proof Subsystem.
* **Nodes:**
  1. `RFC 8785 Canonicalizer`: Byte-for-byte deterministic JSON serialization.
  2. `Witness Hash Chain`: Append-only HMAC-SHA256 log chain.
* **Integrity Guarantee:** Displays authentic receipt IDs (`RCP-phase3-wow-ca5dcec9-...`) from real files in `results/phase3/scenario/`. Zero synthetic random IDs.

---

## 3. Interactive Node Inspector Panel

Selecting any node reveals an authoritative inspection drawer detailing:
* **Node Functional Role:** Plain-language explanation of its security function.
* **Boundary Owner:** Explicit attribution (`Upstream Agent`, `ArmorIQ Engine`, `TripLine Runtime`, `Forensic Witness`).
* **Input / Output Contracts:** Exact parameters evaluated at that boundary.
* **Source Code Link:** Clickable reference to the implementing Python module (`security/path_jail.py`, `security/egress_gateway.py`, etc.).
* **Replay Evidence:** Associated authentic receipt ID, canonical SHA-256 hash, and provenance file.

---

## 4. Phase Gate Acceptance Criteria Check

- [x] **Four Planes Clearly Delineated:** Geometry reflects the actual defense-in-depth pipeline.
- [x] **Zero Synthetic IDs:** Replaced placeholder IDs with authentic `results/phase3/scenario/` data.
- [x] **Zero Timer-Driven Progression:** Removed fake `setTimeout` cascades.
- [x] **Distinct Boundaries:** Upstream ArmorIQ authorization is never conflated with downstream TripLine jail/canary containment.
- [x] **Planar Fallback:** 2D switchable mode supports mobile viewports and reduced-motion environments.
