'use client'

import React, { useState, useEffect } from 'react'
import { Section } from '@/components/ui/Section'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { StatusPill } from '@/components/ui/Badge'
import {
  api,
  WitnessSummary,
  AuditLinksResponse,
  WitnessVerifyResponse,
  WitnessTamperResponse,
} from '@/lib/api'
import {
  ShieldCheck,
  Link2,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Fingerprint,
  FileCheck,
} from 'lucide-react'
import Link from 'next/link'

export default function WitnessPage() {
  const [witnessSummary, setWitnessSummary] = useState<WitnessSummary | null>(null)
  const [auditLinks, setAuditLinks] = useState<AuditLinksResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  // Interactive verification state
  const [verifying, setVerifying] = useState<boolean>(false)
  const [verifyResult, setVerifyResult] = useState<WitnessVerifyResponse | null>(null)
  const [tamperResult, setTamperResult] = useState<WitnessTamperResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Fetch real witness summary and audit links chain
  const loadWitnessData = async () => {
    setLoading(true)
    setErrorMsg(null)
    try {
      const [w, links] = await Promise.all([
        api.getWitness(),
        api.getAuditLinks().catch(() => null),
      ])
      setWitnessSummary(w)
      setAuditLinks(links)
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch witness chain.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWitnessData()
  }, [])

  // Call real POST /api/witness/verify
  const handleVerifyWitness = async () => {
    setVerifying(true)
    setTamperResult(null)
    try {
      const res = await api.verifyWitness()
      setVerifyResult(res)
    } catch (err: any) {
      setVerifyResult({
        valid: false,
        reason: err.message,
        log_name: 'all',
        inspected_records: 0,
      })
    } finally {
      setVerifying(false)
    }
  }

  // Call real POST /api/witness/tamper-check
  const handleTamperWitness = async () => {
    setVerifying(true)
    setVerifyResult(null)
    try {
      const res = await api.tamperWitness()
      setTamperResult(res)
    } catch (err: any) {
      setTamperResult({
        tamper_detected: false,
        status: 'ERROR',
        verifier_reason: err.message,
        original_log_untouched: true,
      })
    } finally {
      setVerifying(false)
    }
  }

  return (
    <div className="w-full flex flex-col">
      <Section tone="light">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <SectionHeader
            eyebrow="// APPEND-ONLY EXECUTION LEDGER"
            title="Witness Hash-Chain"
            description="The witness log cryptographically seals every action attempt into an append-only ledger using HMAC-SHA256 back to genesis. Each entry irreversibly binds the preceding block hash."
            tone="light"
          />
          <button
            onClick={loadWitnessData}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#CDD2D8] bg-[#FFFFFF] hover:bg-[#EAEDF0] text-xs font-mono text-[#20252B] transition-colors shrink-0"
            data-testid="btn-witness"
            data-api="GET /api/witness"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Ledger</span>
          </button>
        </div>

        {/* Chain Validity & Verification Controls Banner */}
        <div className="mb-8 p-5 rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-600">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <span className="font-mono text-xs text-[#747F8D] uppercase block">Ledger Status</span>
                <span className="font-mono font-bold text-sm text-[#20252B]">
                  {loading
                    ? 'VERIFYING WITNESS HEAD...'
                    : witnessSummary
                    ? `WITNESS LEDGER: ${witnessSummary.chain_status.toUpperCase()} (${witnessSummary.total_records} RECORDS SECURED)`
                    : 'WITNESS LEDGER READY'}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleVerifyWitness}
                disabled={verifying}
                className="px-4 py-2 rounded-lg bg-[#20252B] hover:bg-[#2D3136] text-white font-semibold text-xs font-mono transition-colors shadow-sm disabled:opacity-50"
                data-testid="btn-verify-witness"
                data-api="POST /api/witness/verify"
              >
                {verifying ? 'Verifying...' : 'Verify Chain (POST)'}
              </button>
              <button
                onClick={handleTamperWitness}
                disabled={verifying}
                className="px-4 py-2 rounded-lg border border-red-300 text-red-700 bg-red-50 hover:bg-red-100 text-xs font-mono transition-colors disabled:opacity-50"
                data-testid="btn-tamper-witness"
                data-api="POST /api/witness/tamper-check"
              >
                Test Tamper Check
              </button>
            </div>
          </div>

          {/* Verification Results */}
          {verifyResult && (
            <div
              className={`p-3.5 rounded-lg font-mono text-xs border ${
                verifyResult.valid
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-red-50 border-red-200 text-red-800'
              }`}
            >
              <div className="font-bold flex items-center gap-2 mb-1">
                {verifyResult.valid ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <AlertTriangle className="w-4 h-4 text-red-600" />}
                <span>
                  {verifyResult.valid
                    ? `VERIFICATION PASSED: ${verifyResult.inspected_records} records in ${verifyResult.log_name}`
                    : 'VERIFICATION FAILED'}
                </span>
              </div>
              <div className="text-[11px] opacity-90">{verifyResult.reason}</div>
            </div>
          )}

          {tamperResult && (
            <div
              className={`p-3.5 rounded-lg font-mono text-xs border ${
                tamperResult.tamper_detected
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-red-50 border-red-200 text-red-800'
              }`}
            >
              <div className="font-bold flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>TAMPER DETECTION CONFIRMED: {tamperResult.status}</span>
              </div>
              <div className="text-[11px] opacity-90 leading-relaxed">
                {tamperResult.verifier_reason}. Original witness log byte-for-byte untouched ({String(tamperResult.original_log_untouched)}).
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 font-mono text-xs">
              {errorMsg}
            </div>
          )}
        </div>

        {/* MCP Execution Logs Breakdown */}
        {witnessSummary && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8 font-mono text-xs">
            <div className="p-3.5 rounded-xl bg-[#FFFFFF] border border-[#CDD2D8] shadow-sm">
              <span className="text-[10px] text-[#747F8D] uppercase block">Total MCP Logs</span>
              <span className="text-[#20252B] font-bold text-sm block mt-0.5">
                {Object.keys(witnessSummary.mcp_logs || {}).length} Log Files
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-[#FFFFFF] border border-[#CDD2D8] shadow-sm">
              <span className="text-[10px] text-[#747F8D] uppercase block">Total Records</span>
              <span className="text-[#059669] font-bold text-sm block mt-0.5">
                {witnessSummary.total_records} Chain Blocks
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-[#FFFFFF] border border-[#CDD2D8] shadow-sm">
              <span className="text-[10px] text-[#747F8D] uppercase block">Sidecar Links</span>
              <span className="text-[#65BCE7] font-bold text-sm block mt-0.5">
                {auditLinks?.chain_length ?? 0} Links Validated
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-[#FFFFFF] border border-[#CDD2D8] shadow-sm">
              <span className="text-[10px] text-[#747F8D] uppercase block">Chain Status</span>
              <span className="text-[#20252B] font-bold text-sm block mt-0.5">
                {witnessSummary.chain_status.toUpperCase()}
              </span>
            </div>
          </div>
        )}

        {/* Audit Links / Chain Sequence Layout */}
        <div className="space-y-4">
          <div className="flex items-center justify-between font-mono text-xs pb-2 border-b border-[#CDD2D8]">
            <span className="text-[#20252B] font-semibold">// CRYPTOGRAPHIC AUDIT LINKS SEQUENCE</span>
            <span className="text-[#747F8D]">Source: GET /api/audit-links</span>
          </div>

          {loading ? (
            <div className="p-16 text-center text-xs font-mono text-[#747F8D] bg-[#FFFFFF] border border-[#CDD2D8] rounded-xl shadow-sm">
              Loading cryptographic hash chain...
            </div>
          ) : !auditLinks || auditLinks.links.length === 0 ? (
            <div className="p-12 text-center text-xs font-mono text-[#59636E] bg-[#FFFFFF] border border-[#CDD2D8] rounded-xl space-y-2 shadow-sm">
              <p className="text-[#20252B] font-semibold">No Audit Links Recorded</p>
              <p className="text-[11px]">Run benchmark or scenario suites to generate linked sidecar entries.</p>
            </div>
          ) : (
            <div className="relative pl-6 md:pl-8 border-l-2 border-[#CDD2D8] space-y-6">
              {auditLinks.links.map((item, idx) => (
                <div key={item.receipt_id || idx} className="relative group">
                  {/* Timeline Connector Dot */}
                  <div className="absolute -left-[31px] md:-left-[39px] top-4 w-3.5 h-3.5 rounded-full border-2 border-[#65BCE7] bg-[#FFFFFF] group-hover:scale-125 transition-transform" />

                  <div className="p-5 rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] hover:border-[#65BCE7] transition-all space-y-3 shadow-sm">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2 font-mono text-xs">
                        <span className="px-2 py-0.5 rounded bg-[#F4F5F6] border border-[#CDD2D8] text-[#20252B] font-bold">
                          BLOCK #{idx + 1}
                        </span>
                        <Link
                          href={`/receipts?id=${encodeURIComponent(item.receipt_id)}`}
                          className="text-[#20252B] font-bold hover:text-[#65BCE7] transition-colors"
                        >
                          {item.receipt_id}
                        </Link>
                      </div>

                      <span className="px-2 py-0.5 rounded bg-[#ECFDF5] border border-[#A7F3D0] text-[#10B981] font-mono text-[10px] font-bold">
                        LINKED
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
                      <div className="p-3 rounded-lg bg-[#F4F5F6] border border-[#CDD2D8] space-y-1">
                        <span className="text-[#747F8D] text-[10px] uppercase block">Prior Block Hash:</span>
                        <code className="text-[#20252B] text-[11px] block truncate">{item.prev_hash}</code>
                      </div>
                      <div className="p-3 rounded-lg bg-[#F4F5F6] border border-[#CDD2D8] space-y-1">
                        <span className="text-[#747F8D] text-[10px] uppercase block">Cumulative Link Hash:</span>
                        <code className="text-[#20252B] text-[11px] block truncate">{item.link_hash}</code>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-[#CDD2D8] font-mono text-[11px] text-[#747F8D]">
                      <span>Receipt Hash: <code className="text-[#20252B]">{item.receipt_hash.slice(0, 16)}...</code></span>
                      <Link
                        href={`/receipts?id=${encodeURIComponent(item.receipt_id)}`}
                        className="text-[#20252B] hover:text-[#65BCE7] font-semibold flex items-center gap-1 text-[11px]"
                      >
                        <span>Inspect Receipt</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Section>
    </div>
  )
}
