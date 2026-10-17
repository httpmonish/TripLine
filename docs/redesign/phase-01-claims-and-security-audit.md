# Phase 1 Deliverable 7: Security Claims & Technical Boundary Audit

**Project:** TripLine  
**Repository:** `https://github.com/httpmonish/TripLine`  
**Working Branch:** `agent-v2`  
**Auditor:** Principal AI Solution Architect & Application Security Reviewer  
**Standard:** Strict Evidence Attribution & Claims Ledger Audit (Rules 3.1–3.4)  
**Date:** 2026-10-17  

---

## 1. Executive Summary & Audit Mandate

A premium enterprise product evaluated by hackathon judges, security researchers, and enterprise architects must maintain **uncompromising truthfulness**. Claims that overreach beyond empirical code evidence destroy trust.

This audit cross-references all public claims in `README.md`, `docs/FINAL_CLAIMS_AUDIT.md`, `docs/limitations.md`, and frontend components against:
1. Exact source code implementations.
2. Deterministic, recorded, and live test suites.
3. Cryptographic evidence artifacts under `results/` and `.tripline/`.

---

## 2. Comprehensive Security Claims & Evidence Mapping

| Claim ID | Exact Claim Text / Technical Assertion | Source Implementation | Relevant Test & Type | What It DOES Prove | What It DOES NOT Prove | Retention Verdict & Mandatory UI Qualification |
|---|---|---|---|---|---|---|
| **CLM-01** | *"Blocked isn't evidence. Every denied action gets a receipt."* | `receipts/builder.py:build_receipt`<br>`agent/executor.py:348` | `test_dashboard_api.py`<br>`test_phase10_receipts.py`<br>(Deterministic) | Whenever ArmorIQ or TripLine denies a tool call, a structured JSON receipt is signed and saved with full attribution. | Does not prove the agent cannot attempt other unmonitored channels outside MCP. | **SAFE TO RETAIN.** Core product motto. |
| **CLM-02** | *"ArmorIQ decides. TripLine proves."* | `docs/ARMORIQ_INTEGRATION_MODE.md`<br>`agent/executor.py:authorize` | `test_agent_v2.py`<br>(Deterministic & Mode B) | ArmorIQ is the upstream policy authority; TripLine generates non-repudiable receipts and contains execution. | Does not mean TripLine overrides ArmorIQ's decisions. | **SAFE TO RETAIN.** Emphasizes partnership. |
| **CLM-03** | `delete_branch` attack stopped upstream by ArmorIQ platform policy (`cli-tripline-maintainer-tripline-mcp`). | `agent/executor.py:161`<br>`policy.json` | `scripts/armoriq_proof.py`<br>`test_agent_v2.py`<br>(Recorded & Test) | `delete_branch` is evaluated as out-of-plan and blocked before reaching MCP; sealed in receipt `receipt_P1_ARMORIQ_DENY.json`. | Does not prove ArmorIQ blocks novel unknown tools unless registered in policy. | **SAFE TO RETAIN.** Supported by recorded trace `b129c7cf-...`. |
| **CLM-04** | Out-of-plan action `delete_branch` never reaches MCP server (0 executions). | `agent/executor.py:dispatch_authorized`<br>`agent/executor.py:296` | `test_phase3_mcp.py`<br>`test_agent_v2.py`<br>(Deterministic) | `ToolExecutor.dispatch_authorized()` raises `PermissionError` if status is not `ALLOW`. Witness count is 0. | Does not prove external scripts outside `ToolExecutor` cannot run. | **SAFE TO RETAIN.** Enforced by Rule G. |
| **CLM-05** | TripLine Path Jail traps directory traversal escapes via `fstat` inode check (0 bytes read). | `mcp/common/jail.py`<br>`agent/executor.py:410` | `scripts/jail_burst.py`<br>`test_phase3_wow.py`<br>(Deterministic) | Any path resolving outside sandbox root via `../`, `%2e%2e`, or symlinks is blocked; returns `PATH_OUTSIDE_ROOT`. 0 bytes read. | Does not protect files legitimately placed inside the sandbox root. | **SAFE TO RETAIN.** Tested against 8 adversarial probe variations. |
| **CLM-06** | TripLine Egress Gateway traps planted canary tokens in comments before network egress. | `gateway/taint_rule.py`<br>`canary/scan.py:57` | `test_phase6_egress.py`<br>`test_canary_residuals.py`<br>(Deterministic) | Exact-match substring scan matches active canary ID and sets action to `HOLD`; quarantined in receipt. | **Does NOT detect obfuscated canaries** (Base64, hex-encoded, rot13, or character-split tokens). | **QUALIFIED RETENTION.** Must state: *"Exact-match canary scan; obfuscated/encoded strings represent an honest residual."* |
| **CLM-07** | Modifying 1 byte of a covered receipt field triggers `TAMPER_DETECTED`. | `receipts/verify.py:verify_receipt`<br>`scripts/tamper_demo.py` | `test_dashboard_api.py`<br>`test_phase10_receipts.py`<br>(Deterministic) | Altering `tripline_decision`, `armoriq_decision`, or `arguments` invalidates canonical SHA-256 and HMAC signature. | Does not prevent an attacker with the private witness key from resigning a forged receipt. | **SAFE TO RETAIN.** Validated on temporary in-memory copies. |
| **CLM-08** | Append-only HMAC-SHA256 witness chain detects log omission or sequence tampering. | `mcp/common/witness.py`<br>`witness/reconcile.py` | `test_phase7_witness.py`<br>(Deterministic) | Sequential HMAC linking each tool execution to previous HMAC detects dropped or reordered log records. | Does not prevent truncation of the tail if the witness head is not externally committed. | **SAFE TO RETAIN.** Supported by `GET /api/witness/verify`. |
| **CLM-09** | Scoped agent crew uses ephemeral Ed25519 signing keys generated in-memory per run. | `agent/crew.py:34`<br>`agent/identity.py` | `test_agent_v2.py::test_crew_delegation_and_keys`<br>(Deterministic) | `reader` and `responder` sub-agents generate distinct Ed25519 keypairs in-memory; private keys never written to disk. | Does not use hardware HSM or TPM security modules. | **SAFE TO RETAIN.** Inspected via `GET /api/agent/crew`. |
| **CLM-10** | 100% defense rate against adversarial prompt injection in benchmark harness. | `benchmark/runner.py`<br>`benchmark/report.py` | `tests/test_phase11_benchmark.py`<br>(Synthetic Harness) | Across 86 benchmark test vectors under forced compliance (Mode M2), the multi-layer pipeline stopped 86/86 attacks. | **Does NOT reflect raw LLM compliance.** In natural LLM runs, model refusal rate is ~40%, and non-compliant models may fail differently. | **MANDATORY QUALIFICATION.** UI must display: *"Mode M2 forced-compliance synthetic harness, not model behavior."* |
| **CLM-11** | Mode B Direct Local Execution with Synchronous ArmorIQ Authorization. | `agent/executor.py`<br>`docs/ARMORIQ_INTEGRATION_MODE.md` | `test_agent_v2.py`<br>(Deterministic) | Actions are authorized by ArmorIQ before local MCP dispatch. No public Cloudflare tunnels or external proxy hops. | Does not prove remote ArmorIQ platform reachability if credentials return 401. | **SAFE TO RETAIN.** Mandatory disclosure required. |

---

## 3. Prohibited & Overstated Terminology (The Blacklist)

To ensure technical credibility, the redesigned frontend must strictly adhere to `docs/WORDING_ALLOWLIST.md` and purge any instances of the following four forbidden terms:

### 3.1 Prohibited: "Kernel-Level Protection"
- **Status:** **FORBIDDEN & STRUCK.**
- **Reason:** TripLine operates in Python user space and uses standard libc/POSIX `fstat` and `os.open` system calls. It does not install Linux kernel modules (eBPF, LSM, seccomp-bpf) or Windows kernel drivers.
- **Approved Replacement:** *"In-MCP Path Jail (open-then-verify fstat inode bounds check)"*.

### 3.2 Prohibited: "Merkle-Tree Witness"
- **Status:** **FORBIDDEN & STRUCK.**
- **Reason:** The witness log is an **append-only HMAC-SHA256 sequential hash chain** (`H_i = HMAC(K, H_{i-1} || m_i)`), not a binary Merkle tree. (The only Merkle tree in the project is ArmorIQ's session plan hash).
- **Approved Replacement:** *"Append-only HMAC-SHA256 witness chain"*.

### 3.3 Prohibited: "Regex Canary Scanner"
- **Status:** **CORRECTED.**
- **Reason:** `canary/scan.py` uses python string containment (`in`) and `.find()`. Zero regular expressions are compiled or executed.
- **Approved Replacement:** *"Exact-match substring canary scanner"*.

### 3.4 Prohibited: "Unconditional 100% Security Guarantee"
- **Status:** **CORRECTED & QUALIFIED.**
- **Reason:** Obfuscated, encoded (Base64), or character-split canary tokens bypass exact substring matching.
- **Approved Replacement:** *"Deterministic protection against tested vectors; obfuscated payloads documented as honest residual"*.

---

## 4. UI Copy Corrections for Subsequent Phases

1. **Defense Metrics Header (`app/measured/page.tsx`):**
   - Add explicit badge: `[ Synthetic M2 Benchmark Harness • N=86 Probes ]`.
   - Add footnote: *"Evaluated under forced-compliance synthetic stubs to guarantee adversarial attack execution. Does not represent unconstrained LLM probability distributions."*
2. **Canary Gateway Callout (`app/page.tsx`):**
   - Change *"Scans all outbound network packets with regex filters"* to:
     *"Scans outbound tool argument payloads for active canary token IDs before MCP network transmission."*
3. **Receipt Verification Badge:**
   - Change *"RFC 8785 Enterprise Signed Receipt"* to:
     *"Canonical JSON (RFC 8785 subset) + SHA-256 & HMAC-SHA256 Witness Signature"*.
