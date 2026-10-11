# Phase 10 — UI Redesign Audit (P0)

**Date**: 2026-10-11  
**Branch**: `ui-redesign` (cut from `brand-logo` @ `d0d45f8`)

## 1. Framework & Build Discovery

| Item | Finding |
|------|---------|
| Framework | Next.js 16.3.3, React 19, TypeScript 5.7.3 |
| Build tool | Next.js with `output: 'export'` (static export to `out/`) |
| Package manager | pnpm 12.3.4 (pnpm-lock.yaml present, node_modules from npm also exists) |
| Entry points | `app/layout.tsx` (root layout), `app/page.tsx` (single-page SPA, 1474 lines) |
| Routing | Client-side hash routing via `useState<TabKey>` — no Next.js file-based routes. Tabs: overview, console, attribution, burst, receipts, witness, measured, evidence, video, claims, platform, about |
| Styling | Tailwind CSS v4.3.3 + tw-animate-css + shadcn. `globals.css` imports `@import 'tailwindcss'`. Custom CSS variables defined inline in `:root`. Most component styling is inline `style={{}}` props |
| State/data | Local `useState` hooks in single page component. No global state management |
| API client | `lib/api.ts` — typed fetch wrapper with CSRF token handling |
| SSE handling | Native `EventSource` in `page.tsx` for job streaming |
| Frontend serving | Static export (`out/`) served by FastAPI via `StaticFiles` mount |
| Dev commands | `npm run dev` / `pnpm dev` (Next.js dev server) |
| Fonts | System fonts only (`ui-sans-serif, system-ui, sans-serif`, `ui-monospace, monospace`). No CDN fonts. **COMPLIANT with R5** |
| Animation libs | tw-animate-css (Tailwind animation plugin). No other animation library |
| UI component lib | shadcn + lucide-react icons, class-variance-authority, clsx, tailwind-merge |
| **R5 concern** | `@vercel/analytics` in package.json — this sends analytics to Vercel. **VIOLATION of R5**. Must be removed |

## 2. Baseline Results

| Check | Result | Notes |
|-------|--------|-------|
| Frontend build | PENDING | Will run with `npm run build` |
| Lint/type-check | `ignoreBuildErrors: true` in next.config.mjs — TS errors suppressed |
| `make test` | PENDING |
| `make ui-test` | PENDING |
| `make ui-coverage` | PENDING |
| `make audit` | PENDING |
| Bundle sizes | PENDING |

## 3. Defect Root Causes

### D1: Receipts page empty list while Overview shows "5 signed receipts"

**Root cause**: Two separate issues.

1. **API source**: `get_all_receipts()` in `repositories.py:276-294` reads ONLY from `results/demo/receipt_*.json`. There are exactly **2 files** there (`receipt_DP-01.json`, `receipt_IE-01.json`). The phase3 receipts (15 files in `results/phase3/scenario/receipt_*.json`) are **never loaded** by this endpoint.

2. **Overview "5" is a hardcoded fallback**: `page.tsx:480` shows `{receipts.length || 5}` — the `|| 5` means when `receipts` hasn't been fetched yet (tab not visited), it shows 5. This is a **fake number violating R1**.

3. The receipts list does render when the API returns data (the 2 demo receipts). But the count disagrees with the hardcoded Overview fallback.

**Fix needed**: Include phase3 receipts in `get_all_receipts()`. Remove all `|| N` fallbacks from Overview counts.

### D2: Jail Burst table empty despite summary showing 8/8

**Root cause**: 

1. The summary (`burst?.total_probes || 8`) uses a **hardcoded fallback** `|| 8`. Same R1 violation.

2. The API endpoint `get_jail_burst()` calls `run_jail_burst()` **live** each time. This function creates a temp sandbox, runs 8 deterministic probes, and returns results. The probes array IS populated when the API is called.

3. The table renders `burst?.probes?.map(...)` — this works when data is fetched. The likely cause of "empty table" in screenshots is that the page was loaded but the API call to `/api/jail-burst` either hasn't completed yet or failed silently (`.catch(() => {})`).

**Probe count**: The script defines exactly **8 test cases**: 6 traversal attacks + 1 symlink escape + 1 positive control. The "24" number from earlier reports refers to the 24-attack benchmark corpus across all arms, which is a different dataset.

### D3: Scenario job failed with exit code 1

**Root cause**: Model deprecation. The job `job-06f0f80c7a7f` (kind: `scenario`) failed because `gemini-2.5-flash` returns HTTP 404: "This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.8-flash."

**Impact**: This is an environment issue (deprecated model), not a Tripline bug. The UI correctly shows the job as `failed` with exit code 1.

**Fix needed**: Show the failed job honestly with exit code, redacted error tail, and cause hint. Do not hide it.

### D4: Attribution says "Regex canary token scanner"

**Root cause**: `dashboard/api.py:286` hardcodes `mechanism="Regex canary token scanner inspects argument payloads"`.

**Actual code** (`canary/scan.py`): Uses **exact substring matching** via `payload_str.find(c.canary_id)` and **path normalization + substring containment** via `intended_norm in path_norm`. No regex is used anywhere in the scanner.

**Fix**: Change all references from "Regex canary token scanner" → "Exact-match canary token scanner (substring search in outbound payloads)".

### D5: UI says "RFC-8785" — is it real JCS?

**CRITICAL FINDING**: **NOT RFC 8785 (JCS)**.

`receipts/verify.py:62`: `json.dumps(evidence_dict, separators=(',', ':'), sort_keys=True)` — This is Python's `json.dumps` with sorted keys and compact separators. RFC 8785 (JCS) requires specific number serialization (no trailing zeros, specific format for floats), specific string escaping, and deterministic Unicode handling. Python's `json.dumps` does NOT implement these.

No RFC 8785 test vector exists in the test suite.

**Fix**: Replace "RFC-8785" everywhere with "canonical JSON (sorted keys, compact separators) + SHA-256, HMAC-SHA256 signed". Files to update:
- `tripline-frontend/app/page.tsx` (lines 481, 897)
- `dashboard/api.py` (lines 302, 1199)
- `docs/phase9_report.md` (line 67)
- `docs/ui_inventory.md` (line 36)

### D6: Hero status shows "local/sdk (SessionOptions mode='sdk')"

**Root cause**: `dashboard/api.py:153` hardcodes `enforcement_mode="local/sdk (SessionOptions mode='sdk')"`. This is not derived from actual evidence.

The evidence from the recorded runs shows ArmorIQ SDK was used with `SessionOptions(mode='sdk')`. In SDK mode, policy decisions are evaluated locally by the ArmorIQ SDK, NOT by the ArmorIQ cloud platform.

**Honest label**: "ArmorIQ SDK local enforcement (mode='sdk')" — because in SDK mode, the SDK evaluates policies locally, it does not call the ArmorIQ cloud service for each decision.

**CRITICAL**: This means decisions are local policy checks, not platform-enforced. The owner should be informed.

### D7: Hero "Replay of active scenario run" — data-driven?

**Root cause**: `page.tsx:260-267` — `currentIncident` falls back to a **hardcoded object** when no run detail is loaded:
```tsx
const currentIncident = currentRunDetail?.records?.[activeIncidentIndex] || {
    issue: 'issue-304 (P2: Path Jail)',
    action: 'read_file(../../fake_home/.ssh/id_rsa)',
    armoriq: 'ALLOW',
    tripline: 'DENY (JAIL)',
    ...
}
```

**Fix**: Remove hardcoded fallback. Show EmptyState or "Illustration" label when no run data is loaded.

### D8: Overview metrics disagree

| Metric | Shown | Source | Actual |
|--------|-------|--------|--------|
| Runs | `{runs.length \|\| 2}` | Fallback 2 | Depends on API |
| Receipts | `{receipts.length \|\| 5}` | Fallback 5 | 2 (demo) or 17 (all) |
| Probes | `8 / 8` (hardcoded) | No API source | 8 (correct number but hardcoded) |

**Fix**: All must come from a single `/api/summary` endpoint. Remove all `|| N` fallbacks.

### D9: Raw ISO timestamps in job table

**Location**: `page.tsx:750` — `{j.started_at || 'unknown'}` renders raw ISO like `2026-10-11T11:05:44.753207+00:00`.

**Fix**: Format as local time with UTC in tooltip.

### D10: Model identifier conflicts

The `.env` may name one provider/model; the recorded run logs may show another. The API returns `llm_provider` and `llm_model` from `detect_provider()` which reads current env vars, not the model used in recorded runs.

**Fix**: Display model from the specific run's evidence, not from current env.

### D11: Footer links

| Footer Link | Target | Resolves? |
|------------|--------|-----------|
| Receipts | `setTab('receipts')` | ✅ |
| Runs | `setTab('overview')` | ✅ (but label says "Runs", navigates to Overview) |
| Boundary | `setTab('attribution')` | ✅ (but label "Boundary" ≠ tab "Attribution") |
| Benchmark data | `setTab('measured')` | ✅ |
| Limitations | `setTab('claims')` | ✅ (but label "Limitations" ≠ tab "Claims") |
| Run Console | `setTab('console')` | ✅ |
| Checklist | `setTab('platform')` | ✅ |

Missing from footer: Evidence, Witness, Jail Burst, Video, About.

### D12: Headline letter-spacing too tight

`globals.css` line 4: `.hero h1` has `letter-spacing:-.06em`. This is extremely tight and causes character collision at large sizes.

**Fix**: Change to `letter-spacing: -0.02em` per the design spec.

## 4. Additional Findings

- **`@vercel/analytics`** in package.json — violates R5 (no external requests). Must be removed.
- **All error handlers** swallow errors silently (`.catch(() => {})`) — no error states shown to user.
- **No mobile nav** — `@media(max-width:800px) .topbar nav{display:none}` hides all navigation on mobile with no hamburger menu.
- **Single 1474-line component** — entire app in one file. Will need to be split for maintainability.
- **Inline styles everywhere** — no consistent design system.
