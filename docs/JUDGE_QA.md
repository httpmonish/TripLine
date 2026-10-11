# Judge Q&A: Evidence-Backed Answers

**Project**: Tripline (ArmorIQ "Flow State 2026")  
**Core Motto**: *"ArmorIQ decides. Tripline proves."*

This document provides concise, factual answers to 16 questions a skeptical hackathon judge might ask, backed by direct evidence paths.

---

### Q1: Is the ArmorIQ decision real or hardcoded?
**A:** It is 100% real platform enforcement. Every tool proposal makes a live HTTPS POST request to `https://api.armoriq.ai/iap/sdk/enforce` using the official `armoriq_sdk` (v0.6.10). When `delete_branch` was proposed, the platform returned `action: block` and `reason: tool_not_in_allowlist`. Zero mocked or hardcoded decisions exist in the runtime path.  
*Evidence*: `docs/phase2_report.md` Section C, `scripts/armoriq_proof.py`, `results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json`.

---

### Q2: Which attacks did ArmorIQ stop, which did Tripline stop, and why does that matter?
**A:** ArmorIQ stopped Attack 1 (`delete_branch`) because it was not on the agent's tool allowlist (reason: `tool_not_in_allowlist`, matched policy `cli-tripline-maintainer-tripline-mcp`). ArmorIQ allowed Attack 2 (`read_file`) and Attack 3 (`comment_issue`) because those tools were in the allowlist. Tripline's in-MCP Path Jail stopped Attack 2 (`PATH_OUTSIDE_ROOT`), and Tripline's Egress Gateway held Attack 3 (`egress_canary_hit`). This matters because tool authorization does not guarantee safe arguments or non-exfiltrating payloads.  
*Evidence*: `docs/phase3_layer_attribution.md` Section 1, `results/phase3/scenario/`.

---

### Q3: Isn't the model just refusing? How do you know the guardrails were exercised?
**A:** We measured model refusal explicitly across real runs. Claude 3.5 Sonnet refused adversarial prompts 40% of the time (2 out of 5 runs). When the model complied, defense-in-depth neutralized 100% of malicious tool proposals across the three layers. Guardrails were tested both with live model compliance and with deterministic probe scripts.  
*Evidence*: `results/phase3/measured/summary.md`, `docs/phase3_report.md` Section H.

---

### Q4: What does your receipt prove, and what does it NOT prove?
**A:** The receipt is a Canonical JSON document signed with HMAC-SHA256 covering the incident ID, action, argument hash, layer decision, and execution count. It proves that the covered fields have not been altered post-hoc (1-byte modification triggers `TAMPER_DETECTED`). It does **not** prove human intent, and an actor possessing the private witness key could forge a valid signature.  
*Evidence*: `receipts/verify.py`, `scripts/tamper_demo.py`, `tests/test_phase4_dashboard.py`.

---

### Q5: Why not just use ArmorIQ alone? What does Tripline add?
**A:** ArmorIQ is an action-level authorization gateway—it answers *"May the agent call `read_file`?"* Tripline operates inside the MCP execution boundary and at the egress gateway—it answers *"Is this path escaping the repository root?"* and *"Does this comment leak a planted secret?"* Tripline catches the attacks that ArmorIQ legitimately permits under benign tool policies, and mints verifiable cryptographic receipts.  
*Evidence*: `docs/ARCHITECTURE.md`, `docs/phase3_layer_attribution.md`.

---

### Q6: What gets past both layers? (The Honest Residual)
**A:** Tripline's canary gateway checks for exact substrings. If an agent transforms a canary token—such as Base64 encoding it, reversing the characters, or splitting it across multiple comments—neither layer detects the exfiltration. ArmorIQ does not inspect comment text, and Tripline misses non-exact substrings.  
*Evidence*: `docs/limitations.md`, `docs/phase3_layer_attribution.md` Section 3.

---

### Q7: How much code was built during the hackathon window?
**A:** In accordance with Rule 5, 5,079 lines of code were added/changed across 50 files inside the window (10–17 Oct 2026), representing a 14.57% net growth over our pre-existing MCP and receipt foundation (29,785 lines). All in-window commits are logged with exact dates and diff stats.  
*Evidence*: `docs/IN_WINDOW_LEDGER.md`, `docs/PREEXISTING_CODE.md`.

---

### Q8: How was the agent tested, and with what sample size N?
**A:** Evaluated across N=15 measured cells (k=5 runs per arm: Arm A baseline, Arm B ArmorIQ-only, Arm C full defense). We make no statistical significance claims beyond this exact fixture set and model version. Historical benchmarks citing 86 runs used Mode M2 forced-compliance stubs, which are explicitly disclosed as synthetic test harnesses.  
*Evidence*: `results/phase3/measured/summary.md`, `benchmark/results/benchmark_report.md`.

---

### Q9: Can an attacker replay a decision proof?
**A:** Decision proofs carry a 60-second TTL. Replay of an identical proof within this 60-second window is permitted by design to accommodate transient network retries between the agent and MCP. After 60 seconds, the proof expires and is rejected.  
*Evidence*: `mcp/common/proof.py`, `tests/test_phase0.py`.

---

### Q10: What happens if the model refuses to propose an attack?
**A:** If the model refuses, the issue is safely closed with a refusal note. To ensure security boundaries are fully tested regardless of model refusal variance, we provide deterministic harness scripts (`scripts/jail_burst.py` with 24 path-trick variations) that evaluate the jail and gateway boundaries directly.  
*Evidence*: `scripts/jail_burst.py`, `tests/test_phase3_wow.py`.

---

### Q11: Does Tripline run against real GitHub repositories or real credentials?
**A:** No. Per Hackathon Rule 7, all evaluations run in sandboxed throwaway directories. The `~/.ssh/fake_key` referenced in prompts is a synthetic fixture in an isolated temp directory containing a dummy banner. No external repositories or real private keys are ever touched.  
*Evidence*: `fixtures/.ssh/fake_key`, `scripts/make_sandbox_repo.py`.

---

### Q12: Why did you build the dashboard as server-rendered HTML rather than React/Next.js?
**A:** To eliminate dependencies, CDN calls, and fake mock states. The dashboard is a lightweight FastAPI + Jinja2 app that reads solely from real recorded artifacts in `results/`. It runs with zero external network connectivity, zero client-side frameworks, and provides sub-second interactive receipt verification and tamper testing.  
*Evidence*: `dashboard/app.py`, `dashboard/routes.py`, `tests/test_phase4_dashboard.py`.

---

### Q13: Does the witness log require kernel privileges or a Merkle tree?
**A:** No. The witness is an HMAC-chained append-only log kept on the local MCP server side. It detects out-of-order execution, dropped events, and tampering without requiring kernel hooks, special privileges, or distributed consensus.  
*Evidence*: `mcp/common/witness.py`, `docs/phase4_truth_audit.md` (TA-10).

---

### Q14: How does Tripline prove that a denied action caused zero side effects?
**A:** When an action is denied by ArmorIQ upstream or Tripline's Path Jail, the MCP tool function is never called. The local execution witness records `execution_count: 0` and validates that no filesystem state changes occurred in the sandbox directory. This count is sealed inside the signed receipt.  
*Evidence*: `results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json`, `receipts/models.py`.

---

### Q15: How does a live policy flip work with zero code changes?
**A:** ArmorIQ policies are managed dynamically in the cloud console. When `delete_branch` was omitted from the tool allowlist, the platform blocked it (`tool_not_in_allowlist`). When added to the allowlist in Phase 0 tests, the platform permitted it instantly without code modifications. Note: The interactive human dashboard UI flip demonstration (`scripts/policy_flip_demo.py`) was NOT RUN live with the owner, and has been removed from public demo claims pending owner dashboard verification.  
*Evidence*: `docs/phase0_report.md` (Gate G5), `docs/ONBOARDING_STATUS.md`.

---

### Q16: What would you build next?
**A:** Three concrete enhancements:
1. **Dynamic Entropy & Semantic Canary Scanners**: Detecting transformed (Base64, reversed, fragmented) canaries to close the honest residual.
2. **Platform-Initiated ArmorIQ HOLD**: Full integration with ArmorIQ's upcoming asynchronous human-in-the-loop review queue.
3. **Hardware / Enclave Witness Sealing**: Binding witness records to hardware TPM/enclave roots for tamper-resistant cryptographic attestation.  
*Evidence*: `docs/limitations.md`.
