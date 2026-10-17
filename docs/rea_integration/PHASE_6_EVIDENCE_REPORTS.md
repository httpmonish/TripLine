# Phase 6 — Evidence-Backed Investigation Reports

**Date:** 2026-10-17  
**Module:** `agent/rea_report.py`  
**Core Function:** `build_investigation_report`  

---

## 1. Objective and Design

Rather than presenting raw JSON dumps or fabricated conclusions, TripLine generates structured technical reports where every claim is supported by retained Evidence IDs from REA.

The report distinguishes:
1. **Observed Facts:** Verified counts, observed BrowserWindow instances, IPC channels, and module topologies with specific Evidence IDs (`ev_...`).
2. **Inferences:** Deductions grounded directly in observed facts (e.g. inferred Electron IPC flow).
3. **Hypotheses:** Unproven possibilities requiring dynamic instrumentation or manual verification.
4. **Security Warnings:** Prompt-injection attempts found inside source code or comments.
5. **Limitations:** Known boundaries of static analysis (e.g. inability to observe dynamic runtime `eval` or remote network responses).
6. **Governance Status:** ArmorIQ decision status, dispatch status, and verification mode (`LIVE_VERIFIED` vs `TEST_VERIFIED`).

---

## 2. Sample Report Structure

```markdown
# TripLine REA Investigation Report: synthetic_electron_app
**Run ID:** `run_rea_demo_01`  
**Target ID:** `synthetic-electron-app`  
**Verification Status:** `LIVE_VERIFIED`  
**ArmorIQ Authorization:** `ALLOW`  
**Dispatch Status:** `EXECUTED`  

---
## 1. Executive Summary & Architecture Overview
[JSON Summary of relevant files, modules, and Electron BrowserWindow instances]

## 2. Observed Facts (Backed by Cryptographic Evidence)
- **[Structure]** Application components: 5 relevant files, 3 parsed JS modules (Evidence: `ev_acb647...`)
- **[Electron]** Electron framework observed with 1 BrowserWindow instances (Evidence: `ev_acb647...`)

## 3. Feature Trace Findings
- **Seed:** `main.js` (Direction: `both`)
  - Trace relationships: module topologies and IPC endpoints

## 4. Inferences & Hypotheses
### Inferences
- Target uses Electron IPC architecture for main-to-renderer communication.
### Hypotheses
- Potential IPC token validation behavior under invalid parameters.

## 5. Security & Untrusted Content Notice
[Security notice regarding passive untrusted source content]

## 6. Technical Limitations & Gaps
- Static analysis does not execute application code or observe runtime dynamic imports.

## 7. Retained Evidence References
- `ev_acb647be9cb771a130b7c829ee0b348f5a9f10fb4347094a3e6b7367734ea6be`
- `ev_ae74432661dd948a53dc33b5a54fa063a591625fe700ab5a652c6c9a57110576`
```

---

## 3. Acceptance Criteria Verification

- [x] **Useful with Partial Evidence:** Generates honest summaries even when only summary or trace operations are available.
- [x] **No Fabricated Evidence:** Claims link directly to actual REA Evidence IDs.
- [x] **Clear Limitations Section:** Explicitly notes what static analysis could not observe.
