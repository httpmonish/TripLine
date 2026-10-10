# Tripline Limitations & Security Assumptions

This document honestly outlines the boundaries, assumptions, cryptographic models, and known residual limitations of the Tripline architecture as audited during development and Phase 12 Red-Team Hardening.

---

## 1. TOCTOU Residual Edge-Cases
**Implementation:** Tripline's Path Jail enforces an **open-then-verify** pattern (`secure_open_read` and `secure_open_write` in `mcp/common/jail.py`).
- Files are opened using `O_NOFOLLOW` (where supported by the platform/kernel).
- Once opened, the kernel-resolved true path of the file descriptor is queried via `fcntl(fd, F_GETPATH)` on macOS or `/proc/self/fd/<fd>` on Linux.
- The path is verified against the canonical trusted repository root, and non-canonical/escaped descriptors are immediately closed and rejected.
- Path comparison enforces Unicode NFKC normalization and case-folding on case-insensitive filesystems (such as APFS).

**Residual Limitation:** On POSIX kernels lacking `openat2(RESOLVE_BENEATH)` flags, a high-frequency directory swap on an intermediate ancestor directory component between path canonicalization and `os.open` remains theoretically possible in an extreme concurrent attacker scenario. Tripline mitigates this by validating parent descriptors with `O_NOFOLLOW` prior to opening target files.

---

## 2. Cryptographic Receipts & Verification
**Implementation:** Every Tripline Incident Receipt is cryptographically hashed and signed:
- **Canonical JSON SHA-256 (`canonical_hash`):** Deterministic serialization (sorted keys, compact separators) covers all immutable evidence fields (source attribution, tool proposal, ArmorIQ decision, Tripline decision, canary detection, witness count, and confidence level).
- **Witness Chain Binding (`witness_head_hmac`):** The receipt captures the head HMAC of the append-only witness hash chain at the moment of receipt issuance.
- **HMAC Signature (`receipt_signature`):** Generated using the witness secret key over `f"{canonical_hash}:{witness_head_hmac}"`.
- **Verification:** Independent verification is performed via `python -m receipts.verify <receipt.json>`. Any post-issuance tampering with decision fields, execution counts, or timestamps fails canonical hash verification with `TAMPER_DETECTED`.

**Residual Limitation:** Receipts are authenticated with a symmetric HMAC key rather than an asymmetric public-key signature (e.g. Ed25519). Anyone with access to the witness key can forge receipts; external auditors must verify signatures against the trusted signing key.

---

## 3. Client-Side `check()` vs MCP Boundary & Decision Proofs
**Implementation:**
- The agent loop calls `session.check(tool_name, tool_args)` via the ArmorIQ SDK before dispatching MCP tools.
- To prevent direct HTTP bypass of the MCP server, the MCP server binds strictly to `127.0.0.1` and enforces `DecisionProofMiddleware`.
- Every legitimate MCP `tools/call` request must carry an `X-Tripline-Decision-Proof` header containing an HMAC over `f"{args_hash}:{decision}:{timestamp}"` signed with the witness key (60-second TTL). Direct HTTP requests lacking a valid, unexpired proof are rejected with HTTP 403.
- **Replay Policy Within TTL**: Replay of a decision proof within its 60-second TTL window is **allowed by design** to support agent retry loops without requiring redundant ArmorIQ round-trips. The middleware enforces timestamp validity and HMAC integrity, but does not maintain an ephemeral nonce cache.
- **Authorization vs Enforcement Boundaries**:
  - ArmorIQ checks maintainer role and tool authorization. It does **not** inspect filesystem path arguments or unstructured string payloads (e.g. comment text). Therefore, **ArmorIQ ALLOWS both demo attacks (DP-01 and IE-01) at the tool level**.
  - **DP-01** is blocked by Tripline's kernel Path Jail (`PATH_OUTSIDE_ROOT`).
  - **IE-01** is held by Tripline's Egress Gateway upon canary detection. This is an **independent Tripline egress hold, NOT an ArmorIQ delegation**.

**Residual Limitation:**
- **Boundary Limit:** The Decision-Proof header protects against **external / non-agent callers** on localhost attempting to access the MCP server without going through the gateway.
- It does **NOT** protect against a completely compromised agent process (e.g., remote code execution within the agent's Python environment) that has already extracted the witness signing key.

---

## 4. Same-User Witness Key Locality
**Implementation:** The witness signing key (`.tripline/witness_key.txt`) is generated automatically with restricted POSIX permissions (`0o600`).
**Residual Limitation:** The key lives on the local host filesystem. Any process running under the same local OS user UID can read the key file. In a production enterprise deployment, the witness recorder and key storage must reside in an isolated sidecar process, hardware security module (TPM/KMS), or cloud enclave.

---

## 5. Benchmark Scope: M2 vs M1 Evaluation
**Implementation:**
- The primary evaluation (recorded in `benchmark/results/benchmark_runs.csv` and `benchmark_runs.jsonl`, totaling 86 runs across 27 scenarios) was conducted using **M2 (Forced-Compliance Deterministic Stubs)** with N=1 or 2 per scenario.
- M2 deterministically proposes the malicious action, allowing us to evaluate the exact security boundaries (ArmorIQ policy vs. Tripline Gateway vs. Jail vs. Witness) without non-deterministic LLM refusal, alignment training variance, or prompt flakiness.

**Residual Limitation:**
- **No M1 (real-LLM) runs exist** in the benchmark or demo datasets. All 86 benchmark records and all demo runs are Mode M2 forced-compliance stubs.
- In the demo, both the "useful agent" beat and the attack scenarios are scripted to guarantee 100% reproducible forensic receipts.

---

## 6. Provenance Attribution vs Causal Proof
**Implementation:** Tripline provides robust provenance (C1 level attribution via exact string matching and normalized content hashing against context items recorded in the provenance ledger).
**Residual Limitation:** C0 and C1 attribution establish that untrusted content was present in context or matched the proposal verbatim. They do **not** mathematically prove *causation* (C2 level ablation-confirmed causal attribution was not implemented in this phase).

---

## 7. Canary Egress Scanner Encoding Residual (Phase 3 Finding)
**Implementation:** Tripline's Egress Scanner performs substring pattern matching against active Tier-2 canary tokens in outbound tool call payloads (`scan_egress_payload` in `canary/scan.py`).
**Residual Limitation:** Tripline's canary scan does not catch base64-encoded, reversed, or split-token representations of secrets. ArmorIQ authorizes `comment_issue` at the tool policy boundary without inspecting unstructured body text, and Tripline's scanner relies on literal token matching. Consequently, an agent that base64-encodes, reverses, or splits a planted canary across multiple comments evades detection under both layers. This boundary gap is documented honestly as an architecture limitation.
