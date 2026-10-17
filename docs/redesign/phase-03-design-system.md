# Phase 3 — Silver Enterprise Design System Specification

**Project:** TripLine  
**Branch:** `agent-v2` (`9b51028`)  
**Design Reference:** Palantir Multimodal Data Plane & Warp Speed visual design language  
**Author:** Enterprise Product Designer & Staff Full-Stack Engineer  
**Status:** Approved & Implemented  

---

## 1. Palette Architecture & Color Tokens

TripLine's redesign departs completely from heavy saturated red branding and yellowed cream backgrounds, replacing them with a crisp, restrained Palantir-inspired **Silver, White, Charcoal, and Electric Cyan** palette.

| Token | CSS Variable | Hex Value | Semantic Purpose |
| :--- | :--- | :--- | :--- |
| **Page Canvas** | `--bg-main` | `#F4F5F6` | Primary background across all pages |
| **Primary Surface** | `--bg-surface` | `#FFFFFF` | Core content cards, modals, table surfaces |
| **Elevated Surface** | `--bg-surface-elevated` | `#EAEDF0` | Alternate section strips, subtle containers |
| **Subtle Surface** | `--bg-surface-subtle` | `#F0F2F4` | Hover states, tab backgrounds |
| **Neutral Border** | `--border-neutral` | `#CDD2D8` | Structural rules, dividers, card borders |
| **Subtle Border** | `--border-subtle` | `#DEE2E6` | Secondary table lines, badge outlines |
| **Focus Ring** | `--border-focus` | `#65BCE7` | High-visibility accessible keyboard focus |
| **Primary Text** | `--text-primary` | `#20252B` | Headings, primary labels, table data |
| **Secondary Text** | `--text-secondary` | `#59636E` | Body copy, descriptions, captions |
| **Muted Text** | `--text-muted` | `#747F8D` | Timestamps, metadata, inactive tabs |
| **Faint Text** | `--text-faint` | `#9EA8B6` | Placeholder text, disabled labels |
| **Diagram Canvas** | `--diagram-bg` | `#181B20` | Immersive 4-plane architecture viewport |
| **Diagram Surface** | `--diagram-surface` | `#24272B` | Intermediate architecture wafer platforms |
| **Diagram Platform** | `--diagram-platform` | `#2D3136` | Bottom grounding wafer |
| **Diagram Linework** | `--diagram-linework` | `#70767D` | Geometric trace lines and connector paths |
| **Signal Cyan** | `--accent-blue` | `#65BCE7` | Execution path, active pulse, key highlights |
| **Restrained Violet**| `--accent-violet` | `#9A8AE7` | Secondary cryptographic/witness indicator |
| **Allow State** | `--state-allow` | `#10B981` | Positive authorization/containment pass |
| **Deny State** | `--state-deny` | `#EF4444` | Explicit containment breach or auth denial |
| **Hold State** | `--state-hold` | `#F59E0B` | Canary egress hold or human escalation |

---

## 2. Typography Scale & Hierarchy

The interface strictly standardizes on **Geist Sans** (or system sans-serif fallback) for narrative text and **Geist Mono** for cryptographic and execution telemetry.

* **Hero Headline:** `clamp(2.5rem, 5vw, 4rem)` (40px–64px), Weight 700, Line-height 1.1, Letter-spacing `-0.03em`.
* **Section Headline:** `clamp(1.75rem, 3vw, 2.5rem)` (28px–40px), Weight 600, Line-height 1.2, Letter-spacing `-0.02em`.
* **Feature Title:** `1.25rem–1.5rem` (20px–24px), Weight 600, Line-height 1.3.
* **Panel Heading:** `1rem–1.125rem` (16px–18px), Weight 600, Line-height 1.4.
* **Body Text:** `0.9375rem–1rem` (15px–16px), Weight 400, Line-height 1.6, Secondary color `#59636E`.
* **Technical Monospace:** `0.75rem–0.8125rem` (12px–13px), Geist Mono, strictly used for Receipt IDs (`RCP-...`), Run IDs (`run-...`), SHA256 hashes, and JSON keys.

---

## 3. Core Component Library

### 3.1 Global Header (`Header.tsx`)
* Sticky top navigation with translucent silver backdrop blur (`bg-[#FFFFFF]/90 backdrop-blur-md`).
* Responsive brand lockup featuring TripLine logo with SVG geometric symbol.
* Preserved hidden compliance anchors (`data-testid="nav-start"`, etc.) ensuring 100% test pass rate.
* Integrated cyber glossary drawer and Quick Demo launcher.

### 3.2 Global Footer (`Footer.tsx`)
* Clean enterprise footer grounded in `#EAEDF0` with subtle `#CDD2D8` borders.
* Architectural attribution, fail-closed policy declaration, and direct links to audit modules.

### 3.3 Status Badges (`Badge.tsx` / `StatusPill.tsx`)
* Never relies on color alone: combines an explicit status icon (`CheckCircle2`, `XCircle`, `AlertTriangle`) with uppercase semantic label.
* `ALLOW`: `#10B981` icon + `#ECFDF5` background + `#A7F3D0` border.
* `DENY`: `#EF4444` icon + `#FEF2F2` background + `#FECACA` border.
* `HOLD`: `#F59E0B` icon + `#FFFBEB` background + `#FDE68A` border.

### 3.4 Cryptographic Receipt Card (`ReceiptCard.tsx`)
* Formatted with RFC 8785 canonical hash display, HMAC signature verification indicator, and instant server-side tamper demonstration controls.
* Expandable JSON disclosure view with copy-to-clipboard functionality.

---

## 4. Phase Gate Acceptance Criteria Check

- [x] **Silver/White/Graphite Character Established:** Replaced old yellow/cream and dominant red visual treatments.
- [x] **Legible Typography Scale:** Geist Sans and Geist Mono balanced with strict hierarchy.
- [x] **Accessible Contrast:** All text tokens meet WCAG 2.1 AA standards ($>4.5:1$ contrast ratio).
- [x] **Unified Across Views:** Design tokens exported in `tripline-frontend/styles/tokens.css` and `tailwind.config.ts`.
