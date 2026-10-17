'use client'

import React from 'react'
import Link from 'next/link'
import { TripLineLogo } from '../brand/TripLineLogo'
import { ShieldCheck, CheckCircle2 } from 'lucide-react'

export function Footer() {
  return (
    <footer className="w-full bg-[#EAEDF0] border-t border-[#CDD2D8] text-[#59636E] py-16 text-xs">
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-10 pb-12 border-b border-[#CDD2D8]">
          {/* Col 1 & 2: Brand Identity & Mission */}
          <div className="md:col-span-2 space-y-4">
            <Link href="/" className="inline-block" aria-label="TripLine Home">
              <TripLineLogo size="md" variant="light" showWordmark={true} animated={false} />
            </Link>
            <p className="text-sm text-[#59636E] max-w-sm leading-relaxed">
              Governed AI-agent security platform. Enforce upstream authorization boundaries, contain execution inside in-MCP jails, and seal cryptographic receipts for every decision.
            </p>
            <div className="pt-2 flex flex-wrap items-center gap-2 font-mono text-[11px] text-[#747F8D]">
              <span className="px-2 py-0.5 rounded bg-[#FFFFFF] border border-[#CDD2D8] text-[#20252B]">
                Fail-Closed Architecture
              </span>
              <span>•</span>
              <span className="px-2 py-0.5 rounded bg-[#FFFFFF] border border-[#CDD2D8] text-[#20252B]">
                Zero Synthesized Logs
              </span>
              <span>•</span>
              <span className="px-2 py-0.5 rounded bg-[#FFFFFF] border border-[#CDD2D8] text-[#20252B]">
                Offline Verifiable Receipts
              </span>
            </div>
          </div>

          {/* Col 3: Product & Architecture */}
          <div className="space-y-3">
            <span className="block font-mono text-[11px] uppercase tracking-wider text-[#20252B] font-semibold">
              Platform
            </span>
            <ul className="space-y-2">
              <li>
                <Link href="/#product" className="hover:text-[#20252B] transition-colors">
                  Product Overview
                </Link>
              </li>
              <li>
                <Link href="/#architecture" className="hover:text-[#20252B] transition-colors">
                  Security Architecture
                </Link>
              </li>
              <li>
                <Link href="/#how-it-works" className="hover:text-[#20252B] transition-colors">
                  How It Works
                </Link>
              </li>
              <li>
                <Link href="/#workflow" className="hover:text-[#20252B] transition-colors">
                  Execution Demo
                </Link>
              </li>
              <li>
                <Link href="/#evidence" className="hover:text-[#20252B] transition-colors">
                  Receipt Verification
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 4: Evidence Suite */}
          <div className="space-y-3">
            <span className="block font-mono text-[11px] uppercase tracking-wider text-[#20252B] font-semibold">
              Evidence Suite
            </span>
            <ul className="space-y-2">
              <li>
                <Link href="/receipts" className="hover:text-[#20252B] transition-colors">
                  Forensic Receipts
                </Link>
              </li>
              <li>
                <Link href="/witness" className="hover:text-[#20252B] transition-colors">
                  Witness Hash Chain
                </Link>
              </li>
              <li>
                <Link href="/measured" className="hover:text-[#20252B] transition-colors">
                  Defense Metrics
                </Link>
              </li>
              <li>
                <Link href="/claims" className="hover:text-[#20252B] transition-colors">
                  Security Claims
                </Link>
              </li>
              <li>
                <Link href="/layers" className="hover:text-[#20252B] transition-colors">
                  Attribution Matrix
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 5: Forensic Tools */}
          <div className="space-y-3">
            <span className="block font-mono text-[11px] uppercase tracking-wider text-[#20252B] font-semibold">
              Forensic Tools
            </span>
            <ul className="space-y-2">
              <li>
                <Link href="/jail-burst" className="hover:text-[#20252B] transition-colors">
                  Jail Burst Fuzzer
                </Link>
              </li>
              <li>
                <Link href="/console" className="hover:text-[#20252B] transition-colors">
                  Audit Console
                </Link>
              </li>
              <li>
                <Link href="/agent" className="hover:text-[#20252B] transition-colors">
                  Agent Crew Inspector
                </Link>
              </li>
              <li>
                <Link href="/style-guide" className="hover:text-[#20252B] transition-colors">
                  Design Tokens
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Strip */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-[#6E7687]">
          <div>
            © 2026 TripLine. Governed AI Security Platform. Built with ArmorIQ authorization.
          </div>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-[#16A34A]">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Deterministic Cryptographic Receipts</span>
            </span>
            <span>// RFC 8785 Canonical JSON + HMAC-SHA256</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
