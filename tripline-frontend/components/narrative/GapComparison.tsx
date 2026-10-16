'use client'

import React from 'react'
import { SectionHeader } from '../ui/SectionHeader'
import { Badge } from '../ui/Badge'
import { SourceCaption } from '../ui/SourceCaption'
import { ShieldCheck, AlertCircle } from 'lucide-react'

export interface GapComparisonProps {
  receipt?: any
  className?: string
}

export function GapComparison({ receipt, className = '' }: GapComparisonProps) {
  const hash = receipt?.canonical_hash || '84d707a125166845b8aaba424c23b3b77b758dad0c2bdbb3d3739e8f8dc449ec'
  const sig = receipt?.receipt_signature || 'eedc5214f6314bf44881a0a785dada909d60312795c4042bd8f073442180dfd7'
  const receiptId = receipt?.receipt_id || 'RCP-phase3-wow-ca5dcec9-call-p1_'

  return (
    <div className={`w-full ${className}`}>
      <SectionHeader
        eyebrow="// THE EPHEMERAL VERDICT PROBLEM"
        title="A block is a verdict. It is not a record."
        accentWord="record."
        description="Traditional AI guardrails block malicious actions in memory, print a transient log line, and discard forensic context. When an auditor asks for evidence, nothing verifiable exists."
        tone="light"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
        {/* Left Column: Illustrative Plain Guardrail Output */}
        <div
          className="rounded-[4px] border border-[var(--border-light)] bg-[var(--surface-light)] p-6 flex flex-col justify-between"
          aria-label="Illustrative traditional guardrail log line"
        >
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[var(--border-light)] font-mono text-xs">
              <span className="text-[var(--text-muted-on-light)] uppercase tracking-wider">
                TYPICAL GUARDRAIL OUTPUT
              </span>
              <span className="px-1.5 py-0.5 rounded-[2px] bg-amber-500/10 text-amber-800 border border-amber-500/30 font-mono text-[10px] font-bold">
                ILLUSTRATIVE
              </span>
            </div>

            <div className="p-4 rounded-[4px] bg-[#1E1E22] text-[#F3F1EA] font-mono text-xs leading-relaxed space-y-2 border border-[#2A2A2E]">
              <div className="text-[var(--text-faint-on-dark)]">
                [2026-10-10 13:32:55.101] [INFO] agent.worker: dispatching tool
              </div>
              <div className="text-red-400 font-bold">
                [2026-10-10 13:32:55.104] [ERROR] guardrail: ACTION DENIED: tool delete_branch not permitted
              </div>
              <div className="text-[var(--text-faint-on-dark)]">
                [2026-10-10 13:32:55.105] [INFO] agent.worker: continuing loop...
              </div>
            </div>

            <div className="mt-4 space-y-2 font-mono text-xs text-[var(--text-muted-on-light)]">
              <div className="flex items-center gap-2 text-red-700">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>Zero cryptographic bindings to inputs or state</span>
              </div>
              <div className="flex items-center gap-2 text-red-700">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>Easily purged, truncated, or fabricated in transit</span>
              </div>
              <div className="flex items-center gap-2 text-red-700">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>Cannot prove to an auditor whether MCP executed</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-3 border-t border-[var(--border-light)] text-[11px] font-mono text-[var(--text-faint-on-light)]">
            // Ephemeral log line discarded upon container shutdown
          </div>
        </div>

        {/* Right Column: Real Tripline Signed Incident Receipt */}
        <div className="rounded-[4px] border border-[var(--border-light)] bg-white p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[var(--border-light)] font-mono text-xs">
              <span className="text-[var(--text-on-light)] font-bold uppercase tracking-wider">
                TRIPLINE FORENSIC RECEIPT
              </span>
              <Badge state="verified" label="OFFLINE VERIFIABLE" size="sm" />
            </div>

            <div className="p-4 rounded-[4px] bg-[#0E0E12] text-[#F3F1EA] font-mono text-xs leading-relaxed space-y-2 border border-[var(--border-dark)]">
              <div className="text-[var(--text-muted-on-dark)]">
                // Canonical JSON envelope + HMAC signature
              </div>
              <div className="text-white font-semibold">
                receipt_id: &ldquo;{receiptId}&rdquo;
              </div>
              <div className="text-red-400">
                decision: &#123; armoriq: &ldquo;DENY&rdquo;, tripline: &ldquo;NONE (NOT REACHED)&rdquo; &#125;
              </div>
              <div className="text-emerald-400 break-all select-all pt-1 border-t border-[#2A2A2E]">
                canonical_hash: &ldquo;{hash}&rdquo;
              </div>
              <div className="text-blue-300 break-all select-all">
                receipt_signature: &ldquo;{sig}&rdquo;
              </div>
            </div>

            <div className="mt-4 space-y-2 font-mono text-xs text-[var(--text-muted-on-light)]">
              <div className="flex items-center gap-2 text-emerald-800">
                <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
                <span>Binds 10 immutable forensic fields under RFC 8785 canonicalization</span>
              </div>
              <div className="flex items-center gap-2 text-emerald-800">
                <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
                <span>1-byte modification breaks signature (make tamper)</span>
              </div>
              <div className="flex items-center gap-2 text-emerald-800">
                <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
                <span>Cryptographically verifiable offline with zero network calls</span>
              </div>
            </div>
          </div>

          <SourceCaption
            source="results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json"
            className="mt-6 pt-3 border-t border-[var(--border-light)] text-[var(--text-faint-on-light)]"
          />
        </div>
      </div>
    </div>
  )
}
