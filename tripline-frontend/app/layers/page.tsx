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
    <div className="w-full flex flex-col">
      <Section tone="dark">
        <SectionHeader
          eyebrow="// MULTI-LAYER DEFENSE-IN-DEPTH"
          title="Layer Attribution Matrix"
          accentWord="Attribution"
          description="Verifiable breakdown establishing which layer decided each action across recorded evaluations. ArmorIQ decides upstream tool policy; Tripline contains in-MCP parameters and mints offline proof."
          tone="dark"
        />

        {/* 1. Interactive D3 Layer Matrix */}
        <div className="mb-12">
          <LayerMatrix />
        </div>

        {/* 2. Acknowledged Honest Residual Table */}
        <div className="rounded-[4px] border border-amber-500/30 bg-[#0C0C0E] overflow-hidden mb-12">
          <div className="p-4 bg-amber-950/20 border-b border-amber-500/30 font-mono text-xs flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-amber-400 font-bold">
              <AlertTriangle className="w-4 h-4" />
              <span className="uppercase">Acknowledged Honest Residual (Section 6.2)</span>
            </div>
            <span className="text-[11px] text-[var(--text-faint-on-dark)]">
              EXACT-MATCH CANARY LIMITATION
            </span>
          </div>

          <div className="p-4 bg-[#09090B] border-b border-[var(--border-dark)] text-xs text-[var(--text-muted-on-dark)] leading-relaxed">
            <strong>Not stopped by either layer:</strong> Tripline&apos;s egress canary scanner performs literal substring containment matching. If an adversarial agent encodes (Base64), reverses, or fragments the canary token across multiple comments, neither layer traps the outbound payload.
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-[#08080A] text-[var(--text-faint-on-dark)] border-b border-[var(--border-dark)] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Evasion Technique</th>
                  <th className="py-3 px-4">Payload Tested</th>
                  <th className="py-3 px-4">ArmorIQ Decision</th>
                  <th className="py-3 px-4">Tripline Gateway</th>
                  <th className="py-3 px-4 text-right">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-dark)]">
                {layersData.honest_residuals.map((r, idx) => {
                  const isCaught = r.outcome === 'PREVENTED'
                  return (
                    <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-4 font-semibold text-white">
                        {r.technique}
                      </td>
                      <td className="py-3 px-4 text-gray-300">
                        <code className="bg-black/50 px-2 py-0.5 rounded text-[11px] border border-[#2A2A2E]">
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

          <div className="p-4 bg-[#0B0B0D] border-t border-[var(--border-dark)] flex items-center justify-between font-mono text-xs">
            <SourceCaption source="docs/phase3_layer_attribution.md (Section 3)" />
            <Link
              href="/receipts"
              className="text-white hover:text-[var(--accent)] font-semibold flex items-center gap-1.5"
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
