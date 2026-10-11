# Owner Watchlist — Demo Video Inspection Guide

**Target Artifact**: `video/out/tripline_demo_90s.mp4` (86.00s, H.264/AAC, 1.63 MB)  
**Hackathon Limit**: Strict hard maximum of **90.0 seconds** (Rule 11).

---

## 1. Visual Inspection (Watch WITHOUT Sound)

Inspect every beat on a 1080p display:

- [ ] **Beat B1 (0:00–0:06) — Title Card**:
  - Motto displays clearly: *"Blocked isn't evidence. Every denied action gets a receipt."*
  - Hackathon badge: *"Built for ArmorIQ Flow State 2026"*.
- [ ] **Beat B2 (0:06–0:18) — Agent Start & Benign Issues**:
  - Terminal text is crisp and legible.
  - Check terminal prompt: Verify zero personal local user home paths (e.g. `/Users/<name>`) or hostnames are shown.
- [ ] **Beat B3 (0:18–0:32) — Attack 1: ArmorIQ Blocks Delete Branch**:
  - Bottom caption accurately reads: *"ArmorIQ blocks delete_branch (not on ArmorIQ's allowlist for this agent)"*.
  - Terminal displays: `decision: DENY`, `action: block`, `reason: tool_not_in_allowlist`, matched policy `cli-tripline-maintainer-tripline-mcp`.
  - HTTP round-trip confirmation: Outbound POST to `https://api.armoriq.ai/iap/sdk/enforce` verified.
- [ ] **Beat B4 (0:32–0:48) — Attacks 2 & 3: Path Jail & Egress Gateway**:
  - Bottom caption accurately reads: *"ArmorIQ allowed both. Tripline stopped them."*
  - Attack 2: Path Jail blocks `PATH_OUTSIDE_ROOT` with 0 bytes read.
  - Attack 3: Egress Gateway holds `egress_canary_hit`.
- [ ] **Beat B5 (0:48–1:04) — Cryptographic Receipts & Tamper Proof**:
  - Canonical JSON SHA-256 and HMAC signatures verify.
  - 1-character modification in receipt immediately triggers `TAMPER_DETECTED: canonical_hash mismatch`.
- [ ] **Beat B6 (1:04–1:16) — Multi-Layer Attribution**:
  - Three distinct layers displayed with clear boundaries.
- [ ] **Beat B7 (1:16–1:26) — Disclosure Card**:
  - Dwell time is at least 5.0 seconds (card is visible for 10.0 seconds).
  - Disclosure points:
    - Real LLM model identifier accurately disclosed.
    - Real Platform Enforcement (`api.armoriq.ai`).
    - Sandbox environment fixture disclosure.
    - Canary transformation residual disclosure.
    - Repository URL.

---

## 2. Audio Inspection (Watch WITH Sound)

- [ ] **Audio Track Integrity**:
  - Subtitles / captions are perfectly synchronized with on-screen visual transitions.
  - Audio codec: AAC stereo, 44.1 kHz.
  - If silent audio track is used: verify no abrupt clipping or popping at video boundaries.
  - If voiceover audio is added: verify speech matches subtitle text word-for-word.

---

## 3. Strict Pre-Submission Red Lines

- [ ] Duration is ≤ 90.0 seconds (Measured: **86.00s**).
- [ ] File size is < 25 MB (Measured: **1.63 MB**).
- [ ] Zero unredacted real API keys or tokens appear in any frame.
- [ ] Zero claims of 100% bypass prevention or Rule 10 forbidden marketing terms.
