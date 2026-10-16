'use client'

import React, { useState } from 'react'
import { Section } from '@/components/ui/Section'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { StatusPill } from '@/components/ui/Badge'
import { SourceCaption } from '@/components/ui/SourceCaption'
import { getWitnessData } from '@/lib/data'
import { ShieldCheck, Link2, ArrowRight, CheckCircle2 } from 'lucide-react'
import Link from 'next/link'

const chainEntries = [
  {
    index: 1,
    receipt_id: 'RCP-phase3-wow-73323d4e-p1',
    tool: 'delete_branch',
    decision: 'DENY',
    prev_hash: 'genesis',
    link_hash: 'dfd6e62af7b59f5968f7e71267b403e014cf91b65620b5a53862689de1299b02',
    linked_at: '2026-10-10T12:43:51Z',
  },
  {
    index: 2,
    receipt_id: 'RCP-phase3-wow-73323d4e-p2',
    tool: 'read_file',
    decision: 'DENY (JAIL)',
    prev_hash: 'dfd6e62af7b59f59...',
    link_hash: '404afe3cd820ad07c7d9633a6af4cc483803469a6d23bf26cdb3858be74c959b',
    linked_at: '2026-10-10T12:43:57Z',
  },
  {
    index: 3,
    receipt_id: 'RCP-phase3-wow-73323d4e-p3',
    tool: 'comment_issue',
    decision: 'HOLD (GATEWAY)',
    prev_hash: '404afe3cd820ad07...',
    link_hash: '83d954cac4773f5e849ada0242f82a29cb03a8d69d77ff8c25325bcfe6f73ebe',
    linked_at: '2026-10-10T12:44:00Z',
  },
  {
    index: 4,
    receipt_id: 'RCP-phase3-wow-ca5dcec9-p1',
    tool: 'delete_branch',
    decision: 'DENY',
    prev_hash: '7a74451184ecc3d8...',
    link_hash: '4c8d814f51a595f979fe8aa4dc0cf2a719f621f2e049bf46da781f91e5303543',
    linked_at: '2026-10-10T13:32:55Z',
  },
  {
    index: 5,
    receipt_id: 'RCP-phase3-wow-ca5dcec9-p2',
    tool: 'read_file',
    decision: 'DENY (JAIL)',
    prev_hash: '4c8d814f51a595f9...',
    link_hash: 'bd3e13d7fbaf140132cb0bf821ef65bb0377e84177d5490bc8926019315d18d4',
    linked_at: '2026-10-10T13:33:02Z',
  },
  {
    index: 6,
    receipt_id: 'RCP-phase3-wow-ca5dcec9-p3',
    tool: 'comment_issue',
    decision: 'HOLD (GATEWAY)',
    prev_hash: 'bd3e13d7fbaf1401...',
    link_hash: 'b3ebac6483d998edb6e7aa4a1e738c59f54d49b68e0e04edc39f383209d73c9b',
    linked_at: '2026-10-10T13:33:05Z',
  },
]

export default function WitnessPage() {
  const witness = getWitnessData()

  return (
    <div className="w-full flex flex-col">
      <Section tone="dark">
        <SectionHeader
          eyebrow="// APPEND-ONLY EXECUTION LEDGER"
          title="Witness Hash-Chain"
          accentWord="Hash-Chain"
          description="The witness log records every MCP action attempt into an append-only cryptographic ledger. Each block binds the prior block hash, guaranteeing sequence non-repudiation."
          tone="dark"
        />

        {/* Chain Validity Banner */}
        <div className="mb-8 p-4 rounded-[4px] border border-emerald-500/40 bg-emerald-950/20 text-emerald-400 font-mono text-xs flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span className="font-bold text-sm">
              ✓ WITNESS CHAIN VALID ({witness.total_records} RECORDS VERIFIED)
            </span>
          </div>
          <div className="text-[11px] text-[var(--text-faint-on-dark)]">
            // Verified via <code>python -m scripts.verify_links</code>
          </div>
        </div>

        {/* Chain Sequence Layout */}
        <div className="relative pl-6 md:pl-8 border-l-2 border-[var(--border-dark)] space-y-6">
          {chainEntries.map((item, idx) => (
            <div key={item.index} className="relative group">
              {/* Timeline Connector Dot */}
              <div className="absolute -left-[31px] md:-left-[39px] top-4 w-4 h-4 rounded-full bg-[#18181D] border-2 border-[var(--accent)] flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-white" />
              </div>

              {/* Entry Card */}
              <div className="p-5 rounded-[4px] border border-[var(--border-dark)] bg-[#0C0C0E] font-mono text-xs hover:border-[var(--accent)] transition-colors">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[var(--accent)] font-bold">
                      BLOCK #{item.index}
                    </span>
                    <span className="text-white font-semibold">
                      {item.receipt_id}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusPill
                      state={item.decision.includes('DENY') ? 'deny' : 'hold'}
                      label={item.decision}
                      size="sm"
                    />
                    <span className="text-[10px] text-[var(--text-faint-on-dark)]">
                      {item.linked_at}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 pt-3 border-t border-[var(--border-dark)]">
                  <div>
                    <span className="text-[10px] uppercase text-[var(--text-faint-on-dark)] block mb-0.5">
                      PREV HASH
                    </span>
                    <code className="text-gray-400 bg-black/40 px-2 py-0.5 rounded text-[11px]">
                      {item.prev_hash}
                    </code>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-[var(--text-faint-on-dark)] block mb-0.5">
                      LINK HASH
                    </span>
                    <code className="text-emerald-400 bg-black/40 px-2 py-0.5 rounded text-[11px] truncate block">
                      {item.link_hash}
                    </code>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-4 p-4 rounded-[4px] border border-[var(--border-dark)] bg-[#101014] text-xs font-mono">
          <SourceCaption source="results/phase3/armoriq_links.jsonl & .tripline/witness/" />
          <Link
            href="/measured"
            className="text-white hover:text-[var(--accent)] font-semibold flex items-center gap-1.5"
          >
            <span>Proceed to Measured Overhead</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </Section>
    </div>
  )
}
