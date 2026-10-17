# Phase 4 — ArmorIQ Authorization & Enforcement Boundary

**Date:** 2026-10-17  
**Module:** `agent/executor.py` & `armoriq_helper.py`  
**SDK Version:** `armoriq-sdk==0.6.10` (pinned)  

---

## 1. Objective and Lifecycle

Every protected tool execution must pass through the authoritative ArmorIQ policy check before TripLine allows MCP dispatch. If ArmorIQ denies the action or the service cannot be reached, the system fails closed and prevents dispatch.

### Authorization & Enforcement Lifecycle:
```
1. Start Session:
   client.start_session(SessionOptions(mode="sdk", default_mcp_name="tripline-mcp"))
2. Start Plan:
   session.start_plan([ToolCall(name=tool_name, args=tool_args)], goal=task_goal)
3. Check Proposed Action:
   res = session.check(tool_name=tool_name, tool_args=tool_args, user_email=user_email)
4. Evaluate Decision:
   If res.allowed is True and action == "allow":
       PROCEED to Layer 2 (TripLine Confinement & Gateway)
   Else (DENY, timeout, network exception):
       HALT dispatch, produce signed receipt, record witness event.
5. Report Audit Result:
   session.report(status="success" if executed else "denied")
```

---

## 2. Live Platform Verification

Live enforcement was verified using `scripts/armoriq_proof.py` and direct SDK queries:
- **Registration of REA wrapper tools:** Using `armoriq register --config armoriq.yaml`, the narrow allowlist was synchronized to the ArmorIQ control plane for agent `tripline-maintainer` and MCP `tripline-mcp`.
- **In-Policy checks (`analyze_electron_app`, `trace_application_feature`, `inspect_analysis_view`, `hello_tool`):** Returns `ALLOW` (action: `allow`, reason: `allow_with_logging`, matched_policy: `cli-tripline-maintainer-tripline-mcp`, verified HTTP round-trip to `/iap/sdk/enforce`).
- **Out-of-Policy check (`unauthorized_tool`):** Returns `DENY` (action: `block`, reason: `tool_not_in_allowlist`, verified HTTP round-trip to `/iap/sdk/enforce`).

Anti-spoofing verification confirmed that the deny reason originated from ArmorIQ OPA policy rather than local codebase strings. Dispatch is strictly blocked upon DENY (`dispatch_attempted=False`).

---

## 3. Fail-Closed Rules (Rules A through H)

- **Rule A (Missing Session):** Returns `AUTHORIZATION_UNAVAILABLE`. Protected action is NOT dispatched.
- **Rule B (SDK Denial):** Returns `DENY_ARMORIQ`. Action blocked.
- **Rule C (SDK Exception):** Any network timeout or HTTP error returns `AUTHORIZATION_UNAVAILABLE`.
- **Rule D (Invalid Response):** Malformed response returns `AUTHORIZATION_UNAVAILABLE`.
- **Rule E (Verified Allow):** Only `allowed is True` with `action == "allow"` permits dispatch.
- **Rule F (Local Integrity Policy):** TripLine enforces forbidden actions (such as `delete_branch`) even if upstream policy allows it.
- **Rule G (No Bypass):** `dispatch_authorized` enforces `auth_decision.status == "ALLOW"` prior to MCP invocation.
- **Rule H (Argument Binding):** Dispatched tool and arguments must match authorized tool and arguments.

---

## 4. Acceptance Criteria Verification

- [x] **Live Authorization Workflow:** Tested and confirmed with active ArmorIQ credentials.
- [x] **Denied Action Blocked:** Confirmed that denied actions produce zero MCP invocations (`dispatch_attempted=False`).
- [x] **Fail-Closed Behavior:** Uncertain, missing, or errored authorization results never fall through into tool execution.
- [x] **Credential Safety:** Secrets are never hardcoded or printed; redacted from logs and receipts.
