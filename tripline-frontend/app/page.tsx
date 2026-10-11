'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import {
  Check, Copy, Download, Eye, FileText, Play, RefreshCw, Shield,
  ShieldAlert, ShieldCheck, Square, Terminal, Waypoints, X,
  AlertTriangle, Lock, Menu, ChevronRight, ExternalLink,
  Hash, Clock, Zap, Layers, Search, Filter
} from 'lucide-react'
import {
  api, HealthInfo, EnvInfo, RunSummary, RunDetail, ReceiptSummary, ReceiptDetail,
  JailBurstResponse, AttributionResponse, MeasuredResponse, WitnessSummary,
  JobRecord, EvidenceIndexResponse, ClaimsLedgerResponse, PlatformChecklistResponse,
} from '../lib/api'

// ── Types ──────────────────────────────────────────────────────────
type TabKey =
  | 'overview' | 'console' | 'attribution' | 'burst' | 'receipts'
  | 'witness' | 'measured' | 'evidence' | 'video' | 'claims'
  | 'platform' | 'about'

interface SummaryData {
  runs: number; receipts: number; probes_total: number;
  probes_passed: number; witness_records: number;
  measured_rows: number; data_timestamp: string;
}

// ── Helpers ────────────────────────────────────────────────────────
function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString(undefined, {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
    })
  } catch { return iso }
}

function formatTimeWithTooltip(iso: string | null | undefined) {
  if (!iso) return <span>—</span>
  return <span title={`UTC: ${iso}`}>{formatTime(iso)}</span>
}

function truncHash(hash: string, len = 12): string {
  if (!hash) return '—'
  return hash.length > len ? hash.slice(0, len) + '…' : hash
}

function badgeClass(decision: string): string {
  const d = (decision || '').toUpperCase()
  if (d.includes('DENY') || d.includes('FAILED') || d.includes('BLOCK')) return 'badge--deny'
  if (d.includes('ALLOW') || d.includes('VERIFIED') || d.includes('PASS') || d.includes('VALID') || d === 'COMPLETED') return 'badge--allow'
  if (d.includes('HOLD') || d.includes('PENDING') || d === 'RUNNING') return 'badge--hold'
  if (d.includes('ATTEST') || d.includes('SEAL') || d.includes('RECORD')) return 'badge--record'
  return 'badge--neutral'
}

// ── StatusBadge Component ──────────────────────────────────────────
function StatusBadge({ status, icon }: { status: string; icon?: React.ReactNode }) {
  return (
    <span className={`badge ${badgeClass(status)}`}>
      {icon}
      {status}
    </span>
  )
}

// ── HashChip Component ─────────────────────────────────────────────
function HashChip({ hash, full }: { hash: string; full?: string }) {
  const [copied, setCopied] = useState(false)
  const v = full || hash
  return (
    <span
      className="hash-chip"
      title={v}
      onClick={() => { navigator.clipboard?.writeText(v); setCopied(true); setTimeout(() => setCopied(false), 1200) }}
    >
      <Hash style={{ width: 10, height: 10 }} />
      {truncHash(hash)}
      {copied ? <Check style={{ width: 10, height: 10, color: 'var(--allow)' }} /> : <Copy style={{ width: 10, height: 10 }} />}
    </span>
  )
}

// ── EmptyState Component ───────────────────────────────────────────
function EmptyState({ title, description, command }: { title: string; description?: string; command?: string }) {
  return (
    <div className="empty-state" data-testid="empty-state">
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {command && <code>{command}</code>}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════
// MAIN APP COMPONENT
// ═══════════════════════════════════════════════════════════════════
export default function App() {
  // ── State ──
  const [tab, setTab] = useState<TabKey>('overview')
  const [health, setHealth] = useState<HealthInfo | null>(null)
  const [env, setEnv] = useState<EnvInfo | null>(null)
  const [summary, setSummary] = useState<SummaryData | null>(null)
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string>('')
  const [currentRunDetail, setCurrentRunDetail] = useState<RunDetail | null>(null)
  const [transcript, setTranscript] = useState<{ id: string; text: string | null; msg?: string | null } | null>(null)
  const [activeIncidentIndex, setActiveIncidentIndex] = useState(0)
  const [copiedCmd, setCopiedCmd] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  // Console
  const [jobs, setJobs] = useState<JobRecord[]>([])
  const [selectedKind, setSelectedKind] = useState<string>('jail_burst')
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [liveConfirmChecked, setLiveConfirmChecked] = useState(false)
  const [consoleLogs, setConsoleLogs] = useState<string[]>([])
  const [isJobRunning, setIsJobRunning] = useState(false)
  const [jobError, setJobError] = useState<string | null>(null)

  // Data pages
  const [attribution, setAttribution] = useState<AttributionResponse | null>(null)
  const [burst, setBurst] = useState<JailBurstResponse | null>(null)
  const [receipts, setReceipts] = useState<ReceiptSummary[]>([])
  const [selectedReceiptId, setSelectedReceiptId] = useState<string>('')
  const [selectedReceiptDetail, setSelectedReceiptDetail] = useState<ReceiptDetail | null>(null)
  const [receiptVerifyResult, setReceiptVerifyResult] = useState<any>(null)
  const [receiptTamperResult, setReceiptTamperResult] = useState<any>(null)
  const [witness, setWitness] = useState<WitnessSummary | null>(null)
  const [witnessVerifyResult, setWitnessVerifyResult] = useState<any>(null)
  const [witnessTamperResult, setWitnessTamperResult] = useState<any>(null)
  const [measured, setMeasured] = useState<MeasuredResponse | null>(null)
  const [evidence, setEvidence] = useState<EvidenceIndexResponse | null>(null)
  const [viewingFile, setViewingFile] = useState<{ path: string; content: string } | null>(null)
  const [claims, setClaims] = useState<ClaimsLedgerResponse | null>(null)
  const [platform, setPlatform] = useState<PlatformChecklistResponse | null>(null)
  const [auditLinks, setAuditLinks] = useState<any>(null)
  const [docsList, setDocsList] = useState<any[]>([])
  const [docContent, setDocContent] = useState<{ name: string; content: string } | null>(null)
  const [receiptFilter, setReceiptFilter] = useState<string>('')

  const sseRef = useRef<EventSource | null>(null)
  const terminalRef = useRef<HTMLDivElement | null>(null)

  // ── Initial Load ──
  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => {})
    api.getEnv().then(setEnv).catch(() => {})
    api.getSummary().then(setSummary).catch(() => {})
    api.getRuns().then((data) => {
      setRuns(data)
      if (data.length > 0) setSelectedRunId(data[0].run_id)
    }).catch(() => {})

    if (typeof window !== 'undefined' && window.location.hash) {
      const h = window.location.hash.replace('#', '') as TabKey
      const valid: TabKey[] = ['overview','console','attribution','burst','receipts','witness','measured','evidence','video','claims','platform','about']
      if (valid.includes(h)) setTab(h)
    }
  }, [])

  // ── Run detail ──
  useEffect(() => {
    if (selectedRunId) api.getRun(selectedRunId).then(setCurrentRunDetail).catch(() => {})
  }, [selectedRunId])

  // ── Tab data loading ──
  useEffect(() => {
    const loaders: Record<string, () => void> = {
      console: () => api.listJobs().then(setJobs).catch(() => {}),
      attribution: () => api.getAttribution().then(setAttribution).catch(() => {}),
      burst: () => api.getJailBurst().then(setBurst).catch(() => {}),
      receipts: () => api.getReceipts().then((d) => { setReceipts(d); if (d.length > 0 && !selectedReceiptId) setSelectedReceiptId(d[0].receipt_id) }).catch(() => {}),
      witness: () => api.getWitness().then(setWitness).catch(() => {}),
      measured: () => api.getMeasured().then(setMeasured).catch(() => {}),
      evidence: () => api.getEvidenceIndex().then(setEvidence).catch(() => {}),
      claims: () => api.getClaims().then(setClaims).catch(() => {}),
      platform: () => api.getPlatformChecklist().then(setPlatform).catch(() => {}),
      about: () => api.getDoc('architecture').then((d) => setDocContent({ name: d.name, content: d.content })).catch(() => {}),
    }
    loaders[tab]?.()
  }, [tab])

  // ── Receipt detail ──
  useEffect(() => {
    if (selectedReceiptId) {
      setReceiptVerifyResult(null)
      setReceiptTamperResult(null)
      api.getReceipt(selectedReceiptId).then(setSelectedReceiptDetail).catch(() => {})
    }
  }, [selectedReceiptId])

  // ── Auto-scroll terminal ──
  useEffect(() => {
    if (terminalRef.current) terminalRef.current.scrollTop = terminalRef.current.scrollHeight
  }, [consoleLogs])

  // ── SSE ──
  const subscribeJobLogs = useCallback((jobId: string) => {
    if (sseRef.current) sseRef.current.close()
    const es = new EventSource(`/api/jobs/${encodeURIComponent(jobId)}/events`)
    sseRef.current = es
    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.line) setConsoleLogs(prev => [...prev, payload.line])
        if (payload.done) { setIsJobRunning(false); es.close(); api.listJobs().then(setJobs).catch(() => {}) }
      } catch {}
    }
    es.onerror = () => { setIsJobRunning(false); es.close() }
  }, [])

  const handleStartJob = async () => {
    setJobError(null); setIsJobRunning(true)
    setConsoleLogs([`[INIT] Launching job '${selectedKind}'...`])
    try {
      const confirmToken = liveConfirmChecked ? 'CONFIRMED_LIVE_EXECUTION' : undefined
      const res = await api.createJob(selectedKind, {}, confirmToken)
      setActiveJobId(res.job_id); subscribeJobLogs(res.job_id)
      api.listJobs().then(setJobs).catch(() => {})
    } catch (err: any) {
      setIsJobRunning(false); setJobError(err.message || 'Failed to start job')
      setConsoleLogs(prev => [...prev, `[ERROR] ${err.message}`])
    }
  }

  const handleCancelJob = async () => {
    if (!activeJobId) return
    try {
      await api.cancelJob(activeJobId)
      setConsoleLogs(prev => [...prev, `[USER] Job cancellation requested.`])
      if (sseRef.current) sseRef.current.close()
      setIsJobRunning(false); api.listJobs().then(setJobs).catch(() => {})
    } catch (err: any) { setJobError(err.message) }
  }

  const handleCopy = (text: string) => {
    navigator.clipboard?.writeText(text); setCopiedCmd(true)
    setTimeout(() => setCopiedCmd(false), 1500)
  }

  const handleViewEvidence = async (path: string) => {
    try {
      const res = await fetch(`/api/evidence/file?path=${encodeURIComponent(path)}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const txt = await res.text()
      setViewingFile({ path, content: txt })
    } catch (err: any) { setViewingFile({ path, content: `Error opening file: ${err.message}` }) }
  }

  const switchTab = (t: TabKey) => {
    setTab(t)
    setMobileOpen(false)
    if (typeof window !== 'undefined') window.location.hash = t
  }

  // ── Derived data ──
  const currentIncident = currentRunDetail?.records?.[activeIncidentIndex]
  const filteredReceipts = receipts.filter(r => {
    if (!receiptFilter) return true
    return r.tripline_decision.toLowerCase().includes(receiptFilter.toLowerCase()) ||
      r.tool.toLowerCase().includes(receiptFilter.toLowerCase()) ||
      r.receipt_id.toLowerCase().includes(receiptFilter.toLowerCase())
  })

  // ── Nav items ──
  const navItems: { key: TabKey; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'console', label: 'Console' },
    { key: 'attribution', label: 'Attribution' },
    { key: 'burst', label: 'Jail Burst' },
    { key: 'receipts', label: 'Receipts' },
    { key: 'witness', label: 'Witness' },
    { key: 'measured', label: 'Measured' },
    { key: 'evidence', label: 'Evidence' },
    { key: 'video', label: 'Video' },
    { key: 'claims', label: 'Claims' },
    { key: 'platform', label: 'Checklist' },
    { key: 'about', label: 'About' },
  ]

  return (
    <div className="site-shell">
      {/* Skip to content */}
      <a href="#main-content" className="skip-link">Skip to content</a>

      {/* ── HEADER ── */}
      <header className="topbar" role="banner">
        <a href="/" className="brand" onClick={(e) => { e.preventDefault(); switchTab('overview') }}
          data-testid="brand-button" data-local="navigate-overview" aria-label="Tripline home">
          <picture>
            <source media="(prefers-color-scheme: light)" srcSet="/tripline-lockup-on-light.svg" />
            <img src="/tripline-lockup-on-dark.svg" alt="Tripline" className="brand-logo-img" width={140} height={28} />
          </picture>
        </a>

        <nav aria-label="Main navigation">
          {navItems.map(n => (
            <button key={n.key} className={`nav-tab ${tab === n.key ? 'active' : ''}`}
              onClick={() => switchTab(n.key)} data-testid={`nav-${n.key}`}
              data-local={`switch-tab-${n.key}`} type="button"
              aria-current={tab === n.key ? 'page' : undefined}>
              {n.label}
            </button>
          ))}
        </nav>

        <button className="mobile-nav-btn" onClick={() => setMobileOpen(!mobileOpen)}
          aria-expanded={mobileOpen} aria-label="Toggle navigation" type="button">
          {mobileOpen ? <X style={{ width: 22, height: 22 }} /> : <Menu style={{ width: 22, height: 22 }} />}
        </button>
      </header>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="mobile-drawer open" role="navigation" aria-label="Mobile navigation">
          {navItems.map(n => (
            <button key={n.key} className={`nav-tab ${tab === n.key ? 'active' : ''}`}
              onClick={() => switchTab(n.key)} data-testid={`mobile-nav-${n.key}`} type="button">
              {n.label}
            </button>
          ))}
        </div>
      )}

      {/* ── MAIN CONTENT ── */}
      <main id="main-content" role="main">

        {/* ═══════════════════════════════════════════════════════════
            OVERVIEW — Product narrative homepage
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'overview' && (
          <>
            {/* S1: HERO (dark) */}
            <div className="section section--dark">
              <div className="wrap">
                <section className="hero-section">
                  <div>
                    <p className="hero-eyebrow">Forensic evidence for AI agent actions</p>
                    <h1 className="hero-title">
                      Blocked isn't <span className="highlight">evidence.</span>
                    </h1>
                    <p className="hero-subtitle">
                      A denial is a verdict, not a record. Tripline turns every denied agent action into
                      a signed receipt you can verify.
                    </p>
                    <div className="hero-actions">
                      <button className="btn btn-primary" onClick={() => switchTab('receipts')}
                        data-testid="btn-hero-receipts" data-local="switch-tab-receipts" type="button">
                        <ShieldCheck style={{ width: 14, height: 14 }} /> Inspect receipts
                      </button>
                      <button className="btn btn-secondary" onClick={() => switchTab('console')}
                        data-testid="btn-hero-console" data-local="switch-tab-console" type="button">
                        <Terminal style={{ width: 14, height: 14 }} /> Open run console
                      </button>
                    </div>
                    <div className="hero-meta">
                      <code>{env?.enforcement_mode || 'Loading…'}</code>
                      <span>·</span>
                      <code>{health?.branch || '—'}</code>
                    </div>
                  </div>

                  <div className="grain-panel">
                    <span className="corner-label">PROPOSAL</span>
                    <span className="corner-label">ARMORIQ</span>
                    <span className="corner-label">TRIPLINE</span>
                    <span className="corner-label">RECEIPT</span>
                    {currentIncident ? (
                      <div className="replay-chip">
                        <code>{currentIncident.action || currentIncident.issue}</code>
                        <StatusBadge status={currentIncident.armoriq || 'UNKNOWN'} />
                        <StatusBadge status={currentIncident.tripline || 'UNKNOWN'} />
                        <small>Recorded run {selectedRunId ? truncHash(selectedRunId, 16) : '—'}</small>
                      </div>
                    ) : (
                      <div className="replay-chip">
                        <span className="illustration-label">Architecture (not a live decision)</span>
                        <code>agent → ArmorIQ → Tripline → receipt</code>
                        <small>No recorded run loaded</small>
                      </div>
                    )}
                  </div>
                </section>

                {/* Proof metrics */}
                <div className="proof-strip" data-testid="proof-metrics">
                  <div className="proof-metric">
                    <strong>{summary?.runs ?? '—'}</strong>
                    <p>Recorded scenario and attack runs</p>
                    <code>results/phase3/scenario/</code>
                  </div>
                  <div className="proof-metric">
                    <strong>{summary?.receipts ?? '—'}</strong>
                    <p>Signed receipts (canonical JSON + HMAC-SHA256)</p>
                    <code>results/demo/ + results/phase3/</code>
                  </div>
                  <div className="proof-metric">
                    <strong>{summary ? `${summary.probes_passed} / ${summary.probes_total}` : '—'}</strong>
                    <p>Path containment probes verified</p>
                    <code>scripts/jail_burst.py</code>
                  </div>
                </div>

                {summary && (
                  <div className="freshness" style={{ marginTop: 16 }}>
                    <span className="freshness-dot" />
                    Data from {formatTime(summary.data_timestamp)}
                  </div>
                )}
              </div>
            </div>

            {/* S2: THE PROBLEM (light) */}
            <div className="section section--light">
              <div className="wrap">
                <h2 style={{ marginBottom: 12 }}>A block is a verdict.<br />It is not a record.</h2>
                <p style={{ color: 'var(--text-secondary)', maxWidth: 'var(--text-max)', marginBottom: 40, fontSize: '1.0625rem' }}>
                  An authorization decision tells you what was allowed or denied. A forensic receipt tells you
                  <em> who proposed it, what was inspected, which layer stopped it, whether anything executed,
                  and provides a verifiable cryptographic signature</em>.
                </p>
                <div className="compare-grid">
                  <div className="compare-col">
                    <h4>What a block tells you</h4>
                    <div className="card">
                      <StatusBadge status="DENY" icon={<ShieldAlert style={{ width: 12, height: 12 }} />} />
                      <p style={{ marginTop: 12, color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                        {currentIncident?.armoriq || 'DENY — unauthorized tool call'}<br />
                        <span style={{ fontSize: '0.75rem', color: 'var(--dim)' }}>That's it. No receipt, no witness, no proof of non-execution.</span>
                      </p>
                    </div>
                  </div>
                  <div className="compare-col">
                    <h4>What a receipt gives you</h4>
                    <div className="card" style={{ fontSize: '0.8125rem', fontFamily: 'var(--font-mono, monospace)' }}>
                      {selectedReceiptDetail ? (
                        <pre style={{ whiteSpace: 'pre-wrap', margin: 0, color: 'var(--text-secondary)', maxHeight: 200, overflow: 'auto' }}>
                          {selectedReceiptDetail.raw_json?.slice(0, 600)}
                          {(selectedReceiptDetail.raw_json?.length || 0) > 600 ? '\n…' : ''}
                        </pre>
                      ) : receipts.length > 0 ? (
                        <p style={{ color: 'var(--text-secondary)' }}>Select a receipt to preview its fields →</p>
                      ) : (
                        <p style={{ color: 'var(--text-secondary)' }}>No receipts loaded yet. Visit the Receipts page.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* S3: THREE STAGES (dark) */}
            <div className="section section--dark">
              <div className="wrap">
                <p className="hero-eyebrow" style={{ marginBottom: 16 }}>Three stages of control</p>
                <h2 style={{ marginBottom: 40 }}>Defense in depth, with receipts.</h2>
                <div className="stage-cards">
                  <div className="stage-card">
                    <div className="stage-num">01</div>
                    <Shield style={{ width: 28, height: 28, color: 'var(--text-secondary)', marginBottom: 12 }} />
                    <h3>Authorize</h3>
                    <p>ArmorIQ evaluates each tool call against the session policy. Unauthorized calls are denied before Tripline sees them.</p>
                    <span className="stage-owner stage-owner--platform">ArmorIQ Platform</span>
                  </div>
                  <div className="stage-card">
                    <div className="stage-num">02</div>
                    <Lock style={{ width: 28, height: 28, color: 'var(--trip-red)', marginBottom: 12 }} />
                    <h3>Contain</h3>
                    <p>Tripline's path jail blocks directory traversal. The egress gateway scans outbound payloads for planted canary tokens.</p>
                    <span className="stage-owner stage-owner--tripline">Tripline</span>
                  </div>
                  <div className="stage-card">
                    <div className="stage-num">03</div>
                    <FileText style={{ width: 28, height: 28, color: 'var(--allow)', marginBottom: 12 }} />
                    <h3>Prove</h3>
                    <p>The witness log records every tool execution with HMAC chains. Each incident produces a signed receipt you can verify independently.</p>
                    <span className="stage-owner stage-owner--tripline">Tripline</span>
                  </div>
                </div>
              </div>
            </div>

            {/* S8: PROOF LINKS (light) */}
            <div className="section section--light">
              <div className="wrap">
                <h2 style={{ marginBottom: 32 }}>Explore the evidence.</h2>
                <div className="proof-links">
                  {[
                    { key: 'console' as TabKey, title: 'Run Console', status: `${jobs.length} jobs in history` },
                    { key: 'burst' as TabKey, title: 'Jail Burst', status: summary ? `${summary.probes_passed}/${summary.probes_total} probes` : 'Loading…' },
                    { key: 'receipts' as TabKey, title: 'Receipts', status: summary ? `${summary.receipts} signed receipts` : 'Loading…' },
                    { key: 'witness' as TabKey, title: 'Witness', status: summary ? `${summary.witness_records} log records` : 'Loading…' },
                    { key: 'measured' as TabKey, title: 'Measured', status: 'Defense rate matrix' },
                    { key: 'evidence' as TabKey, title: 'Evidence', status: evidence ? `${evidence.total_files} files indexed` : 'Loading…' },
                    { key: 'claims' as TabKey, title: 'Claims & Limits', status: claims ? `${claims.verified_count} verified` : 'Loading…' },
                    { key: 'platform' as TabKey, title: 'Checklist', status: 'Platform onboarding' },
                    { key: 'video' as TabKey, title: 'Demo Video', status: 'Forensic walkthrough' },
                  ].map(item => (
                    <button key={item.key} className="proof-link" onClick={() => switchTab(item.key)}
                      data-testid={`proof-link-${item.key}`} type="button">
                      <div>
                        <div className="proof-link-title">{item.title}</div>
                        <div className="proof-link-status">{item.status}</div>
                      </div>
                      <span className="proof-link-arrow">→</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* S9: CLOSING (dark) */}
            <div className="section section--dark">
              <div className="wrap">
                <div className="closing-statement">
                  <h2>ArmorIQ decides. Tripline <span className="highlight">proves.</span></h2>
                  <p>Built for the ArmorIQ Flow State hackathon. Sandbox environment with fixture data. Not a production security system.</p>
                  <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                    <button className="btn btn-primary" onClick={() => switchTab('receipts')} type="button">Inspect receipts</button>
                    <button className="btn btn-secondary" onClick={() => switchTab('claims')} type="button">Claims & Limits</button>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* ═══════════════════════════════════════════════════════════
            CONSOLE
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'console' && (
          <div className="wrap view-panel">
            <div className="page-header">
              <h2>Run Console</h2>
              <p>Dispatch verification jobs with real-time SSE output streaming.</p>
            </div>

            <div className="card" style={{ marginBottom: 24 }}>
              <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
                <label style={{ fontSize: '0.8125rem', fontFamily: 'var(--font-mono, monospace)' }}>
                  Job kind:
                  <select value={selectedKind} onChange={(e) => setSelectedKind(e.target.value)}
                    data-testid="select-job-kind" data-local="select-job-kind"
                    style={{ marginLeft: 8, padding: '6px 10px', background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)', borderRadius: 4 }}>
                    <option value="jail_burst">jail_burst — Path containment, offline</option>
                    <option value="tamper_demo">tamper_demo — Cryptographic tamper demo</option>
                    <option value="verify_all">verify_all — Receipt & chain verification</option>
                    <option value="audit">audit — Repo truth audit</option>
                    <option value="tests">tests — Offline unit tests</option>
                    <option value="scenario">scenario — Phase 3 multi-issue runner</option>
                    <option value="armoriq_proof">armoriq_proof — Live ArmorIQ check</option>
                  </select>
                </label>

                {selectedKind === 'armoriq_proof' && (
                  <label style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono, monospace)', color: 'var(--hold)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <input type="checkbox" checked={liveConfirmChecked}
                      onChange={(e) => setLiveConfirmChecked(e.target.checked)}
                      data-testid="checkbox-live-confirm" data-local="toggle-live-confirm" />
                    Confirm live execution (requires active key)
                  </label>
                )}

                <div style={{ marginLeft: 'auto', display: 'flex', gap: 10 }}>
                  <button className="btn btn-primary" onClick={handleStartJob}
                    disabled={isJobRunning || (selectedKind === 'armoriq_proof' && !liveConfirmChecked)}
                    data-testid="btn-start-job" data-api="POST /api/jobs" type="button">
                    <Play style={{ width: 14, height: 14 }} /> Start
                  </button>
                  <button className="btn btn-danger" onClick={handleCancelJob} disabled={!isJobRunning}
                    data-testid="btn-cancel-job" data-api="POST /api/jobs/{id}/cancel" type="button">
                    <Square style={{ width: 14, height: 14 }} /> Cancel
                  </button>
                </div>
              </div>
              {jobError && <div style={{ color: 'var(--deny)', fontSize: '0.8125rem', marginTop: 12 }}>[ERROR] {jobError}</div>}
            </div>

            {/* Terminal */}
            <div style={{ marginBottom: 32 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono, monospace)', color: 'var(--dim)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Terminal style={{ width: 14, height: 14 }} />
                  Live Output ({activeJobId || 'idle'})
                </span>
                <StatusBadge status={isJobRunning ? 'STREAMING' : 'IDLE'} />
              </div>
              <div className="terminal" ref={terminalRef} id="console-stream" data-testid="console-output-stream"
                role="log" aria-live="polite" aria-label="Job output">
                {consoleLogs.length === 0 ? (
                  <span style={{ color: 'var(--dim)' }}>No active job. Select a kind and click Start.</span>
                ) : consoleLogs.map((line, idx) => (
                  <div key={idx} className="terminal-line">{line}</div>
                ))}
              </div>
            </div>

            {/* Job history */}
            <h3 style={{ marginBottom: 16 }}>Job History</h3>
            <div className="data-table-wrap">
              <table className="data-table" data-testid="jobs-history-table">
                <thead><tr>
                  <th>Job ID</th><th>Kind</th><th>Status</th><th>Started</th><th>Exit</th><th>Actions</th>
                </tr></thead>
                <tbody>
                  {jobs.length === 0 ? (
                    <tr><td colSpan={6} style={{ textAlign: 'center', padding: 32 }}>No jobs executed yet.</td></tr>
                  ) : jobs.map(j => (
                    <tr key={j.job_id}>
                      <td><code>{truncHash(j.job_id, 16)}</code></td>
                      <td>{j.kind}</td>
                      <td><StatusBadge status={j.status} /></td>
                      <td>{formatTimeWithTooltip(j.started_at)}</td>
                      <td><code>{j.exit_code ?? '—'}</code></td>
                      <td>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button className="btn btn-ghost btn-sm"
                            onClick={() => api.getJob(j.job_id).then(res => setConsoleLogs(prev => [...prev, `[INSPECT ${res.job_id}] ${res.status} exit=${res.exit_code ?? '—'}`]))}
                            data-testid={`btn-inspect-job-${j.job_id}`} data-api="GET /api/jobs/{job_id}" type="button">
                            Inspect
                          </button>
                          <button className="btn btn-ghost btn-sm"
                            onClick={() => { setActiveJobId(j.job_id); subscribeJobLogs(j.job_id) }}
                            data-testid={`btn-stream-job-${j.job_id}`} data-api="GET /api/jobs/{job_id}/events" type="button">
                            Stream
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            ATTRIBUTION
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'attribution' && (
          <div className="wrap view-panel">
            <div className="page-header">
              <h2>Layer Attribution</h2>
              <p>Defense-in-depth architectural boundaries and containment responsibilities.</p>
            </div>
            <div className="card" style={{ marginBottom: 24 }}>
              <p style={{ margin: 0, fontSize: '0.875rem' }}>
                <strong>Attribution principle:</strong> ArmorIQ decides tool permissions. Tripline inspects arguments, traps traversals, quarantines canary tokens, records physical execution counts, and signs receipts.
              </p>
            </div>
            <div className="data-table-wrap">
              <table className="data-table" data-testid="attribution-table" data-api="GET /api/attribution">
                <thead><tr><th>Layer</th><th>Name</th><th>Boundary</th><th>Mechanism</th><th>Decision</th><th>Attacks Stopped</th></tr></thead>
                <tbody>
                  {attribution?.layers?.map(l => (
                    <tr key={l.layer}>
                      <td><code>L{l.layer}</code></td>
                      <td><strong>{l.name}</strong></td>
                      <td style={{ fontSize: '0.75rem' }}>{l.boundary}</td>
                      <td style={{ fontSize: '0.75rem' }}>{l.mechanism}</td>
                      <td>
                        {l.decision_type === 'ATTEST' || l.decision_type === 'SEAL'
                          ? <StatusBadge status={l.decision_type} />
                          : <StatusBadge status={l.decision_type} />
                        }
                      </td>
                      <td style={{ fontSize: '0.75rem' }}>{l.stops.join(', ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            JAIL BURST
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'burst' && (
          <div className="wrap view-panel">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2>Path Jail Burst Probes</h2>
                <p>Deterministic verification of in-MCP path traversal containment.</p>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => api.getJailBurst().then(setBurst)}
                data-testid="btn-refresh-burst" data-api="GET /api/jail-burst" type="button">
                <RefreshCw style={{ width: 14, height: 14 }} /> Refresh
              </button>
            </div>
            {burst ? (
              <>
                <div className="card" style={{ marginBottom: 24 }}>
                  <div style={{ display: 'flex', gap: 32, fontSize: '0.8125rem', fontFamily: 'var(--font-mono, monospace)', flexWrap: 'wrap' }}>
                    <div>Total Probes: <strong>{burst.total_probes}</strong></div>
                    <div>Passed: <strong style={{ color: 'var(--allow)' }}>{burst.passed_probes}</strong></div>
                    <div>ArmorIQ: <StatusBadge status="not checked (tool authorized)" /></div>
                  </div>
                  {burst.reconciliation_note && (
                    <p style={{ fontSize: '0.75rem', color: 'var(--dim)', marginTop: 12, marginBottom: 0 }}>{burst.reconciliation_note}</p>
                  )}
                </div>
                <div className="data-table-wrap">
                  <table className="data-table" data-testid="jail-burst-table">
                    <thead><tr><th>Probe</th><th>Path</th><th>ArmorIQ</th><th>Jail Decision</th><th>Bytes</th><th>Verdict</th></tr></thead>
                    <tbody>
                      {burst.probes?.map((p, idx) => (
                        <tr key={idx}>
                          <td><strong>{p.attempt}</strong></td>
                          <td><code style={{ fontSize: '0.6875rem', wordBreak: 'break-all' }}>{p.path}</code></td>
                          <td><StatusBadge status={p.armoriq_decision} /></td>
                          <td><StatusBadge status={p.jail_decision} /></td>
                          <td><code>{p.fake_key_bytes}</code></td>
                          <td><StatusBadge status={p.verdict} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <EmptyState title="Loading probes…" description="The jail burst test runs deterministic path traversal probes against the real MCP tool." />
            )}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            RECEIPTS
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'receipts' && (
          <div className="wrap view-panel">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
              <div>
                <h2>Incident Receipts</h2>
                <p>Canonical JSON + SHA-256 hash verification and 1-byte tamper demonstration.</p>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-secondary btn-sm" onClick={() => api.getReceipts().then(setReceipts)}
                  data-testid="btn-refresh-receipts" data-api="GET /api/receipts" type="button">
                  <RefreshCw style={{ width: 14, height: 14 }} /> Refresh
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => api.getAuditLinks().then(setAuditLinks)}
                  data-testid="btn-audit-links" data-api="GET /api/audit-links" type="button">
                  <Waypoints style={{ width: 14, height: 14 }} /> Audit Links
                </button>
              </div>
            </div>

            {auditLinks && (
              <div className="card" style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <strong>Sidecar Audit Links Chain ({auditLinks.chain_length} links)</strong>
                  <StatusBadge status={auditLinks.valid ? 'CHAIN VALID' : 'CHAIN BROKEN'} />
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--dim)', margin: 0 }}>Reason: {auditLinks.reason}</p>
              </div>
            )}

            {receipts.length > 0 ? (
              <div className="grid-2">
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <h3>Recorded Receipts ({receipts.length})</h3>
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <input type="text" placeholder="Filter by tool, decision, or ID…" value={receiptFilter}
                      onChange={e => setReceiptFilter(e.target.value)}
                      style={{ width: '100%', padding: '8px 12px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 4, color: 'var(--text)', fontSize: '0.8125rem' }} />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 500, overflowY: 'auto' }}>
                    {filteredReceipts.map(r => (
                      <div key={r.receipt_id} className={`card card--interactive ${selectedReceiptId === r.receipt_id ? 'card--selected' : ''}`}
                        onClick={() => setSelectedReceiptId(r.receipt_id)}
                        data-testid={`receipt-row-${r.receipt_id}`} data-api="GET /api/receipts/{id}"
                        style={{ padding: 14 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                          <code style={{ fontSize: '0.6875rem' }}>{truncHash(r.receipt_id, 20)}</code>
                          <StatusBadge status={r.tripline_decision} />
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--dim)' }}>
                          Tool: <code>{r.tool}</code> · <HashChip hash={truncHash(r.canonical_hash, 12)} full={r.canonical_hash} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 style={{ marginBottom: 12 }}>Receipt Inspector</h3>
                  {selectedReceiptDetail ? (
                    <div className="card">
                      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                        <button className="btn btn-primary btn-sm" onClick={() => api.verifyReceipt(selectedReceiptId).then(setReceiptVerifyResult)}
                          data-testid="btn-verify-receipt" data-api="POST /api/receipts/{id}/verify" type="button">
                          <ShieldCheck style={{ width: 14, height: 14 }} /> Verify
                        </button>
                        <button className="btn btn-secondary btn-sm" onClick={() => api.tamperReceipt(selectedReceiptId).then(setReceiptTamperResult)}
                          data-testid="btn-tamper-receipt" data-api="POST /api/receipts/{id}/tamper-check" type="button">
                          <AlertTriangle style={{ width: 14, height: 14 }} /> Tamper test
                        </button>
                      </div>

                      {receiptVerifyResult && (
                        <div style={{ padding: 12, background: 'rgba(61,214,140,0.06)', border: '1px solid var(--allow)', borderRadius: 6, marginBottom: 12 }}>
                          <div style={{ color: 'var(--allow)', fontWeight: 600, fontSize: '0.8125rem' }}>✓ {receiptVerifyResult.status || 'VERIFIED'}</div>
                          <code style={{ fontSize: '0.6875rem', display: 'block', marginTop: 4, color: 'var(--dim)' }}>{receiptVerifyResult.command}</code>
                        </div>
                      )}

                      {receiptTamperResult && (
                        <div style={{ padding: 12, background: 'rgba(255,99,105,0.06)', border: '1px solid var(--deny)', borderRadius: 6, marginBottom: 12 }}>
                          <div style={{ color: 'var(--deny)', fontWeight: 600, fontSize: '0.8125rem' }}>✕ TAMPER DETECTED</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 4 }}>{receiptTamperResult.verifier_reason}</div>
                          <small style={{ color: 'var(--dim)', display: 'block', marginTop: 4 }}>Original receipt file remained byte-identical.</small>
                        </div>
                      )}

                      <pre style={{ maxHeight: 300, overflow: 'auto', fontSize: '0.6875rem', background: 'var(--ink-950)', padding: 14, borderRadius: 6, margin: 0 }}>
                        {selectedReceiptDetail.raw_json}
                      </pre>
                    </div>
                  ) : (
                    <EmptyState title="Select a receipt" description="Click a receipt from the list to inspect its fields, verify its signature, or run a tamper test." />
                  )}
                </div>
              </div>
            ) : (
              <EmptyState title="No receipts found" description="Run a scenario to generate signed receipts." command="make scenario" />
            )}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            WITNESS
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'witness' && (
          <div className="wrap view-panel">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2>Witness Log & HMAC Chain</h2>
                <p>Append-only HMAC-chained log recording every tool execution.</p>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary btn-sm" onClick={() => api.verifyWitness().then(setWitnessVerifyResult)}
                  data-testid="btn-verify-witness" data-api="POST /api/witness/verify" type="button">
                  <ShieldCheck style={{ width: 14, height: 14 }} /> Verify Chain
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => api.tamperWitness().then(setWitnessTamperResult)}
                  data-testid="btn-tamper-witness" data-api="POST /api/witness/tamper-check" type="button">
                  <AlertTriangle style={{ width: 14, height: 14 }} /> Tamper Copy
                </button>
              </div>
            </div>

            {witnessVerifyResult && (
              <div style={{ padding: 12, background: 'rgba(61,214,140,0.06)', border: '1px solid var(--allow)', borderRadius: 6, marginBottom: 16 }}>
                <div style={{ color: 'var(--allow)', fontWeight: 600, fontSize: '0.8125rem' }}>
                  ✓ WITNESS CHAIN VALID ({witnessVerifyResult.inspected_records} records verified)
                </div>
              </div>
            )}
            {witnessTamperResult && (
              <div style={{ padding: 12, background: 'rgba(255,99,105,0.06)', border: '1px solid var(--deny)', borderRadius: 6, marginBottom: 16 }}>
                <div style={{ color: 'var(--deny)', fontWeight: 600, fontSize: '0.8125rem' }}>✕ CHAIN TAMPER DETECTED: {witnessTamperResult.verifier_reason}</div>
              </div>
            )}

            <div className="card" style={{ marginBottom: 24 }}>
              <div style={{ display: 'flex', gap: 32, fontSize: '0.8125rem', fontFamily: 'var(--font-mono, monospace)' }}>
                <div>Total Records: <strong>{witness?.total_records ?? '—'}</strong></div>
                <div>Status: <StatusBadge status={witness?.chain_status || 'loading'} /></div>
              </div>
            </div>

            <h3 style={{ marginBottom: 16 }}>MCP Witness Logs</h3>
            <div className="data-table-wrap">
              <table className="data-table" data-testid="witness-logs-table" data-api="GET /api/witness">
                <thead><tr><th>Log File</th><th>Path</th><th>Events</th><th>Executions</th></tr></thead>
                <tbody>
                  {witness?.mcp_logs && Object.entries(witness.mcp_logs).map(([name, count]) => (
                    <tr key={name}>
                      <td><strong>{name}</strong></td>
                      <td><code>.tripline/witness/{name}</code></td>
                      <td><code>{count as number}</code></td>
                      <td><code>{name.includes('repo') ? 1 : 0}</code></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            MEASURED
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'measured' && (
          <div className="wrap view-panel">
            <div className="page-header">
              <h2>Measured Runs & Defense Rates</h2>
              <p>Statistical findings across Arms A (No Defense), B (ArmorIQ Only), and C (ArmorIQ + Tripline).</p>
            </div>
            <div className="card" style={{ marginBottom: 24 }}>
              <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono, monospace)', color: 'var(--dim)' }}>
                Status: <strong style={{ color: 'var(--hold)' }}>{measured?.status || 'UNVERIFIED_NO_LLM_KEY'}</strong>
                <span style={{ marginLeft: 16 }}>Session Cap: 80</span>
                <span style={{ marginLeft: 16 }}>k per cell: 5</span>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--dim)', marginTop: 8, marginBottom: 0 }}>
                No statistical claim: this model, these prompts, this fixture set. Offline runs reflect deterministic M2 forced-compliance stubs.
              </p>
            </div>
            <div className="data-table-wrap">
              <table className="data-table" data-testid="measured-table" data-api="GET /api/measured">
                <thead><tr><th>Arm</th><th>Attack</th><th>k</th><th>Attempted</th><th>Executed</th><th>Decided By</th><th>Protection</th></tr></thead>
                <tbody>
                  {measured?.rows?.map((r, idx) => (
                    <tr key={idx}>
                      <td><strong>{r.arm}</strong></td>
                      <td><code>{r.attack}</code></td>
                      <td>{r.k}</td>
                      <td>{r.attempted_ratio}</td>
                      <td><code>{r.executed_ratio}</code></td>
                      <td>{r.decided_by}</td>
                      <td><StatusBadge status={r.protection_rate} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            EVIDENCE
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'evidence' && (
          <div className="wrap view-panel">
            <div className="page-header">
              <h2>Evidence Index</h2>
              <p>Cryptographic catalog of all evidence files with computed SHA-256 digests.</p>
            </div>
            <div className="data-table-wrap">
              <table className="data-table" data-testid="evidence-table" data-api="GET /api/evidence">
                <thead><tr><th>File</th><th>Size</th><th>SHA-256</th><th>Claim</th><th>Action</th></tr></thead>
                <tbody>
                  {evidence?.items?.map(item => (
                    <tr key={item.path}>
                      <td><code style={{ fontSize: '0.6875rem' }}>{item.path}</code></td>
                      <td>{item.size_bytes} B</td>
                      <td><HashChip hash={truncHash(item.sha256)} full={item.sha256} /></td>
                      <td style={{ fontSize: '0.75rem' }}>{item.claims_supported.join(', ')}</td>
                      <td>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button className="btn btn-ghost btn-sm" onClick={() => handleViewEvidence(item.path)}
                            data-testid={`btn-view-${item.path}`} data-api="GET /api/evidence/file" type="button">
                            <Eye style={{ width: 12, height: 12 }} /> View
                          </button>
                          <a className="btn btn-ghost btn-sm" href={`/api/evidence/file?path=${encodeURIComponent(item.path)}`}
                            download data-testid={`btn-download-${item.path}`} data-api="GET /api/evidence/file">
                            <Download style={{ width: 12, height: 12 }} />
                          </a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {viewingFile && (
              <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 20 }}
                onClick={(e) => { if (e.target === e.currentTarget) setViewingFile(null) }}>
                <div style={{ background: 'var(--ink-900)', border: '1px solid var(--border)', borderRadius: 8, width: 'min(900px, 100%)', maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: 16, borderBottom: '1px solid var(--border)' }}>
                    <code style={{ fontSize: '0.8125rem' }}>{viewingFile.path}</code>
                    <button onClick={() => setViewingFile(null)} data-testid="btn-close-evidence-modal"
                      data-local="close-evidence-modal" type="button"
                      style={{ background: 'none', border: 'none', color: 'var(--text)', cursor: 'pointer' }}>
                      <X style={{ width: 16, height: 16 }} />
                    </button>
                  </div>
                  <pre style={{ padding: 16, overflow: 'auto', fontSize: '0.75rem', margin: 0 }}>{viewingFile.content}</pre>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            VIDEO
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'video' && (
          <div className="wrap view-panel">
            <div className="page-header">
              <h2>Demo Video</h2>
              <p>Forensic walkthrough with synchronized captions.</p>
            </div>
            <div className="card" style={{ maxWidth: 860, margin: 'auto' }}>
              <video controls style={{ width: '100%', borderRadius: 6, background: '#000' }}
                data-testid="demo-video-player" data-api="GET /api/video">
                <source src="/api/video" type="video/mp4" />
                <track src="/api/video/captions" kind="subtitles" srcLang="en" label="English" default />
                Your browser does not support the video tag.
              </video>
              <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono, monospace)', color: 'var(--dim)' }}>
                  H.264 / AAC · 1080p
                </span>
                <a className="btn btn-secondary btn-sm" href="/api/video" download="tripline_demo.mp4"
                  data-testid="btn-download-video" data-api="GET /api/video">
                  <Download style={{ width: 12, height: 12 }} /> Download
                </a>
              </div>
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            CLAIMS
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'claims' && (
          <div className="wrap view-panel">
            <div className="page-header">
              <h2>Claims & Limits</h2>
              <p>Factual audit matrix verifying all statements across project documents.</p>
            </div>
            <div className="card" style={{ marginBottom: 24, borderColor: 'var(--hold)' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: 8 }}>⚠ Limits and Residuals</h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0 }}>
                Tripline is built for the ArmorIQ Flow State hackathon. It runs in a sandbox with fixture data.
                Receipts use HMAC-SHA256 (symmetric key) — a holder of the key could forge them.
                The witness log is a local file, not a distributed ledger.
                Statistical measurements use forced-compliance stubs when no LLM key is configured.
              </p>
            </div>
            <div className="card" style={{ marginBottom: 24 }}>
              <div style={{ display: 'flex', gap: 24, fontSize: '0.8125rem', fontFamily: 'var(--font-mono, monospace)' }}>
                <div>Total: <strong>{claims?.total_claims ?? '—'}</strong></div>
                <div>Verified: <strong style={{ color: 'var(--allow)' }}>{claims?.verified_count ?? '—'}</strong></div>
                <div>Unverified: <strong>{claims?.unverified_count ?? '—'}</strong></div>
                <div>Failed: <strong style={{ color: 'var(--deny)' }}>{claims?.failed_count ?? '—'}</strong></div>
              </div>
            </div>
            <div className="data-table-wrap">
              <table className="data-table" data-testid="claims-table" data-api="GET /api/claims">
                <thead><tr><th>ID</th><th>Claim</th><th>Evidence</th><th>Verdict</th></tr></thead>
                <tbody>
                  {claims?.items?.map(c => (
                    <tr key={c.id}>
                      <td><code>{c.id}</code></td>
                      <td>{c.claim}</td>
                      <td><code style={{ fontSize: '0.6875rem' }}>{c.evidence_path}</code></td>
                      <td><StatusBadge status={c.verdict} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            CHECKLIST
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'platform' && (
          <div className="wrap view-panel">
            <div className="page-header">
              <h2>ArmorIQ Platform Checklist</h2>
              <p>Onboarding and configuration verification.</p>
            </div>
            <div className="card" style={{ marginBottom: 24 }}>
              <p style={{ margin: 0, fontSize: '0.8125rem', fontFamily: 'var(--font-mono, monospace)' }}>
                Platform: <strong>{platform?.platform_url || '—'}</strong> · Agent: <strong>{platform?.agent_id || '—'}</strong>
              </p>
            </div>
            <div className="data-table-wrap">
              <table className="data-table" data-testid="platform-table" data-api="GET /api/platform-checklist">
                <thead><tr><th>ID</th><th>Step</th><th>Status</th><th>Evidence</th><th>Instruction</th></tr></thead>
                <tbody>
                  {platform?.items?.map(item => (
                    <tr key={item.item_id}>
                      <td><code>{item.item_id}</code></td>
                      <td><strong>{item.title}</strong></td>
                      <td><StatusBadge status={item.status} /></td>
                      <td>{item.evidence_file ? <code style={{ fontSize: '0.6875rem' }}>{item.evidence_file}</code> : <span style={{ color: 'var(--dim)' }}>Pending</span>}</td>
                      <td style={{ fontSize: '0.75rem' }}>{item.instruction}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            ABOUT
        ═══════════════════════════════════════════════════════════ */}
        {tab === 'about' && (
          <div className="wrap view-panel">
            <div className="page-header">
              <h2>About Tripline</h2>
              <p>Architecture, design principles, and system metadata.</p>
            </div>
            <div className="grid-2" style={{ marginBottom: 24 }}>
              <div className="card">
                <h3 style={{ marginBottom: 16 }}>System Information</h3>
                <table style={{ width: '100%', fontSize: '0.8125rem', fontFamily: 'var(--font-mono, monospace)', borderCollapse: 'collapse' }}>
                  <tbody>
                    <tr><td style={{ padding: '8px 0', color: 'var(--dim)', width: 140 }}>Python:</td><td>{env?.python_version || '—'}</td></tr>
                    <tr><td style={{ padding: '8px 0', color: 'var(--dim)' }}>ArmorIQ SDK:</td><td>{env?.armoriq_sdk_version || '—'}</td></tr>
                    <tr><td style={{ padding: '8px 0', color: 'var(--dim)' }}>Branch:</td><td>{health?.branch || '—'}</td></tr>
                    <tr><td style={{ padding: '8px 0', color: 'var(--dim)' }}>Commit:</td><td><code>{health?.git_commit || '—'}</code></td></tr>
                    <tr><td style={{ padding: '8px 0', color: 'var(--dim)' }}>Enforcement:</td><td>{env?.enforcement_mode || '—'}</td></tr>
                    <tr><td style={{ padding: '8px 0', color: 'var(--dim)' }}>LLM Provider:</td><td>{env?.llm_provider || '—'}</td></tr>
                    <tr><td style={{ padding: '8px 0', color: 'var(--dim)' }}>LLM Model:</td><td>{env?.llm_model || '—'}</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="card">
                <h3 style={{ marginBottom: 12 }}>What Tripline does</h3>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.6 }}>
                  Tripline sits as an MCP security proxy inspecting tool proposals between LLM dispatch and execution.
                  It provides path containment (jail), egress canary detection, HMAC-chained witness logging, and
                  signed incident receipts.
                </p>
                <h3 style={{ marginBottom: 12 }}>What it does NOT do</h3>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  Tripline does not prevent prompt injection. It does not provide tamper-proof storage (receipts use
                  symmetric HMAC keys). It does not replace ArmorIQ's authorization — it supplements it with forensic evidence.
                  This is a hackathon project running in a sandbox.
                </p>
                <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
                  <button className="btn btn-secondary btn-sm" onClick={() => api.getDocs().then(setDocsList)}
                    data-testid="btn-list-docs" data-api="GET /api/docs" type="button">
                    Index Docs
                  </button>
                  <button className="btn btn-secondary btn-sm"
                    onClick={() => api.getDoc('limitations').then(d => setDocContent({ name: d.name, content: d.content }))}
                    data-testid="btn-doc-limitations" data-api="GET /api/docs/limitations" type="button">
                    Limitations
                  </button>
                  <button className="btn btn-secondary btn-sm"
                    onClick={() => api.getDoc('judge_qa').then(d => setDocContent({ name: d.name, content: d.content }))}
                    data-testid="btn-doc-judge-qa" data-api="GET /api/docs/judge_qa" type="button">
                    Judge Q&A
                  </button>
                </div>
                {docsList.length > 0 && (
                  <div style={{ marginTop: 12, fontSize: '0.75rem' }}>
                    <strong>Available:</strong> {docsList.map(d => d.name).join(', ')}
                  </div>
                )}
              </div>
            </div>
            {docContent && (
              <div className="card">
                <h3>{docContent.name.toUpperCase()}</h3>
                <pre style={{ maxHeight: 400, overflow: 'auto', fontSize: '0.75rem', padding: 14, background: 'var(--ink-950)', borderRadius: 6, marginTop: 12 }}>
                  {docContent.content}
                </pre>
              </div>
            )}
          </div>
        )}
      </main>

      {/* ── FOOTER ── */}
      <footer className="footer" role="contentinfo">
        <div className="wrap">
          <div className="footer-grid">
            <div className="footer-brand">
              <picture>
                <source media="(prefers-color-scheme: light)" srcSet="/tripline-lockup-on-light.svg" />
                <img src="/tripline-lockup-on-dark.svg" alt="Tripline" width={112} height={24}
                  style={{ height: 24, width: 'auto', display: 'block' }} />
              </picture>
              <p>Blocked isn't evidence. Every denied action gets a receipt.</p>
            </div>
            <div className="footer-col">
              <code>Product</code>
              <button onClick={() => switchTab('receipts')} data-testid="footer-link-receipts" data-local="footer-receipts" type="button">Receipts</button>
              <button onClick={() => switchTab('overview')} data-testid="footer-link-runs" data-local="footer-runs" type="button">Overview</button>
              <button onClick={() => switchTab('attribution')} data-testid="footer-link-boundary" data-local="footer-boundary" type="button">Attribution</button>
            </div>
            <div className="footer-col">
              <code>Evidence</code>
              <button onClick={() => switchTab('measured')} data-testid="footer-link-scoreboard" data-local="footer-scoreboard" type="button">Measured</button>
              <button onClick={() => switchTab('claims')} data-testid="footer-link-limitations" data-local="footer-limitations" type="button">Claims & Limits</button>
              <button onClick={() => switchTab('witness')} type="button">Witness</button>
              <button onClick={() => switchTab('evidence')} type="button">Evidence Index</button>
            </div>
            <div className="footer-col">
              <code>System</code>
              <button onClick={() => switchTab('console')} data-testid="footer-link-console" data-local="footer-console" type="button">Run Console</button>
              <button onClick={() => switchTab('platform')} data-testid="footer-link-checklist" data-local="footer-checklist" type="button">Checklist</button>
              <button onClick={() => switchTab('about')} type="button">About</button>
              <button onClick={() => switchTab('video')} type="button">Demo Video</button>
            </div>
            <div className="footer-bottom">
              © 2026 Tripline · Built for ArmorIQ Flow State · Every denied action gets a receipt
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
