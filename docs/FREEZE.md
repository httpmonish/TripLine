# Tripline Hackathon Submission Freeze Manifest

**Competition**: ArmorIQ "Flow State 2026" Hackathon  
**Target Submission Date**: 16 Oct 2026  
**Status**: PENDING OWNER FREEZE APPROVAL  

---

## 1. Freeze Notice & Policy

Once this repository is frozen and tagged as `submission-v1`:
1. **Zero New Features**: No modifications may be made to any code, policy, receipt, or documentation files.
2. **Post-Submission Edit Rule**: The organizers' policy regarding post-submission repository commits is **UNVERIFIED**. Modifying the repository after submission carries a significant risk of disqualification under Rule 10 or being evaluated on broken interim states. The safest path is to freeze completely upon submission.
3. **Emergency Fix Procedure**: If a disqualifying submission defect is discovered prior to the 17 Oct 23:59 IST deadline, any change requires re-running the entire verification suite:
   - `make test`
   - `make verify && make tamper`
   - `make audit`
   - Fresh-clone reproduction test in a clean environment.

---

## 2. Frozen File Manifest

The following core artifacts represent the evaluated submission baseline and **must not change** after tagging:

| Component | Path / Directory | Purpose |
|---|---|---|
| **Upstream Enforcement** | `scripts/armoriq_proof.py` | Live ArmorIQ enforcement proof harness |
| **Agent Implementation** | `agent/triage_agent.py` | Real Claude 3.5 Sonnet autonomous triage agent |
| **MCP Execution Boundary** | `mcp/` | In-MCP filesystem jail, path validator, witness logger |
| **Canary Exfiltration Gateway** | `canary/gateway.py` | Outbound payload token inspector |
| **Receipt Verification** | `receipts/models.py`, `receipts/verify.py` | Canonical JSON and HMAC-SHA256 signature verifier |
| **Offline Judge Portal** | `dashboard/app.py`, `dashboard/routes.py` | Read-only server-rendered inspection dashboard |
| **Measured Evidence** | `results/phase3/` | Scenario receipts, measured Claude runs, logs |
| **Demo Video Deliverable** | `video/out/tripline_demo_90s.mp4` | 86.0s compliant demo video (SHA-256: `1664b214...`) |
| **Submissions & Documentation** | `README.md`, `docs/SUBMISSION_FINAL.md` | Authoritative public documentation and pitch packet |

---

## 3. Tagging Instructions

Upon the owner's explicit confirmation (`"FREEZE APPROVED"`):
1. The repository commit will be tagged with local annotated tag `submission-v1`:
   ```bash
   git tag -a submission-v1 -m "Tripline frozen for hackathon submission (ArmorIQ Flow State 2026)"
   ```
2. The owner pushes the tag along with `main` to GitHub:
   ```bash
   git push origin main
   git push origin submission-v1
   ```
