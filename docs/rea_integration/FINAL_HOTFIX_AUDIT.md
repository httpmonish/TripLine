# Final Hotfix Audit: TripLine Security, ArmorIQ Governance & Integrity

**Date:** 2026-10-17  
**Branch:** `agent-v2`  
**Base Commit:** `2bdd730`  
**Repository:** `https://github.com/httpmonish/TripLine`  
**Environment Baseline:**
- OS: macOS Darwin 24.3.0
- Python: 3.13.16 in `.venv313`
- ArmorIQ SDK: `armoriq-sdk==0.6.10`
- Node.js: v22.14.0
- REA Package: `rea-agents@6.5.0`
- Rewriting Utility: `git-filter-repo==2.47.0`

---

## 1. Discovered Vulnerabilities & Architectural Defects

### Defect 1: Compromised Tracked Witness Key & Insecure Fixed Fallback
- **Finding:** `.tripline/witness_key.txt` was tracked into the public Git history in commit `2333590`, and `.gitignore` line 40 explicitly unignored it (`!.tripline/witness_key.txt`).
- **Risk:** Any party with repository read access possesses the signing secret. Consequently, signatures under this key can no longer establish authentic integrity.
- **Defect in `agent/security_receipts.py`:** Previously contained a hardcoded fallback secret (`tripline_receipt_secret_key_fixed`) and silently accepted `.tripline/witness_key.txt`.
- **Remediation Plan:**
  1. Treat the exposed key as permanently compromised. Invalidate authenticity claims of historic receipts.
  2. Refactor `agent/security_receipts.py`: Remove fixed fallback; require a dedicated `TRIPLINE_RECEIPT_SECRET_KEY` (minimum 32 bytes) via explicit configuration; fail closed if missing in live mode.
  3. Generate a cryptographically random 32-byte secret locally in `.env` without user intervention; keep `.env` strictly gitignored with `0o600` file permissions.
  4. In `.gitignore`, remove `!.tripline/witness_key.txt` so it is permanently ignored.
  5. Use `git-filter-repo` to purge `.tripline/witness_key.txt` from the commit history of affected branches, and force-push with lease.

### Defect 2: Authorization-to-Dispatch Mismatch (Confused Deputy)
- **Finding:** In `scripts/rea_investigator.py`, the CLI allowed passing `--tool <name>`, checked ArmorIQ authorization for that name, but then unconditionally dispatched `service.analyze_target()`.
- **Risk:** An attacker or confused model could request authorization for a low-risk action (e.g. `hello_tool`) and TripLine would proceed to dispatch `analyze_electron_app`.
- **Remediation Plan:**
  1. Establish strict 1-to-1 operation binding:
     - `analyze_electron_app` -> calls `service.analyze_target`
     - `trace_application_feature` -> calls `service.trace_feature`
     - `inspect_analysis_view` -> calls `service.inspect_evidence`
  2. Reject unknown or mismatched operations prior to any MCP dispatch.
  3. If an out-of-policy tool probe is requested, evaluate ArmorIQ policy, record the DENY decision, emit a signed receipt with `dispatch_attempted=False`, and halt immediately without contacting REA.

### Defect 3: Missing Independent Authorization for Follow-Up Trace Operations
- **Finding:** In `scripts/rea_investigator.py`, Step [4/5] invoked `service.trace_feature("main.js")` without requesting a separate ArmorIQ authorization check for `trace_application_feature`.
- **Remediation Plan:**
  1. Treat `trace_application_feature` as an independently protected action.
  2. Request an independent ArmorIQ authorization decision before dispatching the trace.
  3. Fail closed if the trace operation is denied.

### Defect 4: Premature ArmorIQ Execution Reporting
- **Finding:** In `check_armoriq_enforcement()`, `session.report(status="success" if allowed else "denied")` was called immediately after `session.check()`, before the protected tool actually executed.
- **Risk:** ArmorIQ audit trails falsely recorded successful tool execution when the tool had not yet run, or when downstream dispatch subsequently failed.
- **Remediation Plan:**
  1. Separate authorization checking (`session.check`) from outcome reporting (`session.report`).
  2. Report execution outcome (`status="success"` or `status="failed"`) ONLY after actual tool dispatch and execution completes.

### Defect 5: Policy Allowlist Discrepancy in `policy.json`
- **Finding:** `armoriq.yaml` had `trace_application_feature` and `inspect_analysis_view` added, but `policy.json` (the committed policy profile template) omitted them.
- **Remediation Plan:**
  1. Synchronize `policy.json` to include `tripline-mcp.trace_application_feature` and `tripline-mcp.inspect_analysis_view`.
  2. Re-register via `armoriq register` to verify control-plane policy alignment.

---

## 2. Verifiable Acceptance Criteria

- [ ] `.tripline/witness_key.txt` is removed from `.gitignore` exceptions, completely purged from git tracking, and purged from reachable branch history.
- [ ] In `agent/security_receipts.py`, all fixed fallback keys are deleted; live signing strictly fails closed unless `TRIPLINE_RECEIPT_SECRET_KEY` (>=32 bytes) is configured.
- [ ] `.env` is updated with a fresh, cryptographically random secret locally without user interaction, and remains gitignored with restricted permissions (`0o600`).
- [ ] Every protected operation in `scripts/rea_investigator.py` is bound 1-to-1 to its authorization decision.
- [ ] `trace_application_feature` requires an independent ArmorIQ authorization check before dispatch.
- [ ] ArmorIQ execution reporting occurs post-dispatch, accurately reflecting real tool outcomes.
- [ ] `policy.json` and `armoriq.yaml` are synchronized and registered with the ArmorIQ control plane.
- [ ] All unit, integration, and regression suites pass cleanly with recorded outputs.
- [ ] Live governed end-to-end investigation succeeds with real REA analysis, independent trace check, and HMAC-signed receipts.
