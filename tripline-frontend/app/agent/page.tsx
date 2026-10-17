'use client'

import React, { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import {
  Shield,
  Bot,
  Key,
  FileText,
  Clock,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  ExternalLink,
  ChevronDown,
  Terminal,
  Cpu,
  Lock,
  Search,
  Radio,
  FileCheck,
  AlertOctagon,
  Copy,
  Check,
} from 'lucide-react'
import {
  api,
  AgentCrewManifest,
  AgentRunManifest,
  AgentRunEvent,
  PlatformStatus,
  JobRecord,
  REATargetItem,
  REAInvestigationSummary,
  subscribeToJobEvents,
  subscribeToAgentRunEvents,
} from '../../lib/api'
import { SecurityDecisionCard } from '../../components/security/SecurityDecisionCard'

export default function AgentPage() {
  // Authoritative state from backend
  const [crew, setCrew] = useState<AgentCrewManifest | null>(null)
  const [crewLoading, setCrewLoading] = useState(true)
  const [runs, setRuns] = useState<AgentRunManifest[]>([])
  const [runsLoading, setRunsLoading] = useState(true)
  const [selectedRun, setSelectedRun] = useState<AgentRunManifest | null>(null)
  const [platformStatus, setPlatformStatus] = useState<PlatformStatus | null>(null)

  // Event stream state
  const [streamMode, setStreamMode] = useState<'run' | 'job'>('run')
  const [runEvents, setRunEvents] = useState<AgentRunEvent[]>([])
  const [jobLines, setJobLines] = useState<string[]>([])
  const [activeJob, setActiveJob] = useState<JobRecord | null>(null)

  // Live execution modal & status
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [launchingLive, setLaunchingLive] = useState(false)
  const [launchError, setLaunchError] = useState<string | null>(null)
  const [killTriggered, setKillTriggered] = useState(false)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  // REA Investigation state
  const [reaTargets, setReaTargets] = useState<REATargetItem[]>([])
  const [selectedReaTarget, setSelectedReaTarget] = useState<string>('synthetic-electron-app')
  const [selectedReaTool, setSelectedReaTool] = useState<string>('analyze_electron_app')
  const [pastInvestigations, setPastInvestigations] = useState<REAInvestigationSummary[]>([])
  const [selectedInvestigation, setSelectedInvestigation] = useState<any | null>(null)
  const [reaRunning, setReaRunning] = useState(false)
  const [reaMessage, setReaMessage] = useState<string | null>(null)

  // Active view tab in Agent console
  const [activeTab, setActiveTab] = useState<'runs' | 'events' | 'decisions' | 'rea'>('runs')

  // Auto-scroll ref for terminal streams
  const terminalEndRef = useRef<HTMLDivElement>(null)

  // 1. Initial Load from Backend APIs
  useEffect(() => {
    // Agent Crew Manifest
    setCrewLoading(true)
    api.getAgentCrew()
      .then((data) => setCrew(data))
      .catch((err) => console.error('Error fetching crew:', err))
      .finally(() => setCrewLoading(false))

    // Agent Runs History
    setRunsLoading(true)
    api.getAgentRuns()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setRuns(data)
          setSelectedRun(data[0])
        }
      })
      .catch((err) => console.error('Error fetching agent runs:', err))
      .finally(() => setRunsLoading(false))

    // Platform status
    api.getPlatformStatus()
      .then((ps) => setPlatformStatus(ps))
      .catch((err) => console.error('Error fetching platform status:', err))

    // REA targets & investigations
    api.getReaTargets()
      .then((res) => {
        if (res && res.targets) {
          setReaTargets(res.targets)
          if (res.targets.length > 0) {
            setSelectedReaTarget(res.targets[0].id)
          }
        }
      })
      .catch(() => {})

    api.getReaInvestigations()
      .then((res) => {
        if (Array.isArray(res)) setPastInvestigations(res)
      })
      .catch(() => {})
  }, [])

  // 2. Stream events when a run is selected
  useEffect(() => {
    if (!selectedRun?.run_id || streamMode !== 'run') return
    setRunEvents([])

    const unsubscribe = subscribeToAgentRunEvents(
      selectedRun.run_id,
      (ev) => {
        setRunEvents((prev) => [...prev.slice(-99), ev])
      },
      (err) => {
        console.error('SSE Stream error:', err)
      }
    )

    return () => unsubscribe()
  }, [selectedRun?.run_id, streamMode])

  // 3. Auto-scroll terminal stream
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [runEvents, jobLines])

  // Handler: Copy public key
  const handleCopyKey = (key: string, id: string) => {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(key)
      setCopiedKey(id)
      setTimeout(() => setCopiedKey(null), 2000)
    }
  }

  // Handler: Start Live Governed Agent Run
  const handleStartLiveRun = async () => {
    setShowConfirmModal(false)
    setLaunchingLive(true)
    setLaunchError(null)
    setJobLines([])

    try {
      const job = await api.startAgentRun()
      setActiveJob(job)
      setStreamMode('job')
      setActiveTab('events')

      // Subscribe to real live job events
      subscribeToJobEvents(
        job.job_id,
        (ev) => {
          if (ev.line) {
            setJobLines((prev) => [...prev, ev.line!])
          }
          if (ev.done) {
            setJobLines((prev) => [...prev, `[COMPLETE] Job ${job.job_id} finished with status: ${ev.status}`])
            // Refresh runs to pick up the newly generated run
            api.getAgentRuns().then((updatedRuns) => {
              if (Array.isArray(updatedRuns) && updatedRuns.length > 0) {
                setRuns(updatedRuns)
                setSelectedRun(updatedRuns[0])
              }
            })
          }
        },
        (err) => {
          setJobLines((prev) => [...prev, `[STREAM ERROR] Connection lost: ${err}`])
        }
      )
    } catch (err: any) {
      setLaunchError(err.message || 'Failed to start live run.')
    } finally {
      setLaunchingLive(false)
    }
  }

  // Handler: Stop Agent / Trigger Kill Switch
  const handleStopRun = async () => {
    if (activeJob) {
      try {
        await api.cancelJob(activeJob.job_id)
        setJobLines((prev) => [...prev, `[CANCELLED] Job ${activeJob.job_id} cancelled via backend.`])
      } catch (e) {}
    }

    if (selectedRun?.run_id) {
      try {
        const res = await api.stopAgentRun(selectedRun.run_id)
        if (res.status === 'stopped') {
          setKillTriggered(true)
        }
      } catch (e: any) {
        console.error('Stop run error:', e)
      }
    }
  }

  // Handler: Run Controlled REA Investigation
  const handleRunRea = async () => {
    setReaRunning(true)
    setReaMessage('Dispatching controlled static analysis to REA MCP engine...')
    try {
      const job = await api.startReaInvestigation(selectedReaTarget, selectedReaTool)
      setReaMessage(`Investigation job ${job.job_id} running against ${selectedReaTarget}...`)
      
      // Poll or listen for completion
      const interval = setInterval(async () => {
        try {
          const detail = await api.getJob(job.job_id)
          if (detail.status === 'completed' || detail.status === 'failed') {
            clearInterval(interval)
            setReaRunning(false)
            setReaMessage(`Investigation finished (${detail.status}). Refreshing reports...`)
            // Refresh investigations
            const updated = await api.getReaInvestigations()
            setPastInvestigations(updated)
            if (updated.length > 0) {
              const fullDetail = await api.getReaInvestigation(updated[0].run_id)
              setSelectedInvestigation(fullDetail)
            }
          }
        } catch {
          clearInterval(interval)
          setReaRunning(false)
        }
      }, 2000)
    } catch (err: any) {
      setReaRunning(false)
      setReaMessage(`Failed to initiate REA investigation: ${err.message}`)
    }
  }

  // Handler: Load REA investigation detail
  const handleSelectInvestigation = async (runId: string) => {
    try {
      const detail = await api.getReaInvestigation(runId)
      setSelectedInvestigation(detail)
    } catch (err) {
      console.error('Error loading investigation:', err)
    }
  }

  return (
    <div className="w-full flex flex-col text-[#20252B] bg-[#F4F5F6] min-h-screen py-10 px-4 sm:px-6">
      <div className="max-w-[1280px] mx-auto w-full space-y-8">
        
        {/* Page Header with Real Status Telemetry */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-[#CDD2D8]">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-mono text-[#65BCE7] uppercase tracking-widest font-semibold">
              <Bot className="w-4 h-4 text-[#65BCE7]" />
              <span>// AUTHORITATIVE AGENT GOVERNANCE CONSOLE</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-[#20252B] tracking-tight">
              Agent Crew, Scoped Delegation & Execution State
            </h1>
            <p className="text-xs sm:text-sm text-[#59636E] max-w-3xl leading-relaxed">
              Live inspection of orchestrator intent contracts, delegated sub-agent Ed25519 public keys, plan hashes, multi-layer security decisions, and verified event streams.
            </p>
          </div>

          {/* Quick Actions & Live Launch Button */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0">
            <button
              data-api="POST /api/agent/runs"
              onClick={() => setShowConfirmModal(true)}
              disabled={!platformStatus?.live_enabled || launchingLive}
              className={`px-5 py-2.5 rounded-lg text-xs font-mono font-semibold flex items-center gap-2 shadow-sm transition-all ${
                platformStatus?.live_enabled
                  ? 'bg-[#20252B] hover:bg-[#2D3136] text-white'
                  : 'bg-[#EAEDF0] border border-[#CDD2D8] text-[#747F8D] cursor-not-allowed'
              }`}
              data-testid="btn-start-agent-run"
            >
              <Play className="w-3.5 h-3.5 text-[#65BCE7]" />
              <span>{launchingLive ? 'Launching...' : 'Start Live Governed Run'}</span>
            </button>

            <button
              data-api="POST /api/agent/runs/{id}/stop"
              onClick={handleStopRun}
              className="px-4 py-2.5 rounded-lg border border-red-300 bg-red-50 text-red-700 hover:bg-red-100 text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
              data-testid="btn-stop-agent-run"
            >
              <AlertOctagon className="w-3.5 h-3.5" />
              <span>Kill Switch</span>
            </button>
          </div>
        </div>

        {/* Readiness Badges Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 font-mono text-xs">
          <div className="p-3 rounded-xl bg-[#FFFFFF] border border-[#CDD2D8] shadow-sm">
            <span className="text-[10px] text-[#747F8D] uppercase block">Orchestrator Role</span>
            <span className="text-[#20252B] font-bold block mt-0.5">
              {crew?.orchestrator?.name || (crewLoading ? 'Loading...' : 'tripline-maintainer')}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-[#FFFFFF] border border-[#CDD2D8] shadow-sm">
            <span className="text-[10px] text-[#747F8D] uppercase block">ArmorIQ Authorization</span>
            <span className="text-[#65BCE7] font-bold block mt-0.5">
              {platformStatus?.key_present ? `Mode B (SDK ${platformStatus.sdk_version || '0.6.10'})` : 'Missing Credentials (Fail-Closed)'}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-[#FFFFFF] border border-[#CDD2D8] shadow-sm">
            <span className="text-[10px] text-[#747F8D] uppercase block">Execution Gate</span>
            <span className={`font-bold block mt-0.5 ${platformStatus?.live_enabled ? 'text-[#10B981]' : 'text-[#747F8D]'}`}>
              {platformStatus?.live_enabled ? 'Live Runs Enabled' : 'Live Gate: TRIPLINE_ENABLE_LIVE=0'}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-[#FFFFFF] border border-[#CDD2D8] shadow-sm">
            <span className="text-[10px] text-[#747F8D] uppercase block">Delegated Keypairs</span>
            <span className="text-[#20252B] font-bold block mt-0.5">
              {crew?.sub_agents?.length ? `${crew.sub_agents.length} Ephemeral Ed25519` : '—'}
            </span>
          </div>
        </div>

        {/* Launch Error Notification */}
        {launchError && (
          <div className="p-4 rounded-xl bg-[#EF4444]/15 border border-[#EF4444]/30 text-xs font-mono text-[#F87171] flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{launchError}</span>
            </div>
            <button
              onClick={() => setLaunchError(null)}
              data-local="dismiss-launch-error"
              className="text-[#9296AD] hover:text-white text-xs underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {killTriggered && (
          <div className="p-4 rounded-xl bg-[#EF4444]/20 border border-[#EF4444]/40 text-xs font-mono text-[#FF6369] flex items-center gap-2.5">
            <AlertOctagon className="w-5 h-5 shrink-0" />
            <span>
              <strong>EMERGENCY KILL SWITCH TRIGGERED:</strong> Subsequent agent triage loops and tool executions have been halted server-side.
            </span>
          </div>
        )}

        {/* SECTION 1: CREW ARCHITECTURE & DELEGATED ROLES */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Bot className="w-4 h-4 text-[#5B4BFF]" />
              <span>Delegated Crew Architecture & Scoped Capabilities</span>
            </h2>
            <span className="text-xs font-mono text-[#6B6E7A]">Source: GET /api/agent/crew</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Orchestrator Card */}
            <div className="p-5 rounded-xl border border-[#1C1F33] bg-[#0D0F18] flex flex-col justify-between space-y-4 shadow-md">
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#5B4BFF]/20 text-[#9A8CFF] font-bold">
                    ORCHESTRATOR
                  </span>
                  <span className="font-mono text-[10px] text-[#6B6E7A]">Parent Intent Token</span>
                </div>
                <h3 className="text-base font-bold text-white">
                  {crew?.orchestrator?.name || (crewLoading ? 'Loading orchestrator...' : 'tripline-maintainer')}
                </h3>
                <p className="text-xs text-[#9296AD] leading-relaxed">
                  Synthesizes trusted triage plans before reading untrusted issue content. Holds parent token authority; strictly blocked from destructive operations like <code className="text-[#F87171]">delete_branch</code>.
                </p>
              </div>
              <div className="pt-3 border-t border-white/5 space-y-1 text-[11px] font-mono">
                <div className="text-[#6B6E7A]">Model: <span className="text-white">{crew?.orchestrator?.model || 'gemini-3.8-flash'}</span></div>
                <div className="text-[#6B6E7A]">Authority: <span className="text-[#34D399]">{crew?.orchestrator?.authority || 'Parent Plan Owner'}</span></div>
              </div>
            </div>

            {/* Sub-Agents from Authoritative Backend Manifest */}
            {crewLoading ? (
              <div className="md:col-span-2 p-8 text-center text-xs text-[#6B6E7A] font-mono bg-[#0D0F18] border border-[#1C1F33] rounded-xl flex items-center justify-center">
                Loading delegated sub-agent capabilities...
              </div>
            ) : crew?.sub_agents && crew.sub_agents.length > 0 ? (
              crew.sub_agents.map((sub, idx) => (
                <div
                  key={sub.name || idx}
                  className="p-5 rounded-xl border border-[#1C1F33] bg-[#0D0F18] flex flex-col justify-between space-y-4 shadow-md"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#30A46C]/15 text-[#34D399] font-bold uppercase">
                        SUB-AGENT: {sub.role}
                      </span>
                      <span className="font-mono text-[10px] text-[#6B6E7A]">Scoped Delegate</span>
                    </div>
                    <h3 className="text-base font-bold text-white">{sub.name}</h3>
                    <p className="text-xs text-[#9296AD] leading-relaxed">
                      {sub.role === 'reader'
                        ? 'Granted repository inspection privileges only. Cannot modify comments or labels.'
                        : 'Granted triage response actions only. Disjoint from file system reading privileges.'}
                    </p>

                    <div className="space-y-1">
                      <span className="text-[10px] font-mono text-[#6B6E7A] uppercase block">Permitted Tool Vocabulary:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {sub.allowed_tools.map((t) => (
                          <span key={t} className="px-2 py-0.5 rounded bg-white/5 border border-white/5 font-mono text-[10px] text-white">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-white/5 space-y-1.5 font-mono text-[11px]">
                    <div className="flex items-center justify-between text-[#6B6E7A]">
                      <span>Ed25519 Pubkey:</span>
                      <button
                        data-local="copy-pubkey"
                        onClick={() => handleCopyKey(sub.public_key_hex, sub.name)}
                        className="text-[#9A8CFF] hover:underline flex items-center gap-1 text-[10px]"
                        title="Copy full 32-byte public key hex"
                      >
                        {copiedKey === sub.name ? <Check className="w-3 h-3 text-[#30A46C]" /> : <Copy className="w-3 h-3" />}
                        <span>{copiedKey === sub.name ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>
                    <code className="text-[10px] text-[#AEB1BA] block truncate bg-[#07080F] p-1.5 rounded border border-white/5">
                      {sub.public_key_hex}
                    </code>
                  </div>
                </div>
              ))
            ) : (
              <div className="md:col-span-2 p-8 text-center text-xs text-[#6B6E7A] font-mono bg-[#0D0F18] border border-[#1C1F33] rounded-xl flex items-center justify-center">
                No sub-agent delegates returned by manifest.
              </div>
            )}
          </div>
        </section>

        {/* SECTION 2: RUN HISTORY & NAVIGATION TABS */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1C1F33]">
            {/* Navigation Tabs */}
            <div className="flex items-center gap-2 font-mono text-xs">
              <button
                data-local="tab-runs"
                onClick={() => setActiveTab('runs')}
                className={`px-3.5 py-1.5 rounded-lg transition-colors font-semibold ${
                  activeTab === 'runs'
                    ? 'bg-[#5B4BFF] text-white shadow-md'
                    : 'text-[#9296AD] hover:bg-white/5'
                }`}
              >
                Run Manifest ({runs.length})
              </button>
              <button
                data-local="tab-decisions"
                onClick={() => setActiveTab('decisions')}
                className={`px-3.5 py-1.5 rounded-lg transition-colors font-semibold ${
                  activeTab === 'decisions'
                    ? 'bg-[#5B4BFF] text-white shadow-md'
                    : 'text-[#9296AD] hover:bg-white/5'
                }`}
              >
                Security Decisions
              </button>
              <button
                data-local="tab-events"
                onClick={() => setActiveTab('events')}
                className={`px-3.5 py-1.5 rounded-lg transition-colors font-semibold ${
                  activeTab === 'events'
                    ? 'bg-[#5B4BFF] text-white shadow-md'
                    : 'text-[#9296AD] hover:bg-white/5'
                }`}
              >
                Event Stream {streamMode === 'job' ? '(Live Job)' : `(${runEvents.length})`}
              </button>
              <button
                data-local="tab-rea"
                onClick={() => setActiveTab('rea')}
                className={`px-3.5 py-1.5 rounded-lg transition-colors font-semibold ${
                  activeTab === 'rea'
                    ? 'bg-[#5B4BFF] text-white shadow-md'
                    : 'text-[#9296AD] hover:bg-white/5'
                }`}
              >
                REA Reverse Engineering
              </button>
            </div>

            {/* Run Selector Dropdown */}
            {runs.length > 0 && (
              <div className="flex items-center gap-2 font-mono text-xs">
                <span className="text-[#6B6E7A]">Selected Run:</span>
                <select
                  data-api="GET /api/agent/runs/{run_id}"
                  value={selectedRun?.run_id || ''}
                  onChange={(e) => {
                    const match = runs.find((r) => r.run_id === e.target.value)
                    if (match) {
                      setSelectedRun(match)
                      setStreamMode('run')
                    }
                  }}
                  className="bg-[#0D0F18] border border-[#1C1F33] text-white px-3 py-1.5 rounded-lg focus:outline-none focus:ring-1 focus:ring-[#5B4BFF]"
                >
                  {runs.map((r) => (
                    <option key={r.run_id} value={r.run_id}>
                      {r.run_id} ({r.model || 'gemini'})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* TAB 1: RUN MANIFEST DETAILS */}
          {activeTab === 'runs' && (
            <div className="p-6 rounded-xl border border-[#1C1F33] bg-[#0D0F18] space-y-6 shadow-xl">
              {runsLoading ? (
                <div className="py-12 text-center text-xs font-mono text-[#6B6E7A]">
                  Loading run records from results/phase11...
                </div>
              ) : !selectedRun ? (
                <div className="py-12 text-center text-xs font-mono text-[#9296AD] space-y-2">
                  <p className="text-white font-semibold">No Run Manifest Found</p>
                  <p>Execute <code className="text-[#9A8CFF]">make agent</code> or use "Start Live Governed Run" to produce a verified run.</p>
                </div>
              ) : (
                <>
                  <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#1C1F33]">
                    <div>
                      <span className="font-mono text-xs uppercase text-[#6B6E7A]">// VERIFIED RUN MANIFEST</span>
                      <h3 className="text-xl font-bold text-white mt-1 font-mono">
                        {selectedRun.run_id}
                      </h3>
                    </div>
                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="px-2.5 py-1 rounded bg-[#30A46C]/15 text-[#34D399] border border-[#30A46C]/30 font-semibold">
                        STATUS: {selectedRun.status || 'RECORDED'}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
                    <div className="p-3.5 rounded-lg bg-[#111422] border border-white/5">
                      <span className="text-[#6B6E7A] text-[10px] uppercase block">Model ID</span>
                      <span className="text-white font-bold mt-0.5 block">{selectedRun.model || 'gemini-3.8-flash'}</span>
                    </div>
                    <div className="p-3.5 rounded-lg bg-[#111422] border border-white/5">
                      <span className="text-[#6B6E7A] text-[10px] uppercase block">Integration Mode</span>
                      <span className="text-white font-bold mt-0.5 block">MODE {selectedRun.mode || 'B (Decide & Prove)'}</span>
                    </div>
                    <div className="p-3.5 rounded-lg bg-[#111422] border border-white/5">
                      <span className="text-[#6B6E7A] text-[10px] uppercase block">Identity Attribution</span>
                      <span className="text-[#AEB1BA] mt-0.5 block truncate">{selectedRun.user_email || 'sandbox-maintainer@example.invalid'}</span>
                    </div>
                    <div className="p-3.5 rounded-lg bg-[#111422] border border-white/5">
                      <span className="text-[#6B6E7A] text-[10px] uppercase block">Forensic Receipts</span>
                      <span className="text-[#9A8CFF] font-bold mt-0.5 block">{selectedRun.receipts?.length ?? 0} Signed Receipts</span>
                    </div>
                  </div>

                  {/* Cryptographic Hashes */}
                  <div className="p-4 rounded-lg bg-[#07080F] border border-white/5 font-mono text-xs space-y-2">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <span className="text-[#6B6E7A]">RFC 8785 Plan Hash:</span>
                      <code className="text-[#AEB1BA] break-all">{selectedRun.plan_hash || 'Unrecorded (synthetic plan)'}</code>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <span className="text-[#6B6E7A]">ArmorIQ Merkle Root:</span>
                      <code className="text-[#AEB1BA] break-all">{selectedRun.merkle_root || 'Unrecorded'}</code>
                    </div>
                  </div>

                  {/* Outcome summary numbers */}
                  <div className="grid grid-cols-2 sm:grid-cols-6 gap-3 font-mono text-xs text-center">
                    <div className="p-3 rounded-lg bg-[#111422] border border-white/5">
                      <span className="text-[#6B6E7A] text-[10px] uppercase block">Total Issues</span>
                      <span className="text-white font-bold text-base mt-1 block">
                        {selectedRun.counts?.total_issues ?? (selectedRun.issues?.length || 0)}
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#111422] border border-white/5">
                      <span className="text-[#30A46C] text-[10px] uppercase block">Executed</span>
                      <span className="text-[#30A46C] font-bold text-base mt-1 block">
                        {selectedRun.counts?.executed ?? 0}
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#111422] border border-white/5">
                      <span className="text-[#FF6369] text-[10px] uppercase block">ArmorIQ Denied</span>
                      <span className="text-[#FF6369] font-bold text-base mt-1 block">
                        {selectedRun.counts?.denied_by_armoriq ?? 0}
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#111422] border border-white/5">
                      <span className="text-[#F5A524] text-[10px] uppercase block">Jail Denied</span>
                      <span className="text-[#F5A524] font-bold text-base mt-1 block">
                        {selectedRun.counts?.denied_by_jail ?? 0}
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#111422] border border-white/5">
                      <span className="text-[#F5A524] text-[10px] uppercase block">Egress Held</span>
                      <span className="text-[#F5A524] font-bold text-base mt-1 block">
                        {selectedRun.counts?.held_by_egress ?? 0}
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#111422] border border-white/5">
                      <span className="text-[#9A8CFF] text-[10px] uppercase block">Receipts</span>
                      <span className="text-[#9A8CFF] font-bold text-base mt-1 block">
                        {selectedRun.receipts?.length ?? 0}
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* TAB 2: MULTI-LAYER SECURITY DECISIONS */}
          {activeTab === 'decisions' && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-[#0D0F18] border border-[#1C1F33] text-xs font-mono text-[#9296AD]">
                Authoritative breakdown of proposed operations from run <strong>{selectedRun?.run_id || 'active'}</strong>, showing independent ArmorIQ upstream authorization vs TripLine parameter and sandbox enforcement.
              </div>

              {selectedRun?.issues && selectedRun.issues.length > 0 ? (
                <div className="space-y-4">
                  {selectedRun.issues.map((iss: any, i: number) => (
                    <SecurityDecisionCard
                      key={iss.issue_id || i}
                      action={iss.proposed_tool || iss.tool || 'read_file'}
                      targetOrArgs={iss.tool_arguments || iss.args || iss.target}
                      armoriqDecision={iss.armoriq_decision || (iss.outcome === 'BLOCKED_BY_ARMORIQ' ? 'DENY' : 'ALLOW')}
                      armoriqReason={iss.armoriq_reason || 'Authorization evaluated against session policy'}
                      armoriqPolicy={iss.matched_policy || 'cli-tripline-maintainer-tripline-mcp'}
                      triplineDecision={
                        iss.outcome === 'DENIED_BY_PATH_JAIL'
                          ? 'DENY'
                          : iss.outcome === 'HELD_BY_EGRESS'
                          ? 'HOLD'
                          : 'ALLOW'
                      }
                      triplineControl={
                        iss.outcome === 'DENIED_BY_PATH_JAIL'
                          ? 'path_jail'
                          : iss.outcome === 'HELD_BY_EGRESS'
                          ? 'egress_canary'
                          : 'in-MCP sandbox'
                      }
                      triplineReason={
                        iss.tripline_reason ||
                        (iss.outcome === 'DENIED_BY_PATH_JAIL'
                          ? 'Attempted directory traversal escaping approved root'
                          : iss.outcome === 'HELD_BY_EGRESS'
                          ? 'Outbound canary token detected in payload'
                          : 'Parameter bounds verified')
                      }
                      dispatchStatus={
                        iss.dispatched === true || iss.executed === true
                          ? 'EXECUTED'
                          : iss.outcome === 'HELD_BY_EGRESS'
                          ? 'HELD'
                          : 'BLOCKED'
                      }
                      executionOutcome={iss.execution_outcome || iss.outcome}
                      receiptId={iss.receipt_id}
                      verificationStatus={iss.verification_status || 'VERIFIED'}
                      timestamp={iss.timestamp}
                    />
                  ))}
                </div>
              ) : (
                <div className="p-12 text-center border border-[#CDD2D8] bg-[#FFFFFF] rounded-xl shadow-sm">
                  <div className="font-mono text-xs text-[#747F8D] uppercase tracking-wider mb-2">
                    No Policy Decisions Recorded for Run {selectedRun?.run_id || 'none'}
                  </div>
                  <p className="text-sm text-[#59636E] max-w-md mx-auto leading-relaxed">
                    This run did not record granular issue actions. Select a different run from the history or launch a governed proof job to inspect real decision boundaries.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: REAL-TIME EVENT STREAM VIEWER */}
          {activeTab === 'events' && (
            <div className="p-6 rounded-xl border border-[#1C1F33] bg-[#0D0F18] flex flex-col space-y-4 shadow-xl">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#1C1F33] text-xs font-mono">
                <div className="flex items-center gap-2 text-[#9A8CFF]">
                  <Terminal className="w-4 h-4" />
                  <span>
                    {streamMode === 'job'
                      ? `// LIVE SUBPROCESS STDOUT: ${activeJob?.job_id || 'job'}`
                      : `// RECORDED EVENT REPLAY: ${selectedRun?.run_id || 'run'}`}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[#6B6E7A]">
                    {streamMode === 'job' ? `${jobLines.length} Lines` : `${runEvents.length} Events`}
                  </span>
                  {streamMode === 'job' && (
                    <button
                      data-local="set-stream-run"
                      onClick={() => setStreamMode('run')}
                      className="text-xs text-[#9A8CFF] hover:underline"
                    >
                      Switch to Recorded Run Events
                    </button>
                  )}
                </div>
              </div>

              <div className="h-[460px] overflow-y-auto space-y-2.5 font-mono text-xs pr-2 bg-[#07080F] p-4 rounded-lg border border-white/5">
                {streamMode === 'job' ? (
                  jobLines.length === 0 ? (
                    <div className="py-20 text-center text-[#6B6E7A] space-y-2">
                      <div className="w-3 h-3 rounded-full bg-[#5B4BFF] animate-ping mx-auto" />
                      <p>Connected to live job event stream. Waiting for subprocess output...</p>
                    </div>
                  ) : (
                    jobLines.map((line, i) => (
                      <div key={i} className="text-[#AEB1BA] leading-relaxed break-all">
                        {line}
                      </div>
                    ))
                  )
                ) : runEvents.length === 0 ? (
                  <div className="py-20 text-center text-[#6B6E7A] space-y-2">
                    <p>No structured SSE events logged for this run.</p>
                  </div>
                ) : (
                  runEvents.map((ev, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-lg bg-[#0F111D] border border-white/5 flex flex-col gap-1.5"
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-[#9A8CFF] font-semibold">{ev.event_type}</span>
                        <span className="text-[#6B6E7A]">{ev.source || 'agent'}</span>
                      </div>
                      <pre className="text-[11px] text-[#AEB1BA] whitespace-pre-wrap overflow-x-auto">
                        {JSON.stringify(ev.data, null, 2)}
                      </pre>
                    </div>
                  ))
                )}
                <div ref={terminalEndRef} />
              </div>
            </div>
          )}

          {/* TAB 4: REA REVERSE ENGINEERING INTEGRATION */}
          {activeTab === 'rea' && (
            <div className="space-y-6">
              {/* REA Control Panel */}
              <div className="p-6 rounded-xl border border-[#1C1F33] bg-[#0D0F18] space-y-5 shadow-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1C1F33]">
                  <div>
                    <span className="font-mono text-xs uppercase tracking-wider text-[#9A8CFF]">
                      // REA MCP SOFTWARE INVESTIGATOR
                    </span>
                    <h3 className="text-xl font-bold text-white mt-1">
                      Static Analysis of Preapproved Targets
                    </h3>
                    <p className="text-xs text-[#9296AD] mt-1 max-w-2xl">
                      TripLine integrates with the official REA MCP server to perform controlled static analysis of synthetic Electron/JavaScript applications, generating untrusted evidence packages and cryptographic receipts.
                    </p>
                  </div>

                  <button
                    data-api="POST /api/jobs"
                    onClick={handleRunRea}
                    disabled={reaRunning}
                    className={`px-5 py-2.5 rounded-lg text-xs font-mono font-semibold flex items-center gap-2 shadow-md shrink-0 ${
                      reaRunning
                        ? 'bg-white/10 text-[#6B6E7A] cursor-not-allowed'
                        : 'bg-[#5B4BFF] hover:bg-[#4E3FE8] text-white'
                    }`}
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>{reaRunning ? 'Analyzing...' : 'Run Governed Analysis'}</span>
                  </button>
                </div>

                {reaMessage && (
                  <div className="p-3.5 rounded-lg bg-[#5B4BFF]/10 border border-[#5B4BFF]/30 font-mono text-xs text-[#9A8CFF]">
                    {reaMessage}
                  </div>
                )}

                {/* Target & Tool Selectors */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
                  <div>
                    <label className="text-[#6B6E7A] uppercase text-[10px] block mb-1">
                      Preapproved Analysis Target:
                    </label>
                    <select
                      data-local="select-rea-target"
                      value={selectedReaTarget}
                      onChange={(e) => setSelectedReaTarget(e.target.value)}
                      className="w-full bg-[#07080F] border border-[#1C1F33] text-white p-2.5 rounded-lg"
                    >
                      {reaTargets.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.id} ({t.path})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-[#6B6E7A] uppercase text-[10px] block mb-1">
                      Protected REA Operation:
                    </label>
                    <select
                      data-local="select-rea-tool"
                      value={selectedReaTool}
                      onChange={(e) => setSelectedReaTool(e.target.value)}
                      className="w-full bg-[#07080F] border border-[#1C1F33] text-white p-2.5 rounded-lg"
                    >
                      <option value="analyze_electron_app">analyze_electron_app (IPC + token extraction)</option>
                      <option value="inspect_analysis_view">inspect_analysis_view (summary evidence)</option>
                      <option value="trace_application_feature">trace_application_feature (feature flow)</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Past Investigations List & Detail View */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* List */}
                <div className="lg:col-span-5 p-5 rounded-xl border border-[#1C1F33] bg-[#0D0F18] space-y-3">
                  <div className="flex items-center justify-between pb-3 border-b border-[#1C1F33] font-mono text-xs">
                    <span className="text-[#9A8CFF] font-semibold">// REA INVESTIGATIONS</span>
                    <span className="text-[#6B6E7A]">{pastInvestigations.length} Packages</span>
                  </div>

                  <div className="space-y-2 max-h-[460px] overflow-y-auto pr-1">
                    {pastInvestigations.length === 0 ? (
                      <div className="py-12 text-center text-xs font-mono text-[#6B6E7A]">
                        No investigation packages found under investigations/. Run an analysis above.
                      </div>
                    ) : (
                      pastInvestigations.map((inv) => (
                        <div
                          key={inv.run_id}
                          onClick={() => handleSelectInvestigation(inv.run_id)}
                          className={`p-3 rounded-lg border cursor-pointer transition-all font-mono text-xs space-y-1.5 ${
                            selectedInvestigation?.run_id === inv.run_id
                              ? 'bg-[#121422] border-[#5B4BFF]'
                              : 'bg-[#0A0B10] border-white/5 hover:border-white/20'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-white font-bold">{inv.run_id}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                              inv.auth_decision === 'ALLOW' ? 'bg-[#10B981]/15 text-[#34D399]' : 'bg-[#EF4444]/15 text-[#F87171]'
                            }`}>
                              {inv.auth_decision || 'ALLOW'}
                            </span>
                          </div>
                          <div className="flex items-center justify-between text-[10px] text-[#6B6E7A]">
                            <span>{inv.operation || 'analyze'}</span>
                            <span>{inv.evidence_count} Evidence Refs</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Detail */}
                <div className="lg:col-span-7 p-5 rounded-xl border border-[#1C1F33] bg-[#0D0F18] space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-[#1C1F33] font-mono text-xs">
                    <span className="text-[#9A8CFF] font-semibold">// REPORT & CRYPTOGRAPHIC RECEIPT</span>
                    {selectedInvestigation && (
                      <span className="text-[#34D399]">{selectedInvestigation.run_id}</span>
                    )}
                  </div>

                  {!selectedInvestigation ? (
                    <div className="py-24 text-center text-xs font-mono text-[#6B6E7A]">
                      Select an investigation from the left to inspect its findings and cryptographic receipt.
                    </div>
                  ) : (
                    <div className="space-y-4 font-mono text-xs max-h-[460px] overflow-y-auto pr-1">
                      {/* Receipt summary */}
                      {selectedInvestigation.receipt && (
                        <div className="p-3.5 rounded-lg bg-[#07080F] border border-white/5 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-[#9A8CFF] font-bold">Forensic Receipt: {selectedInvestigation.receipt.receipt_id}</span>
                            <span className="text-[10px] px-2 py-0.5 rounded bg-white/10 text-white">
                              {selectedInvestigation.receipt.verification_status || 'LIVE_VERIFIED'}
                            </span>
                          </div>
                          <div className="text-[11px] text-[#AEB1BA]">
                            Operation: <strong className="text-white">{selectedInvestigation.receipt.operation}</strong>
                          </div>
                          <div className="text-[10px] text-[#6B6E7A] break-all">
                            HMAC-SHA256: {selectedInvestigation.receipt.hmac_sha256}
                          </div>
                        </div>
                      )}

                      {/* Markdown report preview */}
                      {selectedInvestigation.report_markdown && (
                        <div className="p-3.5 rounded-lg bg-[#07080F] border border-white/5 space-y-2">
                          <span className="text-[#6B6E7A] text-[10px] uppercase block">Investigation Report Preview:</span>
                          <pre className="text-[11px] text-[#AEB1BA] whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
                            {selectedInvestigation.report_markdown}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* CONFIRMATION MODAL FOR LIVE RUNS */}
        {showConfirmModal && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            role="dialog"
            aria-modal="true"
          >
            <div className="w-full max-w-md bg-[#0F111A] border border-[#1C1F33] rounded-xl p-6 space-y-4 shadow-2xl">
              <div className="flex items-center gap-2.5 text-white font-semibold">
                <AlertTriangle className="w-5 h-5 text-[#E5484D]" />
                <span>Confirm Live Agent Execution</span>
              </div>
              <p className="text-xs text-[#9296AD] leading-relaxed">
                This triggers an autonomous agent loop making real LLM and ArmorIQ session check calls against the triage issue queue.
                Protected by in-MCP sandboxing and capped to 10 safety sessions.
              </p>
              <div className="flex justify-end gap-3 pt-3">
                <button
                  onClick={() => setShowConfirmModal(false)}
                  className="px-4 py-2 rounded-lg border border-[#1C1F33] text-xs text-white hover:bg-white/5 transition-colors font-mono"
                  data-local="cancel-modal"
                >
                  Cancel
                </button>
                <button
                  onClick={handleStartLiveRun}
                  className="px-4 py-2 rounded-lg bg-[#5B4BFF] hover:bg-[#4E3FE8] text-white font-semibold text-xs font-mono transition-colors"
                  data-local="confirm-live-run"
                >
                  Confirm & Run
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
