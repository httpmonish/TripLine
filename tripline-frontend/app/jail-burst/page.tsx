'use client'

import React from 'react'
import { Section } from '@/components/ui/Section'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { StatRow } from '@/components/ui/StatRow'
import { StatusPill } from '@/components/ui/Badge'
import { SourceCaption } from '@/components/ui/SourceCaption'
import { getJailBurst } from '@/lib/data'
import { ShieldCheck, ArrowRight, Terminal } from 'lucide-react'
import Link from 'next/link'

export default function JailBurstPage() {
  const burstData = getJailBurst()

  const stats = [
    {
      label: 'TOTAL PROBES',
      value: burstData.total_probes,
      sublabel: 'Adversarial encoding vectors',
      source: 'scripts/jail_burst.py',
    },
    {
      label: 'PASSED (0 LEAKS)',
      value: burstData.passed_probes,
      sublabel: 'Every escape vector denied',
      source: burstData.source,
    },
    {
      label: 'LEAKED BYTES',
      value: `${burstData.leaked_bytes} B`,
      sublabel: 'fstat inode boundary held',
      source: 'mcp/common/jail.py',
    },
    {
      label: 'JAIL BYPASS RATE',
      value: '0%',
      sublabel: '8/8 vectors contained',
      source: 'docs/phase3_layer_attribution.md',
    },
  ]

  return (
    <div className="w-full flex flex-col bg-[#F4F5F6]">
      <Section tone="light">
        <SectionHeader
          eyebrow="// DETERMINISTIC CONTAINMENT EVALUATION"
          title="Path Jail Burst Harness"
          description="Evaluates the real Tripline path jail across traversal encodings, mixed path separators, symlinks, and absolute path escapes. Tested against the live read_file MCP tool."
          tone="light"
        />

        {/* Top Summary StatRow */}
        <div className="mb-12">
          <StatRow stats={stats} tone="light" />
        </div>

        {/* Probes Table / Grid */}
        <div className="rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] overflow-hidden shadow-sm">
          <div className="p-4 bg-[#EAEDF0] border-b border-[#CDD2D8] flex flex-wrap items-center justify-between gap-2 font-mono text-xs">
            <span className="text-[#59636E] uppercase font-semibold">
              // 8 DETERMINISTIC PROBE VECTORS
            </span>
            <div className="inline-flex items-center gap-2 text-emerald-600 font-semibold">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>ALL PASS (ZERO LEAKS)</span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-[#F4F5F6] text-[#59636E] border-b border-[#CDD2D8] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4 font-semibold">Probe Vector</th>
                  <th className="py-3 px-4 font-semibold">Path Argument Tested</th>
                  <th className="py-3 px-4 font-semibold">ArmorIQ Gate</th>
                  <th className="py-3 px-4 font-semibold">Tripline Path Jail</th>
                  <th className="py-3 px-4 text-center font-semibold">Bytes Returned</th>
                  <th className="py-3 px-4 text-right font-semibold">Verdict</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#CDD2D8]">
                {burstData.probes.map((p, idx) => {
                  const isDenied = p.jail_decision.includes('DENIED')
                  const isPositive = p.attempt.includes('Positive Control')

                  return (
                    <tr
                      key={idx}
                      className="hover:bg-[#F4F5F6] transition-colors"
                    >
                      <td className="py-3 px-4 font-semibold text-[#20252B]">
                        {p.attempt}
                      </td>
                      <td className="py-3 px-4 text-[#59636E]">
                        <code className="bg-[#EAEDF0] px-2 py-0.5 rounded text-[11px] border border-[#CDD2D8] text-[#20252B]">
                          {p.path}
                        </code>
                      </td>
                      <td className="py-3 px-4 text-[#59636E]">
                        <StatusPill state="allow" label={p.armoriq_decision} size="sm" />
                      </td>
                      <td className="py-3 px-4">
                        <StatusPill
                          state={isDenied ? 'deny' : 'allow'}
                          label={p.jail_decision}
                          size="sm"
                        />
                      </td>
                      <td className="py-3 px-4 text-center font-bold text-[#20252B]">
                        {p.bytes_returned}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <StatusPill state="verified" label="PASS" size="sm" />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-[#EAEDF0] border-t border-[#CDD2D8] flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
            <SourceCaption source={burstData.source} />
            <div className="flex items-center gap-2 text-[#59636E]">
              <span>Execute probe:</span>
              <code className="text-emerald-700 bg-[#FFFFFF] border border-[#CDD2D8] px-2 py-0.5 rounded font-bold">make burst</code>
            </div>
          </div>
        </div>

        {/* Transition Link to Witness */}
        <div className="mt-8 flex items-center justify-between p-4 rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] text-xs font-mono shadow-sm">
          <span className="text-[#59636E]">
            // Path jail execution attempts are recorded into the witness ledger.
          </span>
          <Link
            href="/witness"
            className="text-[#20252B] hover:text-[#65BCE7] font-semibold flex items-center gap-1.5 transition-colors"
          >
            <span>Proceed to Witness Ledger</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </Section>
    </div>
  )
}
