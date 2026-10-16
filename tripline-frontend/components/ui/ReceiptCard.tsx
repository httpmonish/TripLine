'use client'

import React, { useState } from 'react'
import { Badge, SecurityState } from './Badge'
import { SourceCaption } from './SourceCaption'
import { Check, Copy, ShieldCheck, AlertTriangle } from 'lucide-react'

export interface ReceiptData {
  receipt_id: string
  incident_id?: string
  run_id?: string
  created_at: string
  action?: string
  layer?: string
  verdict?: string
  canonical_hash: string
  receipt_signature: string
  witness_head_hmac?: string
  verification_status?: 'VERIFIED' | 'TAMPER_DETECTED' | 'UNVERIFIED'
  source_file?: string
  proposal?: any
  decision?: any
  witness?: any
  raw_json?: string
}

export interface ReceiptCardProps {
  receipt: ReceiptData
  showRawJsonToggle?: boolean
  onVerify?: () => void
  onTamper?: () => void
  isVerifying?: boolean
  className?: string
}

export function ReceiptCard({
  receipt,
  showRawJsonToggle = true,
  onVerify,
  onTamper,
  isVerifying = false,
  className = '',
}: ReceiptCardProps) {
  const [showJson, setShowJson] = useState(false)
  const [copiedHash, setCopiedHash] = useState(false)
  const [copiedSig, setCopiedSig] = useState(false)

  // Map verdict to SecurityState
  let state: SecurityState = 'deny'
  const verdictStr = String(receipt.verdict || receipt.decision?.tripline_decision || '').toUpperCase()
  if (verdictStr.includes('ALLOW')) state = 'allow'
  else if (verdictStr.includes('HOLD')) state = 'hold'
  else if (verdictStr.includes('DENY')) state = 'deny'

  const actionStr =
    receipt.action ||
    (receipt.proposal?.tool
      ? `${receipt.proposal.tool}(${JSON.stringify(receipt.proposal.args || {})})`
      : 'delete_branch(stale/old-experiment)')

  const layerStr =
    receipt.layer ||
    (receipt.decision?.tripline_decision === 'HOLD'
      ? 'L2 Egress Gateway'
      : receipt.decision?.armoriq_decision === 'DENY'
      ? 'L0 ArmorIQ Policy'
      : 'L1 Tripline Path Jail')

  const copyText = (text: string, setter: (val: boolean) => void) => {
    navigator.clipboard?.writeText(text)
    setter(true)
    setTimeout(() => setter(false), 1200)
  }

  const verStatus = receipt.verification_status || 'VERIFIED'
  const verState: SecurityState =
    verStatus === 'VERIFIED' ? 'verified' : verStatus === 'TAMPER_DETECTED' ? 'tamper' : 'idle'

  return (
    <div
      className={`rounded-[4px] border border-[var(--border-dark)] bg-[#121215] text-[#F3F1EA] p-5 font-mono text-[13px] leading-[1.6] ${className}`}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b border-[var(--border-dark)]">
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase tracking-wider text-[var(--text-faint-on-dark)]">
            INCIDENT RECEIPT
          </span>
          <span className="font-semibold text-white tracking-tight">
            {receipt.receipt_id}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Badge state={state} label={verdictStr || 'DENIED'} />
          <Badge state={verState} label={verStatus} />
        </div>
      </div>

      {/* Grid Key-Values */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
        <div>
          <span className="block text-xs uppercase tracking-wider text-[var(--text-faint-on-dark)]">
            Target Action
          </span>
          <span className="font-mono text-white text-xs break-all">
            {actionStr}
          </span>
        </div>

        <div>
          <span className="block text-xs uppercase tracking-wider text-[var(--text-faint-on-dark)]">
            Enforcement Layer
          </span>
          <span className="font-mono text-white text-xs">{layerStr}</span>
        </div>

        <div>
          <span className="block text-xs uppercase tracking-wider text-[var(--text-faint-on-dark)]">
            Timestamp
          </span>
          <span className="font-mono text-[var(--text-muted-on-dark)] text-xs">
            {receipt.created_at}
          </span>
        </div>

        <div>
          <span className="block text-xs uppercase tracking-wider text-[var(--text-faint-on-dark)]">
            Run Reference
          </span>
          <span className="font-mono text-[var(--text-muted-on-dark)] text-xs">
            {receipt.run_id || receipt.incident_id || 'phase3-scenario'}
          </span>
        </div>

        <div className="md:col-span-2 pt-2 border-t border-[var(--border-dark)]/50">
          <div className="flex items-center justify-between text-xs text-[var(--text-faint-on-dark)] mb-1">
            <span>CANONICAL SHA-256 HASH</span>
            <button
              onClick={() => copyText(receipt.canonical_hash, setCopiedHash)}
              className="hover:text-white transition-colors flex items-center gap-1 cursor-pointer"
              type="button"
            >
              {copiedHash ? <Check className="w-3 h-3 text-[var(--state-allow)]" /> : <Copy className="w-3 h-3" />}
              <span>{copiedHash ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <code className="block bg-[#09090B] p-2 rounded-[2px] text-xs text-emerald-400 break-all select-all border border-[#2A2A2E]/50">
            {receipt.canonical_hash}
          </code>
        </div>

        <div className="md:col-span-2">
          <div className="flex items-center justify-between text-xs text-[var(--text-faint-on-dark)] mb-1">
            <span>HMAC-SHA256 WITNESS SIGNATURE</span>
            <button
              onClick={() => copyText(receipt.receipt_signature, setCopiedSig)}
              className="hover:text-white transition-colors flex items-center gap-1 cursor-pointer"
              type="button"
            >
              {copiedSig ? <Check className="w-3 h-3 text-[var(--state-allow)]" /> : <Copy className="w-3 h-3" />}
              <span>{copiedSig ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <code className="block bg-[#09090B] p-2 rounded-[2px] text-xs text-[var(--text-muted-on-dark)] break-all select-all border border-[#2A2A2E]/50">
            {receipt.receipt_signature}
          </code>
        </div>
      </div>

      {/* Action Buttons & Source Footer */}
      <div className="mt-5 pt-3 border-t border-[var(--border-dark)] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {onVerify && (
            <button
              onClick={onVerify}
              disabled={isVerifying}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-[2px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[#0B0B0C] font-semibold text-xs transition-colors cursor-pointer disabled:opacity-50"
              type="button"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{isVerifying ? 'Verifying...' : 'Verify Signature'}</span>
            </button>
          )}

          {onTamper && (
            <button
              onClick={onTamper}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-[2px] border border-red-500/50 hover:bg-red-500/10 text-red-400 text-xs transition-colors cursor-pointer"
              type="button"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Simulate Tamper Check</span>
            </button>
          )}

          {showRawJsonToggle && (
            <button
              onClick={() => setShowJson(!showJson)}
              className="px-2.5 py-1 text-xs text-[var(--text-muted-on-dark)] hover:text-white transition-colors cursor-pointer"
              type="button"
            >
              {showJson ? 'Hide Raw JSON' : 'View Raw JSON'}
            </button>
          )}
        </div>

        {receipt.source_file && <SourceCaption source={receipt.source_file} className="mt-0" />}
      </div>

      {showJson && (
        <div className="mt-4 pt-4 border-t border-[var(--border-dark)]">
          <pre className="p-3 bg-[#08080A] rounded-[2px] text-xs text-[var(--text-muted-on-dark)] overflow-x-auto max-h-72 border border-[var(--border-dark)]">
            {receipt.raw_json || JSON.stringify(receipt, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
