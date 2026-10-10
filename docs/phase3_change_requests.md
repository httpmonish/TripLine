# Phase 3 Change Requests

Per Phase 3 Section 3, all proposed edits to files within the read-only zone (`receipts/`, `mcp/`, `canary/`) must be documented as formal Change Requests with exact unified diffs, non-breakage guarantees, and test verification procedures.

---

## Change Request CR-1: In-Receipt ArmorIQ Platform Audit Link (Schema v2)

- **Target Files**: `receipts/models.py`, `receipts/verify.py`, `receipts/builder.py`
- **Zone**: Read-Only Zone (Rule R5)
- **Rationale**: Currently, `IncidentReceipt` stores `armoriq_decision` and `armoriq_reason` in `DecisionEvidence`, but does not bind the live platform execution references (e.g. `request_id`, `cloud_trace`, `token_id`, `policy_ref`, `check_timestamp`) directly inside the cryptographically signed receipt structure. Adding an optional `armoriq_ref` field under Schema Version 2 provides undeniable cryptographic linkage between ArmorIQ's cloud policy decision and Tripline's signed receipt.
- **Backward Compatibility (Hard Requirement)**: All existing Version 1 receipts (e.g., `results/demo/receipt_DP-01.json`, `results/demo/receipt_IE-01.json`) lack `armoriq_ref` and `schema_version`. They MUST verify unchanged. If `armoriq_ref` is omitted, the canonical hash computation uses the exact v1 field structure.
- **Tamper Evidence**: For v2 receipts, `canonical_evidence_dict` includes `armoriq_ref`. Any post-signature modification of `armoriq_ref` causes canonical hash mismatch and returns `TAMPER_DETECTED`.

### Unified Diff:

```diff
--- a/receipts/models.py
+++ b/receipts/models.py
@@ -48,6 +48,8 @@ class IncidentReceipt(BaseModel):
     run_id: str
     created_at: str
+    schema_version: Optional[int] = 1
+    armoriq_ref: Optional[Dict[str, Any]] = None
 
     source: SourceEvidence
     proposal: ProposalEvidence

--- a/receipts/verify.py
+++ b/receipts/verify.py
@@ -47,6 +47,10 @@ def canonical_evidence_dict(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
     """Extracts only the immutable evidence fields for canonical hashing."""
-    return {
+    evidence = {
         "receipt_id": receipt_data.get("receipt_id"),
         "incident_id": receipt_data.get("incident_id"),
         "run_id": receipt_data.get("run_id"),
@@ -58,6 +62,10 @@ def canonical_evidence_dict(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
         "canary": receipt_data.get("canary"),
         "witness": receipt_data.get("witness"),
         "confidence": receipt_data.get("confidence"),
     }
+    if receipt_data.get("armoriq_ref") is not None:
+        evidence["armoriq_ref"] = receipt_data.get("armoriq_ref")
+        evidence["schema_version"] = receipt_data.get("schema_version", 2)
+    return evidence

--- a/receipts/builder.py
+++ b/receipts/builder.py
@@ -29,6 +29,8 @@ class IncidentBuilder:
         canary_data: Optional[Dict[str, Any]] = None,
         witness_data: Optional[Dict[str, Any]] = None,
-        confidence_data: Optional[Dict[str, Any]] = None
+        confidence_data: Optional[Dict[str, Any]] = None,
+        armoriq_ref: Optional[Dict[str, Any]] = None
     ) -> IncidentReceipt:
@@ -99,6 +101,10 @@ class IncidentBuilder:
             "witness": witness.model_dump(),
             "confidence": confidence.model_dump(),
+            "schema_version": 2 if armoriq_ref else 1,
+            "armoriq_ref": armoriq_ref,
         }
```

- **Non-Breakage Guarantee**: Does not alter witness signing keys, HMAC algorithms, or validation of existing v1 receipts.
- **Verification Plan**: Dedicated unit tests in `tests/test_phase3_receipt_schema.py` checking:
  1. Existing v1 receipts verify `True`.
  2. Newly generated v2 receipts verify `True`.
  3. Modifying 1 byte inside `armoriq_ref` in a signed v2 receipt yields `TAMPER_DETECTED`.
- **Fallback if Rejected**: Use the standalone hash-chained sidecar ledger (`results/phase3/armoriq_links.jsonl`) with zero edits to `receipts/`.
