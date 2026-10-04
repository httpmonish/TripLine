# Tripline

**"Blocked isn't evidence. Every denied action gets a receipt."**

Tripline is a forensic evidence layer for AI agents that turns blocked or held actions into attributable, witness-backed incident receipts.

## What It Does
When an AI agent attempts to perform an action, security tools (like ArmorIQ) authorize or block the attempt. Tripline captures the full context of this attempt:
- **What** the agent proposed.
- **Where** the instruction came from.
- **What** ArmorIQ decided.
- **What** Tripline's egress and boundary constraints decided.
- **Whether** a canary was triggered.
- **Whether** execution actually occurred.
- **How** confidently the source was attributed.

Every security incident generates an **Incident Receipt**—cryptographically backed evidence rather than just a "Blocked" log entry.

## Why It Exists
"Authorization of one action does not authorize every downstream use of its data."
Existing systems assume that if an action is unauthorized, the prompt is dropped. But what if authorized data is exfiltrated downstream? And how do we provide verifiable forensic evidence that a stopped instruction caused zero MCP tool side effects? Tripline bridges the gap between authorization policy and verifiable execution evidence. 

## 3D Multi-Layer Defense Topology

Tripline implements an orthogonal, four-plane security architecture designed to prevent unauthorized downstream data use even when tool usage has been authorized.

```
       ▲  [PLANE 1: INGRESS & PROVENANCE]
      / \   • Untrusted Inputs (Issues, PRs, Webhooks)
     /   \  • Invariant Hashing & C1 Origin Attribution
    /═════\ • Ledger: Content Hash ⟷ Source URL / Author
   /       \
  /═════════\  [PLANE 2: TOOL-LEVEL AUTHORIZATION — ARMORIQ]
 / \       / \   • Evaluates agent role, task scope & session plan
/   \     /   \  • Authorizes: "May the agent invoke `read_file`?"
\    \   /    /  • Matches Policy: `cli-tripline-maintainer-tripline-mcp`
 \    \ /    /   • Outcome: ALLOW (Cannot see filesystem paths or payload secrets)
  \    V    /
   \═══════/  [PLANE 3: SYSTEM & ARGUMENT CONTAINMENT — TRIPLINE]
    \     /     ┌────────────────────────────────────────────────────────┐
     \   /      │  PATH JAIL: `fstat` + Inode verification               │
      \ /       │  • Evaluates target path against repository root        │
       ▼        │  • Blocks traversal (`../../.ssh/fake_key`) ➔ DENY     │
      / \       ├────────────────────────────────────────────────────────┤
     /   \      │  EGRESS CANARY GATEWAY: Regex & Entropy Scanners       │
    /     \     │  • Scans outbound text arguments for planted tokens    │
   /═══════\    │  • Detects leaked Tier-2 Canary in comment ➔ HOLD      │
  /         \   └────────────────────────────────────────────────────────┘
 /═══════════\  [PLANE 4: KERNEL WITNESS & CRYPTOGRAPHIC PROOF]
/             \   • Append-only HMAC hash chain of real syscall executions
\             /   • Reconciles intent vs reality: `read_file: 0 executed`
 \           /    • Mints Canonical JSON SHA-256 + HMAC-SHA256 Incident Receipt
  \═════════/     • 60-Second Replay-Safe Decision Proof Header
```

---

## Dynamic Execution Pipeline Flow

The following interactive sequence illustrates how an action proposal travels through the Tripline pipeline from raw prompt ingest to cryptographically verified incident receipt:

```mermaid
flowchart TD
    %% Styling
    classDef input fill:#1c1917,stroke:#78716c,stroke-width:1px,color:#f5f5f4;
    classDef armoriq fill:#064e3b,stroke:#059669,stroke-width:1.5px,color:#ecfdf5;
    classDef tripline fill:#701a75,stroke:#c026d3,stroke-width:1.5px,color:#fdf4ff;
    classDef deny fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#fee2e2;
    classDef hold fill:#78350f,stroke:#f59e0b,stroke-width:2px,color:#fef3c7;
    classDef witness fill:#1e1b4b,stroke:#6366f1,stroke-width:1.5px,color:#e0e7ff;
    classDef receipt fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f0f9ff;

    subgraph STAGE_1["01 / INGEST & PROVENANCE"]
        U["Untrusted Input<br/>(Issue #42 / Decoy Config)"]:::input --> P["Origin Ledger<br/>(C1 Attribution Hash)"]:::input
    end

    subgraph STAGE_2["02 / AGENT PROPOSAL & ARMORIQ"]
        P --> A["Agent Loop<br/>(Proposes Tool Call)"]:::input
        A -->|Tool check request| AQ{"ArmorIQ Gate<br/>session.check()"}:::armoriq
        AQ -->|Policy Match:<br/>Tool Allowed| DP["Mint Decision Proof<br/>(HMAC Token, TTL=60s)"]:::armoriq
    end

    subgraph STAGE_3["03 / TRIPLINE ARGUMENT CONTAINMENT"]
        DP --> TG{"Tripline Gateway<br/>Argument Inspector"}:::tripline
        
        %% Direct Path Branch
        TG -->|Path Traversal Check| PJ{"Path Jail<br/>fstat Inode Check"}:::tripline
        PJ -->|Outside Repo Root| D1["TRIPLINE DENY<br/>(PATH_OUTSIDE_ROOT)"]:::deny
        
        %% Egress Canary Branch
        TG -->|Outbound Text Scan| CG{"Canary Gateway<br/>Regex Trap"}:::tripline
        CG -->|Planted Token Detected| D2["TRIPLINE HOLD<br/>(egress_canary_hit)"]:::hold
    end

    subgraph STAGE_4["04 / WITNESS RECONCILIATION"]
        D1 --> W1["Execution Witness<br/>read_file: 0 executed"]:::witness
        D2 --> W2["Execution Witness<br/>comment_issue: 0 executed"]:::witness
    end

    subgraph STAGE_5["05 / CRYPTOGRAPHIC INCIDENT RECEIPT"]
        W1 --> R1["Signed Receipt (DP-01)<br/>SHA-256 Digest + HMAC"]:::receipt
        W2 --> R2["Signed Receipt (IE-01)<br/>SHA-256 Digest + HMAC"]:::receipt
        R1 --> V["Independent Verifier<br/>python -m receipts.verify"]:::receipt
        R2 --> V
    end
```

---

## 3D Forensic Anatomy: Two Live Demo Attacks

| Forensic Dimension | Attack A: Direct Path (`DP-01`) | Attack B: In-Scope Egress (`IE-01`) |
| :--- | :--- | :--- |
| **Ingress Vector** | Poisoned Issue payload requesting SSH key access | Poisoned prompt reading decoy deployment credentials |
| **Proposed Action** | `read_file(path="../../.ssh/fake_key")` | `comment_issue(body="Canary token: ak_live_...")` |
| **Plane 1: Provenance** | Attribution: `C1` (Untrusted issue author) | Attribution: `C1` (Decoy config injected via prompt) |
| **Plane 2: ArmorIQ** | **ALLOW** (Authorized `read_file` under maintainer policy) | **ALLOW** (Authorized `comment_issue` under maintainer policy) |
| **Plane 3: Tripline** | **DENY** via **Path Jail** (`PATH_OUTSIDE_ROOT`) | **HOLD** via **Egress Gateway** (`egress_canary_hit`) |
| **Plane 4: Witness** | `read_file`: **0 executed** (Blocked prior to syscall) | `read_file`: **1 executed** (decoy) $\vert$ `comment`: **0 executed** |
| **Plane 5: Receipt** | Canonical Hash: `a82d65...` $\vert$ HMAC Signature | Canonical Hash: `530db4...` $\vert$ HMAC Signature |
| **Verification** | `make verify FILE=results/demo/receipt_DP-01.json` | `make verify FILE=results/demo/receipt_IE-01.json` |

---

## Decision Proof Cryptographic Protocol

To prevent malicious local processes from bypassing ArmorIQ or Tripline gates, every legitimate tool call is bound to a cryptographically verifiable **Decision Proof**:

```
[Agent Engine] ──── 1. Proposal ────► [Tripline Gateway] ──── 2. Verify Session ────► [ArmorIQ SDK]
                                              │                                             │
                                      4. HMAC Mint                                   3. Policy ALLOW
                                              ▼                                             │
[Tripline MCP Server] ◄── 5. X-Tripline-Decision-Proof ─────────────────────────────────────┘
         │               (args_hash : decision : timestamp : hmac)
         ├──── 6. Validate HMAC using local Witness Secret Key
         ├──── 7. Enforce 60-Second Replay Window (Idempotent Retries)
         ├──── 8. Execute Path Jail / Canary Scan
         └──── 9. Append Step to HMAC Hash Chain (Witness Log)
```

## Demo
The demo showcases two primary attacks:
1. **Attack A (Direct Path, DP-01)**: An agent reads a poisoned issue and proposes direct access to a fake SSH key fixture (`../../.ssh/fake_key`, a synthetic file with no real credentials). ArmorIQ policy authorizes `read_file` at the tool level (`ALLOW`), but Tripline's kernel-verified Path Jail rejects the path traversal outside the repository root (`PATH_OUTSIDE_ROOT` -> `DENY`). A Tier-1 Canary fires. The Witness verifies 0 executions.
2. **Attack B (In-Scope Egress, IE-01)**: The agent reads an authorized decoy configuration (`read_file("config/legacy_deploy.json")`). ArmorIQ correctly allows this read (`ALLOW`), and the decoy canary enters context. The Witness records 1 execution for the decoy read. The agent then proposes a comment containing the canary (`comment_issue`). ArmorIQ authorizes the tool (`ALLOW`), but Tripline detects the canary on egress and **HOLDS** the comment. The Witness records 0 executions for the held comment.

Both the "useful agent" and attack demo segments utilize deterministic stubs (M2) using the real ArmorIQ SDK and live local MCP servers to ensure 100% reproducible execution and forensic receipts without live API non-determinism. No live M1 (real-LLM) runs are used in the demo; the useful-agent beat is scripted.

## Cryptographic Receipts & Verification
Every denied or held action generates an `IncidentReceipt` backed by:
- **Canonical JSON SHA-256 (`canonical_hash`)**: Hashes all immutable evidence fields (source attribution, tool proposal, ArmorIQ decision, Tripline decision, canary, witness count).
- **Witness Chain Head HMAC (`witness_head_hmac`)**: Binds the receipt to the state of the append-only witness chain.
- **HMAC Signature (`receipt_signature`)**: Authenticates the receipt with the witness secret key.

To verify any receipt independently:
```bash
python -m receipts.verify <path_to_receipt.json>
```
Any tampering with evidence fields invalidates the canonical hash and fails verification with `TAMPER_DETECTED`.

## Decision Proofs & Replay Policy
Every legitimate MCP `tools/call` request requires an `X-Tripline-Decision-Proof` header containing an HMAC over `f"{args_hash}:{decision}:{timestamp}"` signed with the witness secret key.
- **Replay Policy**: Replay of a decision proof within its **60-second TTL window is allowed by design** to accommodate legitimate agent retry workflows without requiring redundant `session.check()` round-trips.
- Direct HTTP callers lacking a valid, unexpired decision proof receive HTTP 403 `MISSING_DECISION_PROOF`.

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make demo
```

## `make demo`
This command prepares the demo environment, starts the backend MCP server, executes live attack scenarios, and launches the web dashboard at `http://localhost:8080`. Demo runs and receipts are written to `results/demo/` in isolation from benchmark data.

## Frontend
The dashboard interface is built with Next.js and static export (`tripline-frontend/`), served directly by FastAPI single-process on `http://127.0.0.1:8080`.
- **Offline & Zero-CDN**: All assets, fonts, and scripts are bundled locally. Zero external network calls.
- **REST API**: Mounted under `/api` in `dashboard/api.py`, serving real dynamic data computed directly from forensic artifacts (`results/demo/receipt_*.json`, `events.jsonl`, `demo_runs.jsonl`, and `benchmark_runs.jsonl`).
- **Build**: Run `make dashboard-build` to recompile the frontend static bundle. The pre-built bundle is included in `tripline-frontend/out/` so `make demo` starts without requiring node/npm installed at runtime.


## Benchmark Results
Benchmark scope matches `benchmark/results/benchmark_runs.csv` and `benchmark_summary.csv`:
- **86 evaluated runs** across 27 scenarios (24 attack classes + 3 benign tasks).
- **Arms**: Arm A (No Defense, 29 runs), Arm B (ArmorIQ Only, 29 runs), Arm C (ArmorIQ + Tripline, 28 runs).
- **Mode**: All runs evaluated under **Mode M2 (Forced-Compliance Deterministic Stubs, N=1 or 2)** to strictly measure security boundary efficacy isolated from prompt-refusal noise or LLM non-determinism.
- **No live M1 (real-LLM) runs exist** in benchmark totals.

## Limitations
See [docs/limitations.md](docs/limitations.md) for an honest breakdown of our security boundary assumptions (TOCTOU residuals, unsigned receipt threats, same-user witness key locality, client-side check limits, 60s replay design, and M2 scope).

## Tests
To run the full security verification suite (153 passed as printed by pytest; `tests/test_phase11_benchmark.py` is excluded from `make test` — run it separately with `make bench-test`):
```bash
make test
make test-armoriq
make harden
make demo
make explain
make verify FILE=results/demo/receipt_DP-01.json
```
