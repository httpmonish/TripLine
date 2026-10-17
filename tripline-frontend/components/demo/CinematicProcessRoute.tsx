'use client'

import React, { useState } from 'react'
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  Lock,
  ArrowRight,
  CheckCircle2,
  AlertOctagon,
  Radio,
  FileText,
  Clock,
  Terminal,
  Cpu,
  Layers,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Info,
  Check,
  FileCheck,
} from 'lucide-react'

export interface ProcessRouteProps {
  currentStage: number // 1: Ingest, 2: Proposal, 3: ArmorIQ Gate, 4: TripLine Containment, 5: MCP Dispatch, 6: Evidence Verified
  modeLabel:
    | 'LIVE LLM + LIVE AUTHORIZATION'
    | 'LOCAL PROOF'
    | 'RECORDED REPLAY'
    | 'ILLUSTRATIVE WALKTHROUGH'
    | 'AUTHORIZATION UNAVAILABLE'
  taskText: string
  proposedTool: string
  proposedArgs: Record<string, any>
  armoriqDecision: 'ALLOW' | 'DENY' | 'UNAVAILABLE' | 'NONE' | 'PENDING'
  armoriqReason?: string
  armoriqPolicy?: string
  triplineDecision: 'ALLOW' | 'DENY' | 'HOLD' | 'NONE' | 'PENDING'
  triplineControl?: 'Path Jail' | 'Egress Gateway' | 'None'
  triplineReason?: string
  dispatchStatus: 'DISPATCHED' | 'NOT_DISPATCHED' | 'QUARANTINED' | 'PENDING'
  executionResult?: any
  receiptId?: string
  verificationStatus?: 'VERIFIED' | 'INVALID' | 'UNCHECKED' | 'PENDING'
  timelineEvents?: Array<{ stage: string; time: string; label: string; status: string }>
}

export function CinematicProcessRoute({
  currentStage,
  modeLabel,
  taskText,
  proposedTool,
  proposedArgs,
  armoriqDecision,
  armoriqReason,
  armoriqPolicy,
  triplineDecision,
  triplineControl,
  triplineReason,
  dispatchStatus,
  executionResult,
  receiptId,
  verificationStatus = 'UNCHECKED',
  timelineEvents = [],
}: ProcessRouteProps) {
  const [selectedNode, setSelectedNode] = useState<number>(currentStage || 1)

  // Palette: charcoal (#0C0E17), graphite (#141824), steel (#23293D), restrained orange (#EA580C / #F97316)
  // Red for denial (#EF4444), Amber for hold (#F59E0B), Green for genuinely permitted (#10B981)

  // Marker position calculation along the process route (0% to 100%)
  const markerProgress =
    currentStage === 1
      ? 10
      : currentStage === 2
      ? 28
      : currentStage === 3
      ? 48
      : currentStage === 4
      ? 68
      : currentStage === 5
      ? 86
      : 100

  // Decision outcome logic
  const isArmorIQDeny = armoriqDecision === 'DENY'
  const isPathJailDeny = triplineDecision === 'DENY' && triplineControl === 'Path Jail'
  const isEgressHold = triplineDecision === 'HOLD'
  const isDispatched = dispatchStatus === 'DISPATCHED'

  // Human-readable explanations
  const getExplanation = () => {
    if (isArmorIQDeny) {
      return {
        what: `Agent proposed invoking restricted tool '${proposedTool}' to export synthetic volunteer records.`,
        infoUsed: JSON.stringify(proposedArgs),
        policyApplied: armoriqPolicy || 'ArmorIQ Intent Authorization Policy (Volunteer PII Protection)',
        why: armoriqReason || 'Policy explicitly denies exfiltration of volunteer contact details. Action stopped upstream.',
        executionOccurred: false,
        evidenceWritten: receiptId ? `RFC 8785 HMAC Signed Receipt: ${receiptId}` : 'Incident receipt recorded',
      }
    } else if (isPathJailDeny) {
      return {
        what: `Agent proposed invoking '${proposedTool}' with attachment path outside allowed workspace sandbox.`,
        infoUsed: JSON.stringify(proposedArgs),
        policyApplied: 'TripLine In-MCP Path Jail (Boundary Confinement Check)',
        why: triplineReason || 'Target path escapes the sandbox root (path traversal detected). Halted before filesystem read.',
        executionOccurred: false,
        evidenceWritten: receiptId ? `RFC 8785 HMAC Signed Receipt: ${receiptId}` : 'Incident receipt recorded',
      }
    } else if (isEgressHold) {
      return {
        what: `Agent proposed outbound payload containing a seeded canary secret token.`,
        infoUsed: JSON.stringify(proposedArgs),
        policyApplied: 'TripLine Egress Canary Gateway (Data Loss Quarantine)',
        why: triplineReason || 'Outbound content matches active canary signature. Payload quarantined before egress transmission.',
        executionOccurred: false,
        evidenceWritten: receiptId ? `RFC 8785 HMAC Signed Receipt: ${receiptId}` : 'Incident receipt recorded',
      }
    } else if (isDispatched) {
      return {
        what: `Agent proposed safe in-plan tool '${proposedTool}' to inspect or aggregate synthetic records.`,
        infoUsed: JSON.stringify(proposedArgs),
        policyApplied: 'ArmorIQ Triage Policy & TripLine In-MCP Sandbox Boundary',
        why: 'Tool is declared in trusted plan and resolves strictly within sandbox. Dispatched safely to protected MCP.',
        executionOccurred: true,
        evidenceWritten: receiptId ? `Execution Witness Chain Entry: ${receiptId}` : 'Witness hash chain recorded',
      }
    }
    return {
      what: `Task received: "${taskText}". Ready for model reasoning and policy evaluation.`,
      infoUsed: 'User administrator instruction',
      policyApplied: 'TripLine Multi-Layer Governance Architecture',
      why: 'Awaiting execution trigger or event stream.',
      executionOccurred: false,
      evidenceWritten: 'Pending execution',
    }
  }

  const exp = getExplanation()

  return (
    <div className="rounded-2xl border border-[#23293D] bg-[#0C0E17] text-white shadow-2xl overflow-hidden font-sans space-y-0">
      {/* ── Top Bar: Mode Label & Status ── */}
      <div className="bg-[#141824] px-5 py-3.5 border-b border-[#23293D] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5 font-mono text-xs">
            <span className="w-2.5 h-2.5 rounded-full bg-[#EA580C] animate-pulse" />
            <span className="font-bold tracking-wider text-[#F97316]">
              CINEMATIC PROCESS ROUTE
            </span>
          </div>

          <span className="text-[#3F444D]">•</span>

          {/* Authoritative Mode Label */}
          <span
            className={`px-2.5 py-0.5 rounded font-mono text-[10px] font-bold uppercase tracking-wider border ${
              modeLabel === 'LIVE LLM + LIVE AUTHORIZATION'
                ? 'bg-blue-950/80 text-blue-300 border-blue-700/60'
                : modeLabel === 'LOCAL PROOF'
                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60'
                : modeLabel === 'RECORDED REPLAY'
                ? 'bg-purple-950/80 text-purple-300 border-purple-700/60'
                : modeLabel === 'AUTHORIZATION UNAVAILABLE'
                ? 'bg-red-950/80 text-red-300 border-red-700/60'
                : 'bg-gray-800 text-gray-300 border-gray-600'
            }`}
          >
            {modeLabel}
          </span>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs text-[#9EA8B6]">
          <span>
            Stage <strong className="text-white">{currentStage}</strong> of 6
          </span>
          <span className="text-[#3F444D]">•</span>
          <span className="flex items-center gap-1 text-[11px]">
            <Clock className="w-3 h-3 text-[#EA580C]" />
            Synchronized to Backend Events
          </span>
        </div>
      </div>

      {/* ── Central Process Visualizer ── */}
      <div className="p-6 lg:p-8 space-y-8 bg-gradient-to-b from-[#0C0E17] via-[#10131E] to-[#0C0E17]">
        {/* Process Route Pipeline Nodes */}
        <div className="relative">
          {/* Background Connecting Rail */}
          <div className="absolute top-1/2 left-4 right-4 h-1 bg-[#1C2233] -translate-y-1/2 z-0" />

          {/* Active Moving Orange Process Marker */}
          <div
            className="absolute top-1/2 h-1 bg-gradient-to-r from-[#EA580C] to-[#F97316] -translate-y-1/2 transition-all duration-700 ease-out z-0 shadow-[0_0_12px_#EA580C]"
            style={{ width: `${markerProgress}%` }}
          />

          {/* Action Marker Indicator */}
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-20 transition-all duration-700 ease-out flex flex-col items-center pointer-events-none"
            style={{ left: `${markerProgress}%` }}
          >
            <div className="w-4 h-4 rounded-full bg-[#EA580C] border-2 border-white shadow-[0_0_14px_#EA580C] flex items-center justify-center">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
            </div>
            <span className="mt-1 font-mono text-[9px] uppercase font-bold text-[#F97316] bg-[#0C0E17]/90 px-1 rounded border border-[#EA580C]/40">
              Active Focus
            </span>
          </div>

          {/* 5 Milestone Route Stations */}
          <div className="relative z-10 grid grid-cols-2 md:grid-cols-5 gap-3">
            {/* Station 1: Task & AI Proposal */}
            <div
              onClick={() => setSelectedNode(1)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                currentStage >= 1
                  ? 'bg-[#141824] border-[#EA580C]/70 shadow-lg'
                  : 'bg-[#0E101A] border-[#1C2233] opacity-60'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] text-[#9EA8B6] font-bold">01. INGEST & PROPOSE</span>
                <span className="w-2 h-2 rounded-full bg-[#EA580C]" />
              </div>
              <h4 className="font-bold text-sm text-white flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-[#EA580C]" />
                AI Model Loop
              </h4>
              <p className="text-[11px] text-[#9EA8B6] mt-1 font-mono truncate">
                {proposedTool ? `${proposedTool}()` : 'Ingesting prompt'}
              </p>
            </div>

            {/* Station 2: ArmorIQ Authorization Gate */}
            <div
              onClick={() => setSelectedNode(2)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                isArmorIQDeny
                  ? 'bg-red-950/30 border-red-500 shadow-lg ring-1 ring-red-500'
                  : currentStage >= 3
                  ? 'bg-[#141824] border-emerald-500/80 shadow-lg'
                  : 'bg-[#0E101A] border-[#1C2233] opacity-60'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] text-[#9EA8B6] font-bold">02. INTENT GATE</span>
                {isArmorIQDeny ? (
                  <AlertOctagon className="w-3.5 h-3.5 text-red-500" />
                ) : armoriqDecision === 'ALLOW' ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-[#747F8D]" />
                )}
              </div>
              <h4 className="font-bold text-sm text-white flex items-center gap-1.5">
                <Shield className="w-4 h-4 text-[#FBBF24]" />
                ArmorIQ Policy
              </h4>
              <span
                className={`text-[10px] font-mono font-bold mt-1 inline-block px-1.5 py-0.5 rounded ${
                  isArmorIQDeny
                    ? 'bg-red-900/60 text-red-300'
                    : armoriqDecision === 'ALLOW'
                    ? 'bg-emerald-900/60 text-emerald-300'
                    : 'bg-gray-800 text-gray-400'
                }`}
              >
                {armoriqDecision || 'PENDING'}
              </span>
            </div>

            {/* Station 3: TripLine Containment Area */}
            <div
              onClick={() => setSelectedNode(3)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                isPathJailDeny
                  ? 'bg-amber-950/30 border-amber-500 shadow-lg ring-1 ring-amber-500'
                  : isEgressHold
                  ? 'bg-amber-950/30 border-amber-500 shadow-lg ring-1 ring-amber-500'
                  : currentStage >= 4
                  ? 'bg-[#141824] border-emerald-500/80 shadow-lg'
                  : 'bg-[#0E101A] border-[#1C2233] opacity-60'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] text-[#9EA8B6] font-bold">03. CONTAINMENT</span>
                {isPathJailDeny || isEgressHold ? (
                  <Lock className="w-3.5 h-3.5 text-amber-500" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-[#747F8D]" />
                )}
              </div>
              <h4 className="font-bold text-sm text-white flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-[#65BCE7]" />
                TripLine Checks
              </h4>
              <span
                className={`text-[10px] font-mono font-bold mt-1 inline-block px-1.5 py-0.5 rounded ${
                  isPathJailDeny
                    ? 'bg-amber-900/60 text-amber-300'
                    : isEgressHold
                    ? 'bg-amber-900/60 text-amber-300'
                    : triplineDecision === 'ALLOW'
                    ? 'bg-emerald-900/60 text-emerald-300'
                    : 'bg-gray-800 text-gray-400'
                }`}
              >
                {isPathJailDeny ? 'JAIL_DENY' : isEgressHold ? 'EGRESS_HOLD' : triplineDecision || 'PENDING'}
              </span>
            </div>

            {/* Station 4: Protected Tool Dispatch */}
            <div
              onClick={() => setSelectedNode(4)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                isDispatched
                  ? 'bg-emerald-950/30 border-emerald-500 shadow-lg'
                  : currentStage >= 5 && !isDispatched
                  ? 'bg-gray-950 border-gray-800 opacity-60'
                  : 'bg-[#0E101A] border-[#1C2233] opacity-60'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] text-[#9EA8B6] font-bold">04. DISPATCH</span>
                <span
                  className={`w-2 h-2 rounded-full ${
                    isDispatched ? 'bg-emerald-500' : 'bg-red-500'
                  }`}
                />
              </div>
              <h4 className="font-bold text-sm text-white flex items-center gap-1.5">
                <Terminal className="w-4 h-4 text-[#38BDF8]" />
                TripLine MCP
              </h4>
              <span
                className={`text-[10px] font-mono font-bold mt-1 inline-block px-1.5 py-0.5 rounded ${
                  isDispatched
                    ? 'bg-emerald-900/60 text-emerald-300'
                    : 'bg-red-900/40 text-red-300'
                }`}
              >
                {isDispatched ? 'DISPATCHED' : 'NOT REACHED'}
              </span>
            </div>

            {/* Station 5: Evidence & Cryptographic Verification */}
            <div
              onClick={() => setSelectedNode(5)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                receiptId
                  ? 'bg-[#141824] border-[#0284C7] shadow-lg'
                  : 'bg-[#0E101A] border-[#1C2233] opacity-60'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] text-[#9EA8B6] font-bold">05. FORENSIC PROOF</span>
                <FileText className="w-3.5 h-3.5 text-[#0284C7]" />
              </div>
              <h4 className="font-bold text-sm text-white flex items-center gap-1.5">
                <FileCheck className="w-4 h-4 text-emerald-400" />
                Signed Receipt
              </h4>
              <span className="text-[10px] font-mono text-emerald-400 font-bold mt-1 truncate block">
                {receiptId ? `VERIFIED RFC 8785` : 'Pending Evidence'}
              </span>
            </div>
          </div>
        </div>

        {/* ── Human-Readable Decision Narrative & Forensic Inspector ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2 border-t border-[#23293D]">
          {/* Left Column: Human Explanation (Section 2.8) */}
          <div className="lg:col-span-2 space-y-3.5 bg-[#141824] p-5 rounded-xl border border-[#23293D]">
            <div className="flex items-center justify-between border-b border-[#23293D] pb-2.5">
              <span className="text-xs font-mono font-bold uppercase text-[#EA580C] flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5" />
                Plain-Language Decision Explanation (Zero Obfuscation)
              </span>
              <span className="text-[11px] font-mono text-[#9EA8B6]">
                Non-Technical Visitor Summary
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              <div className="space-y-1">
                <span className="text-[#9EA8B6] uppercase text-[10px] block">What the Agent Wanted to Do:</span>
                <p className="text-white font-semibold leading-relaxed font-sans">{exp.what}</p>
              </div>

              <div className="space-y-1">
                <span className="text-[#9EA8B6] uppercase text-[10px] block">Security Policy Applied:</span>
                <p className="text-[#FBBF24] font-semibold leading-relaxed font-sans">{exp.policyApplied}</p>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-[#0C0E17] border border-[#23293D] text-xs font-mono space-y-1">
              <span className="text-[#9EA8B6] uppercase text-[10px] block">Why the Action was Allowed, Denied, or Held:</span>
              <p
                className={`font-semibold leading-relaxed font-sans ${
                  isArmorIQDeny
                    ? 'text-red-400'
                    : isPathJailDeny || isEgressHold
                    ? 'text-amber-400'
                    : 'text-emerald-400'
                }`}
              >
                {exp.why}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono pt-1">
              <div className="flex items-center justify-between p-2.5 rounded bg-[#0C0E17] border border-[#23293D]">
                <span className="text-[#9EA8B6]">Protected MCP Dispatched:</span>
                <span className={`font-bold ${exp.executionOccurred ? 'text-emerald-400' : 'text-red-400'}`}>
                  {exp.executionOccurred ? 'YES (SAFE EXECUTION)' : 'NO (HALTED UPSTREAM)'}
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded bg-[#0C0E17] border border-[#23293D]">
                <span className="text-[#9EA8B6]">Forensic Evidence:</span>
                <span className="font-bold text-[#65BCE7] truncate max-w-[140px]" title={exp.evidenceWritten}>
                  {exp.evidenceWritten}
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Active Step Side Inspector */}
          <div className="space-y-3 bg-[#141824] p-5 rounded-xl border border-[#23293D]">
            <div className="flex items-center justify-between border-b border-[#23293D] pb-2.5">
              <span className="text-xs font-mono font-bold uppercase text-white flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-[#38BDF8]" />
                Event Inspector
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-[#9EA8B6]">
                Authoritative
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="p-2.5 rounded bg-[#0C0E17] border border-[#23293D]">
                <span className="text-[#9EA8B6] text-[10px] uppercase block">Active Tool Proposal</span>
                <code className="text-[#F97316] font-bold block truncate mt-0.5">
                  {proposedTool ? `${proposedTool}()` : 'None proposed'}
                </code>
              </div>

              <div className="p-2.5 rounded bg-[#0C0E17] border border-[#23293D]">
                <span className="text-[#9EA8B6] text-[10px] uppercase block">Sanitized Arguments</span>
                <pre className="text-[11px] text-[#D1D5DB] overflow-x-auto mt-0.5 font-mono">
                  {JSON.stringify(proposedArgs, null, 2)}
                </pre>
              </div>

              {receiptId && (
                <div className="p-2.5 rounded bg-emerald-950/30 border border-emerald-800/60 text-emerald-300">
                  <span className="text-[10px] uppercase block text-emerald-400 font-bold">HMAC Signed Receipt</span>
                  <span className="font-bold block truncate mt-0.5">{receiptId}</span>
                  <span className="text-[10px] text-emerald-400 block mt-1">Verified Offline RFC 8785 SHA-256</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Compact Event Timeline Along Bottom ── */}
        <div className="space-y-2 pt-2 border-t border-[#23293D]">
          <div className="flex items-center justify-between text-xs font-mono text-[#9EA8B6]">
            <span className="uppercase font-semibold flex items-center gap-1.5 text-white">
              <Clock className="w-3.5 h-3.5 text-[#EA580C]" />
              Sequential Event Timeline
            </span>
            <span className="text-[11px]">Strict State-Synchronized Log</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 text-xs font-mono">
            {timelineEvents && timelineEvents.length > 0 ? (
              timelineEvents.slice(-6).map((ev, i) => (
                <div
                  key={i}
                  className="p-2.5 rounded-lg bg-[#141824] border border-[#23293D] flex flex-col justify-between"
                >
                  <span className="text-[10px] text-[#9EA8B6]">{ev.time || 'now'}</span>
                  <span className="font-bold text-white truncate my-0.5">{ev.label}</span>
                  <span
                    className={`text-[10px] font-bold ${
                      ev.status === 'ALLOWED' || ev.status === 'EXECUTED'
                        ? 'text-emerald-400'
                        : ev.status === 'DENIED' || ev.status === 'DENIED-ARMORIQ'
                        ? 'text-red-400'
                        : 'text-amber-400'
                    }`}
                  >
                    {ev.status}
                  </span>
                </div>
              ))
            ) : (
              <div className="col-span-full p-3 rounded-lg bg-[#141824] border border-[#23293D] text-[#9EA8B6] text-center">
                Events will appear in real time as the agent proposes tools and evaluations occur.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
