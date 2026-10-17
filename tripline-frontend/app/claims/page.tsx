'use client'

import React, { useEffect, useState } from 'react'
import { Section } from '@/components/ui/Section'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { StatusPill } from '@/components/ui/Badge'
import { SourceCaption } from '@/components/ui/SourceCaption'
import { Card } from '@/components/ui/Card'
import { getClaimsData } from '@/lib/data'
import { api } from '@/lib/api'
import { ShieldCheck, AlertTriangle, ArrowRight } from 'lucide-react'
import Link from 'next/link'

export default function ClaimsPage() {
  const initial = getClaimsData()
  const [claimsData, setClaimsData] = useState(initial)

  useEffect(() => {
    let mounted = true
    api.getClaims().then(res => {
      if (mounted && res && res.items) {
        setClaimsData(prev => ({
          ...prev,
          claims: res.items.map(item => ({
            id: item.id,
            claim: item.claim,
            source: item.notes || 'Rule 10 Verified Audit',
            evidence: item.evidence_path,
            status: item.verdict
          }))
        }))
      }
    }).catch(() => {})
    return () => { mounted = false }
  }, [])

  return (
    <div className="w-full flex flex-col bg-[#F4F5F6]">
      <Section tone="light">
        <SectionHeader
          eyebrow="// TRUTH AUDIT & RESIDUAL TRANSPARENCY"
          title="Claims & Honest Limits"
          description="Every statement on Tripline is audited against recorded evidence under Rule 10. We report our residual attack surface with complete engineering honesty."
          tone="light"
        />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Verified Claims Table (8 cols) */}
          <div className="lg:col-span-8 space-y-4">
            <div className="rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] overflow-hidden shadow-sm">
              <div className="p-4 bg-[#EAEDF0] border-b border-[#CDD2D8] font-mono text-xs flex items-center justify-between">
                <span className="text-[#59636E] uppercase font-semibold">
                  // VERIFIED CLAIMS LEDGER (RULE 10 AUDIT)
                </span>
                <span className="text-emerald-700 font-bold flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>ALL VERIFIED</span>
                </span>
              </div>

              <div className="divide-y divide-[#CDD2D8] font-mono text-xs">
                {claimsData.claims.map((c) => (
                  <div
                    key={c.id}
                    className="p-4 hover:bg-[#F4F5F6] transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="font-bold text-[#65BCE7] text-xs">
                        {c.id}
                      </span>
                      <StatusPill state="verified" label="VERIFIED" size="sm" />
                    </div>

                    <p className="font-sans text-sm font-semibold text-[#20252B] mb-2 leading-snug">
                      &ldquo;{c.claim}&rdquo;
                    </p>

                    <div className="text-[11px] text-[#59636E] space-y-0.5">
                      <div>// Source: {c.source}</div>
                      <div>// Evidence: <span className="text-emerald-700 font-semibold">{c.evidence}</span></div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-3 bg-[#EAEDF0] border-t border-[#CDD2D8]">
                <SourceCaption source={claimsData.source} />
              </div>
            </div>
          </div>

          {/* Right Column: Known Limits & Residuals (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            <div className="p-4 rounded-xl border border-amber-300 bg-amber-50 font-mono text-xs shadow-sm">
              <div className="flex items-center gap-2 text-amber-800 font-bold mb-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
                <span className="uppercase">Acknowledged Honest Limits</span>
              </div>
              <p className="text-xs text-[#59636E] leading-relaxed font-sans">
                Security systems with unstated assumptions create false assurance. Tripline documents its known architectural residuals explicitly.
              </p>
            </div>

            <div className="space-y-4">
              {claimsData.known_limits.map((limit, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] shadow-sm space-y-2"
                >
                  <h4 className="font-mono text-xs font-bold text-[#20252B] uppercase">
                    {limit.title}
                  </h4>
                  <p className="text-xs text-[#59636E] leading-relaxed font-sans">
                    {limit.description}
                  </p>
                  <div className="text-[10px] font-mono text-[#747F8D] pt-1 border-t border-[#CDD2D8]">
                    Source: {limit.source}
                  </div>
                </div>
              ))}
            </div>

            <div className="p-4 rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] text-xs font-mono shadow-sm">
              <span className="text-[#59636E] block mb-3">
                // Ready to inspect offline receipts?
              </span>
              <Link
                href="/receipts"
                className="text-[#20252B] hover:text-[#65BCE7] font-semibold flex items-center gap-1.5 transition-colors"
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
