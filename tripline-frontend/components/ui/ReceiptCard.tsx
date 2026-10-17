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
  confidence?: any
  raw_json?: string
}

export interface ReceiptCardProps {
  receipt: ReceiptData
  showRawJsonToggle?: boolean
  onVerify?: () => void
  onTamper?: () => void
  isVerifying?: boolean
  className?: string
  variant?: 'light' | 'dark'
}

export function ReceiptCard({
  receipt,
  showRawJsonToggle = true,
  onVerify,
  onTamper,
  isVerifying = false,
  className = '',
  variant = 'light',
}: ReceiptCardProps) {
  const [showJson, setShowJson] = useState(false)
  const [copiedHash, setCopiedHash] = useState(false)
  const [copiedSig, setCopiedSig] = useState(false)
  const isLight = variant === 'light'

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
      className={`rounded-xl border ${
        isLight
          ? 'border-[#CDD2D8] bg-[#FFFFFF] text-[#20252B] shadow-sm'
          : 'border-[#3F444D] bg-[#181B20] text-[#F4F5F6]'
      } p-5 font-mono text-[13px] leading-[1.6] ${className}`}
    >
      {/* Header */}
      <div
        className={`flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b ${
          isLight ? 'border-[#CDD2D8]' : 'border-[#3F444D]'
        }`}
      >
        <div className="flex items-center gap-2">
          <span
            className={`text-xs uppercase tracking-wider ${
              isLight ? 'text-[#747F8D]' : 'text-[#9EA8B6]'
            }`}
          >
            INCIDENT RECEIPT
          </span>
          <span
            className={`font-semibold tracking-tight ${
              isLight ? 'text-[#20252B]' : 'text-white'
            }`}
          >
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
          <span
            className={`block text-xs uppercase tracking-wider ${
              isLight ? 'text-[#747F8D]' : 'text-[#9EA8B6]'
            }`}
          >
            Target Action
          </span>
          <span
            className={`font-mono text-xs break-all ${
              isLight ? 'text-[#20252B]' : 'text-white'
            }`}
          >
            {actionStr}
          </span>
        </div>

        <div>
          <span
            className={`block text-xs uppercase tracking-wider ${
              isLight ? 'text-[#747F8D]' : 'text-[#9EA8B6]'
            }`}
          >
            Enforcement Layer
          </span>
          <span
            className={`font-mono text-xs ${
              isLight ? 'text-[#20252B]' : 'text-white'
            }`}
          >
            {layerStr}
          </span>
        </div>

        <div>
          <span
            className={`block text-xs uppercase tracking-wider ${
              isLight ? 'text-[#747F8D]' : 'text-[#9EA8B6]'
            }`}
          >
            Timestamp
          </span>
          <span
            className={`font-mono text-xs ${
              isLight ? 'text-[#59636E]' : 'text-[#9EA8B6]'
            }`}
          >
            {receipt.created_at}
          </span>
        </div>

        <div>
          <span
            className={`block text-xs uppercase tracking-wider ${
              isLight ? 'text-[#747F8D]' : 'text-[#9EA8B6]'
            }`}
          >
            Run Reference
          </span>
          <span
            className={`font-mono text-xs ${
              isLight ? 'text-[#59636E]' : 'text-[#9EA8B6]'
            }`}
          >
            {receipt.run_id || receipt.incident_id || 'phase3-scenario'}
          </span>
        </div>

        <div
          className={`md:col-span-2 pt-2 border-t ${
            isLight ? 'border-[#CDD2D8]' : 'border-[#3F444D]'
          }`}
        >
          <div
            className={`flex items-center justify-between text-xs mb-1 ${
              isLight ? 'text-[#747F8D]' : 'text-[#9EA8B6]'
            }`}
          >
            <span>CANONICAL SHA-256 HASH</span>
            <button
              onClick={() => copyText(receipt.canonical_hash, setCopiedHash)}
              className={`${
                isLight ? 'hover:text-[#20252B]' : 'hover:text-white'
              } transition-colors flex items-center gap-1 cursor-pointer`}
              type="button"
            >
              {copiedHash ? <Check className="w-3 h-3 text-[#10B981]" /> : <Copy className="w-3 h-3" />}
              <span>{copiedHash ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <code
            className={`block p-2 rounded-lg text-xs break-all select-all border ${
              isLight
                ? 'bg-[#F4F5F6] border-[#CDD2D8] text-[#059669]'
                : 'bg-[#09090B] border-[#2A2A2E]/50 text-emerald-400'
            }`}
          >
            {receipt.canonical_hash}
          </code>
        </div>

        <div className="md:col-span-2">
          <div
            className={`flex items-center justify-between text-xs mb-1 ${
              isLight ? 'text-[#747F8D]' : 'text-[#9EA8B6]'
            }`}
          >
            <span>HMAC-SHA256 WITNESS SIGNATURE</span>
            <button
              onClick={() => copyText(receipt.receipt_signature, setCopiedSig)}
              className={`${
                isLight ? 'hover:text-[#20252B]' : 'hover:text-white'
              } transition-colors flex items-center gap-1 cursor-pointer`}
              type="button"
            >
              {copiedSig ? <Check className="w-3 h-3 text-[#10B981]" /> : <Copy className="w-3 h-3" />}
              <span>{copiedSig ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <code
            className={`block p-2 rounded-lg text-xs break-all select-all border ${
              isLight
                ? 'bg-[#F4F5F6] border-[#CDD2D8] text-[#59636E]'
                : 'bg-[#09090B] border-[#2A2A2E]/50 text-[#9EA8B6]'
            }`}
          >
            {receipt.receipt_signature}
          </code>
        </div>
      </div>

      {/* Action Buttons & Source Footer */}
      <div
        className={`mt-5 pt-3 border-t ${
          isLight ? 'border-[#CDD2D8]' : 'border-[#3F444D]'
        } flex flex-wrap items-center justify-between gap-3`}
      >
        <div className="flex items-center gap-2">
          {onVerify && (
            <button
              onClick={onVerify}
              disabled={isVerifying}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#20252B] hover:bg-[#2D3136] text-white font-semibold text-xs shadow-sm transition-colors cursor-pointer disabled:opacity-50"
              type="button"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-[#65BCE7]" />
              <span>{isVerifying ? 'Verifying...' : 'Verify Signature'}</span>
            </button>
          )}

          {onTamper && (
            <button
              onClick={onTamper}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-300 bg-red-50 hover:bg-red-100 text-red-700 text-xs font-semibold transition-colors cursor-pointer"
              type="button"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Simulate Tamper Check</span>
            </button>
          )}

          {showRawJsonToggle && (
            <button
              onClick={() => setShowJson(!showJson)}
              className={`px-2.5 py-1 text-xs ${
                isLight ? 'text-[#59636E] hover:text-[#20252B]' : 'text-[#9EA8B6] hover:text-white'
              } transition-colors cursor-pointer`}
              type="button"
            >
              {showJson ? 'Hide Raw JSON' : 'View Raw JSON'}
            </button>
          )}
        </div>

        {receipt.source_file && <SourceCaption source={receipt.source_file} className="mt-0" />}
      </div>

      {showJson && (
        <div
          className={`mt-4 pt-4 border-t ${
            isLight ? 'border-[#CDD2D8]' : 'border-[#3F444D]'
          }`}
        >
          <pre
            className={`p-3 rounded-lg text-xs overflow-x-auto max-h-72 border ${
              isLight
                ? 'bg-[#F4F5F6] text-[#20252B] border-[#CDD2D8]'
                : 'bg-[#08080A] text-[#9EA8B6] border-[#3F444D]'
            }`}
          >
            {receipt.raw_json || JSON.stringify(receipt, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
