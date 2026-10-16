'use client'

import React from 'react'
import { Section } from '@/components/ui/Section'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { StatusPill } from '@/components/ui/Badge'
import { SourceCaption } from '@/components/ui/SourceCaption'
import { Card } from '@/components/ui/Card'
import { getClaimsData } from '@/lib/data'
import { ShieldCheck, AlertTriangle, ArrowRight } from 'lucide-react'
import Link from 'next/link'

export default function ClaimsPage() {
  const claimsData = getClaimsData()

  return (
    <div className="w-full flex flex-col">
      <Section tone="dark">
        <SectionHeader
          eyebrow="// TRUTH AUDIT & RESIDUAL TRANSPARENCY"
          title="Claims & Honest Limits"
          accentWord="Limits"
          description="Every statement on Tripline is audited against recorded evidence under Rule 10. We report our residual attack surface with complete engineering honesty."
          tone="dark"
        />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Verified Claims Table (8 cols) */}
          <div className="lg:col-span-8 space-y-4">
            <div className="rounded-[4px] border border-[var(--border-dark)] bg-[#0C0C0E] overflow-hidden">
              <div className="p-4 bg-[#121215] border-b border-[var(--border-dark)] font-mono text-xs flex items-center justify-between">
                <span className="text-[var(--text-muted-on-dark)] uppercase font-semibold">
                  // VERIFIED CLAIMS LEDGER (RULE 10 AUDIT)
                </span>
                <span className="text-emerald-400 font-bold flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>ALL VERIFIED</span>
                </span>
              </div>

              <div className="divide-y divide-[var(--border-dark)] font-mono text-xs">
                {claimsData.claims.map((c) => (
                  <div
                    key={c.id}
                    className="p-4 hover:bg-white/[0.02] transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="font-bold text-[var(--accent)] text-xs">
                        {c.id}
                      </span>
                      <StatusPill state="verified" label="VERIFIED" size="sm" />
                    </div>

                    <p className="font-sans text-sm font-medium text-white mb-2 leading-snug">
                      &ldquo;{c.claim}&rdquo;
                    </p>

                    <div className="text-[11px] text-[var(--text-muted-on-dark)] space-y-0.5">
                      <div>// Source: {c.source}</div>
                      <div>// Evidence: <span className="text-emerald-400">{c.evidence}</span></div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-3 bg-[#09090B] border-t border-[var(--border-dark)]">
                <SourceCaption source={claimsData.source} />
              </div>
            </div>
          </div>

          {/* Right Column: Known Limits & Residuals (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            <div className="p-4 rounded-[4px] border border-amber-500/30 bg-amber-950/10 font-mono text-xs">
              <div className="flex items-center gap-2 text-amber-400 font-bold mb-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span className="uppercase">Acknowledged Honest Limits</span>
              </div>
              <p className="text-xs text-[var(--text-muted-on-dark)] leading-relaxed font-sans">
                Security systems with unstated assumptions create false assurance. Tripline documents its known architectural residuals explicitly.
              </p>
            </div>

            <div className="space-y-4">
              {claimsData.known_limits.map((limit, idx) => (
                <Card
                  key={idx}
                  variant="ruled-top"
                  accentColor="#F5A524"
                  source={limit.source}
                >
                  <h4 className="font-mono text-xs font-bold text-white uppercase mb-1">
                    {limit.title}
                  </h4>
                  <p className="text-xs text-[var(--text-muted-on-dark)] leading-relaxed font-sans">
                    {limit.description}
                  </p>
                </Card>
              ))}
            </div>

            <div className="p-4 rounded-[4px] border border-[var(--border-dark)] bg-[#101014] text-xs font-mono">
              <span className="text-[var(--text-faint-on-dark)] block mb-3">
                // Ready to inspect offline receipts?
              </span>
              <Link
                href="/receipts"
                className="text-[var(--accent)] hover:underline font-semibold flex items-center gap-1.5"
              >
                <span>Inspect All Incident Receipts</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </Section>
    </div>
  )
}
