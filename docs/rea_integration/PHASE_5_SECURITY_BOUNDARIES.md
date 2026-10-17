# Phase 5 — Target Isolation & Untrusted Content Handling

**Date:** 2026-10-17  
**Modules:** `agent/rea_adapter.py`, `agent/executor.py`, `agent/reasoning_loop.py`  

---

## 1. Target Registry & Path Confinement

To protect against arbitrary filesystem reconnaissance, REA operations cannot accept unvalidated filesystem paths from the model:
1. **Target Allowlist:** The agent must provide a preapproved `target_id` (e.g. `"synthetic-electron-app"`).
2. **Canonical Resolution:** `resolve_approved_target` canonicalizes candidate paths and verifies they reside strictly within `CONTROLLED_ANALYSIS_ROOT` (`fixtures/rea_targets`).
3. **Traversal Prevention:** Any identifier containing `..`, `/`, `\`, or absolute paths is rejected with `REATargetValidationError`.
4. **Symlink Escape Detection:** Target resolution invokes `.resolve()` and confirms `resolved_path.relative_to(CONTROLLED_ANALYSIS_ROOT)`.

---

## 2. Untrusted Content Defense Model

Content retrieved from analyzed JavaScript applications (strings, comments, README files, function identifiers) is considered **Tier 3 (T3) Untrusted Input**:
1. **Passive Data Only:** Analyzed text is never executed as agent directives or system prompts.
2. **Tag Confinement:** All external text is wrapped in `<UNTRUSTED_CONTENT>` tags with explicit security warnings.
3. **Sanitization:** Zero-width characters (`\u200b`–`\u200f`), byte order marks, and directional formatting characters used for payload obfuscation are stripped. Delimiter closing tags (`</UNTRUSTED_CONTENT>`) are escaped.
4. **Provenance Tracking:** Ingested items are recorded in TripLine's cryptographic provenance ledger with SHA-256 content hashes.

---

## 3. Read-Only Investigation Boundary

- REA operations are strictly read-only static analysis and graph tracing.
- Destructive operations (`delete_branch`, arbitrary file writes, shell execution) remain strictly forbidden or gated behind independent maintainer governance.

---

## 4. Acceptance Criteria Verification

- [x] **Registered Target Succeeds:** `synthetic-electron-app` resolves and executes.
- [x] **Unregistered Target Denied:** `evil-app` fails with validation error.
- [x] **Path Traversal Denied:** `../../` fails closed.
- [x] **Prompt Injection Resisted:** Target files containing prompt-injection payloads are ingested as data, not obeyed as instructions.
