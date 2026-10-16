# Tripline Governed Autonomous Agent v2 Architecture (Phase 11 P2)

**Author**: Tripline Engineering  
**Version**: Agent v2 (`agent/` modules)  
**Integration Mode**: MODE B (Direct Local MCP Execution with Synchronous ArmorIQ Authorization)

---

## 1. Executive Thesis

> **"Blocked isn't evidence. Every denied action gets a receipt."**  
> **"ArmorIQ decides. Tripline proves."**

In autonomous agent operations, an agent that evaluates untrusted user inputs (such as external GitHub issues) is inherently vulnerable to prompt injection attacks that attempt destructive actions (`delete_branch`), file system breakouts (`read_file` outside root), or confidential data leaks (exfiltrating canary secrets into issue comments).

Tripline couples upstream policy governance with in-depth boundary defense and cryptographic receipt generation.

---

## 2. Core Architectural Components

Tripline Agent v2 is organized into dedicated, decoupled modules under `agent/`:

```mermaid
graph TD
    TrustedGoal[Trusted Goal & Tool Vocabulary] --> Planner[Trusted Planner (agent/planner_v2.py)]
    Planner --> PlanCapture[ArmorIQ Plan Capture & Intent Token (agent/plan_token.py)]
    PlanCapture --> Crew[Scoped Crew Delegation (agent/crew.py)]
    Crew --> LLM[Brain: LLM Model Loop (agent/real_llm.py)]
    LLM --> ToolProp[Proposed Tool Call]
    ToolProp --> Layer1[Layer 1: ArmorIQ Policy Check]
    Layer1 -- DENY --> Receipt1[Signed HMAC Incident Receipt]
    Layer1 -- ALLOW --> Layer2[Layer 2: Tripline Path Jail]
    Layer2 -- DENY --> Receipt2[Signed HMAC Incident Receipt]
    Layer2 -- ALLOW --> Layer3[Layer 3: Egress Canary Gateway]
    Layer3 -- HOLD --> Receipt3[Signed HMAC Incident Receipt]
    Layer3 -- ALLOW --> MCP[Tripline MCP Tool Execution]
    MCP --> Witness[Witness Append-Only Hash Chain]
```

### 2.1 Identity & User Attribution (`agent/identity.py`)
- Represents the authenticated agent registered on the platform (`agent_id`, `agent_name`, `environment`).
- Binds end-user attribution (`user_email`) to every intent token and audit trace. Defaults to the verified sandbox identity `sandbox-maintainer@example.invalid`.

### 2.2 Trusted Planner (`agent/planner_v2.py`)
- **Why Planning From Trusted Input Matters**:
  A plan synthesized *after* reading untrusted issue text is already compromised: a prompt injection in the issue title or description could direct the planner to include `delete_branch` or unauthorized tools in the plan itself.
  Tripline's trusted planner builds the cryptographic execution plan strictly from trusted, administrator-defined goals and static tool vocabulary *before* any untrusted issue content is ever ingested.
- **Plan Invariants**:
  Destructive tools like `delete_branch` are physically excluded from the plan vocabulary.
- **Honest Boundary Limitation**:
  Plan-binding enforces tool vocabulary restriction, but does *not* protect against attacks that employ tools that *are* authorized in the plan (such as `read_file` targeting `/etc/shadow` or `../../.ssh/id_rsa`, or `comment_issue` leaking a canary token). That is precisely why Tripline's in-MCP Path Jail and Egress Canary Gateway exist.

### 2.3 Plan Capture & Intent Token (`agent/plan_token.py`)
- Computes canonical RFC 8785 plan hashes and SHA-256 Merkle roots over step definitions.
- Requests signed `IntentToken` from ArmorIQ IAP via `client.capture_plan` and `client.get_intent_token`.
- Under Rule R2, secret tokens are held in-memory and never serialized or leaked to logs.

### 2.4 Scoped Authority Crew (`agent/crew.py`)
- **Orchestrator** (`tripline-maintainer`): Holds parent authority and manages the issue triage pipeline.
- **Sub-Agent `reader`**: Granted scoped authority strictly over inspection tools (`list_issues`, `read_issue`, `read_file`, `list_dir`).
- **Sub-Agent `responder`**: Granted scoped authority strictly over reporting tools (`comment_issue`, `label_issue`).
- Ephemeral Ed25519 keypairs are generated in-memory at run start; private keys are never persisted to disk.

### 2.5 Multi-Layer Tool Executor (`agent/executor.py`)
Every proposed tool invocation is routed through the defense hierarchy:
1. **ArmorIQ Policy Authorization**: Evaluates tool against active plan and platform policy. Out-of-policy actions (`delete_branch`) are denied before any MCP code executes.
2. **Tripline Path Jail**: Intercepts `read_file` calls. Performs percent-decode, user-tilde expansion, and canonical realpath boundary verification against the sandbox root. Prevents path traversal and symlink breakouts (`PATH_OUTSIDE_ROOT`).
3. **Tripline Egress Gateway**: Inspects outbound parameters (`comment_issue`, `label_issue`) for planted canary tokens. Intercepts and holds exfiltration attempts (`HELD-EGRESS`).
4. **Tripline Witness & Receipts**: For every blocked or held action, mints an HMAC-SHA256 signed incident receipt containing full forensic evidence.

### 2.6 Observability & Safety Rails (`agent/events.py`, `agent/safety.py`)
- Emits typed events (`run_started`, `plan_captured`, `delegation_created`, `tool_proposed`, `armoriq_decision`, `tripline_decision`, `executed`, `receipt_created`, `witness_appended`, `run_finished`).
- Real-time in-process pub/sub bus feeds SSE streaming to the dashboard.
- Redacts key-shaped strings (`ak_live_`, `AQ.`, `sk-`, `Bearer`, private keys) from all logs and streams.
- Enforces strict execution budgets (max tool calls, max duration, kill switch file).
