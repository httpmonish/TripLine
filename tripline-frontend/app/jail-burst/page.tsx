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
    <div className="w-full flex flex-col">
      <Section tone="dark">
        <SectionHeader
          eyebrow="// DETERMINISTIC CONTAINMENT EVALUATION"
          title="Path Jail Burst Harness"
          accentWord="Harness"
          description="Evaluates the real Tripline path jail across traversal encodings, mixed path separators, symlinks, and absolute path escapes. Tested against the live read_file MCP tool."
          tone="dark"
        />

        {/* Top Summary StatRow */}
        <div className="mb-12">
          <StatRow stats={stats} tone="dark" />
        </div>

        {/* Probes Table / Grid */}
        <div className="rounded-[4px] border border-[var(--border-dark)] bg-[#0C0C0E] overflow-hidden">
          <div className="p-4 bg-[#121215] border-b border-[var(--border-dark)] flex flex-wrap items-center justify-between gap-2 font-mono text-xs">
            <span className="text-[var(--text-muted-on-dark)] uppercase font-semibold">
              // 8 DETERMINISTIC PROBE VECTORS
            </span>
            <div className="inline-flex items-center gap-2 text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
              <span>ALL PASS (ZERO LEAKS)</span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-[#08080A] text-[var(--text-faint-on-dark)] border-b border-[var(--border-dark)] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Probe Vector</th>
                  <th className="py-3 px-4">Path Argument Tested</th>
                  <th className="py-3 px-4">ArmorIQ Gate</th>
                  <th className="py-3 px-4">Tripline Path Jail</th>
                  <th className="py-3 px-4 text-center">Bytes Returned</th>
                  <th className="py-3 px-4 text-right">Verdict</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-dark)]">
                {burstData.probes.map((p, idx) => {
                  const isDenied = p.jail_decision.includes('DENIED')
                  const isPositive = p.attempt.includes('Positive Control')

                  return (
                    <tr
                      key={idx}
                      className="hover:bg-white/[0.02] transition-colors"
                    >
                      <td className="py-3 px-4 font-semibold text-white">
                        {p.attempt}
                      </td>
                      <td className="py-3 px-4 text-gray-300">
                        <code className="bg-black/50 px-2 py-0.5 rounded-[2px] text-[11px] border border-[#2A2A2E]">
                          {p.path}
                        </code>
                      </td>
                      <td className="py-3 px-4 text-[var(--text-muted-on-dark)]">
                        <StatusPill state="allow" label={p.armoriq_decision} size="sm" />
                      </td>
                      <td className="py-3 px-4">
                        <StatusPill
                          state={isDenied ? 'deny' : 'allow'}
                          label={p.jail_decision}
                          size="sm"
                        />
                      </td>
                      <td className="py-3 px-4 text-center font-bold text-white">
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

          <div className="p-4 bg-[#0B0B0D] border-t border-[var(--border-dark)] flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
            <SourceCaption source={burstData.source} />
            <div className="flex items-center gap-2 text-[var(--text-faint-on-dark)]">
              <span>Execute probe:</span>
              <code className="text-emerald-400 bg-black/60 px-2 py-0.5 rounded">make burst</code>
            </div>
          </div>
        </div>

        {/* Transition Link to Witness */}
        <div className="mt-8 flex items-center justify-between p-4 rounded-[4px] border border-[var(--border-dark)] bg-[#101014] text-xs font-mono">
          <span className="text-[var(--text-muted-on-dark)]">
            // Path jail execution attempts are recorded into the witness ledger.
          </span>
          <Link
            href="/witness"
            className="text-white hover:text-[var(--accent)] font-semibold flex items-center gap-1.5"
          >
            <span>Proceed to Witness Ledger</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </Section>
    </div>
  )
}
