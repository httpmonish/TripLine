'use client'

import React, { useState } from 'react'
import { Badge, StatusPill, SecurityState } from '../ui/Badge'
import { SourceCaption } from '../ui/SourceCaption'
import Link from 'next/link'
import { ArrowRight, CheckCircle2 } from 'lucide-react'

export interface LayerMatrixProps {
  previewMode?: boolean
  className?: string
}

export function LayerMatrix({ previewMode = false, className = '' }: LayerMatrixProps) {
  const [selectedAttackId, setSelectedAttackId] = useState<'attack_1' | 'attack_2' | 'attack_3'>('attack_1')

  const attacks = [
    {
      id: 'attack_1',
      label: 'Attack 1: delete_branch',
      action: 'delete_branch(stale/old-experiment)',
      stoppedAt: 'L0',
      receiptId: 'receipt_P1_ARMORIQ_DENY.json',
      source: 'results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json',
    },
    {
      id: 'attack_2',
      label: 'Attack 2: Path Traversal',
      action: 'read_file(../../fake_home/.ssh/id_rsa)',
      stoppedAt: 'L1',
      receiptId: 'receipt_P2_JAIL_DENY.json',
      source: 'results/phase3/scenario/receipt_P2_JAIL_DENY.json',
    },
    {
      id: 'attack_3',
      label: 'Attack 3: Canary Exfil',
      action: 'comment_issue(body with TRPL-...)',
      stoppedAt: 'L2',
      receiptId: 'receipt_P3_GATEWAY_HOLD.json',
      source: 'results/phase3/scenario/receipt_P3_GATEWAY_HOLD.json',
    },
  ] as const

  const layers = [
    {
      id: 'L0',
      name: 'ArmorIQ Session Policy',
      mechanism: 'session.check() evaluates ToolCall against agent allowlist',
      getVerdict: (atk: string) =>
        atk === 'attack_1'
          ? { state: 'deny' as SecurityState, text: 'DENY (tool_not_in_allowlist)' }
          : { state: 'allow' as SecurityState, text: 'ALLOW (In policy)' },
    },
    {
      id: 'L1',
      name: 'Tripline Path Jail',
      mechanism: 'fstat descriptor check guarantees target is inside workspace root',
      getVerdict: (atk: string) => {
        if (atk === 'attack_1') return { state: 'idle' as SecurityState, text: 'NOT REACHED' }
        if (atk === 'attack_2')
          return { state: 'deny' as SecurityState, text: 'DENY (PATH_OUTSIDE_ROOT)' }
        return { state: 'allow' as SecurityState, text: 'ALLOW (Inside Root)' }
      },
    },
    {
      id: 'L2',
      name: 'Tripline Egress Gateway',
      mechanism: 'Exact-match canary token scanner (substring search in outbound payloads)',
      getVerdict: (atk: string) => {
        if (atk === 'attack_1' || atk === 'attack_2')
          return { state: 'idle' as SecurityState, text: 'NOT REACHED' }
        return { state: 'hold' as SecurityState, text: 'HOLD (egress_canary_hit)' }
      },
    },
    {
      id: 'L3',
      name: 'Local Witness Recorder',
      mechanism: 'Append-only HMAC hash chain (.tripline/witness/) records execution state',
      getVerdict: () => ({ state: 'verified' as SecurityState, text: 'RECORDED (0 executions)' }),
    },
    {
      id: 'L4',
      name: 'Incident Receipt Engine',
      mechanism: 'Canonical JSON (RFC 8785 subset) SHA-256 hash + HMAC-SHA256 signature',
      getVerdict: () => ({ state: 'verified' as SecurityState, text: 'SEALED & VERIFIED' }),
    },
  ]

  const activeAttack = attacks.find((a) => a.id === selectedAttackId)!

  return (
    <div
      className={`rounded-[4px] border border-[var(--border-dark)] bg-[#0C0C0E] p-6 text-[#F3F1EA] ${className}`}
      data-testid="diagram-d3"
    >
      {/* Top Header & Attack Selector */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 mb-6 border-b border-[var(--border-dark)]">
        <div>
          <span className="font-mono text-xs text-[var(--text-muted-on-dark)] uppercase tracking-wider block mb-1">
            // 5-LAYER CONTAINMENT MATRIX &amp; RECORDED ATTACKS
          </span>
          <h3 className="font-sans text-xl font-bold text-white tracking-tight">
            Attack Interception &amp; Attribution Trace
          </h3>
        </div>

        {/* Attack Selector Buttons */}
        <div className="flex flex-wrap gap-2">
          {attacks.map((atk) => (
            <button
              key={atk.id}
              onClick={() => setSelectedAttackId(atk.id)}
              className={`px-3 py-1.5 rounded-[2px] font-mono text-xs transition-colors cursor-pointer focus-ring ${
                selectedAttackId === atk.id
                  ? 'bg-[var(--accent)] text-[#0B0B0C] font-semibold'
                  : 'bg-[#18181C] text-[var(--text-muted-on-dark)] hover:text-white border border-[var(--border-dark)]'
              }`}
              type="button"
            >
              {atk.label}
            </button>
          ))}
        </div>
      </div>

      {/* Target Action Banner */}
      <div className="p-3 mb-6 rounded-[2px] bg-[#121215] border border-[var(--border-dark)] font-mono text-xs flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-[var(--text-faint-on-dark)]">AGENT ATTEMPT:</span>
          <code className="text-white bg-black/40 px-2 py-0.5 rounded-[2px]">
            {activeAttack.action}
          </code>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[var(--text-faint-on-dark)]">STOPPED BY:</span>
          <span className="font-bold text-[var(--accent)]">{activeAttack.stoppedAt}</span>
          <Link
            href={`/receipts?file=${activeAttack.receiptId}`}
            className="text-xs text-emerald-400 hover:underline flex items-center gap-1"
          >
            <span>View Receipt</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* 5 Layer Horizontal Bands (L0 to L4) */}
      <div className="space-y-3">
        {layers.map((layer) => {
          const verdict = layer.getVerdict(selectedAttackId)
          const isStoppingLayer = layer.id === activeAttack.stoppedAt

          return (
            <div
              key={layer.id}
              className={`p-4 rounded-[4px] border transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3 ${
                isStoppingLayer
                  ? 'border-[var(--accent)] bg-[#171413]'
                  : 'border-[var(--border-dark)] bg-[#101013]'
              }`}
            >
              <div className="flex items-start md:items-center gap-3">
                <span className="font-mono text-sm font-bold text-white px-2 py-0.5 rounded-[2px] bg-white/10 shrink-0">
                  {layer.id}
                </span>
                <div>
                  <div className="font-mono text-xs font-semibold text-white">
                    {layer.name}
                  </div>
                  <div className="text-xs text-[var(--text-muted-on-dark)] mt-0.5">
                    {layer.mechanism}
                  </div>
                </div>
              </div>

              <div className="shrink-0 flex items-center gap-2">
                <StatusPill state={verdict.state} label={verdict.text} />
              </div>
            </div>
          )
        })}
      </div>

      <SourceCaption
        source={activeAttack.source}
        className="mt-6"
      />
    </div>
  )
}
