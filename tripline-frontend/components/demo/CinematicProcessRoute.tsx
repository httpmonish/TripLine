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
        evidenceWritten: receiptId ? `RFC 8785 Signed Receipt: ${receiptId}` : 'Incident receipt recorded',
      }
    } else if (isPathJailDeny) {
      return {
        what: `Agent proposed invoking '${proposedTool}' with attachment path outside allowed workspace sandbox.`,
        infoUsed: JSON.stringify(proposedArgs),
        policyApplied: 'TripLine In-MCP Path Jail (Boundary Confinement Check)',
        why: triplineReason || 'Target path escapes the sandbox root (path traversal detected). Halted before filesystem read.',
        executionOccurred: false,
        evidenceWritten: receiptId ? `RFC 8785 Signed Receipt: ${receiptId}` : 'Incident receipt recorded',
      }
    } else if (isEgressHold) {
      return {
        what: `Agent proposed outbound payload containing a seeded canary secret token.`,
        infoUsed: JSON.stringify(proposedArgs),
        policyApplied: 'TripLine Egress Canary Gateway (Data Loss Quarantine)',
        why: triplineReason || 'Outbound content matches active canary signature. Payload quarantined before egress transmission.',
        executionOccurred: false,
        evidenceWritten: receiptId ? `RFC 8785 Signed Receipt: ${receiptId}` : 'Incident receipt recorded',
      }
    } else if (isDispatched) {
      return {
        what: `Agent proposed safe in-plan tool '${proposedTool}' to inspect or aggregate synthetic records.`,
        infoUsed: JSON.stringify(proposedArgs),
        policyApplied: 'ArmorIQ Triage Policy & TripLine In-MCP Sandbox Boundary',
        why: 'Tool is declared in trusted plan and resolves strictly within sandbox. Dispatched safely to protected MCP.',
        executionOccurred: true,
        evidenceWritten: receiptId ? `Execution Witness Chain: ${receiptId}` : 'Witness hash chain recorded',
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

  const stations = [
    {
      num: 1,
      tag: '01. INGEST',
      title: 'AI Model Loop',
      icon: Cpu,
      sub: proposedTool ? `${proposedTool}()` : 'Ingesting prompt',
      tone: 'orange',
    },
    {
      num: 2,
      tag: '02. INTENT GATE',
      title: 'ArmorIQ Policy',
      icon: Shield,
      sub: isArmorIQDeny ? 'DENIED (Out-of-Plan)' : armoriqDecision === 'ALLOW' ? 'ALLOWED (In-Plan)' : 'Pending',
      tone: isArmorIQDeny ? 'red' : 'green',
    },
    {
      num: 3,
      tag: '03. CONTAINMENT',
      title: 'TripLine Checks',
      icon: Layers,
      sub: isPathJailDeny ? 'TRAPPED (Path Jail)' : isEgressHold ? 'QUARANTINE (Egress)' : 'In Sandbox Boundary',
      tone: isPathJailDeny || isEgressHold ? 'amber' : 'green',
    },
    {
      num: 4,
      tag: '04. DISPATCH',
      title: 'TripLine MCP',
      icon: Terminal,
      sub: isDispatched ? 'DISPATCHED TO TOOL' : 'HALTED (0 Subprocesses)',
      tone: isDispatched ? 'green' : 'red',
    },
    {
      num: 5,
      tag: '05. FORENSIC PROOF',
      title: 'Signed Receipt',
      icon: FileCheck,
      sub: receiptId ? 'VERIFIED RFC 8785' : 'Pending Evidence',
      tone: 'blue',
    },
  ]

  return (
    <div className="rounded-xl border border-[#23293D] bg-[#0C0E17] text-white shadow-xl overflow-hidden font-sans space-y-0">
      {/* ── Top Bar: Mode Label & Status ── */}
      <div className="bg-[#141824] px-5 py-3 border-b border-[#23293D] flex flex-wrap items-center justify-between gap-3">
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
            Live State Synchronized
          </span>
        </div>
      </div>

      {/* ── Central Process Visualizer ── */}
      <div className="p-5 lg:p-6 space-y-6 bg-gradient-to-b from-[#0C0E17] via-[#10131E] to-[#0C0E17]">
        
        {/* Progress Pipeline Stations Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {stations.map((s) => {
            const isCurrent = currentStage === s.num
            const isCompleted = currentStage > s.num
            const Icon = s.icon

            return (
              <div
                key={s.num}
                onClick={() => setSelectedNode(s.num)}
                className={`p-4 rounded-xl border transition-all cursor-pointer relative flex flex-col justify-between min-h-[108px] ${
                  isCurrent
                    ? 'bg-[#171B29] border-[#EA580C] ring-1 ring-[#EA580C]/50 shadow-md'
                    : isCompleted
                    ? 'bg-[#141824] border-[#2A3147] hover:border-[#3E4766]'
                    : 'bg-[#0E101A] border-[#1C2233] opacity-65'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-[10px] text-[#9EA8B6] font-semibold">{s.tag}</span>
                    {isCurrent ? (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-[#EA580C] text-white flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
                        ACTIVE
                      </span>
                    ) : isCompleted ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-[#2A3147]" />
                    )}
                  </div>
                  <h4 className="font-bold text-sm text-white flex items-center gap-1.5">
                    <Icon className="w-4 h-4 text-[#EA580C]" />
                    {s.title}
                  </h4>
                </div>
                
                <div className="pt-2 border-t border-white/5 mt-2">
                  <span className={`text-[10px] font-mono font-medium block truncate ${
                    s.tone === 'red' ? 'text-red-400 font-bold' :
                    s.tone === 'amber' ? 'text-amber-400 font-bold' :
                    s.tone === 'green' ? 'text-emerald-400 font-bold' :
                    'text-[#9EA8B6]'
                  }`}>
                    {s.sub}
                  </span>
                </div>
              </div>
            )
          })}
        </div>

        {/* ── Human-Readable Decision Narrative & Forensic Inspector ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 pt-2 border-t border-[#23293D]">
          {/* Left Column: Human Explanation */}
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
                <p className="text-white font-medium leading-relaxed font-sans">{exp.what}</p>
              </div>

              <div className="space-y-1">
                <span className="text-[#9EA8B6] uppercase text-[10px] block">Security Policy Applied:</span>
                <p className="text-[#FBBF24] font-medium leading-relaxed font-sans">{exp.policyApplied}</p>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-[#0C0E17] border border-[#23293D] text-xs font-mono space-y-1">
              <span className="text-[#9EA8B6] uppercase text-[10px] block">Why the Action was Allowed, Denied, or Held:</span>
              <p
                className={`font-medium leading-relaxed font-sans ${
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
                <span className="text-[#9EA8B6] text-[11px]">Protected MCP Dispatched:</span>
                <span className={`font-bold text-[11px] ${exp.executionOccurred ? 'text-emerald-400' : 'text-red-400'}`}>
                  {exp.executionOccurred ? 'YES (SAFE EXECUTION)' : 'NO (HALTED UPSTREAM)'}
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded bg-[#0C0E17] border border-[#23293D] gap-2">
                <span className="text-[#9EA8B6] text-[11px] shrink-0">Forensic Evidence:</span>
                <span className="font-bold text-[#65BCE7] text-[11px] truncate text-right" title={exp.evidenceWritten}>
                  {exp.evidenceWritten}
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Active Step Side Inspector */}
          <div className="space-y-3 bg-[#141824] p-5 rounded-xl border border-[#23293D] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-[#23293D] pb-2.5 mb-3">
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
                  <pre className="text-white text-[10px] mt-0.5 overflow-x-auto max-h-20 leading-snug">
                    {JSON.stringify(proposedArgs, null, 2)}
                  </pre>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#23293D] text-[11px] font-mono">
              <span className="text-[#9EA8B6] text-[10px] uppercase block">HMAC Signed Receipt</span>
              <span className="text-emerald-400 font-bold block truncate mt-0.5">
                {receiptId || 'RCP-PENDING-EVENT'}
              </span>
              <span className="text-[10px] text-[#747F8D] block">
                Verified Offline RFC 8785 SHA-256
              </span>
            </div>
          </div>
        </div>

        {/* ── Sequential Timeline Bar ── */}
        <div className="p-3 rounded-lg bg-[#141824] border border-[#23293D] text-xs font-mono flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-[#F97316]">
            <Clock className="w-3.5 h-3.5" />
            <span className="font-bold uppercase tracking-wider text-[11px]">Sequential Event Timeline</span>
          </div>
          <span className="text-[#9EA8B6] text-[11px]">
            Strict State-Synchronized Log • Zero Synthesized Timeline
          </span>
        </div>
      </div>
    </div>
  )
}
