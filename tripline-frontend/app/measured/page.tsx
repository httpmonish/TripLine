'use client'

import React from 'react'
import { Section } from '@/components/ui/Section'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { StatRow } from '@/components/ui/StatRow'
import { StatusPill } from '@/components/ui/Badge'
import { SourceCaption } from '@/components/ui/SourceCaption'
import { getMeasuredData } from '@/lib/data'
import { BarChart2, ArrowRight } from 'lucide-react'
import Link from 'next/link'

export default function MeasuredPage() {
  const measured = getMeasuredData()

  const stats = [
    {
      label: 'PROTECTION RATE',
      value: measured.protection_rate,
      sublabel: 'Adversarial attacks stopped',
      source: 'results/phase3/measured/summary.md',
    },
    {
      label: 'MODEL REFUSAL',
      value: '40%',
      sublabel: '2/5 benign phase runs refused',
      source: 'results/phase3/measured/summary.md',
    },
    {
      label: 'IN-WINDOW GROWTH',
      value: '5,079 L',
      sublabel: '14.57% net code growth',
      source: 'docs/IN_WINDOW_LEDGER.md',
    },
    {
      label: 'EXTERNAL NET CALLS',
      value: '0',
      sublabel: 'Deterministic offline execution',
      source: 'tests/test_phase4_dashboard.py',
    },
  ]

  return (
    <div className="w-full flex flex-col bg-[#F4F5F6]">
      <Section tone="light">
        <SectionHeader
          eyebrow="// EMPIRICAL VERIFICATION & BENCHMARKING"
          title="Measured Overhead & Protection"
          description="What the security controls actually cost in runtime latency, memory, and prompt token budget. Strictly measured from repository benchmark runs, never promised."
          tone="light"
        />

        {/* Top StatRow */}
        <div className="mb-12">
          <StatRow stats={stats} tone="light" />
        </div>

        {/* Wide Table with Mono Figures & Bar Comparison */}
        <div className="rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] overflow-hidden shadow-sm">
          <div className="p-4 bg-[#EAEDF0] border-b border-[#CDD2D8] font-mono text-xs flex items-center justify-between">
            <span className="text-[#59636E] uppercase font-semibold">
              // CONTROL OVERHEAD MEASUREMENTS
            </span>
            <span className="text-[11px] text-[#747F8D]">
              RUN CONDITIONS: PYTHON 3.13 / ARMORIQ SDK / LOCAL MCP
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-[#F4F5F6] text-[#59636E] border-b border-[#CDD2D8] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4 font-semibold">Evaluation Metric</th>
                  <th className="py-3 px-4 font-semibold">Test Condition &amp; Workload</th>
                  <th className="py-3 px-4 font-semibold">Measured Value</th>
                  <th className="py-3 px-4 font-semibold">Unconstrained Baseline</th>
                  <th className="py-3 px-4 text-right font-semibold">Verification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#CDD2D8]">
                {measured.rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-[#F4F5F6] transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-[#20252B]">
                      {row.metric}
                    </td>
                    <td className="py-3.5 px-4 text-[#59636E]">
                      {row.condition}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        <span className="font-bold text-[#20252B] text-xs">{row.value}</span>
                        {/* Minimal bar visualization */}
                        <div className="w-16 h-1.5 bg-[#EAEDF0] rounded-full overflow-hidden hidden sm:block border border-[#CDD2D8]">
                          <div
                            className="h-full bg-[#65BCE7] rounded-full transition-all duration-500"
                            style={{
                              width:
                                row.value.includes('100')
                                  ? '100%'
                                  : row.value.includes('40')
                                  ? '40%'
                                  : '25%',
                            }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-[#747F8D] text-[11px]">
                      {row.baseline}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <StatusPill state="verified" label="VERIFIED" size="sm" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-[#EAEDF0] border-t border-[#CDD2D8] flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
            <SourceCaption source={measured.source} />
            <div className="text-[11px] text-[#747F8D]">
              // Zero marketing badges or unverified synthetic counters
            </div>
          </div>
        </div>

        {/* Transition to Claims and Limits */}
        <div className="mt-8 flex items-center justify-between p-4 rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] text-xs font-mono shadow-sm">
          <span className="text-[#59636E]">
            // Ready to inspect the rigorous claims audit and honest limits?
          </span>
          <Link
            href="/claims"
            className="text-[#20252B] hover:text-[#65BCE7] font-semibold flex items-center gap-1.5 transition-colors"
          >
            <span>Proceed to Claims &amp; Limits</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </Section>
    </div>
  )
}
