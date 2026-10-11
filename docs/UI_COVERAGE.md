# Tripline UI ↔ API Two-Way Coverage Matrix

**Phase 9 Automated Verification Matrix**  
**FastAPI Routes**: 50  
**UI Elements Bound**: 30  
**Allowed Exceptions**: 24  

## 1. Route ↔ Page ↔ Element ↔ Test ID Mapping

| Method | Endpoint | UI Element Test ID | Source Component |
|---|---|---|---|
| GET | `/api/attribution` | `attribution-table` | `page.tsx` |
| GET | `/api/audit-links` | `btn-audit-links` | `page.tsx` |
| GET | `/api/claims` | `claims-table` | `page.tsx` |
| GET | `/api/docs` | `btn-list-docs` | `page.tsx` |
| GET | `/api/docs/judge_qa` | `btn-doc-judge-qa` | `page.tsx` |
| GET | `/api/docs/limitations` | `btn-doc-limitations` | `page.tsx` |
| GET | `/api/env` | `btn-inspect-env` | `page.tsx` |
| GET | `/api/evidence` | `evidence-table` | `page.tsx` |
| GET | `/api/evidence/file` | `unlabeled` | `page.tsx` |
| GET | `/api/evidence/file` | `unlabeled` | `page.tsx` |
| GET | `/api/jail-burst` | `btn-refresh-burst` | `page.tsx` |
| POST | `/api/jobs` | `btn-start-job` | `page.tsx` |
| POST | `/api/jobs/{id}/cancel` | `btn-cancel-job` | `page.tsx` |
| GET | `/api/jobs/{job_id}` | `unlabeled` | `page.tsx` |
| GET | `/api/jobs/{job_id}/events` | `unlabeled` | `page.tsx` |
| GET | `/api/measured` | `measured-table` | `page.tsx` |
| GET | `/api/platform-checklist` | `platform-table` | `page.tsx` |
| GET | `/api/receipts` | `btn-refresh-receipts` | `page.tsx` |
| GET | `/api/receipts/{id}` | `unlabeled` | `page.tsx` |
| POST | `/api/receipts/{id}/tamper-check` | `btn-tamper-receipt` | `page.tsx` |
| POST | `/api/receipts/{id}/verify` | `btn-verify-receipt` | `page.tsx` |
| GET | `/api/runs` | `btn-refresh-runs` | `page.tsx` |
| GET | `/api/runs/latest` | `btn-load-latest-run` | `page.tsx` |
| GET | `/api/runs/{run_id}` | `select-active-run` | `page.tsx` |
| GET | `/api/runs/{run_id}/transcript` | `btn-view-run-transcript` | `page.tsx` |
| GET | `/api/video` | `demo-video-player` | `page.tsx` |
| GET | `/api/video` | `btn-download-video` | `page.tsx` |
| GET | `/api/witness` | `witness-logs-table` | `page.tsx` |
| POST | `/api/witness/tamper-check` | `btn-tamper-witness` | `page.tsx` |
| POST | `/api/witness/verify` | `btn-verify-witness` | `page.tsx` |

## 2. Allowed Route Exceptions

| Route | Reason |
|---|---|
| `/` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/about` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/boundary` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/canary-hits` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/csrf-token` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/api/demo-data` | Documented protocol / background route in `docs/coverage_exceptions.md` |
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
| `/api/witness/{trace_id}` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/attribution` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/boundary` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/measured` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/receipts` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/receipts/{identifier}` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/runs/{run_id}` | Documented protocol / background route in `docs/coverage_exceptions.md` |
| `/scoreboard` | Documented protocol / background route in `docs/coverage_exceptions.md` |
