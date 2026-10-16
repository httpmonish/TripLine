# ArmorIQ Documentation Learning Notes (Phase 11 P0)

**Date of Record**: 2026-10-16  
**Source Root**: `https://docs.armoriq.ai` and `armoriq-sdk 0.6.10` inspection

---

## 1. Documented SDK Core Methods & Signatures

### 1.1 `capture_plan`
- **Documented URL**: `/sdk/core-methods/capture-plan`
- **Method Signature** (verified from installed SDK):
  ```python
  client.capture_plan(
      llm: str,
      prompt: str,
      plan: Optional[Dict[str, Any]] = None,
      metadata: Optional[Dict[str, Any]] = None
  ) -> PlanCapture
  ```
- **Documented Behavior**:
  - Captures the agent's proposed plan structure before execution begins.
  - Plan format: `{"goal": "<str>", "steps": [{"action": "<str>", "mcp": "<str>", "params": {...}}]}`.
  - Generates deterministic `plan_hash` and initial Merkle tree root representing the promised tool execution sequence.

### 1.2 `get_intent_token`
- **Documented URL**: `/sdk/core-methods/get-intent-token`
- **Method Signature** (verified from installed SDK):
  ```python
  client.get_intent_token(
      plan_capture: PlanCapture,
      policy: Optional[Dict[str, Any]] = None,
      validity_seconds: float = 60.0
  ) -> IntentToken
  ```
- **Documented Behavior**:
  - Sends captured plan to ArmorIQ Intent Authorization Proxy (`/iap/sdk/token`).
  - Returns cryptographically signed `IntentToken`.
  - Properties exposed on `IntentToken`:
    - `token_id: str`
    - `plan_hash: str`
    - `plan_id: Optional[str]`
    - `signature: str`
    - `issued_at: datetime`
    - `expires_at: datetime`
    - `policy: Optional[Dict[str, Any]]`
    - `policy_validation: Optional[Dict[str, Any]]`
    - `step_proofs: Optional[List[Dict[str, Any]]]`
    - `total_steps: int`

### 1.3 `invoke` (Platform Proxy)
- **Documented URL**: `/sdk/core-methods/invoke`
- **Method Signature** (verified from installed SDK):
  ```python
  client.invoke(
      mcp: str,
      action: str,
      intent_token: IntentToken,
      params: Optional[Dict[str, Any]] = None,
      merkle_proof: Optional[List[Any]] = None,
      user_email: Optional[str] = None
  ) -> MCPInvocationResult
  ```
- **Documented Behavior**:
  - In MODE A (Proxy mode), invokes the tool by sending the request through `https://proxy.armoriq.ai`.
  - Proxy validates the `intent_token`, confirms `action` is in the plan, checks `allowed_tools` claim, evaluates platform policies, and proxies the call to the registered MCP server endpoint.
  - If action is not in plan, raises `armoriq_sdk.exceptions.PolicyBlockedException` or `armoriq_sdk.exceptions.MCPInvocationException`.

### 1.4 `delegate` (Scoped Authority Delegation)
- **Documented URL**: `/sdk/core-methods/delegate`
- **Method Signature** (verified from installed SDK):
  ```python
  client.delegate(
      intent_token: IntentToken,
      delegate_public_key: str,
      validity_seconds: int = 3600,
      allowed_actions: Optional[List[str]] = None,
      target_agent: Optional[str] = None,
      subtask: Optional[Dict[str, Any]] = None
  ) -> DelegationResult
  ```
- **Documented Behavior**:
  - Mints a scoped sub-token tied to the delegate's Ed25519 public key.
  - Subtask / `allowed_actions` restricts what the sub-agent can invoke.
  - Delegates cannot re-delegate without platform permission.
  - Expiration of parent token invalidates delegations.
  - `DelegationResult` attributes:
    - `delegation_id: str`
    - `delegated_token: IntentToken`
    - `delegate_public_key: str`
    - `target_agent: Optional[str]`
    - `expires_at: datetime`
    - `trust_delta: float`
    - `status: str`

### 1.5 `start_session` and `session.check` (SDK Mode / Local Enforcement)
- **Documented URL**: `/sdk/configuration` / `/sdk/advanced-usage`
- **Method Signature** (verified from installed SDK):
  ```python
  client.start_session(opts: Optional[SessionOptions] = None) -> ArmorIQSession
  session.check(tool_name: str, tool_args: Dict[str, Any], user_email: Optional[str] = None) -> EnforceResult
  ```
- **Behavior**:
  - Evaluates policy against `/iap/sdk/enforce` synchronously.
  - Returns `EnforceResult` with:
    - `reason: Optional[str]`
    - `matched_policy: Optional[str]`
    - `delegation_id: Optional[str]`
  - If allowed: decision allows agent to proceed to local MCP tool.
  - If blocked: raises `PolicyBlockedException` with enforcement reason.

### 1.6 User Attribution
- **Documented Methods**:
  - `client.for_user(user_email: str) -> ArmorIQUserScope`
  - Direct parameter: `user_email: Optional[str]` in `invoke()` and `session.check()`.
- **Behavior**:
  - Attaches end-user identity (`user_email`) to intent tokens and audit logs.

---

## 2. Platform Dashboard & Governance Capabilities

### 2.1 MCP Server Registration
- **Fields**: Server Name, Environment (`Development` / `Staging` / `Production`), Server URL, Port, Protocol Version, Authentication Method (`API Key`, `Bearer`), Capabilities (`Tools`, `Prompts`, `Resources`), Security Scanning.

### 2.2 Agent Registration & Controls
- **Fields**: Name, Framework (A2A / MCP), Description, Environment, Allowed MCP Tools.
- **Agent Controls**: Kill switch capability to immediately terminate active tool calls or invalidate issued intent tokens.

### 2.3 Policy Engine & Priority
- Evaluates policies in priority order (first match wins).
- Default behavior: **ALLOW if no match** (explicit deny rule required to restrict sensitive actions like `delete_branch`).

---

## 3. Unverified Platform Features (Marked per Rule R8)
- **Holds / Platform Human Approval**: UNVERIFIED on platform endpoint without active dashboard credentials.
- **Platform Merkle Audit Chain Verification UI**: UNVERIFIED on platform dashboard directly without live login.
- **Audit-log streaming API / export**: UNVERIFIED without organization admin access.
