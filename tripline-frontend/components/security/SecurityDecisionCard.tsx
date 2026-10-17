'use client'

import React from 'react'
import Link from 'next/link'
import {
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  AlertOctagon,
  FileText,
  ArrowRight,
  ExternalLink,
  Lock,
  Radio,
  CheckCircle2,
  Clock,
} from 'lucide-react'

export interface SecurityDecisionProps {
  action: string
  targetOrArgs?: string | Record<string, any>
  armoriqDecision?: 'ALLOW' | 'DENY' | 'UNAVAILABLE' | 'PENDING' | string
  armoriqReason?: string
  armoriqPolicy?: string
  triplineDecision?: 'ALLOW' | 'DENY' | 'HOLD' | 'UNCHECKED' | string
  triplineControl?: 'path_jail' | 'egress_canary' | 'parameter_sandbox' | string
  triplineReason?: string
  dispatchStatus?: 'EXECUTED' | 'BLOCKED' | 'HELD' | 'FAILED' | 'PENDING' | string
  executionOutcome?: string
  receiptId?: string
  verificationStatus?: string
  timestamp?: string
  className?: string
  compact?: boolean
}

export function SecurityDecisionCard({
  action,
  targetOrArgs,
  armoriqDecision = 'PENDING',
  armoriqReason,
  armoriqPolicy,
  triplineDecision = 'UNCHECKED',
  triplineControl,
  triplineReason,
  dispatchStatus = 'BLOCKED',
  executionOutcome,
  receiptId,
  verificationStatus,
  timestamp,
  className = '',
  compact = false,
}: SecurityDecisionProps) {
  // Normalize decisions
  const armoriqUpper = (armoriqDecision || '').toUpperCase()
  const triplineUpper = (triplineDecision || '').toUpperCase()
  const dispatchUpper = (dispatchStatus || '').toUpperCase()

  // Format arguments
  const argsText =
    typeof targetOrArgs === 'object' && targetOrArgs !== null
      ? JSON.stringify(targetOrArgs)
      : targetOrArgs || 'No arguments specified'

  return (
    <div
      className={`rounded-xl border border-[#1C1F33] bg-[#0C0E17] p-4.5 space-y-4 shadow-lg ${className}`}
    >
      {/* Header: Action & Dispatch Verdict */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 pb-3 border-b border-[#1C1F33]">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-white/5 border border-white/5 text-[#9A8CFF]">
            <Lock className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-mono text-[10px] text-[#6B6E7A] uppercase tracking-wider block">
              Proposed Operation
            </span>
            <span className="font-mono text-sm font-bold text-white tracking-wide">
              {action}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Dispatch Outcome Badge */}
          {dispatchUpper === 'EXECUTED' ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#10B981]/15 text-[#34D399] border border-[#10B981]/30 font-mono text-[11px] font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>DISPATCHED</span>
            </span>
          ) : dispatchUpper === 'HELD' ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#F59E0B]/15 text-[#FBBF24] border border-[#F59E0B]/30 font-mono text-[11px] font-semibold">
              <Radio className="w-3.5 h-3.5" />
              <span>QUARANTINED (HOLD)</span>
            </span>
          ) : dispatchUpper === 'FAILED' ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#EF4444]/15 text-[#F87171] border border-[#EF4444]/30 font-mono text-[11px] font-semibold">
              <AlertOctagon className="w-3.5 h-3.5" />
              <span>EXECUTION FAILED</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#374151]/25 text-[#9CA3AF] border border-[#4B5563]/30 font-mono text-[11px] font-semibold">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>NOT EXECUTED</span>
            </span>
          )}

          {timestamp && (
            <span className="font-mono text-[10px] text-[#6B6E7A] flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Target / Args Snippet */}
      <div className="bg-[#07080F] rounded-lg p-2.5 border border-white/5 font-mono text-xs">
        <span className="text-[#6B6E7A] text-[10px] uppercase block mb-1">Target / Parameter Payload:</span>
        <code className="text-[#AEB1BA] break-all leading-relaxed">{argsText}</code>
      </div>

      {/* Two-Layer Security Evaluation Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Layer 1: ArmorIQ Upstream Authorization */}
        <div className="p-3 rounded-lg bg-[#0F111D] border border-white/5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-[#9296AD]">
              1. ArmorIQ Authorization
            </span>
            {armoriqUpper === 'ALLOW' ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#10B981]/15 text-[#34D399] font-mono text-[10px] font-bold">
                <ShieldCheck className="w-3 h-3" />
                ALLOW
              </span>
            ) : armoriqUpper === 'DENY' ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#EF4444]/15 text-[#F87171] font-mono text-[10px] font-bold">
                <ShieldX className="w-3 h-3" />
                DENY
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-white/10 text-[#9CA3AF] font-mono text-[10px] font-bold">
                {armoriqUpper || 'UNAVAILABLE'}
              </span>
            )}
          </div>
          <p className="text-xs text-[#AEB1BA] leading-normal">
            {armoriqReason || (armoriqUpper === 'ALLOW' ? 'Action conforms to approved task intent' : 'Authorization denied by upstream policy')}
          </p>
          {armoriqPolicy && (
            <div className="font-mono text-[10px] text-[#6B6E7A] pt-1">
              Policy: <span className="text-white/80">{armoriqPolicy}</span>
            </div>
          )}
        </div>

        {/* Layer 2: TripLine Independent Containment */}
        <div className="p-3 rounded-lg bg-[#0F111D] border border-white/5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-[#9296AD]">
              2. TripLine Boundary ({triplineControl || 'in-MCP'})
            </span>
            {triplineUpper === 'ALLOW' ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#10B981]/15 text-[#34D399] font-mono text-[10px] font-bold">
                <ShieldCheck className="w-3 h-3" />
                ALLOW
              </span>
            ) : triplineUpper === 'HOLD' ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#F59E0B]/15 text-[#FBBF24] font-mono text-[10px] font-bold">
                <Radio className="w-3 h-3" />
                HOLD
              </span>
            ) : triplineUpper === 'DENY' ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#EF4444]/15 text-[#F87171] font-mono text-[10px] font-bold">
                <ShieldX className="w-3 h-3" />
                DENY
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-white/5 text-[#6B6E7A] font-mono text-[10px]">
                {triplineUpper || 'NOT REACHED'}
              </span>
            )}
          </div>
          <p className="text-xs text-[#AEB1BA] leading-normal">
            {triplineReason || (triplineUpper === 'DENY' ? 'Blocked by in-MCP path-jail boundary' : triplineUpper === 'HOLD' ? 'Quarantined by outbound canary egress trap' : 'Parameter boundaries confirmed')}
          </p>
        </div>
      </div>

      {/* Forensic Evidence Footer */}
      {(receiptId || executionOutcome) && (
        <div className="pt-2 border-t border-[#1C1F33] flex flex-wrap items-center justify-between gap-3 text-xs">
          {receiptId && (
            <div className="flex items-center gap-2 font-mono text-[11px]">
              <span className="text-[#6B6E7A]">Forensic Receipt:</span>
              <Link
                href={`/receipts?id=${encodeURIComponent(receiptId)}`}
                className="inline-flex items-center gap-1 text-[#9A8CFF] hover:underline font-semibold"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>{receiptId}</span>
              </Link>
              {verificationStatus && (
                <span className="px-1.5 py-0.2 rounded bg-white/5 text-[10px] text-[#AEB1BA]">
                  {verificationStatus}
                </span>
              )}
            </div>
          )}

          {executionOutcome && (
            <div className="font-mono text-[11px] text-[#AEB1BA]">
              <span className="text-[#6B6E7A]">Result: </span>
              <span>{executionOutcome}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
