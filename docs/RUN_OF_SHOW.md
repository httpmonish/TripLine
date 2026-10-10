# Submission Run-of-Show & Deployment Timeline

**Competition**: ArmorIQ "Flow State 2026" Hackathon  
**Owner Timezone**: Asia/Calcutta (UTC+05:30)  
**Submission Target**: 16 Oct 2026 (Hard Close: 17 Oct 2026 23:59 IST)  
**Branch**: `phase7-final`  
**Repository**: `https://github.com/httpmonish/TripLine.git`  

---

## 1. Timeline & Operational Runbook

### Day 1: Wednesday, 15 Oct 2026 (Audit, Verification & Media Review)

| Time (IST) | Task / Milestone | Responsible | Est. Duration | Go / No-Go Gate |
|---|---|---|---|---|
| **10:00** | Review Phase 7 report and `docs/FINAL_CLAIMS_AUDIT.md`. | Owner | 30 min | **Gate 1**: Zero FAILED claims; all residual limits understood. |
| **11:00** | Log into `platform.armoriq.ai`: confirm agent, MCP, and policies active. Capture Audit Log screenshot to `docs/evidence/phase7/armoriq_audit_screenshot.png`. | Owner | 20 min | **Gate 2**: Platform onboarding verified with live screenshot. |
| **14:00** | Watch `video/out/tripline_demo_90s.mp4` end-to-end on two separate devices (e.g., Mac + phone), both with sound and muted. | Owner | 15 min | **Gate 3**: Captions readable, audio track plays cleanly, duration ≤ 90s. |
| **16:00** | Reply `"FREEZE APPROVED"` to create local freeze tag `submission-v1`. | Owner | 5 min | **Gate 4**: Working tree clean; freeze manifest signed off. |
| **18:00** | Upload `video/out/tripline_demo_90s.mp4` to YouTube (Unlisted) or Loom / Google Drive. Verify link opens in an incognito window. | Owner | 20 min | **Gate 5**: Public video streaming link operational. |

---

### Day 2: Thursday, 16 Oct 2026 (Submission Day)

| Time (IST) | Task / Milestone | Responsible | Est. Duration | Go / No-Go Gate |
|---|---|---|---|---|
| **09:30** | Check hackathon Discord / announcement channel for last-minute sponsor addenda or portal guidelines. | Owner | 15 min | **Gate 6**: No unexpected sponsor constraints. |
| **10:30** | Run fresh-clone smoke test on a clean directory: `make verify && make tamper && make audit`. | Owner | 10 min | **Gate 7**: 100% checks pass on clean clone. |
| **11:30** | Execute Git Push commands to publish `phase7-final` and tag `submission-v1` to GitHub. | Owner | 10 min | **Gate 8**: Remote repository reflects exact frozen commit. |
| **12:00** | Confirm repository visibility (make repo **Public** per hackathon rules). Confirm GitHub README renders cleanly. | Owner | 10 min | **Gate 9**: Public clone works without authentication. |
| **14:00** | Open submission portal. Use `docs/FORM_MAP.md` and `docs/SUBMISSION_FINAL.md` to paste all fields. | Owner | 30 min | **Gate 10**: All required fields populated; video URL verified. |
| **15:00** | Submit entry on portal. Take full-page screenshot of submission confirmation page. Save image locally to `docs/evidence/phase7/submission_confirmation.png` (do not commit if it contains personal phone/PII). | Owner | 10 min | **Gate 11**: Official portal confirmation timestamped. |
| **16:00** | Stand down. Repo enters freeze state. | Owner | — | Submissions complete 30 hours ahead of hard close. |

---

### Day 3: Friday, 17 Oct 2026 (Buffer Day)

| Time (IST) | Task / Milestone | Responsible | Est. Duration | Notes |
|---|---|---|---|---|
| **All Day** | Emergency buffer only. Hard freeze in effect. | Owner | — | **No code edits** unless a disqualifying submission defect is discovered. |
| **23:59** | Hackathon portal closes permanently. | Organizers | — | Results announced 22 Oct 2026. |

---

## 2. Git Merge & Push Commands for Owner

Execute these commands in your local `tripline/` terminal to merge and publish to GitHub:

```bash
# 1. Switch to your main branch
git checkout main

# 2. Merge the frozen phase7-final branch cleanly
git merge --ff-only phase7-final

# 3. Verify status and commit history
git status -sb
git log --oneline -5

# 4. Push main and the annotated submission tag to GitHub
git push origin main
git push origin submission-v1

# 5. Push the phase7-final branch for traceability
git push origin phase7-final
```

> **Post-Push Check**:
> Open `https://github.com/httpmonish/TripLine` in your browser. Confirm:
> 1. README is displayed with correct shields and architecture diagrams.
> 2. The `submission-v1` tag is visible under Releases / Tags.
> 3. Repository Settings -> Change visibility to **Public**.
