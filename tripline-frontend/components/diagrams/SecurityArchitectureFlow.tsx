'use client'

import React, { useState } from 'react'
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Lock,
  Layers,
  Terminal,
  KeyRound,
  FileCheck,
  ArrowRight,
  Eye,
  Info,
} from 'lucide-react'

export interface ArchitectureStage {
  id: string
  number: string
  title: string
  subtitle: string
  plane: string
  description: string
  boundaryOwner: 'TripLine Orchestrator' | 'ArmorIQ Platform Gate' | 'TripLine MCP Containment' | 'TripLine Cryptographic Proof'
  enforcementRule: string
  outcomeTypes: {
    label: string
    color: 'allow' | 'deny' | 'hold' | 'not-reached'
    desc: string
  }[]
  icon: React.ComponentType<{ className?: string }>
}

export const ARCHITECTURE_STAGES: ArchitectureStage[] = [
  {
    id: 'stage-1',
    number: '01',
    title: 'Pre-Ingestion Plan Synthesis',
    subtitle: 'Plan & Vocabulary Confinement',
    plane: 'Plane 1: Orchestrator Layer',
    boundaryOwner: 'TripLine Orchestrator',
    description:
      'Before untrusted prompts or issue bodies are ingested, the orchestrator constructs a locked session plan strictly from authorized goals. High-risk administrative tools (e.g. delete_branch) are excluded from the allowed tool vocabulary.',
    enforcementRule: 'Planner lock prevents prompt injection from modifying tool allowlist after ingestion.',
    outcomeTypes: [
      { label: 'Plan Minted', color: 'allow', desc: 'Valid tool set synthesized and hashed before prompt ingestion' },
      { label: 'Replan Locked', color: 'allow', desc: 'Attempts to re-plan after reading untrusted inputs are rejected' },
    ],
    icon: Terminal,
  },
  {
    id: 'stage-2',
    number: '02',
    title: 'Upstream Authorization Gate',
    subtitle: 'ArmorIQ Intent Policy Evaluation',
    plane: 'Plane 2: ArmorIQ IAP Gate',
    boundaryOwner: 'ArmorIQ Platform Gate',
    description:
      'When an agent proposes an action, ArmorIQ evaluates the active session policy and Merkle-linked session plan. If the tool is unpermitted or violates plan scope, ArmorIQ returns DENY upstream. Zero execution occurs in MCP.',
    enforcementRule: 'Action evaluated before tool dispatch. Denied calls fail closed upstream.',
    outcomeTypes: [
      { label: 'ALLOW', color: 'allow', desc: 'Proposed tool matches active plan; dispatched to MCP' },
      { label: 'DENY', color: 'deny', desc: 'Out-of-plan action denied upstream; execution aborted immediately' },
    ],
    icon: KeyRound,
  },
  {
    id: 'stage-3',
    number: '03',
    title: 'TripLine MCP Containment',
    subtitle: 'In-MCP Path Jail & Egress Gateway',
    plane: 'Plane 3: TripLine Containment',
    boundaryOwner: 'TripLine MCP Containment',
    description:
      'Even when ArmorIQ permits a benign tool (read_file, comment_issue), TripLine enforces deep parameter containment: Path Jail traps directory traversal escapes (../../.ssh/id_rsa) and Egress Gateway quarantines canary tokens.',
    enforcementRule: 'Open-then-verify inode checks prevent path traversal. Canary hits quarantine egress.',
    outcomeTypes: [
      { label: 'EXECUTED', color: 'allow', desc: 'Safe parameters inside sandboxed repo; executed cleanly' },
      { label: 'DENIED (JAIL)', color: 'deny', desc: 'Path escapes sandbox root; blocked by fstat inode check' },
      { label: 'HELD (EGRESS)', color: 'hold', desc: 'Outbound comment contains Canary Token; held in quarantine' },
      { label: 'NOT REACHED', color: 'not-reached', desc: 'If ArmorIQ denied upstream, TripLine layer was not reached' },
    ],
    icon: ShieldCheck,
  },
  {
    id: 'stage-4',
    number: '04',
    title: 'Sealed Forensic Evidence',
    subtitle: 'RFC 8785 Canonical JSON & HMAC Witness',
    plane: 'Plane 4: Cryptographic Proof',
    boundaryOwner: 'TripLine Cryptographic Proof',
    description:
      'Every blocked or quarantined action produces an immutable cryptographic receipt containing source provenance, proposal hash, matched policy, and HMAC signature linked to the append-only witness chain.',
    enforcementRule: 'Canonical RFC 8785 JSON SHA-256 + HMAC-SHA256 signature enables offline audit.',
    outcomeTypes: [
      { label: 'SEALED (HMAC)', color: 'allow', desc: 'Receipt written with witness HMAC signature & linked in chain' },
      { label: 'TAMPER EVIDENT', color: 'deny', desc: 'Any 1-byte mutation breaks signature and halts verification' },
    ],
    icon: FileCheck,
  },
]

interface SecurityArchitectureFlowProps {
  currentStageIndex?: number
  lastEventSummary?: {
    stage: number
    toolName?: string
    armoriqDecision?: string
    tripLineDecision?: string
    receiptId?: string
    issueId?: string
    outcome?: string
  } | null
}

export function SecurityArchitectureFlow({
  currentStageIndex = 0,
  lastEventSummary,
}: SecurityArchitectureFlowProps) {
  const [selectedStageId, setSelectedStageId] = useState<string>('stage-2')

  const selectedStage =
    ARCHITECTURE_STAGES.find((s) => s.id === selectedStageId) || ARCHITECTURE_STAGES[1]

  return (
    <div className="w-full space-y-8">
      {/* 4-Stage Horizontal Architecture Diagram */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {ARCHITECTURE_STAGES.map((stage, idx) => {
          const StageIcon = stage.icon
          const isSelected = selectedStageId === stage.id
          const isCurrentInLiveRun = currentStageIndex === idx + 1
          const wasNotReached =
            lastEventSummary?.armoriqDecision === 'DENY' && idx === 2

          return (
            <div
              key={stage.id}
              onClick={() => setSelectedStageId(stage.id)}
              className={`p-5 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'border-[#0D7A73] bg-[#FFFFFF] shadow-md ring-1 ring-[#0D7A73]'
                  : 'border-[#E2DFD6] bg-[#FFFFFF] hover:border-[#C4C0B4] hover:bg-[#FAF8F2]'
              } ${isCurrentInLiveRun ? 'ring-2 ring-[#0D7A73]' : ''}`}
              role="button"
              tabIndex={0}
              data-local={`select-arch-${stage.id}`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-[#F5F3EC] text-[#4D535F]">
                    STAGE {stage.number}
                  </span>
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                      isSelected
                        ? 'bg-[#0D7A73] text-white'
                        : 'bg-[#F5F3EC] text-[#4D535F]'
                    }`}
                  >
                    <StageIcon className="w-4 h-4" />
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-[#191C21] leading-snug">
                    {stage.title}
                  </h3>
                  <span className="text-[11px] font-sans text-[#6E7687] block mt-0.5">
                    {stage.subtitle}
                  </span>
                </div>

                <p className="text-xs text-[#4D535F] line-clamp-3 leading-relaxed">
                  {stage.description}
                </p>
              </div>

              {/* Dynamic Live Status Indicator */}
              <div className="mt-4 pt-3 border-t border-[#EDEAE1] text-[11px] font-sans">
                {wasNotReached ? (
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#F3F4F6] text-[#6E7687] font-mono text-[10px] font-semibold border border-[#E5E7EB]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#959DAE]" />
                    NOT REACHED (BLOCKED UPSTREAM)
                  </span>
                ) : isCurrentInLiveRun ? (
                  <span className="inline-flex items-center gap-1.5 text-[#0D7A73] font-semibold">
                    <span className="w-2 h-2 rounded-full bg-[#0D7A73] animate-pulse" />
                    Active In Current Step
                  </span>
                ) : (
                  <span className="text-[#6E7687]">{stage.plane}</span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Selected Stage Deep-Dive Card */}
      <div className="p-6 sm:p-7 rounded-xl border border-[#E2DFD6] bg-[#FFFFFF] shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[#EDEAE1]">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-[#0D7A73]/10 text-[#0D7A73]">
                STAGE {selectedStage.number} SPECIFICATION
              </span>
              <span className="text-xs text-[#6E7687]">•</span>
              <span className="text-xs font-medium text-[#4D535F]">
                Enforced by: <strong className="text-[#191C21]">{selectedStage.boundaryOwner}</strong>
              </span>
            </div>
            <h3 className="text-xl font-bold text-[#191C21]">
              {selectedStage.title}: {selectedStage.subtitle}
            </h3>
          </div>

          <div className="px-3 py-1.5 rounded-lg bg-[#FAF8F2] border border-[#E2DFD6] text-xs font-mono text-[#4D535F]">
            {selectedStage.plane}
          </div>
        </div>

        {/* Detailed Explanation & Rule */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          <div className="md:col-span-7 space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#6E7687]">
              // Boundary Architecture
            </h4>
            <p className="text-sm text-[#4D535F] leading-relaxed">
              {selectedStage.description}
            </p>
            <div className="p-3 rounded-lg bg-[#F5F3EC] border border-[#E2DFD6] text-xs text-[#4D535F]">
              <strong className="text-[#191C21] block mb-0.5">Enforcement Invariant:</strong>
              {selectedStage.enforcementRule}
            </div>
          </div>

          {/* Authentic Outcome Types for this Stage */}
          <div className="md:col-span-5 space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#6E7687]">
              // Possible Verdicts at this Boundary
            </h4>
            <div className="space-y-2">
              {selectedStage.outcomeTypes.map((out, i) => {
                let badgeClass = 'bg-[#F0FDF4] text-[#16A34A] border-[#BBF7D0]'
                if (out.color === 'deny') {
                  badgeClass = 'bg-[#FEF2F2] text-[#DC2626] border-[#FECACA]'
                } else if (out.color === 'hold') {
                  badgeClass = 'bg-[#FFFBEB] text-[#D97706] border-[#FDE68A]'
                } else if (out.color === 'not-reached') {
                  badgeClass = 'bg-[#F3F4F6] text-[#6E7687] border-[#E5E7EB]'
                }

                return (
                  <div
                    key={i}
                    className="p-2.5 rounded-lg border border-[#EDEAE1] bg-[#FAF8F2] flex flex-col gap-1 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span
                        className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded border ${badgeClass}`}
                      >
                        {out.label}
                      </span>
                    </div>
                    <span className="text-[11px] text-[#4D535F] leading-snug">
                      {out.desc}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
