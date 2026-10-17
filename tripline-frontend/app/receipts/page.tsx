'use client'

import React, { useState, useEffect } from 'react'
import { Section } from '@/components/ui/Section'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { ReceiptCard, ReceiptData } from '@/components/ui/ReceiptCard'
import { VerifyStrip } from '@/components/diagrams/VerifyStrip'
import { StatusPill, SecurityState } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import {
  api,
  ReceiptSummary,
  ReceiptDetail,
  ReceiptVerifyResponse,
  ReceiptTamperResponse,
} from '@/lib/api'
import { ShieldCheck, Search, AlertTriangle, ArrowRight, RefreshCw } from 'lucide-react'
import Link from 'next/link'

export default function ReceiptsPage() {
  const [receiptsList, setReceiptsList] = useState<ReceiptSummary[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [selectedId, setSelectedId] = useState<string>('')
  const [search, setSearch] = useState('')
  const [activeReceipt, setActiveReceipt] = useState<ReceiptData | null>(null)
  const [receiptDetailLoading, setReceiptDetailLoading] = useState<boolean>(false)

  // Verification state
  const [verifyStatus, setVerifyStatus] = useState<'VERIFIED' | 'TAMPER_DETECTED' | 'IDLE' | 'VERIFYING'>('IDLE')
  const [verificationReason, setVerificationReason] = useState<string>('')
  const [computedHash, setComputedHash] = useState<string>('')
  const [commandRun, setCommandRun] = useState<string>('')

  // 1. Fetch real receipts list from backend
  const loadReceipts = async () => {
    setLoading(true)
    try {
      const data = await api.getReceipts()
      setReceiptsList(data)
      if (data.length > 0) {
        // Check for query param if present in browser
        let initialId = data[0].receipt_id
        if (typeof window !== 'undefined') {
          const params = new URLSearchParams(window.location.search)
          const qId = params.get('id')
          if (qId && data.some((r) => r.receipt_id === qId)) {
            initialId = qId
          }
        }
        setSelectedId(initialId)
      }
    } catch (err) {
      console.error('Error fetching receipts:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReceipts()
  }, [])

  // 2. Fetch full detail when selected receipt changes
  useEffect(() => {
    if (!selectedId) return
    setReceiptDetailLoading(true)
    setVerifyStatus('IDLE')
    setVerificationReason('')
    setCommandRun('')

    api.getReceipt(selectedId)
      .then((detail) => {
        const d = detail.data || {}
        const mapped: ReceiptData = {
          receipt_id: detail.receipt_id,
          run_id: d.run_id || detail.receipt_id,
          created_at: d.timestamp_utc || d.created_at || new Date().toISOString(),
          action: d.operation || (d.proposal ? `${d.proposal.tool}(${JSON.stringify(d.proposal.args || {})})` : 'read_file'),
          layer: d.decision?.tripline_decision ? `TripLine ${d.decision.tripline_decision}` : 'ArmorIQ Policy',
          verdict: d.decision?.tripline_decision || d.authorization_decision || 'DENY',
          canonical_hash: d.canonical_hash || d.hmac_sha256 || 'RFC-8785 pending',
          receipt_signature: d.signature || d.hmac_sha256 || 'Ed25519 sealed',
          witness_head_hmac: d.witness?.head_hmac || d.witness_head_hmac,
          verification_status: d.verification_status || 'VERIFIED',
          source_file: `results/receipts/${detail.receipt_id}.json`,
          proposal: d.proposal || { tool: d.operation, args: d.normalized_arguments },
          decision: d.decision || { tripline_decision: d.authorization_decision, reason: d.authorization_reason },
          witness: d.witness,
          confidence: d.confidence,
          raw_json: detail.raw_json,
        }
        setActiveReceipt(mapped)
        setComputedHash(mapped.canonical_hash)
      })
      .catch((err) => {
        console.error('Error loading receipt detail:', err)
      })
      .finally(() => {
        setReceiptDetailLoading(false)
      })
  }, [selectedId])

  // Search filter
  const filteredReceipts = receiptsList.filter(
    (r) =>
      r.receipt_id.toLowerCase().includes(search.toLowerCase()) ||
      r.tool.toLowerCase().includes(search.toLowerCase()) ||
      (r.tripline_decision || '').toLowerCase().includes(search.toLowerCase()) ||
      (r.armoriq_decision || '').toLowerCase().includes(search.toLowerCase())
  )

  // Real backend cryptographic verification
  const handleVerify = async () => {
    if (!selectedId) return
    setVerifyStatus('VERIFYING')
    try {
      const res: ReceiptVerifyResponse = await api.verifyReceipt(selectedId)
      if (res.verified) {
        setVerifyStatus('VERIFIED')
        setVerificationReason(`Cryptographic verification passed. Status: ${res.status}. ${res.reason}`)
      } else {
        setVerifyStatus('TAMPER_DETECTED')
        setVerificationReason(`Signature mismatch: ${res.reason}`)
      }
      if (res.canonical_hash) {
        setComputedHash(res.canonical_hash)
      }
      setCommandRun(res.command)
    } catch (err: any) {
      setVerifyStatus('TAMPER_DETECTED')
      setVerificationReason(`Backend verification call rejected: ${err.message}`)
    }
  }

  // Real server-side tamper check (preserves original file)
  const handleSimulateTamper = async () => {
    if (!selectedId) return
    setVerifyStatus('VERIFYING')
    try {
      const res: ReceiptTamperResponse = await api.tamperReceipt(selectedId)
      if (res.tamper_detected) {
        setVerifyStatus('TAMPER_DETECTED')
        setVerificationReason(
          `Mutation in field '${res.tampered_field}' detected! Verifier rejected: ${res.verifier_reason}. Original receipt file confirmed untouched.`
        )
      } else {
        setVerifyStatus('VERIFIED')
        setVerificationReason(`Tamper check status: ${res.status}`)
      }
    } catch (err: any) {
      setVerifyStatus('TAMPER_DETECTED')
      setVerificationReason(`Tamper check error: ${err.message}`)
    }
  }

  return (
    <div className="w-full flex flex-col">
      <Section tone="dark">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <SectionHeader
            eyebrow="// FORENSIC REGISTRY"
            title="Incident Receipts"
            description="Every denied or quarantined action produces a Canonical JSON receipt (RFC 8785) signed with the witness key. Authoritative verification executes directly against backend cryptographic routines."
            tone="light"
          />
          <button
            onClick={loadReceipts}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#CDD2D8] bg-[#FFFFFF] hover:bg-[#EAEDF0] text-xs font-mono text-[#20252B] transition-colors shrink-0"
            data-testid="btn-refresh-receipts"
            data-api="GET /api/receipts"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Receipts</span>
          </button>
        </div>

        {loading ? (
          <div className="p-16 text-center text-xs font-mono text-[#747F8D] bg-[#FFFFFF] border border-[#CDD2D8] rounded-xl shadow-sm">
            Loading authoritative receipts from backend...
          </div>
        ) : receiptsList.length === 0 ? (
          <EmptyState
            title="No receipts recorded"
            description="Execute live agent runs, scenario suites, or REA investigations to mint signed forensic receipts."
            command="make wow"
            source="results/"
          />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left: Ruled list of receipts (5 cols) */}
            <div className="lg:col-span-5 rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] p-4 shadow-sm">
              <div className="mb-4">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#747F8D]" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search by tool, ID, or decision..."
                    data-local="receipts-search"
                    className="w-full pl-9 pr-3 py-2 rounded-lg bg-[#F4F5F6] border border-[#CDD2D8] text-xs font-mono text-[#20252B] placeholder-[#747F8D] focus-ring"
                  />
                </div>
              </div>

              <div className="font-mono text-[11px] uppercase tracking-wider text-[#747F8D] pb-2 mb-2 border-b border-[#CDD2D8] flex items-center justify-between">
                <span>{filteredReceipts.length} RECEIPTS FOUND</span>
                <span>AUTHENTIC</span>
              </div>

              {/* Ruled list rows */}
              <div className="divide-y divide-[#CDD2D8] max-h-[600px] overflow-y-auto">
                {filteredReceipts.map((r) => {
                  const isSelected = r.receipt_id === selectedId
                  let state: SecurityState = 'deny'
                  const v = (r.tripline_decision || r.armoriq_decision || '').toUpperCase()
                  if (v.includes('ALLOW')) state = 'allow'
                  if (v.includes('HOLD')) state = 'hold'

                  return (
                    <div
                      key={r.receipt_id}
                      onClick={() => setSelectedId(r.receipt_id)}
                      className={`p-3 cursor-pointer transition-colors focus-ring rounded-lg ${
                        isSelected
                          ? 'bg-[#EAEDF0] border-l-2 border-l-[#65BCE7]'
                          : 'hover:bg-[#F4F5F6]'
                      }`}
                      role="button"
                      tabIndex={0}
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="font-mono text-xs font-bold text-[#20252B] truncate">
                          {r.receipt_id}
                        </span>
                        <StatusPill state={state} label={r.tripline_decision || r.armoriq_decision || 'DENY'} size="sm" />
                      </div>

                      <div className="font-mono text-[11px] text-[#059669] truncate mb-1">
                        {r.tool}
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-[#747F8D] font-mono">
                        <span>Run: {r.run_id?.slice(0, 16) || 'standard'}</span>
                        <span>{r.created_at?.slice(0, 10)}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Right: ReceiptCard detail + Real Verification (7 cols) */}
            <div className="lg:col-span-7 space-y-6">
              {receiptDetailLoading ? (
                <div className="p-16 text-center text-xs font-mono text-[#747F8D] bg-[#FFFFFF] border border-[#CDD2D8] rounded-xl shadow-sm">
                  Loading receipt detail...
                </div>
              ) : activeReceipt ? (
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
                      className={`p-4 rounded-xl font-mono text-xs border ${
                        verifyStatus === 'VERIFIED'
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                          : 'bg-red-50 border-red-200 text-red-800'
                      }`}
                    >
                      <div className="font-bold flex items-center gap-1.5 mb-1">
                        {verifyStatus === 'VERIFIED' ? (
                          <>
                            <ShieldCheck className="w-4 h-4 text-emerald-600" />
                            <span>VERIFICATION PASSED</span>
                          </>
                        ) : (
                          <>
                            <AlertTriangle className="w-4 h-4 text-red-600" />
                            <span>TAMPER_DETECTED / VERIFICATION REJECTED</span>
                          </>
                        )}
                      </div>
                      <div className="text-[11px] opacity-90 leading-relaxed">{verificationReason}</div>
                      {commandRun && (
                        <div className="mt-2 pt-2 border-t border-black/10 text-[10px] text-[#59636E]">
                          Backend Command: <code>{commandRun}</code>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Transition link to Witness */}
                  <div className="pt-4 border-t border-[#CDD2D8] flex items-center justify-between text-xs font-mono">
                    <span className="text-[#747F8D]">
                      // Receipt canonical hash binds execution state
                    </span>
                    <Link
                      href="/witness"
                      className="text-[#20252B] hover:text-[#65BCE7] transition-colors flex items-center gap-1.5 font-semibold"
                    >
                      <span>Inspect Witness Hash-Chain</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </>
              ) : null}
            </div>
          </div>
        )}
      </Section>
    </div>
  )
}
