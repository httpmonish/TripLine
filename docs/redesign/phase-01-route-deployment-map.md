# Phase 1 Deliverable 2: Route and Deployment Truth Map

**Project:** TripLine  
**Repository:** `https://github.com/httpmonish/TripLine`  
**Working Branch:** `agent-v2`  
**Auditor:** Principal AI Solution Architect & Deployment Auditor  
**Standard:** Empirical Verification via Source Inspection & Runtime TestClient (Rules 3.1–3.4)  
**Date:** 2026-10-17  

---

## 1. Executive Summary & Serving Architecture

The TripLine serving architecture exhibits an empirical **"dual-router split"** between:
1. **The Modern Next.js 16 Static Export:** Compiled from `tripline-frontend/app/` into `tripline-frontend/out/` (14 static HTML pages and `_next/` chunk directories).
2. **The Legacy Server-Rendered Jinja2 Router:** Defined in `dashboard/routes.py` and mounted in `dashboard/app.py` for backward compatibility with early automated test suites (`tests/test_phase10_dashboard.py`).

Because FastAPI evaluates route matches in the order of registration in `dashboard/app.py`, any route defined in `legacy_router` takes precedence over the dynamic `{slug}` fallback that serves Next.js exported pages. This creates severe route collisions where visitors to `/receipts`, `/measured`, `/attribution`, and `/about` receive the old 2026-10-10 server-rendered templates, while visitors to `/`, `/agent`, `/overview`, `/witness`, `/console`, `/jail-burst`, `/claims`, and `/layers` receive the Next.js frontend.

```
                             [ INCOMING HTTP REQUEST ]
                                         │
                                         ▼
                                  FastAPI (app.py)
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
        Matches `/api/...` ?                           Matches `/` ?
        [ YES: api_router ]                            [ YES: serve_root() ]
                 │                                               │
                 ▼                                               ▼
         API Endpoints                                Next.js out/index.html
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         │ NO MATCH
                                         ▼
                            Matches `legacy_router` ?
                 (routes.py: /receipts, /attribution, /measured, /about)
                                         │
                    ┌────────────────────┴────────────────────┐
                    │ YES                                     │ NO
                    ▼                                         ▼
         Jinja2 Templates                        Matches Next.js Static Asset ?
      (templates/receipts.html,                  (/_next, /static, or /{slug})
       attribution.html, etc.)                                │
                                                 ┌────────────┴────────────┐
                                                 │ YES                     │ NO
                                                 ▼                         ▼
                                        Next.js HTML / JS Chunks       HTTP 404
                                         (out/agent.html, etc.)
```

---

## 2. Complete Serving Path Trace

### 2.1 Next.js Static Export Configuration
- **File:** `tripline-frontend/next.config.mjs`
  ```javascript
  const nextConfig = {
    output: 'export',
    typescript: { ignoreBuildErrors: true },
    images: { unoptimized: true },
  }
  ```
- **Build Command:** `npm run build --prefix tripline-frontend`
- **Output Directory:** `tripline-frontend/out/`
- **Exported HTML Artifacts:**
  - `index.html`, `agent.html`, `overview.html`, `receipts.html`, `witness.html`, `console.html`, `jail-burst.html`, `measured.html`, `claims.html`, `layers.html`, `attribution.html`, `style-guide.html`, `404.html`, `_not-found.html`.
- **Status of `out/`:** Freshly regenerated on `agent-v2`.

### 2.2 FastAPI Registration Order (`dashboard/app.py`)
1. **Line 53:** `app.include_router(api_router)` — Handles all `/api/*` endpoints.
2. **Line 56:** `@app.get("/")` — Checks for `FRONTEND_OUT / "index.html"`. If found, returns the Next.js single-page application.
3. **Line 71:** `app.include_router(legacy_router)` — **INTERCEPT POINT**: Registers `/attribution`, `/receipts`, `/receipts/{id}`, `/runs/{id}`, `/boundary`, `/scoreboard`, `/measured`, `/about`.
4. **Line 77:** `app.mount("/_next", StaticFiles(directory=str(next_static_dir)))` — Serves Turbopack JS/CSS chunks.
5. **Line 82:** `app.mount("/static", StaticFiles(directory=str(static_dir)))` — Serves legacy static assets.
6. **Line 88:** `@app.get("/{slug}")` — Fallback serving `FRONTEND_OUT / f"{slug}.html"`. Only reached if not matched by steps 1–3!

---

## 3. Authoritative Route Resolution Matrix

Every route was tested live against `dashboard.app:app` using Python `fastapi.testclient.TestClient`.

| URL & Method | Expected Design Destination | Actual Registered Handler | Status Code & Content-Type | Rendered UI Layer | Data Source | Collision / Defect |
|---|---|---|---|---|---|---|
| `GET /` | Next.js Homepage | `dashboard/app.py:serve_root` | `200 text/html` | **Next.js 16** (`out/index.html`) | Client-side `/api/summary`, `/api/env` | None. Serves intended Next.js homepage. |
| `GET /agent` | Next.js Agent Console | `dashboard/app.py:serve_frontend_page` | `200 text/html` | **Next.js 16** (`out/agent.html`) | `/api/agent/crew`, `/api/agent/runs`, SSE | None. Modern Agent Crew UI loads properly. |
| `GET /overview` | Next.js System Overview | `dashboard/app.py:serve_frontend_page` | `200 text/html` | **Next.js 16** (`out/overview.html`) | `/api/summary`, `/api/health`, `/api/env` | None. Modern overview loads cleanly. |
| `GET /receipts` | Next.js Receipts Explorer | `dashboard/routes.py:receipts_list_view` | `200 text/html` | **Legacy Jinja2** (`templates/receipts.html`) | `DashboardRepository.get_phase3_receipts()` | **CRITICAL COLLISION**: Intercepted by `legacy_router`. Ignores modern `out/receipts.html`. |
| `GET /receipts/{id}` | Receipt Forensic Detail | `dashboard/routes.py:receipt_detail_view` | `200 text/html` | **Legacy Jinja2** (`templates/receipt.html`) | `DashboardRepository.get_receipt()` | Intended server-side Jinja2 verification view. |
| `GET /witness` | Next.js Witness Explorer | `dashboard/app.py:serve_frontend_page` | `200 text/html` | **Next.js 16** (`out/witness.html`) | `/api/witness`, `/api/witness/verify` | None. Modern witness view loads properly. |
| `GET /console` | Next.js Interactive Console | `dashboard/app.py:serve_frontend_page` | `200 text/html` | **Next.js 16** (`out/console.html`) | `/api/jobs`, `/api/jobs/{id}/events` | None. Modern job runner loads properly. |
| `GET /jail-burst` | Next.js Jail Burst Fuzzer | `dashboard/app.py:serve_frontend_page` | `200 text/html` | **Next.js 16** (`out/jail-burst.html`) | `/api/jail-burst` | None. Modern jail burst loads properly. |
| `GET /measured` | Next.js Benchmark View | `dashboard/routes.py:measured_view` | `200 text/html` | **Legacy Jinja2** (`templates/measured.html`) | Empty Jinja template context | **CRITICAL COLLISION**: Intercepted by `legacy_router`. Ignores modern `out/measured.html`. |
| `GET /claims` | Next.js Claims Ledger | `dashboard/app.py:serve_frontend_page` | `200 text/html` | **Next.js 16** (`out/claims.html`) | `/api/claims` | None. Modern claims ledger loads properly. |
| `GET /layers` | Next.js Attribution Matrix | `dashboard/app.py:serve_frontend_page` | `200 text/html` | **Next.js 16** (`out/layers.html`) | `/api/attribution` | None. Modern layers view loads properly. |
| `GET /attribution` | Next.js Attribution View | `dashboard/routes.py:attribution_view` | `200 text/html` | **Legacy Jinja2** (`templates/attribution.html`) | `DashboardRepository.get_burst_results()` | **CRITICAL COLLISION**: Intercepted by `legacy_router`. |
| `GET /about` | Next.js About Page | `dashboard/routes.py:about_view` | `200 text/html` | **Legacy Jinja2** (`templates/about.html`) | Legacy template context | Legacy server-rendered page. No Next.js equivalent currently exists. |
| `GET /api/health` | JSON Health Endpoint | `dashboard/api.py:get_health` | `200 application/json` | REST API | Local git subprocess check | None. Verified runtime 200. |
| `GET /api/env` | Environment Config | `dashboard/api.py:get_env_info` | `200 application/json` | REST API | Redacted os.environ check | None. Verified runtime 200. |
| `GET /api/platform/status` | ArmorIQ Status | `dashboard/api.py:get_platform_status` | `200 application/json` | REST API | Mode B status & cred existence | None. Verified runtime 200. |
| `GET /api/agent/crew` | Crew Manifest | `dashboard/api.py:get_agent_crew` | `200 application/json` | REST API | `agent/crew.py` Ed25519 keys | None. Verified runtime 200. |
| `GET /api/agent/runs` | Agent Runs List | `dashboard/api.py:list_agent_runs` | `200 application/json` | REST API | `results/phase11/` manifests | None. Verified runtime 200. |
| `GET /api/jobs` | Job Runner List | `dashboard/api.py:list_jobs` | `200 application/json` | REST API | `results/ui_jobs/` records | None. Verified runtime 200. |
| `GET /api/receipts` | Receipts JSON List | `dashboard/api.py:list_receipts` | `200 application/json` | REST API | Scans all `results/` receipt files | None. Verified runtime 200. |

---

## 4. Diagnostic Inquiries & Root-Cause Findings

### 4.1 Why Does `/receipts` Serve the Legacy Jinja Template?
- **Root Cause:** In `tests/test_phase10_dashboard.py:14-18`:
  ```python
  def test_2_receipt_list_loads():
      response = client.get("/receipts")
      assert response.status_code == 200
      assert "Incident Receipts" in response.text
  ```
  The test asserts that the exact string `"Incident Receipts"` is in the HTML returned by `/receipts`. In the legacy Jinja template `dashboard/templates/receipts.html`, the header is literally `<h1>Incident Receipts</h1>`.
  Because `legacy_router` was mounted before the Next.js static page handler, FastAPI always matches `routes.py:receipts_list_view` first. As a result, the user never sees `tripline-frontend/app/receipts/page.tsx` when navigating directly to `/receipts`.

### 4.2 Why Does `/measured` Show Legacy Content?
- **Root Cause:** `dashboard/routes.py:175` explicitly defines `@router.get("/measured")` returning `templates.TemplateResponse("measured.html")`. This intercepts `/measured` before `serve_frontend_page("measured")` in `app.py:88` can serve `out/measured.html`.

### 4.3 Why Does `/attribution` Show Legacy Content?
- **Root Cause:** `dashboard/routes.py:47` defines `@router.get("/attribution")`. Next.js has two routes: `/attribution` and `/layers`. When navigating to `/layers`, the Next.js page displays. When navigating to `/attribution`, the legacy Jinja template displays.

### 4.4 How Are Static JavaScript, CSS, Fonts, and Logos Resolved?
- **Next.js Chunks:** Handled by `app.mount("/_next", StaticFiles(directory=str(FRONTEND_OUT / "_next")))`. All JS bundles and CSS (`1z8r66gxmml63.css`) resolve with HTTP 200.
- **Brand Logos & SVGs:** Root mount `app.mount("/", StaticFiles(directory=str(FRONTEND_OUT), html=False))` resolves `/tripline-favicon.svg`, `/tripline-lockup-on-dark.svg`, and `/tripline-lockup-on-light.svg`.
- **Fonts:** Geist Sans and Geist Mono are embedded via Next.js Font Optimization in `/_next/static/media/geist-s.p.*.woff2`.

---

## 5. Route Consolidation Strategy (Phase 4 Plan)

To eliminate the dual-router split without breaking existing backward-compatibility tests:

1. **Option A (URL Path Segregation - Recommended):**
   - Remap legacy Jinja routes to `/legacy/receipts`, `/legacy/measured`, `/legacy/attribution`.
   - Update `dashboard/app.py` so that `@app.get("/{slug}")` executes **before** `legacy_router`, or selectively delegate `/receipts` to Next.js while ensuring `out/receipts.html` contains the required compatibility string `"Incident Receipts"`.
2. **Option B (Header-Aware Routing):**
   - If the request includes `Accept: text/html` from a browser, serve the Next.js static export. If called by test fixture without browser headers or on a legacy query parameter `?legacy=true`, serve Jinja.
3. **Execution Decision:**
   - In Phase 1, make **no changes** to route registration to preserve test baselines.
   - In Phase 4 (Route Consolidation & Navigation), unify all public routes to point exclusively to the authoritative Next.js enterprise frontend while maintaining test compatibility.
