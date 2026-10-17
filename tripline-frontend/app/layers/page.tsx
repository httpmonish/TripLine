'use client'

import React from 'react'
import { Section } from '@/components/ui/Section'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { LayerMatrix } from '@/components/diagrams/LayerMatrix'
import { StatusPill } from '@/components/ui/Badge'
import { SourceCaption } from '@/components/ui/SourceCaption'
import { getLayersData } from '@/lib/data'
import { AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react'
import Link from 'next/link'

export default function LayersPage() {
  const layersData = getLayersData()

  return (
    <div className="w-full flex flex-col bg-[#F4F5F6]">
      <Section tone="light">
        <SectionHeader
          eyebrow="// MULTI-LAYER DEFENSE-IN-DEPTH"
          title="Layer Attribution Matrix"
          description="Verifiable breakdown establishing which layer decided each action across recorded evaluations. ArmorIQ decides upstream tool policy; Tripline contains in-MCP parameters and mints offline proof."
          tone="light"
        />

        {/* 1. Interactive D3 Layer Matrix */}
        <div className="mb-12">
          <LayerMatrix />
        </div>

        {/* 2. Acknowledged Honest Residual Table */}
        <div className="rounded-xl border border-amber-300 bg-[#FFFFFF] overflow-hidden mb-12 shadow-sm">
          <div className="p-4 bg-amber-50 border-b border-amber-200 font-mono text-xs flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-amber-800 font-bold">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span className="uppercase">Acknowledged Honest Residual (Section 6.2)</span>
            </div>
            <span className="text-[11px] text-[#747F8D]">
              EXACT-MATCH CANARY LIMITATION
            </span>
          </div>

          <div className="p-4 bg-[#FFFFFF] border-b border-[#CDD2D8] text-xs text-[#59636E] leading-relaxed">
            <strong className="text-[#20252B]">Not stopped by either layer:</strong> Tripline&apos;s egress canary scanner performs literal substring containment matching. If an adversarial agent encodes (Base64), reverses, or fragments the canary token across multiple comments, neither layer traps the outbound payload.
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-[#F4F5F6] text-[#59636E] border-b border-[#CDD2D8] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4 font-semibold">Evasion Technique</th>
                  <th className="py-3 px-4 font-semibold">Payload Tested</th>
                  <th className="py-3 px-4 font-semibold">ArmorIQ Decision</th>
                  <th className="py-3 px-4 font-semibold">Tripline Gateway</th>
                  <th className="py-3 px-4 text-right font-semibold">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#CDD2D8]">
                {layersData.honest_residuals.map((r, idx) => {
                  const isCaught = r.outcome === 'PREVENTED'
                  return (
                    <tr key={idx} className="hover:bg-[#F4F5F6] transition-colors">
                      <td className="py-3 px-4 font-semibold text-[#20252B]">
                        {r.technique}
                      </td>
                      <td className="py-3 px-4 text-[#59636E]">
                        <code className="bg-[#EAEDF0] px-2 py-0.5 rounded text-[11px] border border-[#CDD2D8] text-[#20252B]">
                          {r.payload}
                        </code>
                      </td>
                      <td className="py-3 px-4">
                        <StatusPill state="allow" label={r.armoriq} size="sm" />
                      </td>
                      <td className="py-3 px-4">
                        <StatusPill
                          state={isCaught ? 'hold' : 'allow'}
                          label={r.tripline}
                          size="sm"
                        />
                      </td>
                      <td className="py-3 px-4 text-right">
                        <StatusPill
                          state={isCaught ? 'verified' : 'deny'}
                          label={r.outcome}
                          size="sm"
                        />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-[#EAEDF0] border-t border-[#CDD2D8] flex items-center justify-between font-mono text-xs">
            <SourceCaption source="docs/phase3_layer_attribution.md (Section 3)" />
            <Link
              href="/receipts"
              className="text-[#20252B] hover:text-[#65BCE7] font-semibold flex items-center gap-1.5 transition-colors"
            >
              <span>Inspect Matching Incident Receipts</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </Section>
    </div>
  )
}
