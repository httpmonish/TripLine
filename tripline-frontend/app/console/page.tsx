'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Section } from '@/components/ui/Section'
import { SectionHeader } from '@/components/ui/SectionHeader'
import {
  api,
  JobRecord,
  subscribeToJobEvents,
} from '@/lib/api'
import {
  Terminal,
  Shield,
  ArrowRight,
  FileText,
  CheckCircle2,
  AlertOctagon,
  Play,
  RotateCcw,
  RefreshCw,
  Clock,
  Check,
  AlertTriangle,
  StopCircle,
} from 'lucide-react'
import Link from 'next/link'
import { SecurityDecisionCard } from '@/components/security/SecurityDecisionCard'

interface AllowlistedJobMeta {
  kind: string
  title: string
  description: string
  live: boolean
  cost: string
  timeoutSec: number
  sideEffects: string
  requiresConfirm?: boolean
}

const ALLOWLISTED_JOBS: AllowlistedJobMeta[] = [
  {
    kind: 'security_proof',
    title: 'Deterministic Sandbox Security Proof',
    description: 'Executes deterministic sandbox scenarios demonstrating ArmorIQ upstream policy denial, Path Jail containment, or Canary Egress quarantine.',
    live: false,
    cost: '$0.00',
    timeoutSec: 60,
    sideEffects: 'Generates structured scenario execution log and signed HMAC receipts in results/phase3/scenario/.',
  },
  {
    kind: 'jail_burst',
    title: 'Path-Jail Fuzzer Probes',
    description: 'Executes 8 directory traversal probes (dot-dot, hex-decode, symlinks) against the in-MCP jail boundary.',
    live: false,
    cost: '$0.00',
    timeoutSec: 30,
    sideEffects: 'Verifies 0 bytes leaked; returns structured pass/fail verdicts.',
  },
  {
    kind: 'verify_all',
    title: 'Verify All Cryptographic Links',
    description: 'Cryptographically re-computes all incident receipts, witness HMAC hash-chains, and sidecar audit links.',
    live: false,
    cost: '$0.00',
    timeoutSec: 30,
    sideEffects: 'Validates cryptographic non-repudiation back to genesis.',
  },
  {
    kind: 'tamper_demo',
    title: 'Cryptographic Tamper Check',
    description: 'Injects single-byte mutations into temporary copies of receipts and witness logs to demonstrate immediate tamper detection.',
    live: false,
    cost: '$0.00',
    timeoutSec: 30,
    sideEffects: 'Confirms original evidence files remain 100% byte-for-byte untouched.',
  },
  {
    kind: 'rea_investigate',
    title: 'Controlled REA Static Analysis',
    description: 'Invokes persistent REA MCP server to statically analyze synthetic Electron app and extract IPC handler evidence.',
    live: false,
    cost: '$0.00',
    timeoutSec: 90,
    sideEffects: 'Saves investigation report and cryptographic receipt under investigations/.',
  },
  {
    kind: 'scenario',
    title: 'Multi-Layer Scenario (Rung 0)',
    description: 'Executes deterministic offline scenario across benign triage, branch deletion attacks, traversal escapes, and canary hits.',
    live: false,
    cost: '$0.00',
    timeoutSec: 60,
    sideEffects: 'Generates scenario run log and receipts under results/phase3/scenario/.',
  },
  {
    kind: 'audit',
    title: 'Repository Truth & Secret Audit',
    description: 'Scans repository truth claims, forbidden terminology, and secret hygiene.',
    live: false,
    cost: '$0.00',
    timeoutSec: 30,
    sideEffects: 'Verifies repository security posture and zero leaked credentials.',
  },
  {
    kind: 'armoriq_proof',
    title: 'ArmorIQ Platform Proof (Live)',
    description: 'Contacts remote ArmorIQ Intent Authorization Proxy to verify active IAP tokens and policy evaluation.',
    live: true,
    cost: '$0.00 (platform quota)',
    timeoutSec: 30,
    sideEffects: 'Requires ARMORIQ_API_KEY. Checks live control plane connectivity.',
    requiresConfirm: true,
  },
  {
    kind: 'tests',
    title: 'Security & Hygiene Test Suite',
    description: 'Executes test_test_hygiene.py and test_phase4_dashboard.py using local pytest.',
    live: false,
    cost: '$0.00',
    timeoutSec: 60,
    sideEffects: 'Validates core assertions and boundary controls.',
  },
]

export default function ConsolePage() {
  const [jobs, setJobs] = useState<JobRecord[]>([])
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [activeJobDetail, setActiveJobDetail] = useState<JobRecord | null>(null)
  const [liveStreamLines, setLiveStreamLines] = useState<string[]>([])
  const [isStreaming, setIsStreaming] = useState<boolean>(false)
  const [runningJobKind, setRunningJobKind] = useState<string | null>(null)
  const [jobError, setJobError] = useState<string | null>(null)

  const terminalLogsRef = useRef<HTMLDivElement>(null)

  // 1. Fetch job list from backend
  const loadJobs = async () => {
    try {
      const data = await api.listJobs()
      setJobs(data)
      if (data.length > 0 && !selectedJobId) {
        setSelectedJobId(data[0].job_id)
      }
    } catch (err: any) {
      console.error('Failed to list jobs:', err)
    }
  }

  useEffect(() => {
    loadJobs()
  }, [])

  // 2. Load job details when selected
  useEffect(() => {
    if (!selectedJobId) return
    api.getJob(selectedJobId)
      .then((detail) => {
        setActiveJobDetail(detail)
        setLiveStreamLines(detail.output_preview || [])
      })
      .catch((err) => console.error('Failed to get job detail:', err))
  }, [selectedJobId])

  // 3. Scroll terminal container internally
  useEffect(() => {
    if (liveStreamLines.length > 0 && terminalLogsRef.current) {
      terminalLogsRef.current.scrollTop = terminalLogsRef.current.scrollHeight
    }
  }, [liveStreamLines])

  // Start an allowlisted job
  const handleLaunchJob = async (jobMeta: AllowlistedJobMeta) => {
    setRunningJobKind(jobMeta.kind)
    setJobError(null)
    setLiveStreamLines([])
    setIsStreaming(true)

    try {
      const confirmToken = jobMeta.requiresConfirm ? 'CONFIRMED_LIVE_EXECUTION' : undefined
      const newJob = await api.createJob(jobMeta.kind, {}, confirmToken)
      setSelectedJobId(newJob.job_id)
      setActiveJobDetail(newJob)

      // Subscribe to SSE output
      const unsubscribe = subscribeToJobEvents(
        newJob.job_id,
        (ev) => {
          if (ev.line) {
            setLiveStreamLines((prev) => [...prev, ev.line!])
          }
          if (ev.done) {
            setIsStreaming(false)
            setRunningJobKind(null)
            loadJobs()
          }
        },
        (err) => {
          setIsStreaming(false)
          setRunningJobKind(null)
        }
      )
    } catch (err: any) {
      setIsStreaming(false)
      setRunningJobKind(null)
      setJobError(err.message || 'Failed to dispatch job.')
    }
  }

  // Cancel currently running job
  const handleCancelJob = async () => {
    if (!selectedJobId) return
    try {
      await api.cancelJob(selectedJobId)
      setLiveStreamLines((prev) => [...prev, '[CANCELLED] Job terminated by user request.'])
      loadJobs()
    } catch (err: any) {
      setJobError(err.message || 'Failed to cancel job.')
    }
  }

  return (
    <div className="w-full flex flex-col text-[#20252B] bg-[#F4F5F6]">
      <Section tone="light">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <SectionHeader
            eyebrow="// CONTROLLED EXECUTION CONSOLE"
            title="Safe Job Runner & System Console"
            description="Execute allowlisted verification, fuzzing, and investigation jobs in safe sandboxed subprocesses. Real-time SSE streaming derived directly from backend outputs with zero simulated delays."
            tone="light"
          />
          <button
            onClick={loadJobs}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#CDD2D8] bg-[#FFFFFF] hover:bg-[#EAEDF0] text-xs font-mono text-[#59636E] hover:text-[#20252B] transition-colors shrink-0 shadow-sm"
            data-testid="btn-refresh-jobs"
            data-api="GET /api/jobs"
          >
            <RefreshCw className="w-3.5 h-3.5 text-[#65BCE7]" />
            <span>Refresh Jobs</span>
          </button>
        </div>

        {jobError && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-300 text-red-700 font-mono text-xs flex items-center justify-between gap-3 shadow-sm">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{jobError}</span>
            </div>
            <button onClick={() => setJobError(null)} data-local="dismiss-job-error" className="text-red-700 hover:text-red-900 text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        {/* SECTION 1: ALLOWLISTED JOBS RUNNER */}
        <div className="space-y-4 mb-10">
          <div className="flex items-center justify-between font-mono text-xs">
            <span className="text-[#20252B] font-semibold">// ALLOWLISTED SECURE OPERATIONS</span>
            <span className="text-[#747F8D]">Strict Allowlist (dashboard/jobs.py)</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {ALLOWLISTED_JOBS.map((j) => {
              const isRunning = runningJobKind === j.kind
              return (
                <div
                  key={j.kind}
                  className="p-5 rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] hover:border-[#65BCE7] transition-all flex flex-col justify-between space-y-4 shadow-sm"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between font-mono text-[10px]">
                      <span className={`px-2 py-0.5 rounded font-bold ${j.live ? 'bg-red-100 text-red-800 border border-red-200' : 'bg-emerald-100 text-emerald-800 border border-emerald-200'}`}>
                        {j.live ? 'LIVE PLATFORM' : 'OFFLINE SANDBOX'}
                      </span>
                      <span className="text-[#747F8D]">{j.cost}</span>
                    </div>
                    <h3 className="text-sm font-bold text-[#20252B]">{j.title}</h3>
                    <p className="text-xs text-[#59636E] leading-relaxed">{j.description}</p>
                  </div>

                  <div className="space-y-3 pt-3 border-t border-[#CDD2D8] font-mono text-[11px]">
                    <div className="text-[10px] text-[#747F8D]">
                      Side Effects: <span className="text-[#59636E]">{j.sideEffects}</span>
                    </div>

                    <button
                      onClick={() => handleLaunchJob(j)}
                      disabled={isRunning || isStreaming}
                      data-api="POST /api/jobs"
                      className={`w-full py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                        isRunning
                          ? 'bg-[#EAEDF0] text-[#59636E] border border-[#CDD2D8] cursor-wait'
                          : 'bg-[#0284C7] hover:bg-[#0369A1] text-white shadow-sm'
                      }`}
                    >
                      <Play className="w-3.5 h-3.5 text-white" />
                      <span className="text-white">{isRunning ? 'Executing...' : 'Dispatch Operation'}</span>
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* SECTION 2: LIVE JOB MONITOR & TERMINAL */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left: Job History (4 cols) */}
          <div className="lg:col-span-4 rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] p-4 space-y-3 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-[#CDD2D8] font-mono text-xs">
              <span className="text-[#20252B] font-semibold">// JOB AUDIT HISTORY</span>
              <span className="text-[#747F8D]">{jobs.length} Executions</span>
            </div>

            <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
              {jobs.length === 0 ? (
                <div className="py-16 text-center text-xs font-mono text-[#747F8D]">
                  No jobs dispatched in current session. Select an operation above.
                </div>
              ) : (
                jobs.map((job) => {
                  const isSelected = selectedJobId === job.job_id
                  return (
                    <div
                      key={job.job_id}
                      onClick={() => setSelectedJobId(job.job_id)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all font-mono text-xs space-y-1.5 ${
                        isSelected
                          ? 'bg-[#EAEDF0] border-[#65BCE7] ring-1 ring-[#65BCE7]'
                          : 'bg-[#FFFFFF] border-[#CDD2D8] hover:border-[#65BCE7]/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[#20252B] font-bold">{job.job_id}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                          job.status === 'completed'
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                            : job.status === 'running'
                            ? 'bg-blue-100 text-blue-800 border border-blue-200 animate-pulse'
                            : 'bg-red-100 text-red-800 border border-red-200'
                        }`}>
                          {job.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-[#747F8D]">
                        <span>Kind: <strong className="text-[#20252B]">{job.kind}</strong></span>
                        <span>{job.started_at ? new Date(job.started_at).toLocaleTimeString() : 'queued'}</span>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>

          {/* Right: Real-time Terminal Log (8 cols) */}
          <div className="lg:col-span-8 rounded-xl border border-[#CDD2D8] bg-[#FFFFFF] p-5 flex flex-col space-y-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#CDD2D8] font-mono text-xs">
              <div className="flex items-center gap-2 text-[#20252B]">
                <Terminal className="w-4 h-4 text-[#65BCE7]" />
                <span className="font-semibold">
                  // EXECUTION STDOUT: {selectedJobId || 'NONE SELECTED'}
                </span>
              </div>

              <div className="flex items-center gap-3">
                {activeJobDetail?.status === 'running' && (
                  <button
                    onClick={handleCancelJob}
                    data-api="POST /api/jobs/{id}/cancel"
                    className="px-3 py-1 rounded-lg bg-red-100 border border-red-300 text-red-800 hover:bg-red-200 font-semibold flex items-center gap-1 text-[11px] transition-colors"
                  >
                    <StopCircle className="w-3.5 h-3.5 text-red-700" />
                    <span>Cancel Subprocess</span>
                  </button>
                )}
                <span className="text-[#747F8D] text-[11px]">
                  {liveStreamLines.length} Lines Logged
                </span>
              </div>
            </div>

            <div ref={terminalLogsRef} className="h-[460px] overflow-y-auto font-mono text-xs bg-[#181B20] text-[#CDD2D8] p-4 rounded-xl border border-[#2D3136] space-y-1.5 shadow-inner">
              {liveStreamLines.length === 0 ? (
                <div className="py-24 text-center text-[#747F8D] space-y-2">
                  <p>No output recorded for this job.</p>
                  <p className="text-[11px]">Click "Dispatch Operation" above to run an allowlisted security task.</p>
                </div>
              ) : (
                liveStreamLines.map((line, idx) => (
                  <div key={idx} className="leading-relaxed break-all font-mono">
                    {line}
                  </div>
                ))
              )}
            </div>

            {activeJobDetail && (
              <div className="pt-2 border-t border-[#CDD2D8] flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-[#747F8D]">
                <span>Started: <code className="text-[#20252B] font-semibold">{activeJobDetail.started_at || '—'}</code></span>
                <span>Finished: <code className="text-[#20252B] font-semibold">{activeJobDetail.finished_at || '—'}</code></span>
                <span>Exit Code: <code className="text-[#20252B] font-semibold">{activeJobDetail.exit_code ?? 'running'}</code></span>
              </div>
            )}
          </div>
        </div>
      </Section>
    </div>
  )
}
