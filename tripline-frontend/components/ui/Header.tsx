'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Menu, X, ShieldCheck, ExternalLink } from 'lucide-react'

export const NAV_LINKS = [
  { href: '/', label: '// OVERVIEW', short: 'Overview' },
  { href: '/receipts', label: '// RECEIPTS', short: 'Receipts' },
  { href: '/console', label: '// CONSOLE', short: 'Console' },
  { href: '/jail-burst', label: '// JAIL BURST', short: 'Jail Burst' },
  { href: '/witness', label: '// WITNESS', short: 'Witness' },
  { href: '/measured', label: '// MEASURED', short: 'Measured' },
  { href: '/claims', label: '// CLAIMS & LIMITS', short: 'Claims & Limits' },
  { href: '/layers', label: '// LAYER ATTRIBUTION', short: 'Layers' },
]

export function Header() {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 w-full bg-[#0B0B0C]/90 backdrop-blur-md border-b border-[var(--border-dark)] text-[#F3F1EA]">
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand Lockup */}
        <Link
          href="/"
          className="flex items-center gap-3 focus-ring group"
          aria-label="Tripline Home"
        >
          <svg
            viewBox="0 0 64 64"
            className="w-7 h-7 shrink-0 transition-transform group-hover:scale-105"
            role="img"
            aria-label="Tripline logo"
          >
            <rect width="64" height="64" rx="14" fill="#141416" />
            <rect x="11" y="26" width="42" height="7" rx="3.5" fill="#FFFFFF" />
            <path
              d="M27 33H37V50L35 53L33 50L31 53L29 50L27 53Z"
              fill="#FFFFFF"
            />
            <rect
              x="29.75"
              y="7"
              width="4.5"
              height="13"
              rx="2.25"
              fill="#E5484D"
            />
          </svg>
          <div className="flex flex-col">
            <span className="font-bold text-base tracking-tight leading-none text-white">
              TRIPLINE
            </span>
            <span className="font-mono text-[9px] uppercase tracking-widest text-[var(--text-faint-on-dark)] mt-0.5">
              GOVERNED AGENT PROOF LAYER
            </span>
          </div>
        </Link>

        {/* Desktop Nav */}
        <nav
          className="hidden xl:flex items-center gap-1 font-mono text-xs"
          aria-label="Main Navigation"
        >
          {NAV_LINKS.map((link) => {
            const isActive =
              link.href === '/'
                ? pathname === '/'
                : pathname?.startsWith(link.href)
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`px-2.5 py-1.5 rounded-[2px] transition-colors focus-ring ${
                  isActive
                    ? 'text-[var(--accent)] font-semibold bg-white/5'
                    : 'text-[var(--text-muted-on-dark)] hover:text-white hover:bg-white/[0.03]'
                }`}
              >
                {link.label}
              </Link>
            )
          })}
        </nav>

        {/* Desktop Right CTA */}
        <div className="hidden lg:flex items-center gap-3 font-mono text-xs">
          <Link
            href="/receipts"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[2px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[#0B0B0C] font-semibold transition-colors focus-ring"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>INSPECT RECEIPTS</span>
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="xl:hidden p-2 rounded-[2px] text-[var(--text-muted-on-dark)] hover:text-white hover:bg-white/5 focus-ring"
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          type="button"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="xl:hidden border-b border-[var(--border-dark)] bg-[#0E0E10] px-4 py-4 font-mono text-xs">
          <nav className="flex flex-col gap-1">
            {NAV_LINKS.map((link) => {
              const isActive =
                link.href === '/'
                  ? pathname === '/'
                  : pathname?.startsWith(link.href)
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={`px-3 py-2 rounded-[2px] transition-colors ${
                    isActive
                      ? 'text-[var(--accent)] font-semibold bg-white/5'
                      : 'text-[var(--text-muted-on-dark)] hover:text-white'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
          </nav>
        </div>
      )}
    </header>
  )
}
