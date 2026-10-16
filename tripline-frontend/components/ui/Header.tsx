'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Menu, X, ShieldCheck, HelpCircle } from 'lucide-react'
import { GlossaryDrawer } from './GlossaryDrawer'

export const NAV_LINKS = [
  { href: '/', label: '// START', short: 'Start', testid: 'nav-start' },
  { href: '/agent', label: '// AGENT', short: 'Agent', testid: 'nav-agent' },
  { href: '/overview', label: '// OVERVIEW', short: 'Overview', testid: 'nav-overview' },
  { href: '/receipts', label: '// RECEIPTS', short: 'Receipts', testid: 'nav-receipts' },
  { href: '/console', label: '// CONSOLE', short: 'Console', testid: 'nav-console' },
  { href: '/jail-burst', label: '// JAIL BURST', short: 'Jail Burst', testid: 'nav-burst' },
  { href: '/witness', label: '// WITNESS', short: 'Witness', testid: 'nav-witness' },
  { href: '/measured', label: '// MEASURED', short: 'Measured', testid: 'nav-measured' },
  { href: '/claims', label: '// CLAIMS', short: 'Claims', testid: 'nav-claims' },
  { href: '/layers', label: '// ATTRIBUTION', short: 'Attribution', testid: 'nav-attribution' },
]

export function Header() {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [glossaryOpen, setGlossaryOpen] = useState(false)

  return (
    <>
      <header className="sticky top-0 z-40 w-full bg-[#0B0B0C]/90 backdrop-blur-md border-b border-[var(--border-dark)] text-[#F3F1EA]">
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          {/* Brand Lockup */}
          <Link
            href="/"
            className="flex items-center gap-3 focus-ring group"
            aria-label="Tripline Home"
          >
            <div className="flex items-center">
              <img
                src="/tripline-lockup-on-dark.svg"
                alt="Tripline"
                className="h-7 w-auto block dark:block"
              />
              <img
                src="/tripline-lockup-on-light.svg"
                alt="Tripline"
                className="h-7 w-auto hidden"
              />
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
                  data-testid={link.testid}
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

          {/* Desktop Right CTA + Glossary */}
          <div className="hidden lg:flex items-center gap-2 font-mono text-xs">
            <button
              onClick={() => setGlossaryOpen(true)}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-[2px] border border-[var(--border-dark)] bg-white/5 hover:bg-white/10 text-[var(--text-muted-on-dark)] hover:text-white transition-colors"
              title="Open Glossary (?)"
              data-local="toggle-glossary"
              data-testid="btn-open-glossary"
            >
              <HelpCircle className="w-3.5 h-3.5 text-[var(--accent)]" />
              <span>GLOSSARY (?)</span>
            </button>

            <Link
              href="/#live"
              data-local="skip-to-live"
              data-testid="btn-skip-live"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[2px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[#0B0B0C] font-semibold transition-colors focus-ring"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>WATCH LIVE</span>
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center gap-2 xl:hidden">
            <button
              onClick={() => setGlossaryOpen(true)}
              className="p-2 rounded text-[var(--text-muted-on-dark)] hover:text-white"
              aria-label="Open Glossary"
              data-local="open-glossary-mobile"
            >
              <HelpCircle className="w-4 h-4 text-[var(--accent)]" />
            </button>
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-2 rounded text-[var(--text-muted-on-dark)] hover:text-white"
              aria-label="Toggle navigation"
              data-local="toggle-mobile-nav"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown */}
        {mobileOpen && (
          <div className="xl:hidden bg-[#0F0F11] border-b border-[var(--border-dark)] px-4 py-3 space-y-1">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                data-testid={`${link.testid}-mobile`}
                onClick={() => setMobileOpen(false)}
                className="block px-3 py-2 text-xs font-mono text-[var(--text-muted-on-dark)] hover:text-white hover:bg-white/5 rounded"
              >
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </header>

      {/* Floating Glossary Drawer */}
      <GlossaryDrawer isOpen={glossaryOpen} onClose={() => setGlossaryOpen(false)} />
    </>
  )
}
