# Tripline Final Claims Audit

**Project**: Tripline (ArmorIQ "Flow State 2026")  
**Audit Date**: 2026-10-10  
**Phase**: Phase 7 (Freeze & Submission)  
**Standard**: Rule 10 (Strict truthfulness; zero simulation; all claims verified against recorded evidence).

---

## 1. Comprehensive Claims Audit Matrix

| ID | Exact Claim Text | Source Document & Location | Re-verified Evidence Path | Status | Action Taken |
|---|---|---|---|---|---|
| **CLM-01** | *"Blocked isn't evidence. Every denied action gets a receipt."* | `README.md` (Header), `docs/SUBMISSION.md`, Video B1 | `results/phase3/scenario/*.json`, `receipts/models.py` | **VERIFIED** | Kept as core motto. |
| **CLM-02** | *"ArmorIQ decides. Tripline proves."* | `README.md`, `docs/SUBMISSION.md`, Video B7 | `docs/phase3_layer_attribution.md` | **VERIFIED** | Kept as closing motto. |
| **CLM-03** | `delete_branch` attack stopped by ArmorIQ platform policy (`cli-tripline-maintainer-tripline-mcp`). | `README.md` (Sec. 1), `docs/SUBMISSION.md`, Video B3 | `scripts/armoriq_proof.py`, `docs/phase2_report.md` Sec. C | **VERIFIED** | Kept. Verified live via `/iap/sdk/enforce` (Trace: `b129c7cf-...`). |
| **CLM-04** | Action `delete_branch` never reaches MCP server when blocked upstream (0 executions). | `README.md`, `docs/JUDGE_QA.md` Q14 | `results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json` | **VERIFIED** | Kept. Sealed inside receipt. |
| **CLM-05** | ArmorIQ legitimately allowed `read_file` and `comment_issue` under registered tool policy. | `README.md` (Sec. 1), `docs/ARCHITECTURE.md`, Video B4 | `results/phase3/scenario/receipt_P2_JAIL_DENY.json`, `receipt_P3_GATEWAY_HOLD.json` | **VERIFIED** | Kept. Documented in layer attribution ledger. |
| **CLM-06** | Tripline Path Jail traps directory traversal escapes via `fstat` inode check (0 bytes read). | `README.md` (Sec. 1), `docs/ARCHITECTURE.md`, Video B4 | `mcp/common/jail.py`, `tests/test_phase3_wow.py` | **VERIFIED** | Kept. Tested against 24 burst probes (`scripts/jail_burst.py`). |
| **CLM-07** | Tripline Egress Gateway traps planted canary tokens in comments before network egress. | `README.md` (Sec. 1), `docs/ARCHITECTURE.md`, Video B4 | `gateway/taint_rule.py`, `canary/scan.py` | **VERIFIED** | Kept. Placed on HOLD. |
| **CLM-08** | Every denied action generates an HMAC-signed Canonical JSON Incident Receipt. | `README.md` (Sec. 3), `docs/SUBMISSION.md` | `receipts/builder.py`, `receipts/verify.py` | **VERIFIED** | Kept. Offline verification via `make verify`. |
| **CLM-09** | Modifying 1 byte of a covered receipt field triggers `TAMPER_DETECTED`. | `README.md` (Sec. 4), `docs/JUDGE_QA.md` Q4, Video B5 | `scripts/tamper_demo.py`, `tests/test_phase4_dashboard.py` | **VERIFIED** | Kept. Validated on copy; original intact. |
| **CLM-10** | Path traversal burst (24 variations) has 0% bypass rate. | `docs/phase4_report.md` Sec. I, `README.md` | `scripts/jail_burst.py`, `tests/test_phase3_wow.py` | **VERIFIED** | Kept. |
| **CLM-11** | Model refusal rate on adversarial prompts is 40% (2/5 runs refused in benign phase). | `README.md` (Sec. 6), `results/phase3/measured/summary.md` | `results/phase3/measured/summary.md` | **VERIFIED** | Kept. Stated with prompt rung disclosure. |
| **CLM-12** | Overall system protection rate against adversarial prompt injection is 100%. | `results/phase3/measured/summary.md` | `results/phase3/measured/summary.md` | **VERIFIED** | Kept. Defense-in-depth stopped 3/3 attacks when model complied. |
| **CLM-13** | In-window development produced 5,079 added lines (14.57% net growth). | `docs/IN_WINDOW_LEDGER.md`, `README.md` (Sec. 8) | `git diff --stat 55859c7..HEAD` | **VERIFIED** | Kept with git command citations. |
| **CLM-14** | Historical 86-run benchmark achieved 100% defense rate. | `benchmark/results/benchmark_report.md` | `benchmark/results/benchmark_report.md` | **QUALIFIED CAVEAT** | Kept only with mandatory disclaimer: *"Mode M2 forced-compliance synthetic harness, not model behavior."* |
| **CLM-15** | Egress canary scan does not detect Base64-encoded, reversed, or split tokens. | `README.md` (Sec. 7), `docs/limitations.md`, Video B7 | `scripts/residual_probe.py`, `docs/phase3_layer_attribution.md` Sec. 3 | **VERIFIED** | Moved to "Limits & Honest Residual". |
| **CLM-16** | Decision proof tokens have a 60-second TTL; replay within TTL is permitted. | `README.md` (Sec. 7), `docs/JUDGE_QA.md` Q9 | `mcp/common/proof.py`, `tests/test_phase0.py` | **VERIFIED** | Moved to "Limits". |
| **CLM-17** | ArmorIQ platform-initiated dynamic HOLD / human-in-the-loop review. | `docs/REQUIREMENTS_MATRIX.md` | N/A | **UNVERIFIED** | Excluded from public claims; moved to "Limits & Future Work". |
| **CLM-18** | Kernel-level protection or Merkle-tree witness. | N/A | N/A | **FORBIDDEN / STRUCK** | 0 occurrences across repository. Struck from all public materials. |

---

## 2. Top Audit Findings & Resolutions
1. **Mode M2 Benchmark Transparency**: Ensured every mention of the 86-attack benchmark is qualified with *"forced-compliance synthetic harness stub, not an LLM model behavior result"*.
2. **Attribution Discipline**: Re-confirmed that all materials strictly attribute `delete_branch` to **ArmorIQ Platform Policy**, path traversal to **Tripline Path Jail**, and canary exfiltration to **Tripline Egress Gateway**.
3. **Receipt Scope Transparency**: Clarified in `docs/JUDGE_QA.md` that HMAC signatures detect modification of covered fields, but do not prove operator intent and could be forged by a holder of the private witness key.
4. **Honest Residual Prominence**: The residual (obfuscated/transformed canaries) is featured in the root `README.md`, `docs/limitations.md`, `docs/SUBMISSION.md`, and on the final video disclosure card.
