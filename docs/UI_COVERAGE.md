# Tripline UI ↔ API Two-Way Coverage Matrix

**Phase 9 Automated Verification Matrix**  
**FastAPI Routes**: 67  
**UI Elements Bound**: 51  
**Allowed Exceptions**: 31  

## 1. Route ↔ Page ↔ Element ↔ Test ID Mapping

| Method | Endpoint | UI Element Test ID | Source Component |
|---|---|---|---|
| GET | `/api/agent/crew` | `anchor-agent-crew` | `page.tsx` |
| GET | `/api/agent/runs` | `anchor-agent-runs` | `page.tsx` |
| POST | `/api/agent/runs` | `anchor-agent-runs-post` | `page.tsx` |
| POST | `/api/agent/runs` | `btn-start-agent-run` | `page.tsx` |
| POST | `/api/agent/runs/{id}/stop` | `unlabeled` | `page.tsx` |
| GET | `/api/agent/runs/{run_id}` | `anchor-agent-run-id` | `page.tsx` |
| GET | `/api/agent/runs/{run_id}` | `unlabeled` | `page.tsx` |
| GET | `/api/agent/runs/{run_id}/events` | `anchor-agent-run-events` | `page.tsx` |
| POST | `/api/agent/runs/{run_id}/stop` | `anchor-agent-runs-stop` | `page.tsx` |
| GET | `/api/attribution` | `anchor-attribution` | `page.tsx` |
| GET | `/api/audit-links` | `btn-audit-links` | `page.tsx` |
| GET | `/api/claims` | `anchor-video` | `page.tsx` |
| GET | `/api/docs` | `btn-list-docs` | `page.tsx` |
| GET | `/api/docs/{name}` | `anchor-doc-name` | `page.tsx` |
| GET | `/api/env` | `btn-inspect-env` | `page.tsx` |
| GET | `/api/evidence` | `anchor-evidence` | `page.tsx` |
| GET | `/api/evidence/file` | `anchor-evidence-file` | `page.tsx` |
| GET | `/api/glossary` | `anchor-glossary` | `page.tsx` |
| GET | `/api/jail-burst` | `btn-refresh-burst` | `page.tsx` |
| GET | `/api/jobs` | `btn-refresh-jobs` | `page.tsx` |
| POST | `/api/jobs` | `btn-start-job` | `page.tsx` |
| POST | `/api/jobs` | `unlabeled` | `page.tsx` |
| POST | `/api/jobs` | `unlabeled` | `page.tsx` |
| POST | `/api/jobs/{id}/cancel` | `btn-cancel-job` | `page.tsx` |
| POST | `/api/jobs/{id}/cancel` | `unlabeled` | `page.tsx` |
| GET | `/api/jobs/{job_id}` | `anchor-job-id` | `page.tsx` |
| GET | `/api/jobs/{job_id}/events` | `anchor-job-events` | `page.tsx` |
| GET | `/api/measured` | `anchor-measured` | `page.tsx` |
| GET | `/api/platform-checklist` | `anchor-platform` | `page.tsx` |
| GET | `/api/platform/status` | `anchor-platform-status` | `page.tsx` |
| GET | `/api/rea/investigations` | `anchor-rea-investigations` | `page.tsx` |
| GET | `/api/rea/investigations/{run_id}` | `anchor-rea-investigation-id` | `page.tsx` |
| GET | `/api/rea/targets` | `anchor-rea-targets` | `page.tsx` |
| GET | `/api/receipts` | `btn-refresh-receipts` | `page.tsx` |
| GET | `/api/receipts` | `btn-refresh-receipts` | `page.tsx` |
| GET | `/api/receipts/{identifier}` | `anchor-receipt-id` | `page.tsx` |
| POST | `/api/receipts/{identifier}/tamper-check` | `btn-tamper-receipt` | `page.tsx` |
| POST | `/api/receipts/{identifier}/verify` | `btn-verify-receipt` | `page.tsx` |
| POST | `/api/receipts/{id}/verify` | `unlabeled` | `page.tsx` |
| GET | `/api/runs` | `btn-refresh-runs` | `page.tsx` |
| GET | `/api/runs/latest` | `btn-load-latest-run` | `page.tsx` |
| GET | `/api/runs/{run_id}` | `btn-list-docs` | `page.tsx` |
| GET | `/api/runs/{run_id}/transcript` | `btn-view-run-transcript` | `page.tsx` |
| GET | `/api/summary` | `anchor-summary` | `page.tsx` |
| GET | `/api/video` | `anchor-video` | `page.tsx` |
| GET | `/api/witness` | `anchor-witness` | `page.tsx` |
| GET | `/api/witness` | `btn-witness` | `page.tsx` |
| POST | `/api/witness/tamper-check` | `btn-tamper-witness` | `page.tsx` |
| POST | `/api/witness/tamper-check` | `btn-tamper-witness` | `page.tsx` |
| POST | `/api/witness/verify` | `btn-verify-witness` | `page.tsx` |
| POST | `/api/witness/verify` | `btn-verify-witness` | `page.tsx` |

## 2. Allowed Route Exceptions

| Route | Reason |
|---|---|
| `/` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/about` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/agent/task` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/boundary` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/canary-hits` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/csrf-token` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/demo-data` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/demo/analyze-credential-file` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/demo/chat` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/events` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/health` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/limitations` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/openapi.json` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/receipts/{filename}/verify-tampered` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/receipts/{identifier}/verify` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/scoreboard` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/status` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/summary` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/video/captions` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/volunteer/applications/{application_id}` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/volunteer/media-preview` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/volunteer/portal` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/volunteer/stats` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/witness/{trace_id}` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/attribution` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/boundary` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/measured` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/receipts` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/receipts/{identifier}` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/runs/{run_id}` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/scoreboard` | Documented protocol / background route in `docs/coverage_exceptions.md` |
