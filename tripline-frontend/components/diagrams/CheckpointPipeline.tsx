'use client'

import React, { useState } from 'react'
import { Badge } from '../ui/Badge'
import { SourceCaption } from '../ui/SourceCaption'

export function CheckpointPipeline({ className = '' }: { className?: string }) {
  const [activeStep, setActiveStep] = useState<number | null>(null)

  const checkpoints = [
    {
      num: '01',
      title: 'Capture',
      sdk: 'capture_plan(llm, prompt, plan)',
      desc: 'Planner boundary capture of declared intent graph before invocation.',
    },
    {
      num: '02',
      title: 'Evaluate',
      sdk: 'get_intent_token(captured)',
      desc: 'Matches declared intent against identity and policy. Ed25519-signed token.',
    },
    {
      num: '03',
      title: 'Enforce',
      sdk: 'invoke(mcp, action, intent_token)',
      desc: 'Proxy step verification with Merkle inclusion proof over reasoning graph.',
      verdicts: ['allow', 'hold', 'block'],
    },
    {
      num: '04',
      title: 'Prove',
      sdk: 'audit_record(session)',
      desc: 'Central intent-assurance audit trail of agent action decisions.',
    },
  ]

  return (
    <div
      className={`rounded-[4px] border border-[var(--border-dark)] bg-[#0C0C0E] p-6 text-[#F3F1EA] ${className}`}
      data-testid="diagram-d2"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 pb-4 mb-6 border-b border-[var(--border-dark)] font-mono text-xs">
        <span className="text-[var(--text-muted-on-dark)] uppercase tracking-wider">
          // UPSTREAM INTENT ASSURANCE: ARMORIQ FOUR CHECKPOINTS
        </span>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-[var(--text-faint-on-dark)]">VERDICTS:</span>
          <Badge state="allow" label="allow" size="sm" />
          <Badge state="hold" label="hold" size="sm" />
          <Badge state="deny" label="block" size="sm" />
        </div>
      </div>

      {/* Responsive SVG / Layout */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
        {checkpoints.map((cp, idx) => (
          <div
            key={cp.num}
            onMouseEnter={() => setActiveStep(idx)}
            onMouseLeave={() => setActiveStep(null)}
            className={`p-4 rounded-[4px] border transition-all duration-200 ${
              activeStep === idx
                ? 'border-[var(--accent)] bg-[#141418]'
                : 'border-[var(--border-dark)] bg-[#101013]'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-xs text-[var(--accent)] font-bold">
                {cp.num}
              </span>
              <span className="font-mono text-xs text-white font-semibold">
                {cp.title}
              </span>
            </div>

            <p className="text-xs text-[var(--text-muted-on-dark)] mb-3 leading-relaxed">
              {cp.desc}
            </p>

            <code className="block bg-[#08080A] p-2 rounded-[2px] text-[11px] font-mono text-emerald-400 break-all border border-[#2A2A2E]/60">
              {cp.sdk}
            </code>
          </div>
        ))}
      </div>

      {/* Row 2: Tripline Adds (Contain & Prove Offline) */}
      <div className="mt-6 pt-5 border-t border-[var(--border-dark)]">
        <div className="flex items-center gap-2 mb-3 font-mono text-xs text-[var(--text-faint-on-dark)] uppercase">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
          <span>TRIPLINE ADDS DOWNSTREAM:</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-[4px] border border-[var(--border-dark)] bg-[#101013] border-l-2 border-l-[var(--accent)]">
            <div className="font-mono text-xs font-semibold text-white mb-1">
              Contain (Path Jail &amp; Canary Gate)
            </div>
            <p className="text-xs text-[var(--text-muted-on-dark)] leading-relaxed">
              In-MCP boundary check verifying open descriptor inodes via <code>fstat</code> (0 bytes leaked on traversal), and exact-match outbound canary traps (HOLD before network).
            </p>
          </div>

          <div className="p-4 rounded-[4px] border border-[var(--border-dark)] bg-[#101013] border-l-2 border-l-[var(--state-allow)]">
            <div className="font-mono text-xs font-semibold text-white mb-1">
              Prove Offline (Witness Ledger &amp; HMAC Receipts)
            </div>
            <p className="text-xs text-[var(--text-muted-on-dark)] leading-relaxed">
              Append-only witness HMAC chain binding tool execution counts, and offline Canonical JSON receipts verifiable via <code>make verify</code> with zero network dependencies.
            </p>
          </div>
        </div>
      </div>

      <SourceCaption
        source="Checkpoint model: ArmorIQ Intent Engine documentation & docs/ARCHITECTURE.md"
        className="mt-4"
      />
    </div>
  )
}
