# Tripline Backend Inventory

**Phase 9 Preflight Discovery: Repository Capabilities & Entry Points**  
**Repository**: Tripline (`httpmonish/TripLine`)  
**Branch**: `phase9-ui`  
**Generated**: 2026-10-11  

---

## 1. Capabilities Matrix

| Identifier | Type | Function / Command | Inputs | Outputs & File Locations | Cost / Side Effects | Live or Offline | Safe from UI Button? | Proposed Route / Action |
|---|---|---|---|---|---|---|---|---|
| **CAP-01** | Make Target | `make test` | None | Test summary to stdout | CPU; runs local test suite | Offline (unit tests) | Yes | `POST /api/jobs` (`tests`) |
| **CAP-02** | Make Target | `make test-armoriq` | Live ArmorIQ API key | Output to stdout | ArmorIQ API calls | Live | No (runs in terminal/CI) | N/A (documented) |
| **CAP-03** | Make Target | `make audit` | None | Truth/hygiene report | CPU; scans working tree | Offline | Yes | `POST /api/jobs` (`audit`) |
| **CAP-04** | Make Target | `make wow` | None | Runs scenario, burst, verify, links, tamper | Creates scenario run logs, receipts | Deterministic / offline rung 0 | Yes | `POST /api/jobs` (`scenario` / `verify_all`) |
| **CAP-05** | Make Target | `make verify` | `FILE=<path>` | Verification status | Read-only | Offline | Yes | `POST /api/receipts/{id}/verify` |
| **CAP-06** | Make Target | `make tamper` | None | Tamper demo report | Reads files, tests copies | Offline | Yes | `POST /api/jobs` (`tamper_demo`) |
| **CAP-07** | Make Target | `make burst` | None | Jail burst probe table | Writes burst results | Deterministic / offline | Yes | `POST /api/jobs` (`jail_burst`) |
| **CAP-08** | Make Target | `make demo` | Mock/Live fixtures | Demo logs & receipts in `results/demo/` | Resets demo repo, runs attacks | Offline stubs / Live | No (standalone terminal run) | Historical data displayed |
| **CAP-09** | Make Target | `make explain` | `results/demo/events.jsonl` | Formatted timeline to stdout | Read-only | Offline | Yes | UI Events viewer |
| **CAP-10** | Make Target | `make video` | Storyboard & captures | `video/out/tripline_demo_90s.mp4` | CPU intensive (rendering) | Offline | No | `GET /api/video` (serve built) |
| **CAP-11** | Script | `scripts/jail_burst.py` | None | Probe table stdout | Deterministic | Offline | Yes | `POST /api/jobs` (`jail_burst`) & `GET /api/jail-burst` |
| **CAP-12** | Script | `scripts/tamper_demo.py` | None | Tamper demonstration report | Temp files created & deleted | Offline | Yes | `POST /api/jobs` (`tamper_demo`) |
| **CAP-13** | Script | `scripts/verify_links.py` | `results/phase3/armoriq_links.jsonl` | Chain verification stdout | Read-only | Offline | Yes | `GET /api/audit-links` |
| **CAP-14** | Script | `scripts/armoriq_proof.py` | ArmorIQ credentials | Verification output | Live API calls to ArmorIQ | Live | Yes (with confirm token) | `POST /api/jobs` (`armoriq_proof`) |
| **CAP-15** | Script | `scripts/run_phase3_scenario.py` | `--rung <0-4>` | `results/phase3/scenario/*.jsonl` | Creates new run logs & receipts | Rung 0 (offline) / Rung 1-4 (live) | Yes (Rung 0 default; live guarded) | `POST /api/jobs` (`scenario`) |
| **CAP-16** | Script | `scripts/number_check.py` | None | Number audit stdout | Read-only | Offline | Yes | Checked via `make audit` |
| **CAP-17** | Module | `receipts.verify` | Raw receipt dict / JSON | `(bool, str)` verification tuple | Read-only | Offline | Yes | `POST /api/receipts/{id}/verify` |
| **CAP-18** | Module | `witness.reconcile` | Witness `.jsonl` path | `(bool, reason)` chain verification | Read-only | Offline | Yes | `POST /api/witness/verify` |
| **CAP-19** | Module | `canary.scan` | String payload | Detected canary tokens list | Read-only | Offline | Yes | Internal to gateway & jobs |
| **CAP-20** | Evidence | `results/demo/*.json` | File paths | Signed incident receipts | Read-only | Offline | Yes | `GET /api/receipts` |
| **CAP-21** | Evidence | `results/demo/events.jsonl` | File path | Forensic timeline events | Read-only | Offline | Yes | `GET /api/runs/{id}` |
| **CAP-22** | Evidence | `results/phase3/measured/*` | File path | Statistical measured runs | Read-only | Offline | Yes | `GET /api/measured` |
| **CAP-23** | Evidence | `docs/evidence/**` | File path | Raw API capture JSON/text | Read-only | Offline | Yes | `GET /api/evidence` |
| **CAP-24** | Video | `video/out/*.mp4` | File path | 86-second demo video | Read-only stream | Offline | Yes | `GET /api/video` |

---

## 2. Safety & Job Dispatch Allowlist

Only non-destructive, sandboxed jobs are dispatched via `POST /api/jobs`:
1. `scenario`: runs `python scripts/run_phase3_scenario.py --rung 0` (or live if enabled).
2. `armoriq_proof`: runs `python scripts/armoriq_proof.py` (live guarded).
3. `jail_burst`: runs `python scripts/jail_burst.py` (deterministic).
4. `verify_all`: runs batch verification of receipts, witness chains, and sidecar links.
5. `tamper_demo`: runs `python scripts/tamper_demo.py`.
6. `tests`: runs `make test`.
7. `audit`: runs `make audit`.
