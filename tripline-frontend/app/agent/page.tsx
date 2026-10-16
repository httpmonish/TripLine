'use client'

import React, { useState, useEffect } from 'react'
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
} from 'lucide-react'

export default function AgentPage() {
  const [crew, setCrew] = useState<any>(null)
  const [runs, setRuns] = useState<any[]>([])
  const [selectedRun, setSelectedRun] = useState<any>(null)
  const [events, setEvents] = useState<any[]>([])
  const [killTriggered, setKillTriggered] = useState(false)

  useEffect(() => {
    fetch('/api/agent/crew')
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setCrew(data)
      })
      .catch(() => {})

    fetch('/api/agent/runs')
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setRuns(data)
          setSelectedRun(data[0])
        }
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedRun?.run_id) return
    const sse = new EventSource(`/api/agent/runs/${selectedRun.run_id}/events`)
    setEvents([])
    sse.onmessage = (e) => {
      try {
        const ev = JSON.parse(e.data)
        setEvents((prev) => [...prev, ev])
      } catch (err) {}
    }
    return () => sse.close()
  }, [selectedRun?.run_id])

  const handleStopRun = async () => {
    if (!selectedRun?.run_id) return
    try {
      const csrfRes = await fetch('/api/csrf-token')
      const csrfData = await csrfRes.json()
      await fetch(`/api/agent/runs/${selectedRun.run_id}/stop`, {
        method: 'POST',
        headers: {
          'x-csrf-token': csrfData.csrf_token,
          origin: window.location.origin,
        },
      })
      setKillTriggered(true)
    } catch (e) {}
  }

  return (
    <div className="w-full flex flex-col text-[#F3F1EA] bg-[#0A0A0C] min-h-screen py-12 px-4 sm:px-6">
      <div className="max-w-[1280px] mx-auto w-full space-y-10">
        {/* Page Header */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2 text-xs font-mono text-[var(--accent)] uppercase tracking-widest">
            <Bot className="w-4 h-4" />
            <span>// GOVERNED AGENT INSPECTION PORTAL</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-semibold text-white">
            Agent Crew, Scoped Delegation & Execution State
          </h1>
          <p className="text-sm text-[var(--text-muted-on-dark)] max-w-3xl leading-relaxed">
            Detailed inspection of the Tripline maintainer orchestrator, scoped sub-agent delegations, in-memory Ed25519 public keys, plan hashes, and live SSE execution events.
          </p>
        </div>

        {/* SECTION 1: CREW & DELEGATION ARCHITECTURE */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Orchestrator */}
          <div className="p-5 rounded border border-[var(--border-dark)] bg-[#121216] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[var(--accent)]/10 text-[var(--accent)] font-semibold">
                  ORCHESTRATOR
                </span>
                <span className="font-mono text-[10px] text-[var(--text-faint-on-dark)]">Parent Token</span>
              </div>
              <h2 className="text-lg font-semibold text-white">
                {crew?.orchestrator?.name || 'tripline-maintainer'}
              </h2>
              <p className="text-xs text-[var(--text-muted-on-dark)] mt-2">
                Owns the parent intent token and coordinates triage queue execution. Never receives delete_branch authority.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[var(--border-dark)] font-mono text-[11px] text-[var(--text-faint-on-dark)]">
              Authority: Parent Intent Token Owner
            </div>
          </div>

          {/* Sub-Agent 1: Reader */}
          <div className="p-5 rounded border border-[var(--border-dark)] bg-[#121216] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#30A46C]/10 text-[#30A46C] font-semibold">
                  SUB-AGENT
                </span>
                <span className="font-mono text-[10px] text-[var(--text-faint-on-dark)]">Scoped Delegate</span>
              </div>
              <h2 className="text-lg font-semibold text-white">reader</h2>
              <p className="text-xs text-[var(--text-muted-on-dark)] mt-2">
                Granted inspection privileges only. Ephemeral Ed25519 keypair generated at run start.
              </p>
              <div className="mt-3 flex flex-wrap gap-1">
                {['list_issues', 'read_issue', 'read_file', 'list_dir'].map((act) => (
                  <span key={act} className="px-1.5 py-0.5 rounded bg-white/5 font-mono text-[10px] text-white">
                    {act}
                  </span>
                ))}
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-[var(--border-dark)] font-mono text-[10px] text-[var(--text-faint-on-dark)] truncate">
              Pubkey: {crew?.sub_agents?.[0]?.public_key_hex || 'b84f93...'}
            </div>
          </div>

          {/* Sub-Agent 2: Responder */}
          <div className="p-5 rounded border border-[var(--border-dark)] bg-[#121216] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#30A46C]/10 text-[#30A46C] font-semibold">
                  SUB-AGENT
                </span>
                <span className="font-mono text-[10px] text-[var(--text-faint-on-dark)]">Scoped Delegate</span>
              </div>
              <h2 className="text-lg font-semibold text-white">responder</h2>
              <p className="text-xs text-[var(--text-muted-on-dark)] mt-2">
                Granted triage response actions only. Disjoint from file reading capabilities.
              </p>
              <div className="mt-3 flex flex-wrap gap-1">
                {['comment_issue', 'label_issue'].map((act) => (
                  <span key={act} className="px-1.5 py-0.5 rounded bg-white/5 font-mono text-[10px] text-white">
                    {act}
                  </span>
                ))}
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-[var(--border-dark)] font-mono text-[10px] text-[var(--text-faint-on-dark)] truncate">
              Pubkey: {crew?.sub_agents?.[1]?.public_key_hex || 'a17c22...'}
            </div>
          </div>
        </div>

        {/* SECTION 2: RUN MANIFEST & ACTIVE STATE */}
        <div className="p-6 rounded border border-[var(--border-dark)] bg-[#101014] space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[var(--border-dark)]">
            <div>
              <span className="font-mono text-xs uppercase text-[var(--text-faint-on-dark)]">// ACTIVE RUN MANIFEST</span>
              <h2 className="text-xl font-semibold text-white mt-1">
                {selectedRun?.run_id || 'run_20261016_122123_0e2179'}
              </h2>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleStopRun}
                className="px-3 py-1.5 rounded border border-[#E5484D] text-[#FF6369] hover:bg-[#E5484D]/10 text-xs font-mono font-semibold"
                data-api="POST /api/agent/runs/{id}/stop"
                data-testid="btn-stop-agent-run"
              >
                Kill Switch (Stop)
              </button>
              {killTriggered && (
                <span className="text-xs font-mono text-[#E5484D]">Kill switch triggered!</span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
            <div className="p-3 rounded bg-[#16161B]">
              <span className="text-[var(--text-faint-on-dark)] block">Model:</span>
              <span className="text-white font-semibold">{selectedRun?.model || 'gemini-3.8-flash'}</span>
            </div>
            <div className="p-3 rounded bg-[#16161B]">
              <span className="text-[var(--text-faint-on-dark)] block">Integration Mode:</span>
              <span className="text-white font-semibold">MODE {selectedRun?.mode || 'B'}</span>
            </div>
            <div className="p-3 rounded bg-[#16161B]">
              <span className="text-[var(--text-faint-on-dark)] block">User Attribution:</span>
              <span className="text-white font-semibold">{selectedRun?.user_email || 'sandbox-maintainer@example.invalid'}</span>
            </div>
            <div className="p-3 rounded bg-[#16161B]">
              <span className="text-[var(--text-faint-on-dark)] block">Signed Receipts:</span>
              <span className="text-[var(--accent)] font-semibold">{selectedRun?.receipts?.length || 3} Receipts</span>
            </div>
          </div>

          <div className="pt-2 font-mono text-xs text-[var(--text-muted-on-dark)] space-y-1">
            <div>
              <span className="text-[var(--text-faint-on-dark)]">Plan Hash: </span>
              <span className="text-white">{selectedRun?.plan_hash || '328fe3910c4f...'}</span>
            </div>
            <div>
              <span className="text-[var(--text-faint-on-dark)]">Merkle Root: </span>
              <span className="text-white">{selectedRun?.merkle_root || 'b78a9c21...'}</span>
            </div>
          </div>
        </div>

        {/* SECTION 3: REAL-TIME EVENT STREAM */}
        <div className="p-6 rounded border border-[var(--border-dark)] bg-[#101014] flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--border-dark)] text-xs font-mono text-[var(--text-faint-on-dark)]">
            <span>// SSE EVENT REPLAY</span>
            <span>{events.length} Events Logged</span>
          </div>
          <div className="mt-4 space-y-2 h-[400px] overflow-y-auto pr-2 font-mono text-xs">
            {events.map((ev, i) => (
              <div key={i} className="p-2.5 rounded bg-[#141419] border border-white/5 flex flex-col gap-1">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="text-[var(--accent)] font-semibold">{ev.event_type}</span>
                  <span className="text-[var(--text-faint-on-dark)]">{ev.source}</span>
                </div>
                <pre className="text-[11px] text-[var(--text-muted-on-dark)] whitespace-pre-wrap overflow-x-auto">
                  {JSON.stringify(ev.data, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
