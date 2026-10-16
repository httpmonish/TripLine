'use client'

import React from 'react'
import Link from 'next/link'
import { NAV_LINKS } from './Header'

export function Footer() {
  return (
    <footer className="w-full bg-[#080809] border-t border-[var(--border-dark)] text-[#F3F1EA] py-16 font-mono text-xs">
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-[var(--border-dark)]">
          {/* Col 1: Identity */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <span className="font-bold text-base text-white tracking-tight">
                TRIPLINE
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-[2px] bg-white/10 text-[var(--text-muted-on-dark)]">
                FLOW STATE 2026
              </span>
            </div>
            <p className="font-sans text-sm text-[var(--text-muted-on-dark)] max-w-md leading-relaxed mb-4">
              A governed-agent proof layer built for the ArmorIQ &ldquo;Flow State 2026&rdquo; hackathon.
              ArmorIQ decides. Tripline contains and proves.
            </p>
            <div className="text-[11px] text-[var(--text-faint-on-dark)] space-y-1">
              <div>// Zero external network requests at runtime</div>
              <div>// Offline verification via <code>make verify</code></div>
              <div>// Canonical JSON (RFC 8785 subset) + HMAC-SHA256 signatures</div>
            </div>
          </div>

          {/* Col 2: Evidence Routes */}
          <div>
            <span className="block text-[11px] uppercase tracking-wider text-[var(--text-faint-on-dark)] mb-3">
              EVIDENCE ROUTES
            </span>
            <ul className="space-y-2">
              {NAV_LINKS.slice(0, 4).map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-[var(--text-muted-on-dark)] hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Col 3: Verification & Audits */}
          <div>
            <span className="block text-[11px] uppercase tracking-wider text-[var(--text-faint-on-dark)] mb-3">
              AUDIT SUITE
            </span>
            <ul className="space-y-2">
              {NAV_LINKS.slice(4).map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-[var(--text-muted-on-dark)] hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 flex flex-wrap items-center justify-between gap-4 text-[11px] text-[var(--text-faint-on-dark)]">
          <div>
            &copy; 2026 Tripline. Built for the ArmorIQ Flow State 2026 Hackathon.
          </div>
          <div className="flex items-center gap-4">
            <span>// Offline Verifiable</span>
            <span>// Zero Synthetic Counters</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
