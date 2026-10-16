# ArmorIQ SDK Introspection Data (Phase 11 P1)

**SDK Package**: `armoriq-sdk 0.6.10`  
**Location**: `.venv313/lib/python3.13/site-packages`  
**License**: MIT  
**Introspected**: 2026-10-16

---

## 1. Public Classes and Models

### 1.1 Core Client & Sessions
- `ArmorIQClient`: Primary client entrypoint.
- `ArmorIQSession`: Session context for checking/enforcing tool actions.
- `ArmorIQUserScope`: Returned by `client.for_user(user_email)`.

### 1.2 Data & Token Models
- `PlanCapture`:
  - `plan: Dict[str, Any]` (`goal`, `steps`)
  - `llm: str`
  - `prompt: str`
  - `metadata: Dict[str, Any]`
- `IntentToken`:
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
- `EnforceResult`:
  - `reason: Optional[str]`
  - `matched_policy: Optional[str]`
  - `delegation_id: Optional[str]`
- `DelegationResult`:
  - `delegation_id: str`
  - `delegated_token: IntentToken`
  - `delegate_public_key: str`
  - `target_agent: Optional[str]`
  - `expires_at: datetime`
  - `trust_delta: float`
  - `status: str`
  - `metadata: Dict[str, Any]`
- `MCPInvocationResult`:
  - `mcp: str`
  - `action: str`
  - `result: Any`
  - `status: str`
  - `execution_time: float`
  - `verified: bool`
  - `metadata: Dict[str, Any]`

### 1.3 Exception Hierarchy
- `ArmorIQException`
  - `ConfigurationException`
  - `DelegationException(message, target_agent, delegation_id, status_code)`
  - `IntentMismatchException(message, action, plan_hash)`
  - `InvalidTokenException(message, token_id)`
  - `MCPInvocationException(message, mcp, action, status_code)`
  - `PolicyBlockedException(message, enforcement_action, reason, metadata)`
  - `PolicyHoldException(message, delegation_context, metadata)`
  - `RevokedTokenError(message, token_id, reason)`
  - `TokenExpiredException(message, token_id, expired_at)`

---

## 2. Configuration & Reality Probe Results

1. **Local Credentials & Config**:
   - `~/.armoriq/credentials.json`: Present
   - `armoriq.yaml`: Present (declares identity, proxy, mcp_servers with legacy trycloudflare endpoint)
   - `ARMORIQ_API_KEY`: Not set in current shell environment

2. **Network Probe Result**:
   - `scripts/armoriq_proof.py` executed:
     ```
     FATAL: Could not fetch platform bootstrap from ArmorIQ backend:
     sdk/bootstrap failed: 401 {"message":"Invalid or expired API key","error":"Unauthorized","statusCode":401}
     ```
   - Observed behavior: Active credentials stored in `~/.armoriq/credentials.json` are expired/invalid (owner rotating keys).
   - Mode A platform proxy route is unreachable without an active key and registered reachable MCP.
