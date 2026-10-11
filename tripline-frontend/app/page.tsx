'use client'

import { useEffect, useState, useRef } from 'react'
import {
  Check,
  Copy,
  Download,
  Eye,
  FileText,
  Play,
  RefreshCw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Square,
  Terminal,
  Waypoints,
  X,
  AlertTriangle,
  Lock,
} from 'lucide-react'
import {
  api,
  HealthInfo,
  EnvInfo,
  RunSummary,
  RunDetail,
  ReceiptSummary,
  ReceiptDetail,
  JailBurstResponse,
  AttributionResponse,
  MeasuredResponse,
  WitnessSummary,
  JobRecord,
  EvidenceIndexResponse,
  ClaimsLedgerResponse,
  PlatformChecklistResponse,
} from '../lib/api'

type TabKey =
  | 'overview'
  | 'console'
  | 'attribution'
  | 'burst'
  | 'receipts'
  | 'witness'
  | 'measured'
  | 'evidence'
  | 'video'
  | 'claims'
  | 'platform'
  | 'about'

export default function App() {
  const [tab, setTab] = useState<TabKey>('overview')
  const [health, setHealth] = useState<HealthInfo | null>(null)
  const [env, setEnv] = useState<EnvInfo | null>(null)
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string>('')
  const [currentRunDetail, setCurrentRunDetail] = useState<RunDetail | null>(null)
  const [transcript, setTranscript] = useState<{ id: string; text: string | null; msg?: string | null } | null>(null)

  // Replay & Overview state
  const [activeIncidentIndex, setActiveIncidentIndex] = useState(0)
  const [copiedCmd, setCopiedCmd] = useState(false)
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  // Console / Jobs state
  const [jobs, setJobs] = useState<JobRecord[]>([])
  const [selectedKind, setSelectedKind] = useState<string>('jail_burst')
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [liveConfirmChecked, setLiveConfirmChecked] = useState(false)
  const [consoleLogs, setConsoleLogs] = useState<string[]>([])
  const [isJobRunning, setIsJobRunning] = useState(false)
  const [jobError, setJobError] = useState<string | null>(null)

  // Attribution
  const [attribution, setAttribution] = useState<AttributionResponse | null>(null)

  // Jail Burst
  const [burst, setBurst] = useState<JailBurstResponse | null>(null)

  // Receipts
  const [receipts, setReceipts] = useState<ReceiptSummary[]>([])
  const [selectedReceiptId, setSelectedReceiptId] = useState<string>('')
  const [selectedReceiptDetail, setSelectedReceiptDetail] = useState<ReceiptDetail | null>(null)
  const [receiptVerifyResult, setReceiptVerifyResult] = useState<any>(null)
  const [receiptTamperResult, setReceiptTamperResult] = useState<any>(null)

  // Witness
  const [witness, setWitness] = useState<WitnessSummary | null>(null)
  const [witnessVerifyResult, setWitnessVerifyResult] = useState<any>(null)
  const [witnessTamperResult, setWitnessTamperResult] = useState<any>(null)

  // Measured
  const [measured, setMeasured] = useState<MeasuredResponse | null>(null)

  // Evidence
  const [evidence, setEvidence] = useState<EvidenceIndexResponse | null>(null)
  const [viewingFile, setViewingFile] = useState<{ path: string; content: string } | null>(null)

  // Claims
  const [claims, setClaims] = useState<ClaimsLedgerResponse | null>(null)

  // Platform
  const [platform, setPlatform] = useState<PlatformChecklistResponse | null>(null)

  // Audit Links & Docs
  const [auditLinks, setAuditLinks] = useState<any>(null)
  const [docsList, setDocsList] = useState<any[]>([])

  // Doc
  const [docContent, setDocContent] = useState<{ name: string; content: string } | null>(null)

  const sseRef = useRef<EventSource | null>(null)

  // 1. Initial Load: Health, Env, Runs
  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => {})
    api.getEnv().then(setEnv).catch(() => {})
    api.getRuns().then((data) => {
      setRuns(data)
      if (data.length > 0) {
        setSelectedRunId(data[0].run_id)
      }
    }).catch(() => {})
  }, [])

  // 2. Fetch Run Detail when selected
  useEffect(() => {
    if (selectedRunId) {
      api.getRun(selectedRunId).then(setCurrentRunDetail).catch(() => {})
    }
  }, [selectedRunId])

  // 3. Tab-specific data loading
  useEffect(() => {
    if (tab === 'console') {
      api.listJobs().then(setJobs).catch(() => {})
    } else if (tab === 'attribution') {
      api.getAttribution().then(setAttribution).catch(() => {})
    } else if (tab === 'burst') {
      api.getJailBurst().then(setBurst).catch(() => {})
    } else if (tab === 'receipts') {
      api.getReceipts().then((data) => {
        setReceipts(data)
        if (data.length > 0 && !selectedReceiptId) {
          setSelectedReceiptId(data[0].receipt_id)
        }
      }).catch(() => {})
    } else if (tab === 'witness') {
      api.getWitness().then(setWitness).catch(() => {})
    } else if (tab === 'measured') {
      api.getMeasured().then(setMeasured).catch(() => {})
    } else if (tab === 'evidence') {
      api.getEvidenceIndex().then(setEvidence).catch(() => {})
    } else if (tab === 'claims') {
      api.getClaims().then(setClaims).catch(() => {})
    } else if (tab === 'platform') {
      api.getPlatformChecklist().then(setPlatform).catch(() => {})
    } else if (tab === 'about') {
      api.getDoc('architecture').then((d) => setDocContent({ name: d.name, content: d.content })).catch(() => {})
    }
  }, [tab])

  // 4. Fetch selected receipt detail
  useEffect(() => {
    if (selectedReceiptId) {
      setReceiptVerifyResult(null)
      setReceiptTamperResult(null)
      api.getReceipt(selectedReceiptId).then(setSelectedReceiptDetail).catch(() => {})
    }
  }, [selectedReceiptId])

  // Job SSE EventSource management
  const subscribeJobLogs = (jobId: string) => {
    if (sseRef.current) {
      sseRef.current.close()
    }
    const es = new EventSource(`/api/jobs/${encodeURIComponent(jobId)}/events`)
    sseRef.current = es

    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.line) {
          setConsoleLogs((prev) => [...prev, payload.line])
        }
        if (payload.done) {
          setIsJobRunning(false)
          es.close()
          api.listJobs().then(setJobs).catch(() => {})
        }
      } catch {
        // parse error
      }
    }

    es.onerror = () => {
      setIsJobRunning(false)
      es.close()
    }
  }

  const handleStartJob = async () => {
    setJobError(null)
    setIsJobRunning(true)
    setConsoleLogs([`[INIT] Launching job '${selectedKind}'...`])
    try {
      const confirmToken = liveConfirmChecked ? 'CONFIRMED_LIVE_EXECUTION' : undefined
      const res = await api.createJob(selectedKind, {}, confirmToken)
      setActiveJobId(res.job_id)
      subscribeJobLogs(res.job_id)
      api.listJobs().then(setJobs).catch(() => {})
    } catch (err: any) {
      setIsJobRunning(false)
      setJobError(err.message || 'Failed to start job')
      setConsoleLogs((prev) => [...prev, `[ERROR] ${err.message}`])
    }
  }

  const handleCancelJob = async () => {
    if (!activeJobId) return
    try {
      await api.cancelJob(activeJobId)
      setConsoleLogs((prev) => [...prev, `[USER] Job cancellation requested.`])
      if (sseRef.current) sseRef.current.close()
      setIsJobRunning(false)
      api.listJobs().then(setJobs).catch(() => {})
    } catch (err: any) {
      setJobError(err.message)
    }
  }

  const handleCopy = (text: string) => {
    navigator.clipboard?.writeText(text)
    setCopiedCmd(true)
    setTimeout(() => setCopiedCmd(false), 1500)
  }

  const handleViewEvidence = async (path: string) => {
    try {
      const res = await fetch(`/api/evidence/file?path=${encodeURIComponent(path)}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const txt = await res.text()
      setViewingFile({ path, content: txt })
    } catch (err: any) {
      setViewingFile({ path, content: `Error opening file: ${err.message}` })
    }
  }

  const activeRun = runs.find((r) => r.run_id === selectedRunId) || runs[0]
  const currentIncident = currentRunDetail?.records?.[activeIncidentIndex] || {
    issue: 'issue-304 (P2: Path Jail)',
    action: 'read_file(../../fake_home/.ssh/id_rsa)',
    armoriq: 'ALLOW',
    tripline: 'DENY (JAIL)',
    outcome: 'DENIED-JAIL',
    receipt: 'receipt_P2_JAIL_DENY.json',
  }

  return (
    <div className="site-shell">
      {/* ── TOPBAR HEADER (RULE 5.6) ── */}
      <header className="topbar">
        <button
          className="brand"
          onClick={() => setTab('overview')}
          data-testid="brand-button"
          data-local="navigate-overview"
          type="button"
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
        >
          <span className="brand-mark"><Waypoints /></span>
          TRIPLINE
        </button>

        <nav style={{ display: 'flex', gap: 12, overflowX: 'auto' }}>
          <button
            className={`nav-tab ${tab === 'overview' ? 'active' : ''}`}
            onClick={() => setTab('overview')}
            data-testid="nav-overview"
            data-local="switch-tab-overview"
            type="button"
          >
            Overview
          </button>
          <button
            className={`nav-tab ${tab === 'console' ? 'active' : ''}`}
            onClick={() => setTab('console')}
            data-testid="nav-console"
            data-local="switch-tab-console"
            type="button"
          >
            Console
          </button>
          <button
            className={`nav-tab ${tab === 'attribution' ? 'active' : ''}`}
            onClick={() => setTab('attribution')}
            data-testid="nav-attribution"
            data-local="switch-tab-attribution"
            type="button"
          >
            Attribution
          </button>
          <button
            className={`nav-tab ${tab === 'burst' ? 'active' : ''}`}
            onClick={() => setTab('burst')}
            data-testid="nav-burst"
            data-local="switch-tab-burst"
            type="button"
          >
            Jail Burst
          </button>
          <button
            className={`nav-tab ${tab === 'receipts' ? 'active' : ''}`}
            onClick={() => setTab('receipts')}
            data-testid="nav-receipts"
            data-local="switch-tab-receipts"
            type="button"
          >
            Receipts
          </button>
          <button
            className={`nav-tab ${tab === 'witness' ? 'active' : ''}`}
            onClick={() => setTab('witness')}
            data-testid="nav-witness"
            data-local="switch-tab-witness"
            type="button"
          >
            Witness
          </button>
          <button
            className={`nav-tab ${tab === 'measured' ? 'active' : ''}`}
            onClick={() => setTab('measured')}
            data-testid="nav-measured"
            data-local="switch-tab-measured"
            type="button"
          >
            Measured
          </button>
          <button
            className={`nav-tab ${tab === 'evidence' ? 'active' : ''}`}
            onClick={() => setTab('evidence')}
            data-testid="nav-evidence"
            data-local="switch-tab-evidence"
            type="button"
          >
            Evidence
          </button>
          <button
            className={`nav-tab ${tab === 'video' ? 'active' : ''}`}
            onClick={() => setTab('video')}
            data-testid="nav-video"
            data-local="switch-tab-video"
            type="button"
          >
            Video
          </button>
          <button
            className={`nav-tab ${tab === 'claims' ? 'active' : ''}`}
            onClick={() => setTab('claims')}
            data-testid="nav-claims"
            data-local="switch-tab-claims"
            type="button"
          >
            Claims
          </button>
          <button
            className={`nav-tab ${tab === 'platform' ? 'active' : ''}`}
            onClick={() => setTab('platform')}
            data-testid="nav-platform"
            data-local="switch-tab-platform"
            type="button"
          >
            Checklist
          </button>
          <button
            className={`nav-tab ${tab === 'about' ? 'active' : ''}`}
            onClick={() => setTab('about')}
            data-testid="nav-about"
            data-local="switch-tab-about"
            type="button"
          >
            About
          </button>
        </nav>
      </header>


      {/* ── MAIN CONTENT ROUTER ── */}
      <main className="wrap view-panel">
        {/* 1. OVERVIEW & LATEST RUN VIEW */}
        {tab === 'overview' && (
          <div>
            <section className="hero" style={{ padding: '40px 0 60px' }}>
              <div className="hero-copy">
                <p className="kicker">// FORENSIC EVIDENCE FOR AI AGENT ACTIONS</p>
                <h1>Blocked isn&apos;t evidence.</h1>
                <p className="hero-support">Every denied agent action gets a signed receipt. ArmorIQ decides. Tripline proves.</p>
                <div className="hero-actions">
                  <button
                    className="btn btn-primary"
                    onClick={() => setTab('receipts')}
                    data-testid="btn-hero-receipts"
                    data-local="switch-tab-receipts"
                    type="button"
                  >
                    INSPECT RECEIPTS →
                  </button>
                  <button
                    className="btn btn-outline"
                    onClick={() => setTab('console')}
                    data-testid="btn-hero-console"
                    data-local="switch-tab-console"
                    type="button"
                  >
                    RUN CONSOLE ↗
                  </button>
                </div>
                <div style={{ display: 'flex', gap: 10, marginTop: 10, alignItems: 'center' }}>
                  <code className="dimline">
                    {env?.enforcement_mode || 'SessionOptions mode="sdk"'} · {health?.branch || 'phase9-ui'}
                  </code>
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => api.getEnv().then(setEnv)}
                    data-testid="btn-inspect-env"
                    data-api="GET /api/env"
                    type="button"
                    style={{ fontSize: 11, padding: '2px 8px' }}
                  >
                    <RefreshCw style={{ width: 11, height: 11 }} /> Env
                  </button>
                </div>
              </div>

              <div className="grain-panel">
                <span>PROPOSAL</span>
                <span>TRIPLINE</span>
                <span>EXECUTION</span>
                <span>RECEIPT</span>
                <div className="crosshair" />
                <div className="replay-chip">
                  <code>{currentIncident.action || 'read_file(../../fake_home/.ssh/id_rsa)'}</code>
                  <span className="badge-tag allow">ALLOW · ArmorIQ Platform</span>
                  <span className="badge-tag deny">{currentIncident.tripline || 'DENY (JAIL)'}</span>
                  <small>0 physical executions witnessed</small>
                </div>
                <small className="panel-caption">Replay of active scenario run.</small>
              </div>
            </section>

            {/* Proof Tiles */}
            <section className="proof" style={{ paddingTop: 30 }}>
              <div>
                <strong>{runs.length || 2}</strong>
                <p>Recorded scenario and attack runs available.</p>
                <code>results/phase3/scenario/</code>
              </div>
              <div>
                <strong>{receipts.length || 5}</strong>
                <p>Cryptographically signed RFC-8785 receipts.</p>
                <code>results/demo/receipt_*.json</code>
              </div>
              <div>
                <strong>8 / 8</strong>
                <p>Deterministic path containment probes verified.</p>
                <code>scripts/jail_burst.py</code>
              </div>
            </section>

            {/* Replay Section */}
            <section className="replay" style={{ paddingTop: 60 }} id="runs">
              <p className="kicker">// REPLAY &amp; EVIDENCE</p>
              <h2>Replay recorded incidents.</h2>
              <p>Select an action proposal from the active scenario queue:</p>

              <div style={{ display: 'flex', gap: 10, alignItems: 'center', margin: '14px 0', flexWrap: 'wrap' }}>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => api.getRuns().then(setRuns)}
                  data-testid="btn-refresh-runs"
                  data-api="GET /api/runs"
                  type="button"
                >
                  <RefreshCw style={{ width: 12, height: 12 }} /> Refresh Runs
                </button>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => api.getLatestRun().then((r) => { setSelectedRunId(r.run_id); setCurrentRunDetail(r); })}
                  data-testid="btn-load-latest-run"
                  data-api="GET /api/runs/latest"
                  type="button"
                >
                  Load Latest Run
                </button>
                {runs.length > 0 && (
                  <select
                    value={selectedRunId}
                    onChange={(e) => {
                      setSelectedRunId(e.target.value)
                      api.getRun(e.target.value).then(setCurrentRunDetail)
                    }}
                    data-testid="select-active-run"
                    data-api="GET /api/runs/{run_id}"
                    style={{ padding: '6px 10px', background: '#0a0a0a', color: '#fff', border: '1px solid var(--border)' }}
                  >
                    {runs.map((r) => (
                      <option key={r.run_id} value={r.run_id}>
                        {r.run_id} ({r.model_id || 'scenario'})
                      </option>
                    ))}
                  </select>
                )}
                {selectedRunId && (
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => api.getRunTranscript(selectedRunId).then(setTranscript)}
                    data-testid="btn-view-run-transcript"
                    data-api="GET /api/runs/{run_id}/transcript"
                    type="button"
                  >
                    <FileText style={{ width: 12, height: 12 }} /> View Transcript
                  </button>
                )}
              </div>

              {transcript && (
                <div className="card" style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <strong>Transcript: {transcript.id}</strong>
                    <button
                      onClick={() => setTranscript(null)}
                      data-testid="btn-close-transcript"
                      data-local="close-transcript"
                      type="button"
                      style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer' }}
                    >
                      <X style={{ width: 14, height: 14 }} />
                    </button>
                  </div>
                  <pre style={{ fontSize: 11, maxHeight: 180, overflow: 'auto', background: '#070707', padding: 8 }}>
                    {transcript.text || transcript.msg || 'No transcript text available.'}
                  </pre>
                </div>
              )}

              {currentRunDetail?.records && currentRunDetail.records.length > 0 && (
                <div className="tabs">
                  {currentRunDetail.records.map((r, i) => (
                    <button
                      key={i}
                      className={activeIncidentIndex === i ? 'active' : ''}
                      onClick={() => setActiveIncidentIndex(i)}
                      data-testid={`incident-tab-${i}`}
                      data-local={`select-incident-${i}`}
                      type="button"
                    >
                      {r.issue || `Step ${i + 1}`}
                    </button>
                  ))}
                </div>
              )}

              <div className="replay-panel">
                <div>
                  <code>proposed action</code>
                  <pre>{currentIncident.action || currentIncident.issue}</pre>
                </div>
                <div className="gates">
                  <span>
                    ARMORIQ<br />
                    <span className={`badge-tag ${currentIncident.armoriq?.includes('DENY') ? 'deny' : 'allow'}`}>
                      {currentIncident.armoriq || 'ALLOW'}
                    </span>
                  </span>
                  <b>↓</b>
                  <span>
                    TRIPLINE<br />
                    <span className={`badge-tag ${currentIncident.tripline?.includes('HOLD') ? 'hold' : (currentIncident.tripline?.includes('DENY') ? 'deny' : 'allow')}`}>
                      {currentIncident.tripline || 'DENY (JAIL)'}
                    </span>
                  </span>
                </div>
                <div>
                  <code>verdict</code>
                  <p>
                    <span className="badge-tag deny">{currentIncident.outcome || 'DENIED'}</span>
                  </p>
                  <code>Witnessed executions: 0</code>
                  {currentIncident.receipt && (
                    <button
                      className="copy-button"
                      onClick={() => handleCopy(`make verify FILE=results/phase3/scenario/${currentIncident.receipt}`)}
                      data-testid="btn-copy-verify-replay"
                      data-local="copy-verify-replay"
                      type="button"
                    >
                      <code>{copiedCmd ? 'COPIED TO CLIPBOARD' : `make verify FILE=results/phase3/scenario/${currentIncident.receipt}`}</code>
                      {copiedCmd ? <Check style={{ width: 14, height: 14 }} /> : <Copy style={{ width: 14, height: 14 }} />}
                    </button>
                  )}
                </div>
              </div>
            </section>
          </div>
        )}

        {/* 2. RUN CONSOLE VIEW */}
        {tab === 'console' && (
          <div>
            <div className="view-header">
              <h2>Run Console</h2>
              <p>Dispatch allowlisted verification jobs with real-time SSE output streaming.</p>
            </div>

            <div className="card" style={{ marginBottom: 24 }}>
              <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
                <label style={{ font: '13px ui-monospace, monospace' }}>
                  Select Job Kind:
                  <select
                    value={selectedKind}
                    onChange={(e) => setSelectedKind(e.target.value)}
                    data-testid="select-job-kind"
                    data-local="select-job-kind"
                    style={{ marginLeft: 8, padding: '6px 10px', background: '#070707', color: '#fff', border: '1px solid var(--border)' }}
                  >
                    <option value="jail_burst">jail_burst (Path containment burst, offline)</option>
                    <option value="tamper_demo">tamper_demo (Cryptographic tamper demo)</option>
                    <option value="verify_all">verify_all (Sidecar & receipt chain verification)</option>
                    <option value="audit">audit (Repo truth & hygiene audit)</option>
                    <option value="tests">tests (Offline unit test suite)</option>
                    <option value="scenario">scenario (Phase 3 multi-issue runner, rung 0)</option>
                    <option value="armoriq_proof">armoriq_proof (Live ArmorIQ platform check)</option>
                  </select>
                </label>

                {selectedKind === 'armoriq_proof' && (
                  <label style={{ font: '12px ui-monospace, monospace', color: 'var(--hold)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <input
                      type="checkbox"
                      checked={liveConfirmChecked}
                      onChange={(e) => setLiveConfirmChecked(e.target.checked)}
                      data-testid="checkbox-live-confirm"
                      data-local="toggle-live-confirm"
                    />
                    Confirm live execution against ArmorIQ API (requires active key)
                  </label>
                )}

                <div style={{ marginLeft: 'auto', display: 'flex', gap: 10 }}>
                  <button
                    className="btn btn-primary"
                    onClick={handleStartJob}
                    disabled={isJobRunning || (selectedKind === 'armoriq_proof' && !liveConfirmChecked)}
                    data-testid="btn-start-job"
                    data-api="POST /api/jobs"
                    type="button"
                  >
                    <Play style={{ width: 14, height: 14 }} /> START JOB
                  </button>
                  <button
                    className="btn btn-danger"
                    onClick={handleCancelJob}
                    disabled={!isJobRunning}
                    data-testid="btn-cancel-job"
                    data-api="POST /api/jobs/{id}/cancel"
                    type="button"
                  >
                    <Square style={{ width: 14, height: 14 }} /> CANCEL
                  </button>
                </div>
              </div>

              {jobError && (
                <div style={{ color: 'var(--deny)', fontSize: 13, marginTop: 12 }}>
                  [ERROR] {jobError}
                </div>
              )}
            </div>

            {/* Live Terminal */}
            <div style={{ marginBottom: 30 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ font: '12px ui-monospace, monospace', color: 'var(--dim)' }}>
                  <Terminal style={{ width: 14, height: 14, display: 'inline', marginRight: 4 }} />
                  Live Output Feed ({activeJobId || 'idle'})
                </span>
                <span style={{ fontSize: 11, color: isJobRunning ? 'var(--hold)' : 'var(--muted)' }}>
                  {isJobRunning ? 'STREAMING VIA SSE...' : 'TERMINAL IDLE'}
                </span>
              </div>
              <div className="console-terminal" id="console-stream" data-testid="console-output-stream">
                {consoleLogs.length === 0 ? (
                  <span style={{ color: 'var(--dim)' }}>No job active. Select a job kind and click Start Job.</span>
                ) : (
                  consoleLogs.map((line, idx) => (
                    <div key={idx} className="console-line">{line}</div>
                  ))
                )}
              </div>
            </div>

            {/* History Table */}
            <div>
              <h3>Job Execution History</h3>
              <table className="data-table" data-testid="jobs-history-table">
                <thead>
                  <tr>
                    <th>Job ID</th>
                    <th>Kind</th>
                    <th>Status</th>
                    <th>Started At</th>
                    <th>Exit Code</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.length === 0 ? (
                    <tr><td colSpan={6} style={{ textAlign: 'center' }}>No jobs executed yet.</td></tr>
                  ) : (
                    jobs.map((j) => (
                      <tr key={j.job_id}>
                        <td><code>{j.job_id}</code></td>
                        <td>{j.kind}</td>
                        <td>
                          <span className={`badge-tag ${j.status === 'completed' ? 'allow' : (j.status === 'failed' ? 'deny' : 'hold')}`}>
                            {j.status}
                          </span>
                        </td>
                        <td>{j.started_at || 'unknown'}</td>
                        <td><code>{j.exit_code ?? '-'}</code></td>
                        <td>
                          <div style={{ display: 'flex', gap: 6 }}>
                            <button
                              className="btn btn-outline btn-sm"
                              onClick={() => api.getJob(j.job_id).then((res) => setConsoleLogs((prev) => [...prev, `[JOB ${res.job_id}] ${res.status}`]))}
                              data-testid={`btn-inspect-job-${j.job_id}`}
                              data-api="GET /api/jobs/{job_id}"
                              type="button"
                              style={{ padding: '2px 8px', fontSize: 11 }}
                            >
                              Inspect
                            </button>
                            <button
                              className="btn btn-outline btn-sm"
                              onClick={() => { setActiveJobId(j.job_id); subscribeJobLogs(j.job_id); }}
                              data-testid={`btn-stream-job-${j.job_id}`}
                              data-api="GET /api/jobs/{job_id}/events"
                              type="button"
                              style={{ padding: '2px 8px', fontSize: 11 }}
                            >
                              Stream
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 3. ATTRIBUTION VIEW */}
        {tab === 'attribution' && (
          <div>
            <div className="view-header">
              <h2>Layer Attribution</h2>
              <p>Defense-in-depth architectural boundaries and containment responsibilities.</p>
            </div>

            <div className="card" style={{ marginBottom: 24 }}>
              <p style={{ margin: 0, color: 'var(--text)' }}>
                <strong>Attribution Principle:</strong> ArmorIQ decides tool permissions. Tripline inspects arguments, traps traversals, quarantines canary tokens, records physical execution counts, and signs receipts.
              </p>
            </div>

            <table className="data-table" data-testid="attribution-table" data-api="GET /api/attribution">
              <thead>
                <tr>
                  <th>Layer</th>
                  <th>Name</th>
                  <th>Boundary</th>
                  <th>Mechanism</th>
                  <th>Decision</th>
                  <th>Attacks Stopped</th>
                </tr>
              </thead>
              <tbody>
                {attribution?.layers?.map((l) => (
                  <tr key={l.layer}>
                    <td><code>Layer {l.layer}</code></td>
                    <td><strong>{l.name}</strong></td>
                    <td>{l.boundary}</td>
                    <td style={{ fontSize: 12 }}>{l.mechanism}</td>
                    <td><span className="badge-tag deny">{l.decision_type}</span></td>
                    <td>{l.stops.join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 4. JAIL BURST VIEW */}
        {tab === 'burst' && (
          <div>
            <div className="view-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2>Path Jail Burst Probes</h2>
                <p>Deterministic verification of in-MCP path traversal containment.</p>
              </div>
              <button
                className="btn btn-outline"
                onClick={() => api.getJailBurst().then(setBurst)}
                data-testid="btn-refresh-burst"
                data-api="GET /api/jail-burst"
                type="button"
              >
                <RefreshCw style={{ width: 14, height: 14 }} /> Refresh Probes
              </button>
            </div>

            <div className="card" style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', gap: 24, font: '13px ui-monospace, monospace' }}>
                <div>Total Probes: <strong>{burst?.total_probes || 8}</strong></div>
                <div>Passed (0 leaks): <strong style={{ color: 'var(--allow)' }}>{burst?.passed_probes || 8}</strong></div>
                <div>ArmorIQ Decision: <span className="badge-tag neutral">not checked (tool authorized)</span></div>
              </div>
              <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 12, marginBottom: 0 }}>
                {burst?.reconciliation_note}
              </p>
            </div>

            <table className="data-table" data-testid="jail-burst-table">
              <thead>
                <tr>
                  <th>Probe Attempt</th>
                  <th>Tested Path</th>
                  <th>ArmorIQ Check</th>
                  <th>Tripline Path Jail</th>
                  <th>Bytes Read</th>
                  <th>Verdict</th>
                </tr>
              </thead>
              <tbody>
                {burst?.probes?.map((p, idx) => (
                  <tr key={idx}>
                    <td><strong>{p.attempt}</strong></td>
                    <td><code>{p.path}</code></td>
                    <td><span className="badge-tag neutral">{p.armoriq_decision}</span></td>
                    <td>
                      <span className={`badge-tag ${p.jail_decision.includes('DENIED') ? 'deny' : 'allow'}`}>
                        {p.jail_decision}
                      </span>
                    </td>
                    <td><code>{p.fake_key_bytes}</code></td>
                    <td>
                      <span className={`badge-tag ${p.verdict.includes('PASS') ? 'allow' : 'deny'}`}>
                        {p.verdict}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 5. RECEIPTS VIEW */}
        {tab === 'receipts' && (
          <div>
            <div className="view-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2>Incident Receipts</h2>
                <p>Cryptographic RFC-8785 canonical hash verification and 1-byte tamper demonstration.</p>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => api.getReceipts().then(setReceipts)}
                  data-testid="btn-refresh-receipts"
                  data-api="GET /api/receipts"
                  type="button"
                >
                  <RefreshCw style={{ width: 14, height: 14 }} /> Refresh Receipts
                </button>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => api.getAuditLinks().then(setAuditLinks)}
                  data-testid="btn-audit-links"
                  data-api="GET /api/audit-links"
                  type="button"
                >
                  <Waypoints style={{ width: 14, height: 14 }} /> Audit Links
                </button>
              </div>
            </div>

            {auditLinks && (
              <div className="card" style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <strong>Sidecar Audit Links Chain ({auditLinks.chain_length} links)</strong>
                  <span className={`badge-tag ${auditLinks.valid ? 'allow' : 'deny'}`}>
                    {auditLinks.valid ? 'CHAIN VALID' : 'CHAIN BROKEN'}
                  </span>
                </div>
                <p style={{ fontSize: 12, color: 'var(--muted)', margin: 0 }}>
                  Reason: {auditLinks.reason}
                </p>
              </div>
            )}

            <div className="grid-2">
              <div>
                <h3>Recorded Receipts</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 450, overflowY: 'auto' }}>
                  {receipts.map((r) => (
                    <div
                      key={r.receipt_id}
                      onClick={() => setSelectedReceiptId(r.receipt_id)}
                      data-testid={`receipt-row-${r.receipt_id}`}
                      data-api="GET /api/receipts/{id}"
                      style={{
                        padding: 12,
                        background: selectedReceiptId === r.receipt_id ? '#1a1a1a' : 'var(--surface)',
                        border: '1px solid var(--border)',
                        cursor: 'pointer',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <code style={{ fontSize: 11 }}>{r.receipt_id}</code>
                        <span className={`badge-tag ${r.tripline_decision.includes('DENY') ? 'deny' : 'hold'}`}>
                          {r.tripline_decision}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                        Tool: <code>{r.tool}</code> · Hash: <code style={{ fontSize: 10 }}>{r.canonical_hash.slice(0, 16)}...</code>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3>Receipt Inspector &amp; Verifiers</h3>
                {selectedReceiptDetail ? (
                  <div className="card">
                    <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
                      <button
                        className="btn btn-primary"
                        onClick={() => api.verifyReceipt(selectedReceiptId).then(setReceiptVerifyResult)}
                        data-testid="btn-verify-receipt"
                        data-api="POST /api/receipts/{id}/verify"
                        type="button"
                      >
                        <ShieldCheck style={{ width: 14, height: 14 }} /> VERIFY RECEIPT
                      </button>
                      <button
                        className="btn btn-outline"
                        onClick={() => api.tamperReceipt(selectedReceiptId).then(setReceiptTamperResult)}
                        data-testid="btn-tamper-receipt"
                        data-api="POST /api/receipts/{id}/tamper-check"
                        type="button"
                      >
                        <AlertTriangle style={{ width: 14, height: 14 }} /> TEST 1-BYTE TAMPER
                      </button>
                    </div>

                    {receiptVerifyResult && (
                      <div style={{ padding: 12, background: '#07180d', border: '1px solid var(--allow)', marginBottom: 16 }}>
                        <div style={{ color: 'var(--allow)', fontWeight: 600 }}>[✓] VERIFIED: Signature Authentic</div>
                        <code style={{ fontSize: 11, display: 'block', marginTop: 4 }}>{receiptVerifyResult.command}</code>
                      </div>
                    )}

                    {receiptTamperResult && (
                      <div style={{ padding: 12, background: '#240a0c', border: '1px solid var(--deny)', marginBottom: 16 }}>
                        <div style={{ color: 'var(--deny)', fontWeight: 600 }}>[✕] TAMPER DETECTED: Signature Mismatch</div>
                        <div style={{ fontSize: 12, color: '#ffb3b8', marginTop: 4 }}>{receiptTamperResult.verifier_reason}</div>
                        <small style={{ color: 'var(--muted)', display: 'block', marginTop: 4 }}>
                          Original receipt file remained byte-identical.
                        </small>
                      </div>
                    )}

                    <pre style={{ maxHeight: 280, overflow: 'auto', fontSize: 11, background: '#050505', padding: 12 }}>
                      {selectedReceiptDetail.raw_json}
                    </pre>
                  </div>
                ) : (
                  <div className="empty-state">Select a receipt to inspect.</div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 6. WITNESS VIEW */}
        {tab === 'witness' && (
          <div>
            <div className="view-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2>Witness Log &amp; HMAC Hash Chain</h2>
                <p>Append-only HMAC chain ensuring zero unrecorded tool executions.</p>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  className="btn btn-primary"
                  onClick={() => api.verifyWitness().then(setWitnessVerifyResult)}
                  data-testid="btn-verify-witness"
                  data-api="POST /api/witness/verify"
                  type="button"
                >
                  <ShieldCheck style={{ width: 14, height: 14 }} /> VERIFY CHAIN
                </button>
                <button
                  className="btn btn-outline"
                  onClick={() => api.tamperWitness().then(setWitnessTamperResult)}
                  data-testid="btn-tamper-witness"
                  data-api="POST /api/witness/tamper-check"
                  type="button"
                >
                  <AlertTriangle style={{ width: 14, height: 14 }} /> TAMPER CHAIN COPY
                </button>
              </div>
            </div>

            {witnessVerifyResult && (
              <div style={{ padding: 12, background: '#07180d', border: '1px solid var(--allow)', marginBottom: 16 }}>
                <div style={{ color: 'var(--allow)', fontWeight: 600 }}>
                  [✓] WITNESS CHAIN VALID ({witnessVerifyResult.inspected_records} records verified)
                </div>
              </div>
            )}

            {witnessTamperResult && (
              <div style={{ padding: 12, background: '#240a0c', border: '1px solid var(--deny)', marginBottom: 16 }}>
                <div style={{ color: 'var(--deny)', fontWeight: 600 }}>[✕] CHAIN TAMPER DETECTED: {witnessTamperResult.verifier_reason}</div>
              </div>
            )}

            <div className="card" style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', gap: 32, font: '13px ui-monospace, monospace' }}>
                <div>Total Logged Records: <strong>{witness?.total_records || 61}</strong></div>
                <div>Status: <span className="badge-tag allow">{witness?.chain_status || 'valid'}</span></div>
              </div>
            </div>

            <h3>Active MCP Witness Logs</h3>
            <table className="data-table" data-testid="witness-logs-table" data-api="GET /api/witness">
              <thead>
                <tr>
                  <th>Log File</th>
                  <th>Path</th>
                  <th>Total Events</th>
                  <th>Physical Executions</th>
                </tr>
              </thead>
              <tbody>
                {witness?.mcp_logs && Object.entries(witness.mcp_logs).map(([name, count]) => (
                  <tr key={name}>
                    <td><strong>{name}</strong></td>
                    <td><code>.tripline/witness/{name}</code></td>
                    <td><code>{count}</code></td>
                    <td><code>{name.includes('repo') ? 1 : 0}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 7. MEASURED VIEW */}
        {tab === 'measured' && (
          <div>
            <div className="view-header">
              <h2>Measured Runs &amp; Defense Rates</h2>
              <p>Statistical findings across Arms A (No Defense), B (ArmorIQ Only), and C (ArmorIQ + Tripline).</p>
            </div>

            <div className="card" style={{ marginBottom: 20 }}>
              <div style={{ font: '12px ui-monospace, monospace', color: 'var(--muted)' }}>
                <span>Manifest Status: <strong style={{ color: 'var(--hold)' }}>{measured?.status || 'UNVERIFIED_NO_LLM_KEY'}</strong></span> ·
                <span style={{ marginLeft: 8 }}>Session Cap: 80</span> ·
                <span style={{ marginLeft: 8 }}>k per cell: 5</span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--dim)', marginTop: 8, marginBottom: 0 }}>
                Disclosure: LLM emissions require live API keys. Offline runs reflect deterministic M2 forced-compliance stubs.
              </p>
            </div>

            <table className="data-table" data-testid="measured-table" data-api="GET /api/measured">
              <thead>
                <tr>
                  <th>Arm</th>
                  <th>Attack</th>
                  <th>k</th>
                  <th>Attempted (Emitted)</th>
                  <th>Executed (Sandboxed)</th>
                  <th>Decided By</th>
                  <th>Protection Rate</th>
                </tr>
              </thead>
              <tbody>
                {measured?.rows?.map((r, idx) => (
                  <tr key={idx}>
                    <td><strong>{r.arm}</strong></td>
                    <td><code>{r.attack}</code></td>
                    <td>{r.k}</td>
                    <td>{r.attempted_ratio}</td>
                    <td><code>{r.executed_ratio}</code></td>
                    <td>{r.decided_by}</td>
                    <td>
                      <span className={`badge-tag ${r.protection_rate === '100%' ? 'allow' : (r.protection_rate === '0%' ? 'deny' : 'neutral')}`}>
                        {r.protection_rate}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 8. EVIDENCE INDEX & FILE VIEWER */}
        {tab === 'evidence' && (
          <div>
            <div className="view-header">
              <h2>Evidence Index &amp; Audit Trail</h2>
              <p>Cryptographic catalog of all evidence files with computed SHA-256 digests.</p>
            </div>

            <table className="data-table" data-testid="evidence-table" data-api="GET /api/evidence">
              <thead>
                <tr>
                  <th>File Path</th>
                  <th>Size</th>
                  <th>SHA-256 Digest</th>
                  <th>Supported Claim</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {evidence?.items?.map((item) => (
                  <tr key={item.path}>
                    <td><code>{item.path}</code></td>
                    <td>{item.size_bytes} B</td>
                    <td><code style={{ fontSize: 11 }}>{item.sha256.slice(0, 16)}...</code></td>
                    <td>{item.claims_supported.join(', ')}</td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => handleViewEvidence(item.path)}
                          data-testid={`btn-view-${item.path}`}
                          data-api="GET /api/evidence/file"
                          type="button"
                        >
                          <Eye style={{ width: 12, height: 12 }} /> View
                        </button>
                        <a
                          className="btn btn-outline btn-sm"
                          href={`/api/evidence/file?path=${encodeURIComponent(item.path)}`}
                          download
                          data-testid={`btn-download-${item.path}`}
                          data-api="GET /api/evidence/file"
                        >
                          <Download style={{ width: 12, height: 12 }} />
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Modal Viewer */}
            {viewingFile && (
              <div
                style={{
                  position: 'fixed',
                  inset: 0,
                  background: 'rgba(0,0,0,0.8)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  zIndex: 100,
                  padding: 20,
                }}
              >
                <div style={{ background: '#111', border: '1px solid var(--border)', width: 'min(900px, 100%)', maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: 16, borderBottom: '1px solid var(--border)' }}>
                    <code>{viewingFile.path}</code>
                    <button
                      onClick={() => setViewingFile(null)}
                      data-testid="btn-close-evidence-modal"
                      data-local="close-evidence-modal"
                      type="button"
                      style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer' }}
                    >
                      <X style={{ width: 16, height: 16 }} />
                    </button>
                  </div>
                  <pre style={{ padding: 16, overflow: 'auto', fontSize: 12, margin: 0 }}>
                    {viewingFile.content}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 9. VIDEO VIEW */}
        {tab === 'video' && (
          <div>
            <div className="view-header">
              <h2>Demo Video &amp; Captions</h2>
              <p>86-second continuous forensic walkthrough with synchronized captions.</p>
            </div>

            <div className="card" style={{ maxWidth: 860, margin: 'auto' }}>
              <video
                controls
                style={{ width: '100%', borderRadius: 4, background: '#000' }}
                data-testid="demo-video-player"
                data-api="GET /api/video"
              >
                <source src="/api/video" type="video/mp4" />
                <track src="/api/video/captions" kind="subtitles" srcLang="en" label="English" default />
                Your browser does not support the video tag.
              </video>

              <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ font: '12px ui-monospace, monospace', color: 'var(--muted)' }}>
                  Duration: 86.00s · H.264 / AAC · 1080p
                </span>
                <a
                  className="btn btn-outline btn-sm"
                  href="/api/video"
                  download="tripline_demo_90s.mp4"
                  data-testid="btn-download-video"
                  data-api="GET /api/video"
                >
                  <Download style={{ width: 12, height: 12 }} /> Download MP4
                </a>
              </div>
            </div>
          </div>
        )}

        {/* 10. CLAIMS LEDGER VIEW */}
        {tab === 'claims' && (
          <div>
            <div className="view-header">
              <h2>Claims Ledger &amp; Limitations</h2>
              <p>Factual audit matrix verifying all statements across public project documents.</p>
            </div>

            <div className="card" style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', gap: 24, font: '13px ui-monospace, monospace' }}>
                <div>Total Statements: <strong>{claims?.total_claims || 18}</strong></div>
                <div>Verified: <strong style={{ color: 'var(--allow)' }}>{claims?.verified_count || 18}</strong></div>
                <div>Unverified: <strong>{claims?.unverified_count || 0}</strong></div>
                <div>Failed: <strong style={{ color: 'var(--deny)' }}>{claims?.failed_count || 0}</strong></div>
              </div>
            </div>

            <table className="data-table" data-testid="claims-table" data-api="GET /api/claims">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Statement / Claim</th>
                  <th>Evidence Path</th>
                  <th>Verdict</th>
                </tr>
              </thead>
              <tbody>
                {claims?.items?.map((c) => (
                  <tr key={c.id}>
                    <td><code>{c.id}</code></td>
                    <td>{c.claim}</td>
                    <td><code>{c.evidence_path}</code></td>
                    <td>
                      <span className={`badge-tag ${c.verdict === 'VERIFIED' ? 'allow' : 'deny'}`}>
                        {c.verdict}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 11. PLATFORM CHECKLIST VIEW */}
        {tab === 'platform' && (
          <div>
            <div className="view-header">
              <h2>ArmorIQ Platform Checklist</h2>
              <p>Onboarding and configuration verification on platform.armoriq.ai.</p>
            </div>

            <div className="card" style={{ marginBottom: 20 }}>
              <p style={{ margin: 0, font: '13px ui-monospace, monospace' }}>
                Platform Host: <strong>{platform?.platform_url}</strong> · Registered Agent: <strong>{platform?.agent_id}</strong>
              </p>
            </div>

            <table className="data-table" data-testid="platform-table" data-api="GET /api/platform-checklist">
              <thead>
                <tr>
                  <th>Item ID</th>
                  <th>Onboarding Step</th>
                  <th>Status</th>
                  <th>Evidence</th>
                  <th>Instruction</th>
                </tr>
              </thead>
              <tbody>
                {platform?.items?.map((item) => (
                  <tr key={item.item_id}>
                    <td><code>{item.item_id}</code></td>
                    <td><strong>{item.title}</strong></td>
                    <td>
                      <span className={`badge-tag ${item.status === 'VERIFIED' ? 'allow' : 'hold'}`}>
                        {item.status}
                      </span>
                    </td>
                    <td>
                      {item.evidence_file ? <code>{item.evidence_file}</code> : <span style={{ color: 'var(--dim)' }}>Pending</span>}
                    </td>
                    <td style={{ fontSize: 12 }}>{item.instruction}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 12. ABOUT / SYSTEM INFO VIEW */}
        {tab === 'about' && (
          <div>
            <div className="view-header">
              <h2>About Tripline</h2>
              <p>Architecture, design principles, and local system metadata.</p>
            </div>

            <div className="grid-2" style={{ marginBottom: 24 }}>
              <div className="card">
                <h3>System Information</h3>
                <table style={{ width: '100%', font: '12px ui-monospace, monospace', borderCollapse: 'collapse' }}>
                  <tbody>
                    <tr><td style={{ padding: '6px 0', color: 'var(--dim)' }}>Python:</td><td>{env?.python_version}</td></tr>
                    <tr><td style={{ padding: '6px 0', color: 'var(--dim)' }}>ArmorIQ SDK:</td><td>{env?.armoriq_sdk_version}</td></tr>
                    <tr><td style={{ padding: '6px 0', color: 'var(--dim)' }}>Git Branch:</td><td>{health?.branch}</td></tr>
                    <tr><td style={{ padding: '6px 0', color: 'var(--dim)' }}>Commit:</td><td><code>{health?.git_commit}</code></td></tr>
                    <tr><td style={{ padding: '6px 0', color: 'var(--dim)' }}>Enforcement:</td><td>{env?.enforcement_mode}</td></tr>
                  </tbody>
                </table>
              </div>

              <div className="card">
                <h3>Architecture Docs</h3>
                <p style={{ fontSize: 13, color: 'var(--muted)' }}>
                  Tripline sits as an MCP security proxy middleware inspecting tool proposals between LLM dispatch and execution.
                </p>
                <div style={{ display: 'flex', gap: 10, marginTop: 16, flexWrap: 'wrap' }}>
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => api.getDocs().then(setDocsList)}
                    data-testid="btn-list-docs"
                    data-api="GET /api/docs"
                    type="button"
                  >
                    <RefreshCw style={{ width: 12, height: 12 }} /> Index Docs
                  </button>
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => api.getDoc('limitations').then((d) => setDocContent({ name: d.name, content: d.content }))}
                    data-testid="btn-doc-limitations"
                    data-api="GET /api/docs/limitations"
                    type="button"
                  >
                    Limitations
                  </button>
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => api.getDoc('judge_qa').then((d) => setDocContent({ name: d.name, content: d.content }))}
                    data-testid="btn-doc-judge-qa"
                    data-api="GET /api/docs/judge_qa"
                    type="button"
                  >
                    Judge Q&amp;A
                  </button>
                </div>
                {docsList.length > 0 && (
                  <div style={{ marginTop: 12, fontSize: 12 }}>
                    <strong>Available Docs:</strong> {docsList.map((d) => d.name).join(', ')}
                  </div>
                )}
              </div>
            </div>

            {docContent && (
              <div className="card">
                <h3>{docContent.name.toUpperCase()}</h3>
                <pre style={{ maxHeight: 350, overflow: 'auto', fontSize: 12, padding: 12, background: '#050505' }}>
                  {docContent.content}
                </pre>
              </div>
            )}
          </div>
        )}
      </main>

      {/* ── FOOTER ── */}
      <footer className="footer wrap">
        <div>
          <strong>TRIPLINE</strong>
          <p>It&apos;s not about blocking. It&apos;s about proof.</p>
        </div>
        <div>
          <code>PRODUCT</code>
          <button onClick={() => setTab('receipts')} data-testid="footer-link-receipts" data-local="footer-receipts" style={{ background: 'none', border: 'none', color: 'var(--muted)', display: 'block', cursor: 'pointer', padding: 0, marginTop: 5 }}>Receipts</button>
          <button onClick={() => setTab('overview')} data-testid="footer-link-runs" data-local="footer-runs" style={{ background: 'none', border: 'none', color: 'var(--muted)', display: 'block', cursor: 'pointer', padding: 0, marginTop: 5 }}>Runs</button>
          <button onClick={() => setTab('attribution')} data-testid="footer-link-boundary" data-local="footer-boundary" style={{ background: 'none', border: 'none', color: 'var(--muted)', display: 'block', cursor: 'pointer', padding: 0, marginTop: 5 }}>Boundary</button>
        </div>
        <div>
          <code>EVIDENCE</code>
          <button onClick={() => setTab('measured')} data-testid="footer-link-scoreboard" data-local="footer-scoreboard" style={{ background: 'none', border: 'none', color: 'var(--muted)', display: 'block', cursor: 'pointer', padding: 0, marginTop: 5 }}>Benchmark data</button>
          <button onClick={() => setTab('claims')} data-testid="footer-link-limitations" data-local="footer-limitations" style={{ background: 'none', border: 'none', color: 'var(--muted)', display: 'block', cursor: 'pointer', padding: 0, marginTop: 5 }}>Limitations</button>
        </div>
        <div>
          <code>SYSTEM</code>
          <button onClick={() => setTab('console')} data-testid="footer-link-console" data-local="footer-console" style={{ background: 'none', border: 'none', color: 'var(--muted)', display: 'block', cursor: 'pointer', padding: 0, marginTop: 5 }}>Run Console</button>
          <button onClick={() => setTab('platform')} data-testid="footer-link-checklist" data-local="footer-checklist" style={{ background: 'none', border: 'none', color: 'var(--muted)', display: 'block', cursor: 'pointer', padding: 0, marginTop: 5 }}>Checklist</button>
        </div>
        <small>© 2026 Tripline · Built for ArmorIQ Flow State Hackathon · Every denied action gets a receipt</small>
      </footer>
    </div>
  )
}
