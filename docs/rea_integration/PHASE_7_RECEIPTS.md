# Phase 7 — Verifiable Security Receipts for REA Operations

**Date:** 2026-10-17  
**Module:** `agent/security_receipts.py`  
**Schema:** `REASecurityReceipt` with HMAC-SHA256 integrity  

---

## 1. Audit Trail Semantics

A central requirement of TripLine is that execution receipts must never conflate distinct stages of an agentic action. The `REASecurityReceipt` records each phase independently:

| Field | Meaning | Possible Values |
|:---|:---|:---|
| `policy_check_status` | Status of ArmorIQ policy query | `CHECKED`, `SKIPPED`, `ERROR` |
| `authorization_decision` | ArmorIQ decision outcome | `ALLOW`, `DENY`, `UNAVAILABLE`, `NONE` |
| `dispatch_attempted` | Did the agent attempt MCP dispatch? | `True` (only if ALLOW), `False` (if DENIED or blocked) |
| `dispatch_status` | Outcome of dispatch attempt | `EXECUTED`, `BLOCKED`, `FAILED`, `NONE` |
| `tool_result_status` | Result of tool execution | `SUCCESS`, `ERROR`, `NONE` |
| `report_status` | ArmorIQ audit report transmission | `REPORTED`, `FAILED`, `NONE` |
| `failure_stage` | Point of failure if any | `NONE`, `AUTHORIZATION`, `TRIPLINE_CONFINEMENT`, `DISPATCH`, `TOOL_EXECUTION`, `REPORTING` |
| `verification_status` | Evidence provenance mode | `LIVE_VERIFIED`, `TEST_SIMULATED`, `UNVERIFIED` |

---

## 2. Cryptographic Integrity

Each receipt calculates a SHA-256 HMAC signature over its canonical JSON serialization:
```python
receipt = create_security_receipt(...)
assert receipt.verify_signature() is True
```
Any tampering with fields (such as changing a `DENY` to an `ALLOW`, or modifying `dispatch_attempted`) invalidates the cryptographic signature immediately.

---

## 3. Invariants Enforced

1. **Denied Actions Have Zero Execution:**
   - If `authorization_decision == "DENY"`, then `dispatch_attempted == False`, `dispatch_status == "BLOCKED"`, and `tool_result_status == "NONE"`.
2. **Authorization Failures Fail Closed:**
   - If ArmorIQ times out or disconnects, `authorization_decision == "UNAVAILABLE"`, `dispatch_attempted == False`, and `failure_stage == "AUTHORIZATION"`.
3. **Execution Errors Do Not Masquerade as Denials:**
   - If a tool fails inside REA after dispatch, `dispatch_attempted == True`, `dispatch_status == "EXECUTED"`, and `tool_result_status == "ERROR"`.
4. **Mocks are Explicitly Marked:**
   - Simulated test doubles receive `verification_status == "TEST_SIMULATED"`.
