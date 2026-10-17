# Phase 6 — Cinematic Motion & Choreography Specification

**Project:** TripLine  
**Branch:** `agent-v2` (`9b51028`)  
**Design Reference:** Palantir Multimodal Data Plane & Warp Speed visual design language  
**Author:** Creative Frontend Engineer & 3D/Web Animation Architect  
**Status:** Approved & Implemented  

---

## 1. Cinematic Motion Principles & Rhythm

TripLine’s motion system is designed for enterprise gravitas and technical clarity. Animations exist exclusively to explain spatial relationships and state transitions, avoiding decorative or distracting gaming effects.

### 1.1 Core Motion Tokens
* **Standard Easing:** `cubic-bezier(0.16, 1, 0.3, 1)` (smooth deceleration into rest).
* **Signal Pulse:** Controlled breathing cycle on active execution paths (`duration: 2.4s, opacity: 0.7 -> 1.0`).
* **Camera Transition:** `duration: 700ms`, hardware-accelerated transform matrix.
* **Plane Hover Parallax:** Subtle elevation (`translateZ: +16px`) without jarring scale distortion.

---

## 2. Scroll Storytelling Choreography

As the user explores the architecture, the camera pans through 7 narrative scenes:

| Scene | Spatial Focus | Visual Event | Security Concept Explained |
| :--- | :--- | :--- | :--- |
| **Scene 1: Task Ingress** | Plane 1 (Top) | Inbound packet lands on Ingress node | Ingestion of untrusted external text |
| **Scene 2: Plan Synthesis** | Plane 1 $\to$ 2 | Packet traverses REA planning compiler | Action normalization before OS interaction |
| **Scene 3: ArmorIQ Evaluation** | Plane 2 | Gateway evaluates intent policy | Upstream authorization check (`ALLOW` / `DENY`) |
| **Scene 4: Execution Halt** | Plane 2 (if Denied) | Connector terminates; downstream unlit | Upstream denial terminates before MCP |
| **Scene 5: TripLine Containment** | Plane 3 (if Allowed) | Path Jail / Canary Gateway inspection | In-MCP OS boundary enforcement |
| **Scene 6: Cryptographic Seal** | Plane 4 | RFC 8785 canonical hash generated | Non-repudiation witness recording |
| **Scene 7: System Overview** | Full 4 Planes | Full dimensional isometric framing | Unified multi-layer defense view |

---

## 3. Strict Boundary Discipline: Replay vs Live Streaming

1. **Recorded Demonstrations:**
   * Explicitly flagged with a persistent `"Recorded Demonstration Replay"` badge.
   * Event timelines directly mirror historical disk artifacts (`results/phase3/scenario/`).
   * No synthetic network latency or fake random IDs injected.
2. **Live Agent Runs:**
   * Initiated via explicit user action (`Run Governed Demo` / `Start Agent Run`).
   * State transitions driven exclusively by server-sent events (`/api/jobs/{id}/events`).
   * If an event is dropped, the UI reflects `RECONNECTING` or `UNRESOLVED` rather than assuming success.

---

## 4. Accessibility & Reduced Motion Mode

TripLine fully honors `prefers-reduced-motion: reduce`:
* **Zero 3D Tilt:** Switches automatically to planar 2D orthogonal layout.
* **Instant State Transitions:** Replaces camera pan animations with immediate cross-fades.
* **Full Semantic Labeling:** All interactive nodes remain navigable via keyboard (`Tab`, `Enter`, `Space`) with visible focus outlines (`outline: 2px solid #65BCE7`).
