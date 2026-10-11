# Tripline Design System Specification

**Version**: 1.0 (Phase 10 Enterprise UI Redesign)  
**Target Submission**: ArmorIQ Flow State Hackathon (October 2026)  
**Branch**: `ui-redesign`

---

## 1. Design Philosophy & Thesis

> **"Blocked isn't evidence. Every denied action gets a signed receipt you can verify."**  
> **"ArmorIQ decides. Tripline proves."**

Tripline's interface is designed as an authoritative enterprise AI security product site, not a generic dashboard. It features:
- Strong editorial typography and technical clarity.
- Alternating dark and light sections with purposeful contrast.
- Custom interactive architecture diagrams explaining the real layered defense.
- Full data integrity: every number, badge, table row, and annotation is bound to verified API endpoints.

---

## 2. Surfaces & Palette

### Dark Sections
| Token | Hex | Role | Contrast Ratio vs Text |
|-------|-----|------|------------------------|
| `--ink-950` | `#0A0B0D` | Base page background | 16.8:1 (AAA) |
| `--ink-900` | `#0F1115` | Elevated surface / Card background | 15.3:1 (AAA) |
| `--ink-800` | `#171A20` | Secondary surface / Table headers | 13.5:1 (AAA) |
| `--line-dark` | `#232832` | Structural borders & grid lines | 3.4:1 vs surface |
| `--text` | `#F4F5F7` | Primary text | — |
| `--text-secondary` | `#A3A9B5` | Metadata & labels | 7.9:1 (AAA) |

### Light Sections
| Token | Hex | Role | Contrast Ratio vs Text |
|-------|-----|------|------------------------|
| `--paper` | `#F6F4EF` | Base page background | 15.2:1 (AAA) |
| `--paper-2` | `#EDEAE3` | Elevated surface / Card background | 13.8:1 (AAA) |
| `--line-light` | `#D9D5CB` | Structural borders | 3.2:1 vs surface |
| `--text` | `#14161A` | Primary text | — |
| `--text-secondary` | `#4B5160` | Metadata & descriptions | 7.1:1 (AAA) |

### Brand Accent (Sparingly Used)
| Token | Hex | Context | Usage Rules |
|-------|-----|---------|-------------|
| `--trip-red` | `#E5484D` | On dark backgrounds | Headline accent, brand logo, active stopped paths |
| `--trip-red-on-light` | `#C2272D` | On light backgrounds | Headline accent, brand mark |

*Rule*: Brand red is never used for primary buttons or positive states. Primary CTA buttons use white-on-ink (`#FFFFFF` on `#0A0B0D`) or ink-on-paper. Focus outlines use neutral/ink rings.

### Decision & Status Colors
| State | Dark Hex | Light Hex | Meaning | Icon/Shape Requirement |
|-------|----------|-----------|---------|------------------------|
| **ALLOW** | `#3DD68C` | `#12703F` | Upstream platform allowed | Check / ShieldCheck + text |
| **DENY** | `#FF6369` | `#C4232B` | Blocked by layer (Jail/ArmorIQ) | ShieldAlert / X + text |
| **HOLD** | `#F5A524` | `#8A5A00` | Outbound canary detected | AlertTriangle + text |
| **ATTEST / SEAL** | `#8B93A1` | `#5B6270` | Audit record / HMAC receipt | Lock / Key + text |
| **NEUTRAL** | `#8B93A1` | `#5B6270` | Pending / Unverified | Dash / Square + text |

*Rule*: Color is never the sole indicator; text label and icon are mandatory. Genuine DENY or FAILED is never displayed in green.

---

## 3. Typography & Hierarchy

Bundled locally via Next.js (`next/font/google` built-in package, zero external network requests).

- **Display & Body**: Geist Sans (`--font-sans`), OFL license.
- **Code & Monospace**: Geist Mono (`--font-mono`), OFL license.

### Type Scale (CSS Clamp)
| Level | Mobile (390px) | Desktop (1440px) | Line Height | Tracking |
|-------|----------------|------------------|-------------|----------|
| **Hero H1** | `2.0rem` (32px) | `4.5rem`–`6.0rem` | `1.0` | `-0.02em` |
| **Section H2** | `1.5rem` (24px) | `2.5rem`–`3.25rem` | `1.08` | `-0.015em` |
| **Card H3** | `1.25rem` (20px) | `1.5rem`–`1.75rem` | `1.2` | Normal |
| **Body** | `0.9375rem` (15px) | `1.0rem` (16px) | `1.6` | Normal |
| **Small / Meta** | `0.8125rem` (13px) | `0.875rem` (14px) | `1.4` | Normal |
| **Monospace** | `0.75rem` (12px) | `0.8125rem` (13px) | `1.45` | Normal |

---

## 4. Spacing & Grid System

- **Base unit**: 4px.
- **Container max-width**: 1200px (`.wrap`).
- **Text reading width**: max `68ch`.
- **Gutters**: 16px (mobile), 24px (tablet), 32px (desktop).
- **Section Padding**: `clamp(4rem, 8vw, 8rem)` vertical rhythm.

---

## 5. Motion Tokens & Accessibility

- **Durations**:
  - `fast`: 120ms (buttons, badges)
  - `normal`: 200ms (drawers, tabs, cards)
  - `slow`: 320ms (page transitions)
  - `deliberate`: 600ms (steppers)
- **Easing**: `cubic-bezier(0.2, 0.7, 0.2, 1)` (snappy ease-out).
- **Reduced Motion**: Under `@media (prefers-reduced-motion: reduce)`, animations scale to 0 (`--motion-scale: 0`). Elements render statically with opacity 1 and zero translation.

---

## 6. Component Inventory

1. **SiteHeader**: Sticky header (56px) with brand lockup, responsive nav tabs, live freshness chip, and mobile drawer trigger.
2. **MobileNav**: Focus-trapped, accessible navigation drawer with 44×44px touch targets.
3. **HeroSection**: Left editorial narrative (eyebrow, title with brand red accent, subtitle, CTA pair, proof strip, run switcher); right FlowDiagram / Architecture replay container.
4. **FlowDiagram / ReplayChip**: Interactive visualization of proposal → upstream ArmorIQ policy → Tripline path jail / egress canary → witness log → HMAC receipt.
5. **LayerExplorer**: 5 defense layers with ownership badges (ArmorIQ Platform vs Tripline MCP), mechanism descriptions, and failure modes.
6. **ReceiptWorkflow**: 5-step cryptographic verification stepper bound to live FastAPI verification and tamper-check endpoints.
7. **DataTable**: Responsive table wrapper with hover states, sorting, status badges, and HashChip truncated values.
8. **TerminalPanel**: Monospace live job output display with copy control, ANSI handling, and auto-scroll.
9. **StatusBadge**: Accessible badge pairing status color, icon, and uppercase text label.
10. **SiteFooter**: 4-column structured footer with Thesis statement, navigation routes, and hackathon attribution.
