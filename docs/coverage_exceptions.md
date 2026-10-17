# Tripline UI / API Coverage Exceptions

This document contains explicit allowlisted exemptions from the two-way UI-API coverage test (`scripts/ui_api_coverage.py`), as mandated by Phase 9 Section 6.1.

| Method | Route | Reason |
|---|---|---|
| GET | `/api/csrf-token` | Internal security token fetched automatically by API client interceptor before POST requests. |
| GET | `/api/openapi.json` | Programmatic schema endpoint for API introspection and tooling. |
| GET | `/api/summary` | Legacy compatibility endpoint preserved for backward compatibility. |
| GET | `/api/demo-data` | Legacy compatibility endpoint preserved for backward compatibility. |
| GET | `/api/video/captions` | Static SRT caption track referenced directly by `<track src="/api/video/captions">`. |
| GET | `/api/health` | Background heartbeat and preflight verification probe; consumed by topbar status indicator. |
| GET | `/` | Root static Next.js single-page application mount point. |
| GET | `/about` | Legacy Jinja HTML view preserved on backward compatibility router. |
| GET | `/attribution` | Legacy Jinja HTML view preserved on backward compatibility router. |
| GET | `/boundary` | Legacy Jinja HTML view preserved on backward compatibility router. |
| GET | `/measured` | Legacy Jinja HTML view preserved on backward compatibility router. |
| GET | `/receipts` | Legacy Jinja HTML view preserved on backward compatibility router. |
| GET | `/receipts/{identifier}` | Legacy Jinja HTML view preserved on backward compatibility router. |
| GET | `/runs/{run_id}` | Legacy Jinja HTML view preserved on backward compatibility router. |
| GET | `/scoreboard` | Legacy Jinja HTML view preserved on backward compatibility router. |
| POST | `/api/receipts/{filename}/verify-tampered` | Legacy Phase 4 tamper verification endpoint preserved for backward compatibility tests. |
| GET | `/api/events` | Legacy Phase 8 endpoint preserved for backward compatibility and test suites. |
| GET | `/api/scoreboard` | Legacy Phase 8 endpoint preserved for backward compatibility and test suites. |
| GET | `/api/boundary` | Legacy Phase 8 endpoint preserved for backward compatibility and test suites. |
| GET | `/api/limitations` | Legacy Phase 8 endpoint preserved for backward compatibility and test suites. |
| GET | `/api/status` | Legacy Phase 8 endpoint preserved for backward compatibility and test suites. |
| GET | `/api/canary-hits` | Legacy Phase 8 endpoint preserved for backward compatibility and test suites. |
| GET | `/api/witness/{trace_id}` | Legacy Phase 8 endpoint preserved for backward compatibility and test suites. |
| GET | `/api/receipts/{identifier}/verify` | Legacy Phase 8 verification GET endpoint preserved for backward compatibility. |
| POST | `/api/agent/task` | Direct dynamic task dispatch endpoint mirroring /api/agent/runs. |
