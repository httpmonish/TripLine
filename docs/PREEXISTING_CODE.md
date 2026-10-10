# Pre-Existing Code Disclosure (Hackathon Rule 5)

**Project:** Tripline  
**Event:** ArmorIQ "Flow State" Hackathon (10–17 Oct 2026)  
**Date:** 2026-10-10  

In accordance with Hackathon Rule 5, this document discloses components of the Tripline repository created prior to the hackathon window start (10 October 2026 00:00:00 +0530), their architectural purpose, and the work performed on them during the hackathon window.

> *Organizer Notification Statement:*  
> **"Tripline's pre-build-week foundation was disclosed to hackathon organizers and approved by the founder prior to competition start."**  
> *(Note: Stated by the repository owner; not independently verifiable by the AI agent).*

---

## 1. Disclosed Pre-Window Components

| Component / Path | Pre-Window Role | In-Window Work Performed (10–17 Oct 2026) |
|---|---|---|
| **`mcp/`** (Base Server & Common) | Provided basic MCP server boilerplate, `jail.py` path validator, and witness HMAC structure. | Added `delete_branch` tool definition with strict path containment safeguards; wired into live scenario runner. |
| **`receipts/`** (Schemas & Hasher) | Provided Pydantic models for `IncidentReceipt` and canonical JSON SHA-256 serializer. | Audited signature coverage; built verification scripts; created `results/phase3/armoriq_links.jsonl` hash-chained audit sidecar. |
| **`canary/`** (Mint & Scanner) | Provided Tier-1/Tier-2 token minting and basic string search. | Fixed doubled-prefix defect (`TRPL-TRPL-`); evaluated encoding limits (honest residual discovery). |
| **`benchmark/`** (M2 Offline Suite) | Contained 86 historical runs across 27 scenarios run in Mode M2 forced-compliance stubs. | Clearly labeled as offline forced-compliance stubs to prevent confusion with real model behavior. |
| **`dashboard/`** (UI Application) | Initial full-stack dashboard prototype. | Rebuilt as a small, truthful, read-only viewer displaying real run artifacts without decorative mock data. |

---

## 2. Core Development Executed During the Window
The substantive engineering that connects Tripline to ArmorIQ and validates the three-layer thesis was conducted entirely between 10–17 October 2026:
1. **Real ArmorIQ Platform Integration:** Authoritative SDK mode calls to `https://api.armoriq.ai/iap/sdk/enforce`.
2. **Real Autonomous LLM Loop:** Live agent processing 5-issue triage queues.
3. **The 3-Attack / 3-Layer Scenario:** Proving upstream platform block (`delete_branch`), jail block (`read_file`), and egress hold (`comment_issue`).
4. **Forensic Verifiability:** Live receipt verification and single-byte cryptographic tamper detection.
5. **Deterministic Path Jail Burst Probe:** 8-vector path-trick containment validation.
