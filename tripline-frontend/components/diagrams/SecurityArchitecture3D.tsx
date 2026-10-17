'use client'

import React, { useState, useEffect } from 'react'
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Lock,
  Layers,
  FileCode2,
  Terminal,
  Cpu,
  KeyRound,
  FileCheck,
  Play,
  RotateCcw,
  Info,
} from 'lucide-react'

export interface ArchitectureNode {
  id: string
  label: string
  subtitle: string
  plane: string
  planeNumber: number
  description: string
  securityFunction: string
  inboundData: string
  decision: string
  outboundResult: string
  icon: React.ComponentType<{ className?: string }>
}

export const ARCHITECTURE_NODES: ArchitectureNode[] = [
  {
    id: 'request',
    label: '1. Inbound Request',
    subtitle: 'External Untrusted Ingress',
    plane: 'Plane 1: External',
    planeNumber: 1,
    description: 'Receives external issues or user prompts from GitHub, webhooks, or API clients. Untrusted text may contain hidden prompt injection attacks.',
    securityFunction: 'Untrusted input ingestion without granting immediate tool execution rights.',
    inboundData: 'Issue body, PR comments, user prompts (e.g. "Fix bug #42" or hidden prompt payload).',
    decision: 'Queued for pre-ingestion plan analysis.',
    outboundResult: 'Forwarded to Orchestrator with untrusted status flag.',
    icon: Terminal,
  },
  {
    id: 'orchestrator',
    label: '2. Orchestrator & Crew',
    subtitle: 'Pre-Ingestion Plan Synthesis',
    plane: 'Plane 1: Agent Layer',
    planeNumber: 1,
    description: 'The tripline-maintainer orchestrator and scoped sub-agents (reader and responder) synthesize a structured execution plan before ingesting untrusted prompt bodies.',
    securityFunction: 'Strict separation of administrative goals from untrusted input text; tool capability scoping.',
    inboundData: 'Administrator goals + untrusted issue description.',
    decision: 'Pre-synthesizes plan with permitted tool vocabularies; binds reader and responder roles.',
    outboundResult: 'Proposed tool calls with cryptographic plan Merkle hash.',
    icon: Cpu,
  },
  {
    id: 'rea',
    label: '3. REA Action Planning',
    subtitle: 'Deterministic Intent Model',
    plane: 'Plane 1: Planning Engine',
    planeNumber: 1,
    description: 'Reasoning-Execution-Action (REA) engine compiles proposed actions into deterministic intent structures before touching live system resources.',
    securityFunction: 'Prevents arbitrary runtime drift; validates tool invocation schema and parameter constraints.',
    inboundData: 'Raw agent reasoning trace and target resource descriptors.',
    decision: 'Compiles concrete action proposals and parameters for upstream policy checking.',
    outboundResult: 'Structured action request dispatched to the ArmorIQ authorization boundary.',
    icon: FileCode2,
  },
  {
    id: 'armoriq',
    label: '4. ArmorIQ Policy Gate',
    subtitle: 'Upstream Authorization Boundary',
    plane: 'Plane 2: ArmorIQ IAP',
    planeNumber: 2,
    description: 'The ArmorIQ Intent Authorization Proxy (IAP) verifies the active session plan binding and evaluates security policies. Disallowed tools are blocked upstream.',
    securityFunction: 'Fail-closed intent authorization. Out-of-plan tools (e.g. delete_branch) are halted before any execution.',
    inboundData: 'Proposed action name, session intent token, user attribution identity.',
    decision: 'ALLOW (if tool in registered plan allowlist) or DENY (if out-of-plan or policy violation).',
    outboundResult: 'Signed authorization token if approved, or immediate upstream DENY verdict.',
    icon: KeyRound,
  },
  {
    id: 'mcp_jail',
    label: '5. TripLine MCP Boundary',
    subtitle: 'In-MCP Containment & Egress',
    plane: 'Plane 3: TripLine Containment',
    planeNumber: 3,
    description: 'Even when ArmorIQ permits a benign tool like read_file or comment_issue, TripLine enforces in-MCP parameter checks: Path Jail canonicalization and Outbound Egress Canary Gateway.',
    securityFunction: 'Traps path traversal (../../.ssh/id_rsa), percent-encoding bypasses, symlink escapes, and canary token exfiltration.',
    inboundData: 'Authorized tool parameters and runtime data payloads.',
    decision: 'ALLOW (sandbox path verified) or DENY (path traversal) or HOLD (egress canary detected).',
    outboundResult: 'Safe execution grant or in-MCP interception receipt.',
    icon: ShieldCheck,
  },
  {
    id: 'tool_exec',
    label: '6. Tool Execution',
    subtitle: 'Isolated Sandbox Execution',
    plane: 'Plane 3: Execution Layer',
    planeNumber: 3,
    description: 'Authorized tools execute exclusively within sandboxed fixture repositories. Read operations are restricted to permitted files; write operations post sanitized comments.',
    securityFunction: 'Zero access to host filesystem, production repositories, or sensitive credentials.',
    inboundData: 'Validated path and sanitized message parameters.',
    decision: 'Executed strictly if all upstream authorization and containment layers passed.',
    outboundResult: 'Tool output and execution metadata captured for evidence.',
    icon: Layers,
  },
  {
    id: 'evidence',
    label: '7. Witness & Receipts',
    subtitle: 'Cryptographic Audit Proof',
    plane: 'Plane 4: Cryptographic Evidence',
    planeNumber: 4,
    description: 'Every security event — especially denials and holds — produces a canonical JSON incident receipt cryptographically linked to the append-only HMAC-SHA256 witness hash chain.',
    securityFunction: 'Non-repudiation and offline verifiability. Anyone can re-verify signatures or detect single-byte tampering.',
    inboundData: 'Event trace, policy rule ID, parameter hash, timestamp, previous witness chain hash.',
    decision: 'Cryptographic receipt signed and appended to immutable audit log.',
    outboundResult: 'Public receipt ID (e.g. RCP-call-902) verifiable in-browser.',
    icon: FileCheck,
  },
]

export type ScenarioId = 'S1' | 'S2' | 'S3' | 'S4'

interface ScenarioConfig {
  id: ScenarioId
  name: string
  shortLabel: string
  badge: string
  action: string
  attackVector: string
  armoriqVerdict: 'DENIED' | 'ALLOWED'
  mcpVerdict: 'BYPASSED' | 'DENIED' | 'HELD' | 'PASSED'
  finalOutcome: 'BLOCKED_ARMORIQ' | 'BLOCKED_JAIL' | 'QUARANTINED_EGRESS' | 'EXECUTED_SAFE'
  outcomeText: string
  receiptId: string
  activeNodeIds: string[]
  stoppedAtNodeId: string
}

export const SCENARIOS: Record<ScenarioId, ScenarioConfig> = {
  S1: {
    id: 'S1',
    name: 'Scenario 1: Out-of-Plan Destructive Tool (delete_branch)',
    shortLabel: 'S1: delete_branch',
    badge: 'ArmorIQ Policy Block',
    action: 'delete_branch("experiment/candidate")',
    attackVector: 'Hidden prompt injection inside issue body instructs agent to delete repository branch.',
    armoriqVerdict: 'DENIED',
    mcpVerdict: 'BYPASSED',
    finalOutcome: 'BLOCKED_ARMORIQ',
    outcomeText: 'Halted Upstream: ArmorIQ policy evaluated delete_branch as out-of-plan. Action never reached MCP.',
    receiptId: 'RCP-P1-ARMORIQ-DENY-7a89f',
    activeNodeIds: ['request', 'orchestrator', 'rea', 'armoriq', 'evidence'],
    stoppedAtNodeId: 'armoriq',
  },
  S2: {
    id: 'S2',
    name: 'Scenario 2: Path Traversal Attack (../../.ssh/id_rsa)',
    shortLabel: 'S2: Path Jail Traversal',
    badge: 'TripLine Jail Trap',
    action: 'read_file("../../fake_home/.ssh/id_rsa")',
    attackVector: 'Agent hijacked to exfiltrate private SSH keys via permitted read_file tool with relative traversal.',
    armoriqVerdict: 'ALLOWED',
    mcpVerdict: 'DENIED',
    finalOutcome: 'BLOCKED_JAIL',
    outcomeText: 'Trapped by TripLine: In-MCP Path Jail detected directory boundary escape and inode anomaly. Access blocked.',
    receiptId: 'RCP-P2-JAIL-DENIED-e14a2',
    activeNodeIds: ['request', 'orchestrator', 'rea', 'armoriq', 'mcp_jail', 'evidence'],
    stoppedAtNodeId: 'mcp_jail',
  },
  S3: {
    id: 'S3',
    name: 'Scenario 3: Egress Canary Exfiltration (Canary Token Leak)',
    shortLabel: 'S3: Egress Canary Leak',
    badge: 'TripLine Egress Quarantine',
    action: 'comment_issue("Found token: canary-trip-sec-8820")',
    attackVector: 'Prompt injection coerces agent to leak detected canary credentials via public issue comment.',
    armoriqVerdict: 'ALLOWED',
    mcpVerdict: 'HELD',
    finalOutcome: 'QUARANTINED_EGRESS',
    outcomeText: 'Quarantined: Outbound Egress Gateway matched active canary token pattern and halted outbound dispatch.',
    receiptId: 'RCP-P3-EGRESS-HELD-99b34',
    activeNodeIds: ['request', 'orchestrator', 'rea', 'armoriq', 'mcp_jail', 'evidence'],
    stoppedAtNodeId: 'mcp_jail',
  },
  S4: {
    id: 'S4',
    name: 'Scenario 4: Authorized Triage (Safe Repository Read)',
    shortLabel: 'S4: Authorized Read',
    badge: 'Safe Execution Verified',
    action: 'read_file("src/app/index.ts")',
    attackVector: 'Benign user issue requesting assistance analyzing repository entry point.',
    armoriqVerdict: 'ALLOWED',
    mcpVerdict: 'PASSED',
    finalOutcome: 'EXECUTED_SAFE',
    outcomeText: 'Authorized & Safe: ArmorIQ confirmed policy approval; TripLine validated sandbox boundaries. Executed cleanly.',
    receiptId: 'RCP-BENIGN-EXEC-110cd',
    activeNodeIds: ['request', 'orchestrator', 'rea', 'armoriq', 'mcp_jail', 'tool_exec', 'evidence'],
    stoppedAtNodeId: 'tool_exec',
  },
}

export function SecurityArchitecture3D() {
  const [activeScenario, setActiveScenario] = useState<ScenarioId>('S1')
  const [selectedNodeId, setSelectedNodeId] = useState<string>('armoriq')
  const [isSimulating, setIsSimulating] = useState<boolean>(false)
  const [simulationStep, setSimulationStep] = useState<number>(3)

  const scenario = SCENARIOS[activeScenario]
  const selectedNode = ARCHITECTURE_NODES.find((n) => n.id === selectedNodeId) || ARCHITECTURE_NODES[3]

  // Play animation through active nodes when scenario changes
  useEffect(() => {
    setIsSimulating(true)
    setSimulationStep(0)

    const timer1 = setTimeout(() => setSimulationStep(1), 300)
    const timer2 = setTimeout(() => setSimulationStep(2), 700)
    const timer3 = setTimeout(() => setSimulationStep(3), 1100)
    const timer4 = setTimeout(() => setSimulationStep(4), 1600)
    const timer5 = setTimeout(() => setIsSimulating(false), 2200)

    return () => {
      clearTimeout(timer1)
      clearTimeout(timer2)
      clearTimeout(timer3)
      clearTimeout(timer4)
      clearTimeout(timer5)
    }
  }, [activeScenario])

  return (
    <div className="w-full bg-[#0D0E12] border border-[#1C1F33] rounded-xl overflow-hidden shadow-2xl">
      {/* Header bar with Scenario Switcher */}
      <div className="p-4 sm:p-6 bg-[#111319] border-b border-[#1C1F33] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-[#5B4BFF] animate-pulse" />
            <span className="font-mono text-xs uppercase tracking-widest text-[#9A8CFF]">
              Interactive Governed Flow
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-white/5 border border-white/10 font-mono text-[#AEB1BA]">
              4 Defense Planes
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            How TripLine Governs Every Action
          </h3>
          <p className="text-xs sm:text-sm text-[#9296AD] mt-1 max-w-2xl">
            Select a scenario to trace how untrusted prompts travel from ingress through REA planning, ArmorIQ policy evaluation, in-MCP containment, and cryptographic sealing.
          </p>
        </div>

        {/* Scenario Pill Selectors */}
        <div className="flex flex-wrap items-center gap-1.5 p-1 bg-[#090A14] border border-[#1C1F33] rounded-lg">
          {(Object.keys(SCENARIOS) as ScenarioId[]).map((sid) => {
            const sc = SCENARIOS[sid]
            const isSelected = activeScenario === sid
            return (
              <button
                key={sid}
                onClick={() => {
                  setActiveScenario(sid)
                  setSelectedNodeId(sc.stoppedAtNodeId)
                }}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
                  isSelected
                    ? 'bg-[#5B4BFF] text-white shadow-md'
                    : 'text-[#9296AD] hover:text-white hover:bg-white/5'
                }`}
                data-testid={`btn-scenario-${sid.toLowerCase()}`}
              >
                {sc.shortLabel}
              </button>
            )
          })}
        </div>
      </div>

      {/* Active Scenario Banner */}
      <div className="px-4 sm:px-6 py-3 bg-[#131622] border-b border-[#1C1F33] flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-2.5">
          <span className="px-2 py-0.5 rounded bg-[#5B4BFF]/20 border border-[#5B4BFF]/40 text-[#9A8CFF] font-semibold">
            {scenario.badge}
          </span>
          <span className="text-[#AEB1BA]">Target Action:</span>
          <code className="text-white px-2 py-0.5 rounded bg-black/40 border border-white/10">
            {scenario.action}
          </code>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[#9296AD] hidden sm:inline">{scenario.attackVector}</span>
          <button
            onClick={() => {
              setIsSimulating(true)
              setSimulationStep(0)
              setTimeout(() => setSimulationStep(1), 300)
              setTimeout(() => setSimulationStep(2), 700)
              setTimeout(() => setSimulationStep(3), 1100)
              setTimeout(() => setIsSimulating(false), 1800)
            }}
            className="flex items-center gap-1.5 text-[#9A8CFF] hover:text-white underline cursor-pointer shrink-0"
            title="Replay Execution Path"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Replay Flow</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Interactive Diagram + Selected Node Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[#1C1F33]">
        {/* Left Column: Flow Diagram Nodes */}
        <div className="lg:col-span-7 p-4 sm:p-6 bg-[#0B0C10] flex flex-col justify-between">
          <div className="space-y-3">
            {ARCHITECTURE_NODES.map((node, index) => {
              const isSelected = selectedNodeId === node.id
              const isStoppedHere = scenario.stoppedAtNodeId === node.id
              const isActiveInScenario = scenario.activeNodeIds.includes(node.id)

              // Determine state badge & colors
              let statusBadge = 'PASSING'
              let statusColor = 'text-[#30A46C] bg-[#30A46C]/10 border-[#30A46C]/30'
              let statusIcon = CheckCircle2

              if (isStoppedHere) {
                if (scenario.finalOutcome === 'BLOCKED_ARMORIQ' || scenario.finalOutcome === 'BLOCKED_JAIL') {
                  statusBadge = 'DENIED'
                  statusColor = 'text-[#FF6369] bg-[#E5484D]/15 border-[#E5484D]/40'
                  statusIcon = XCircle
                } else if (scenario.finalOutcome === 'QUARANTINED_EGRESS') {
                  statusBadge = 'HELD / QUARANTINED'
                  statusColor = 'text-[#F5A524] bg-[#F5A524]/15 border-[#F5A524]/40'
                  statusIcon = AlertTriangle
                } else {
                  statusBadge = 'EXECUTED'
                  statusColor = 'text-[#30A46C] bg-[#30A46C]/15 border-[#30A46C]/40'
                  statusIcon = CheckCircle2
                }
              } else if (!isActiveInScenario) {
                statusBadge = 'SKIPPED (Bypassed by denial)'
                statusColor = 'text-[#6B6E7A] bg-white/5 border-white/10'
                statusIcon = Clock
              }

              const NodeIcon = node.icon
              const StatusIcon = statusIcon

              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNodeId(node.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      setSelectedNodeId(node.id)
                    }
                  }}
                  tabIndex={0}
                  role="button"
                  aria-pressed={isSelected}
                  className={`group relative p-3.5 rounded-lg border cursor-pointer transition-all focus:outline-none focus:ring-2 focus:ring-[#5B4BFF] ${
                    isSelected
                      ? 'border-[#5B4BFF] bg-[#141628] shadow-lg shadow-[#5B4BFF]/10'
                      : isStoppedHere
                      ? 'border-[#E5484D]/50 bg-[#161215]'
                      : 'border-[#1C1F33] bg-[#10121A] hover:border-[#2C314E] hover:bg-[#121522]'
                  }`}
                  data-testid={`arch-node-${node.id}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 border ${
                          isSelected
                            ? 'bg-[#5B4BFF] text-white border-[#5B4BFF]'
                            : isStoppedHere && scenario.finalOutcome !== 'EXECUTED_SAFE'
                            ? 'bg-[#E5484D]/20 text-[#FF6369] border-[#E5484D]/40'
                            : 'bg-white/5 text-[#AEB1BA] border-white/10 group-hover:text-white'
                        }`}
                      >
                        <NodeIcon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm text-white group-hover:text-[#9A8CFF] transition-colors">
                            {node.label}
                          </span>
                          <span className="text-[10px] font-mono text-[#6B6E7A]">
                            [{node.plane}]
                          </span>
                        </div>
                        <p className="text-xs text-[#9296AD] line-clamp-1 mt-0.5">
                          {node.subtitle}
                        </p>
                      </div>
                    </div>

                    {/* Status Pill */}
                    <div className="flex items-center gap-2">
                      <span
                        className={`hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-mono font-medium border ${statusColor}`}
                      >
                        <StatusIcon className="w-3.5 h-3.5" />
                        <span>{statusBadge}</span>
                      </span>
                      <ArrowRight
                        className={`w-4 h-4 transition-transform ${
                          isSelected ? 'text-[#5B4BFF] translate-x-1' : 'text-[#6B6E7A] opacity-40'
                        }`}
                      />
                    </div>
                  </div>

                  {/* Flow Direction Indicator */}
                  {index < ARCHITECTURE_NODES.length - 1 && (
                    <div className="absolute -bottom-3 left-7 w-0.5 h-3 bg-[#1C1F33] z-10" />
                  )}
                </div>
              )
            })}
          </div>

          {/* Color Legend at bottom of left column */}
          <div className="mt-6 pt-4 border-t border-[#1C1F33] flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
            <span className="text-[#6B6E7A]">Status Legend:</span>
            <div className="flex flex-wrap items-center gap-4">
              <span className="flex items-center gap-1.5 text-[#30A46C]">
                <span className="w-2 h-2 rounded-full bg-[#30A46C]" />
                Authorized / Permitted
              </span>
              <span className="flex items-center gap-1.5 text-[#FF6369]">
                <span className="w-2 h-2 rounded-full bg-[#E5484D]" />
                Denied / Blocked
              </span>
              <span className="flex items-center gap-1.5 text-[#F5A524]">
                <span className="w-2 h-2 rounded-full bg-[#F5A524]" />
                Held / Quarantined
              </span>
              <span className="flex items-center gap-1.5 text-[#6B6E7A]">
                <span className="w-2 h-2 rounded-full bg-[#6B6E7A]" />
                Bypassed / Skipped
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Node Inspector & Cryptographic Decision Panel */}
        <div className="lg:col-span-5 p-5 sm:p-6 bg-[#0E1017] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#1C1F33]">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs uppercase tracking-wider text-[#9A8CFF]">
                  // NODE INSPECTOR
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-[#AEB1BA]">
                  {selectedNode.plane}
                </span>
              </div>
              <span className="text-xs font-mono text-[#6B6E7A]">
                Layer {ARCHITECTURE_NODES.findIndex((n) => n.id === selectedNode.id) + 1} of 7
              </span>
            </div>

            {/* Selected Node Details */}
            <div className="mt-4 space-y-4">
              <div>
                <h4 className="text-lg font-bold text-white tracking-tight">
                  {selectedNode.label}
                </h4>
                <p className="text-xs text-[#9296AD] mt-1 leading-relaxed">
                  {selectedNode.description}
                </p>
              </div>

              {/* Security Function */}
              <div className="p-3 rounded-lg bg-[#141724] border border-[#1C1F33]">
                <span className="block font-mono text-[10px] text-[#9A8CFF] uppercase mb-1">
                  Enforcement Function
                </span>
                <p className="text-xs text-white leading-relaxed">
                  {selectedNode.securityFunction}
                </p>
              </div>

              {/* Inbound & Outbound Data */}
              <div className="grid grid-cols-1 gap-2.5 font-mono text-xs">
                <div className="p-2.5 rounded bg-[#10121A] border border-white/5">
                  <span className="text-[#6B6E7A] block text-[10px] uppercase">Inbound Data:</span>
                  <span className="text-[#AEB1BA] mt-0.5 block">{selectedNode.inboundData}</span>
                </div>
                <div className="p-2.5 rounded bg-[#10121A] border border-white/5">
                  <span className="text-[#6B6E7A] block text-[10px] uppercase">Decision Logic:</span>
                  <span className="text-white mt-0.5 block">{selectedNode.decision}</span>
                </div>
                <div className="p-2.5 rounded bg-[#10121A] border border-white/5">
                  <span className="text-[#6B6E7A] block text-[10px] uppercase">Outbound Transition:</span>
                  <span className="text-[#9A8CFF] mt-0.5 block">{selectedNode.outboundResult}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Decision Outcome Summary for Current Scenario */}
          <div className="mt-6 pt-5 border-t border-[#1C1F33]">
            <div className="p-4 rounded-lg bg-[#090A12] border border-[#1C1F33] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs text-[#AEB1BA] uppercase">Active Verdict</span>
                <span className="font-mono text-[10px] text-[#6B6E7A]">Fail-Closed Enforced</span>
              </div>
              <p className="text-xs text-[#F4F5FB] leading-relaxed">
                {scenario.outcomeText}
              </p>
              <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[11px] font-mono">
                <span className="text-[#6B6E7A]">Evidence Receipt:</span>
                <a
                  href={`/receipts?id=${scenario.receiptId}`}
                  className="text-[#9A8CFF] hover:underline"
                >
                  {scenario.receiptId}
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
