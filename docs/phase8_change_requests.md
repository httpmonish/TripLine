# Phase 8 Change Requests Log

**Repository**: Tripline  
**Branch**: `phase8-fix`  
**Rule R4 Policy**: READ-ONLY ZONE (`mcp/`, `receipts/`, `canary/`, `gateway/`, and ArmorIQ policy files) requires a formal Change Request (CR) documented with file, reason, exact diff, risk, and test, approved by the repository owner before application.

---

## CR Index

| CR ID | Target File | Status | Description |
|---|---|---|---|
| **CR-00** | N/A | **NO CHANGES NEEDED** | Full audit confirms zero code modifications required in `mcp/`, `receipts/`, `canary/`, `gateway/`, or policy files. All layer behaviors, receipt structures, and gateway logic function as specified. |

---

## CR Details

### CR-00: Zero Read-Only Zone Modifications
* **Target Files**: None (`mcp/*`, `receipts/*`, `canary/*`, `gateway/*`, `armoriq.yaml`)
* **Reason**: 
  - W1 SDK integration truth: Agent invokes ArmorIQ exclusively via `armoriq_sdk.ArmorIQClient` (`session.check` in `mode="sdk"`). No raw HTTP enforcement calls exist in application code.
  - W2 MCP invocation: Invocation path is "enforce-check then direct call", matching architecture specification. No routing changes needed.
  - W3 The block: `tool_not_in_allowlist` is returned authoritatively by platform OPA policy. No local policy simulation exists.
  - W9 Residuals: Residuals (Base64, ROT13, reversed, split) are tested via deterministic unit tests outside the read-only zone without modifying `canary/scan.py`.
* **Risk**: None.
* **Test**: `make test`, `make audit`, `make verify`, `make tamper`.
