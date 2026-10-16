'use client'

import React, { useState, useEffect } from 'react'
import { Section } from '@/components/ui/Section'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { ReceiptCard } from '@/components/ui/ReceiptCard'
import { VerifyStrip } from '@/components/diagrams/VerifyStrip'
import { Badge, StatusPill, SecurityState } from '@/components/ui/Badge'
import { SourceCaption } from '@/components/ui/SourceCaption'
import { EmptyState } from '@/components/ui/EmptyState'
import { getReceipts, verifyReceiptLocally, ReceiptRecord } from '@/lib/data'
import { ShieldCheck, Search, AlertTriangle, ArrowRight } from 'lucide-react'
import Link from 'next/link'

export default function ReceiptsPage() {
  const receipts = getReceipts()
  const [selectedId, setSelectedId] = useState<string>(receipts[0]?.receipt_id || '')
  const [search, setSearch] = useState('')
  const [verifyStatus, setVerifyStatus] = useState<'VERIFIED' | 'TAMPER_DETECTED' | 'IDLE' | 'VERIFYING'>('IDLE')
  const [verificationReason, setVerificationReason] = useState<string>('')
  const [computedHash, setComputedHash] = useState<string>('')
  const [activeReceipt, setActiveReceipt] = useState<ReceiptRecord | null>(receipts[0] || null)

  useEffect(() => {
    const found = receipts.find((r) => r.receipt_id === selectedId)
    if (found) {
      setActiveReceipt(found)
      setVerifyStatus('IDLE')
      setVerificationReason('')
      setComputedHash(found.canonical_hash)
    }
  }, [selectedId, receipts])

  const filteredReceipts = receipts.filter(
    (r) =>
      r.receipt_id.toLowerCase().includes(search.toLowerCase()) ||
      r.action.toLowerCase().includes(search.toLowerCase()) ||
      r.layer.toLowerCase().includes(search.toLowerCase())
  )

  const handleVerify = async () => {
    if (!activeReceipt) return
    setVerifyStatus('VERIFYING')
    setTimeout(async () => {
      // Try local verification first
      const res = await verifyReceiptLocally(activeReceipt)
      setVerifyStatus(res.status)
      setVerificationReason(res.reason)
      setComputedHash(res.computed_hash)
    }, 350)
  }

  const handleSimulateTamper = async () => {
    if (!activeReceipt) return
    setVerifyStatus('VERIFYING')
    setTimeout(async () => {
      // Copy and mutate one byte in decision
      const tampered = JSON.parse(JSON.stringify(activeReceipt))
      if (tampered.decision) {
        tampered.decision.tripline_decision =
          tampered.decision.tripline_decision === 'ALLOW' ? 'DENY' : 'ALLOW'
      } else {
        tampered.receipt_id = tampered.receipt_id + '_tampered'
      }
      const res = await verifyReceiptLocally(tampered)
      setVerifyStatus('TAMPER_DETECTED')
      setVerificationReason(res.reason)
      setComputedHash(res.computed_hash)
    }, 350)
  }

  return (
    <div className="w-full flex flex-col">
      <Section tone="dark">
        <SectionHeader
          eyebrow="// FORENSIC REGISTRY"
          title="Incident Receipts"
          accentWord="Receipts"
          description="Every denied or held action produces a Canonical JSON receipt (RFC 8785) signed with the local witness HMAC-SHA256 key. Verifiable offline without network access."
          tone="dark"
        />

        {receipts.length === 0 ? (
          <EmptyState
            title="No receipts recorded"
            description="Run the Phase 3 multi-layer scenario to generate incident receipts."
            command="make wow"
            source="results/phase3/scenario/"
          />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left: Ruled list of receipts (5 cols) */}
            <div className="lg:col-span-5 rounded-[4px] border border-[var(--border-dark)] bg-[#0C0C0E] p-4">
              <div className="mb-4">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-faint-on-dark)]" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search by action, ID, or layer..."
                    className="w-full pl-9 pr-3 py-1.5 rounded-[2px] bg-[#141418] border border-[var(--border-dark)] text-xs font-mono text-white placeholder-[var(--text-faint-on-dark)] focus-ring"
                  />
                </div>
              </div>

              <div className="font-mono text-[11px] uppercase tracking-wider text-[var(--text-faint-on-dark)] pb-2 mb-2 border-b border-[var(--border-dark)] flex items-center justify-between">
                <span>{filteredReceipts.length} RECEIPTS FOUND</span>
                <span>RESULTS/</span>
              </div>

              {/* Ruled list rows */}
              <div className="divide-y divide-[var(--border-dark)] max-h-[600px] overflow-y-auto">
                {filteredReceipts.map((r) => {
                  const isSelected = r.receipt_id === selectedId
                  let state: SecurityState = 'deny'
                  if (r.verdict.includes('HOLD')) state = 'hold'
                  if (r.verdict.includes('ALLOW')) state = 'allow'

                  return (
                    <div
                      key={r.receipt_id}
                      onClick={() => setSelectedId(r.receipt_id)}
                      className={`p-3 cursor-pointer transition-colors focus-ring rounded-[2px] ${
                        isSelected
                          ? 'bg-[#18181D] border-l-2 border-l-[var(--accent)]'
                          : 'hover:bg-white/[0.03]'
                      }`}
                      role="button"
                      tabIndex={0}
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="font-mono text-xs font-bold text-white truncate">
                          {r.receipt_id}
                        </span>
                        <StatusPill state={state} label={r.verdict} size="sm" />
                      </div>

                      <div className="font-mono text-[11px] text-emerald-400 truncate mb-1">
                        {r.action}
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-[var(--text-faint-on-dark)] font-mono">
                        <span>{r.layer}</span>
                        <span>{r.created_at.slice(0, 10)}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Right: ReceiptCard detail + D5 Verify Strip (7 cols) */}
            <div className="lg:col-span-7 space-y-6">
              {activeReceipt && (
                <>
                  <ReceiptCard
                    receipt={activeReceipt}
                    onVerify={handleVerify}
                    onTamper={handleSimulateTamper}
                    isVerifying={verifyStatus === 'VERIFYING'}
                  />

                  {/* D5 Verify Strip */}
                  <VerifyStrip
                    status={verifyStatus}
                    canonicalHash={activeReceipt.canonical_hash}
                    computedHash={computedHash}
                  />

                  {verificationReason && (
                    <div
                      className={`p-3 rounded-[2px] font-mono text-xs border ${
                        verifyStatus === 'VERIFIED'
                          ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-400'
                          : 'bg-red-950/20 border-red-500/40 text-red-400'
                      }`}
                    >
                      <div className="font-bold flex items-center gap-1.5 mb-1">
                        {verifyStatus === 'VERIFIED' ? (
                          <>
                            <ShieldCheck className="w-4 h-4" />
                            <span>VERIFICATION PASSED</span>
                          </>
                        ) : (
                          <>
                            <AlertTriangle className="w-4 h-4" />
                            <span>TAMPER_DETECTED</span>
                          </>
                        )}
                      </div>
                      <div className="text-[11px] opacity-90">{verificationReason}</div>
                    </div>
                  )}

                  {/* Transition link to Witness */}
                  <div className="pt-4 border-t border-[var(--border-dark)] flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--text-faint-on-dark)]">
                      // Verified receipt binds execution state
                    </span>
                    <Link
                      href="/witness"
                      className="text-white hover:text-[var(--accent)] transition-colors flex items-center gap-1.5 font-semibold"
                    >
                      <span>Inspect Witness Log Chain</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </Section>
    </div>
  )
}
