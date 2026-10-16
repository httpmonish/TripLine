# Tripline Architecture Specification

**Thesis**: *"Blocked isn't evidence. Every denied action gets a receipt."*  
**Closing Line**: *"ArmorIQ decides. Tripline proves."*

---

## 1. Multi-Layer Architecture Diagram

The Tripline architecture enforces multi-layered defense-in-depth across the agent runtime:

```mermaid
flowchart TD
    %% Styling
    classDef agent fill:#1e293b,stroke:#475569,stroke-width:1.5px,color:#f8fafc;
    classDef armoriq fill:#064e3b,stroke:#059669,stroke-width:2px,color:#ecfdf5;
    classDef tripline fill:#4c1d95,stroke:#8b5cf6,stroke-width:2px,color:#f5f3ff;
    classDef sandbox fill:#1f2937,stroke:#374151,stroke-width:1.5px,color:#f9fafb;
    classDef receipt fill:#0c4a6e,stroke:#0284c7,stroke-width:2px,color:#f0f9ff;
    classDef deny fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#fee2e2;
    classDef hold fill:#78350f,stroke:#f59e0b,stroke-width:2px,color:#fef3c7;

    subgraph AGENT_PLANE ["Agent Plane"]
        A["Autonomous LLM Agent<br/>(Claude 3.5 Sonnet)"]:::agent
        Q["Untrusted Ingest Queue<br/>(5 Issues: 2 Benign, 3 Attacks)"]:::agent --> A
    end

    subgraph LAYER_1 ["Layer 1: ArmorIQ Platform Enforcement"]
        AQ{"ArmorIQ Policy Gate<br/>/iap/sdk/enforce"}:::armoriq
        A -->|Proposes tool call| AQ
        AQ -->|P1: delete_branch<br/>Tool Not In Allowlist| D1["DENY: ArmorIQ Platform<br/>(Action Never Reaches MCP)"]:::deny
        AQ -->|P2 / P3: read_file / comment_issue<br/>Tool Allowed| DP["Mint Decision Proof<br/>(HMAC Token, TTL=60s)"]:::armoriq
    end

    subgraph LAYER_2 ["Layer 2: Tripline In-MCP Containment"]
        MCP["Tripline MCP Server<br/>(:8000 FastMCP)"]:::tripline
        DP -->|Forward with Decision Proof| MCP
        
        PJ{"Path Jail<br/>fstat Inode Check"}:::tripline
        MCP -->|Inspect path argument| PJ
        PJ -->|P2: ../../fake_home/.ssh/fake_key<br/>Path Outside Repo Root| D2["DENY: Tripline Path Jail<br/>(0 Executions, 0 Bytes Read)"]:::deny
        PJ -->|Path inside sandbox root| EXEC["Execute Sandbox Action"]:::sandbox
        
        EG{"Egress Gateway<br/>Regex Canary Trap"}:::tripline
        MCP -->|Inspect outbound text| EG
        EG -->|P3: Body contains TRPL-TRA-...<br/>Planted Canary Hit| D3["HOLD: Egress Gateway<br/>(Quarantine Before Network)"]:::hold
        EG -->|Clean benign text| EXEC
    end

    subgraph LAYER_3 ["Layer 3: Forensics & Verification"]
        WIT["Witness Log<br/>(HMAC Hash-Chain)"]:::receipt
        D1 -.->|Platform Event| WIT
        D2 -.->|Jail Event| WIT
        D3 -.->|Gateway Event| WIT
        EXEC -.->|Execution Event| WIT
        
        RCP["Cryptographic Receipt<br/>(Canonical JSON + HMAC)"]:::receipt
        WIT --> RCP
    end

    EXEC --> SBOX["Local Sandbox Repo<br/>(Isolated Temp Root)"]:::sandbox
```

*Note: GitHub renders the Mermaid diagram above natively; standalone Mermaid source is preserved in [`docs/architecture.mmd`](file:///Users/themonishnawaz/tripline/docs/architecture.mmd).*

---

## 2. Trust Boundaries and Layer Responsibilities

Each enforcement layer operates within strict, well-defined visibility boundaries:

### Layer 1: ArmorIQ Platform Gate (`https://api.armoriq.ai`)
* **What it trusts**: The authenticated API key and agent identity registered on `platform.armoriq.ai`.
* **What it sees**: The proposed tool name (`delete_branch`, `read_file`, `comment_issue`) and registered policy rules.
* **What it cannot see**: Argument payloads, file path strings, or repository contents.
* **Its role**: Authorizes whether this agent is permitted to invoke the tool. When an unauthorized action like `delete_branch` is attempted, ArmorIQ halts the call upstream. The action never touches the MCP server or local filesystem.

### Layer 2: Tripline In-MCP Containment (`mcp/`)
* **What it trusts**: The valid ArmorIQ Decision Proof minted during Layer 1 (TTL 60s).
* **What it sees**: The exact parameter values passed to tools, open file descriptors, and target inodes.
* **What it cannot see**: High-level organizational role policies or agent plans.
* **Its role**:
  * **Path Jail**: Executes an `fstat` inode check on the resolved target descriptor to verify it resides strictly inside the repository root. Traversal escapes (`../../fake_home/.ssh/fake_key`) are denied with `PATH_OUTSIDE_ROOT`, guaranteeing 0 executions and 0 bytes leaked.
  * **Egress Canary Gateway**: Scans outbound comment payloads against active canary token registries (`TRPL-TRA-...`). If a planted token is detected, the action is placed on `HOLD` before network dispatch.

### Layer 3: Witness Log & Receipt Builder (`receipts/`, `witness/`)
* **What it trusts**: Local cryptographic secret keys (`TRIPLINE_WITNESS_KEY`).
* **What it sees**: Raw events, exit codes, execution counts, and canonical argument hashes.
* **What it cannot see**: Future actions or human operator intent.
* **Its role**: Appends execution records into a local HMAC-chained log (`repo-mcp.jsonl`) and emits HMAC-SHA256 signed Incident Receipts in Canonical JSON format. The signature guarantees that any modification of covered fields is deterministically detected.

---

## 3. The Honest Residual

No security system prevents all threats, and Tripline reports its limitations with complete transparency:
* **Obfuscated / Transformed Egress**: Tripline's egress scanner performs exact substring matching for canary tokens. If an adversarial agent transforms the token (e.g., Base64 encoding, reversing, or splitting across multiple comments), the exact substring match fails and the exfiltration is not trapped by either layer (*documented in `docs/phase3_layer_attribution.md` Section 3*).
* **Action Replay**: Decision proofs carry a 60-second TTL. Replaying an identical valid proof within the active 60-second window is permitted by design.

---

## 4. Website Architecture

The Tripline website is implemented in `tripline-frontend/` (aliased as `web/`):
- **Framework**: Next.js (App Router) static export served by FastAPI unified dashboard at port 8080.
- **Visual Design**: Alternating dark and light editorial sections, SVG architecture diagrams (D1 Hero Intercept, D2 Checkpoint Pipeline, D3 Layer Matrix, D5 Verify Strip), and restrained enterprise typography.
- **Evidence Integrity**: All metrics, counts, hashes, and receipts are synced directly from `results/` and `docs/` at build time via `scripts/sync-data.ts`. Zero third-party network requests, zero synthetic counters.

