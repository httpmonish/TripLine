'use client'

import React from 'react'
import { Check, X, ShieldCheck, AlertTriangle } from 'lucide-react'

export interface VerifyStripProps {
  status?: 'VERIFIED' | 'TAMPER_DETECTED' | 'IDLE' | 'VERIFYING'
  canonicalHash?: string
  computedHash?: string
  className?: string
}

export function VerifyStrip({
  status = 'VERIFIED',
  canonicalHash,
  computedHash,
  className = '',
}: VerifyStripProps) {
  const steps = [
    { num: '01', title: 'Select Receipt', desc: 'Read immutable fields' },
    { num: '02', title: 'Canonicalize JSON', desc: 'RFC 8785 key sort' },
    { num: '03', title: 'Recompute Hash', desc: 'SHA-256 + HMAC' },
    { num: '04', title: 'Compare', desc: 'Constant-time verification' },
  ]

  const isVerified = status === 'VERIFIED'
  const isTamper = status === 'TAMPER_DETECTED'
  const isVerifying = status === 'VERIFYING'

  return (
    <div
      className={`rounded-[4px] border border-[var(--border-dark)] bg-[#0B0B0D] p-5 font-mono text-xs text-[#F3F1EA] ${className}`}
      data-testid="diagram-d5"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-4 border-b border-[var(--border-dark)]">
        <span className="text-[var(--text-muted-on-dark)] uppercase tracking-wider text-[11px]">
          // FOUR-STEP CRYPTOGRAPHIC VERIFICATION STRIP
        </span>
        <div className="flex items-center gap-2">
          {isVerifying && (
            <span className="text-blue-400 font-semibold animate-pulse">
              ● VERIFYING...
            </span>
          )}
          {isVerified && (
            <span className="text-[var(--state-allow)] font-bold flex items-center gap-1">
              <ShieldCheck className="w-4 h-4" />
              <span>VERIFIED</span>
            </span>
          )}
          {isTamper && (
            <span className="text-[var(--state-deny)] font-bold flex items-center gap-1">
              <AlertTriangle className="w-4 h-4" />
              <span>TAMPER_DETECTED</span>
            </span>
          )}
        </div>
      </div>

      {/* 4 sequential step blocks */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {steps.map((step, idx) => {
          const isFinal = idx === 3
          let borderStyle = 'border-[var(--border-dark)] bg-[#121215]'
          if (isVerified) {
            borderStyle = isFinal
              ? 'border-[var(--state-allow)] bg-[rgba(47,191,113,0.08)]'
              : 'border-[var(--border-dark)] bg-[#141418]'
          } else if (isTamper && isFinal) {
            borderStyle = 'border-[var(--state-deny)] bg-[rgba(229,72,77,0.08)]'
          }

          return (
            <div
              key={step.num}
              className={`p-3 rounded-[2px] border ${borderStyle} transition-colors`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-[var(--text-faint-on-dark)]">
                  {step.num}
                </span>
                {idx < 3 && isVerified && (
                  <Check className="w-3 h-3 text-[var(--state-allow)]" />
                )}
                {isFinal && isVerified && (
                  <ShieldCheck className="w-3.5 h-3.5 text-[var(--state-allow)]" />
                )}
                {isFinal && isTamper && (
                  <X className="w-3.5 h-3.5 text-[var(--state-deny)]" />
                )}
              </div>
              <div className="font-semibold text-white text-[11px]">
                {step.title}
              </div>
              <div className="text-[10px] text-[var(--text-muted-on-dark)] mt-0.5">
                {step.desc}
              </div>
            </div>
          )
        })}
      </div>

      {(canonicalHash || computedHash) && (
        <div className="mt-4 pt-3 border-t border-[var(--border-dark)] space-y-1 text-[11px]">
          {canonicalHash && (
            <div className="flex items-center justify-between text-[var(--text-muted-on-dark)]">
              <span>DECLARED HASH:</span>
              <code className="text-white select-all">{canonicalHash}</code>
            </div>
          )}
          {computedHash && (
            <div className="flex items-center justify-between text-[var(--text-muted-on-dark)]">
              <span>RECOMPUTED:</span>
              <code
                className={
                  computedHash === canonicalHash
                    ? 'text-[var(--state-allow)]'
                    : 'text-[var(--state-deny)]'
                }
              >
                {computedHash}
              </code>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
