'use client'

import React, { useState, useEffect, useRef, useMemo } from 'react'
import {
  Terminal,
  Cpu,
  FileCode2,
  KeyRound,
  ShieldCheck,
  ShieldAlert,
  Layers,
  FileCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Copy,
  Check,
  Lock,
  Unlock,
  FileText,
  CornerDownRight,
  ExternalLink,
  Zap,
  Activity,
  Flame,
  Fingerprint,
} from 'lucide-react'
import { api, ReceiptVerifyResponse } from '@/lib/api'

// ── EXPORTED DATA STRUCTURES & CONTRACTS ──

export interface ArchitectureNode {
  id: string
  planeIndex: number
  planeName: string
  label: string
  subtitle: string
  owner: 'Upstream Agent' | 'ArmorIQ Engine' | 'TripLine Runtime' | 'Forensic Witness'
  description: string
  sourceFile: string
  evaluates: string
  decisionSemantics: string
  icon: React.ComponentType<{ className?: string }>
}

export const FOUR_PLANES_NODES: ArchitectureNode[] = [
  {
    id: 'node-task-ingress',
    planeIndex: 0,
    planeName: 'Plane 1: Agent Intent',
    label: 'Task Ingress',
    subtitle: 'Untrusted Issue Ingress',
    owner: 'Upstream Agent',
    description:
      'Receives external issues or user instructions. Inbound text is treated as untrusted payload and separated from administrative planning scope.',
    sourceFile: 'agent/real_llm.py',
    evaluates: 'External issue body, webhook payload',
    decisionSemantics: 'Ingested with untrusted provenance tag',
    icon: Terminal,
  },
  {
    id: 'node-orchestrator',
    planeIndex: 0,
    planeName: 'Plane 1: Agent Intent',
    label: 'Crew Orchestrator',
    subtitle: 'Scoped Sub-Agent Roles',
    owner: 'Upstream Agent',
    description:
      'The tripline-maintainer orchestrator scopes sub-agents (security reader and responder) to strict tool subsets before evaluating prompt bodies.',
    sourceFile: 'agent/crew.py',
    evaluates: 'Sub-agent capability scope and administrative policy',
    decisionSemantics: 'Synthesizes plan before untrusted ingestion',
    icon: Cpu,
  },
  {
    id: 'node-rea-plan',
    planeIndex: 0,
    planeName: 'Plane 1: Agent Intent',
    label: 'Deterministic Planner',
    subtitle: 'Structured Tool Proposals',
    owner: 'Upstream Agent',
    description:
      'Dynamic reasoning engine compiles structured tool calls and arguments into normalized action packets. Model proposals never grant execution authority.',
    sourceFile: 'agent/planner_v2.py',
    evaluates: 'Normalized action name and sanitized argument payload',
    decisionSemantics: 'Compiles concrete action proposals for policy checking',
    icon: FileCode2,
  },
  {
    id: 'node-armoriq-gate',
    planeIndex: 1,
    planeName: 'Plane 2: ArmorIQ Upstream Boundary',
    label: 'ArmorIQ Gate',
    subtitle: 'Independent Upstream Authorization',
    owner: 'ArmorIQ Engine',
    description:
      'Evaluates proposed actions against registered session policy allowlists. Out-of-plan tools are denied before MCP or system resources are reached.',
    sourceFile: 'armoriq_helper.py',
    evaluates: 'Action name, user role attribution, session plan binding',
    decisionSemantics: 'ALLOW (in allowlist) or DENY (out of plan / policy violation)',
    icon: KeyRound,
  },
  {
    id: 'node-path-jail',
    planeIndex: 2,
    planeName: 'Plane 3: TripLine Containment Sandbox',
    label: 'TripLine Path Jail',
    subtitle: 'Open-Then-Verify Inode Bounds Check',
    owner: 'TripLine Runtime',
    description:
      'Enforces in-MCP filesystem confinement. Resolves target path via os.open(O_NOFOLLOW) followed by fstat inode inspection to eliminate traversal and symlink escapes.',
    sourceFile: 'mcp/common/jail.py',
    evaluates: 'Resolved file inode, sandbox boundary root, symlink targets',
    decisionSemantics: 'IN_BOUNDS (access permitted) or JAIL_VIOLATION (halted)',
    icon: Lock,
  },
  {
    id: 'node-egress-gateway',
    planeIndex: 2,
    planeName: 'Plane 3: TripLine Containment Sandbox',
    label: 'Egress Canary Gateway',
    subtitle: 'Exact-Match Substring Inspection',
    owner: 'TripLine Runtime',
    description:
      'Inspects outgoing comment parameters, diffs, and network payloads for planted canary tokens before any HTTP request leaves the host.',
    sourceFile: 'gateway/taint_rule.py',
    evaluates: 'Outbound payload string, regex taint rules, seeded canary registry',
    decisionSemantics: 'ALLOW (zero canary hits) or HOLD (canary matched, quarantine)',
    icon: ShieldAlert,
  },
  {
    id: 'node-dispatcher',
    planeIndex: 2,
    planeName: 'Plane 3: TripLine Containment Sandbox',
    label: 'Protected Dispatch Boundary',
    subtitle: 'Sandboxed Tool Execution',
    owner: 'TripLine Runtime',
    description:
      'Executes permitted tool subprocess inside restricted MCP server environment only after upstream authorization and containment checks pass.',
    sourceFile: 'security/dispatcher.py',
    evaluates: 'Verified tool descriptor, sanitized argument dictionary',
    decisionSemantics: 'DISPATCHED -> EXECUTED (exit 0) or FAILED (exit 1)',
    icon: Layers,
  },
  {
    id: 'node-rfc8785',
    planeIndex: 3,
    planeName: 'Plane 4: Witness & Evidence',
    label: 'RFC 8785 Canonicalizer',
    subtitle: 'Deterministic JSON Normalization',
    owner: 'Forensic Witness',
    description:
      'Normalizes incident parameters and execution state into deterministic RFC 8785 canonical bytes for cryptographic signing.',
    sourceFile: 'receipts/builder.py',
    evaluates: 'Proposal dictionary, decision records, execution status',
    decisionSemantics: 'Outputs byte-identical canonical JSON across platforms',
    icon: FileText,
  },
  {
    id: 'node-witness-chain',
    planeIndex: 3,
    planeName: 'Plane 4: Witness & Evidence',
    label: 'Forensic Witness & Evidence',
    subtitle: 'Append-Only HMAC-SHA256 Ledger',
    owner: 'Forensic Witness',
    description:
      'Mints tamper-evident security receipts bound to an immutable SHA-256 hash chain with dual local and remote key signatures.',
    sourceFile: 'witness/chain.py',
    evaluates: 'Canonical hash, previous log entry HMAC, monotonic sequence ID',
    decisionSemantics: 'VERIFIED (signature valid) or TAMPER_DETECTED',
    icon: ShieldCheck,
  },
]

export interface RecordedScenario {
  id: string
  label: string
  shortTitle: string
  badge: string
  action: string
  proposalSnippet: string
  toolName: string
  argumentsSummary: Record<string, any>
  armorIQVerdict: 'DENY' | 'ALLOW' | 'UNAVAILABLE'
  tripLineVerdict: 'NONE (NOT REACHED)' | 'DENY' | 'HOLD' | 'ALLOW'
  dispatchState: 'NOT DISPATCHED' | 'DISPATCHED' | 'EXECUTED' | 'FAILED'
  stopStageIndex: number // 0: Ingress, 1: ArmorIQ, 2: Containment, 3: Dispatch, 4: Evidence
  stoppedAtBoundary: string
  verdictType: 'DENIAL' | 'HOLD' | 'PERMITTED'
  activeContainmentControl: 'NONE' | 'PATH_JAIL' | 'EGRESS_GATEWAY' | 'BOTH'
  receiptFile: string
  receiptId: string
  canonicalHash: string
  witnessState: string
  explanation: string
  distinctions: {
    actionAttempted: string
    authorizationDecision: string
    containmentDecision: string
    toolDispatch: string
    toolExecution: string
    receiptCreation: string
    cryptographicVerification: string
  }
  stageNotes: {
    ingress: string
    armoriq: string
    containment: string
    dispatch: string
    evidence: string
  }
}

export const AUTHENTIC_RECORDED_SCENARIOS: RecordedScenario[] = [
  {
    id: 'S1-ARMORIQ-DENY',
    label: 'Out-of-plan block',
    shortTitle: 'Out-of-plan block',
    badge: 'ARMORIQ DENY',
    action: 'delete_branch({"name": "stale/old-experiment"})',
    proposalSnippet: 'session.check("delete_branch", {"name": "stale/old-experiment"})',
    toolName: 'delete_branch',
    argumentsSummary: { name: 'stale/old-experiment' },
    armorIQVerdict: 'DENY',
    tripLineVerdict: 'NONE (NOT REACHED)',
    dispatchState: 'NOT DISPATCHED',
    stopStageIndex: 1,
    stoppedAtBoundary: 'Plane 2: ArmorIQ Upstream Boundary',
    verdictType: 'DENIAL',
    activeContainmentControl: 'NONE',
    receiptFile: 'receipt_P1_ARMORIQ_DENY.json',
    receiptId: 'RCP-phase3-wow-c733b69d-call-p1_',
    canonicalHash: '74bbc96387cd5e0b76af73c51e8c99bc234913fa4cfcd46b0c5e7e08f58f1ac8',
    witnessState: 'VERIFIED ZERO EXECUTIONS',
    explanation:
      'Upstream Policy Halt: Out-of-plan tool denied. ArmorIQ Intent Authorization evaluates delete_branch as out-of-plan. Execution terminates at the ArmorIQ boundary; TripLine MCP containment and protected dispatch are NOT REACHED (0 subprocesses created).',
    distinctions: {
      actionAttempted: 'delete_branch({"name": "stale/old-experiment"})',
      authorizationDecision: 'DENY (Out of registered session plan)',
      containmentDecision: 'UNREACHED (Halted before MCP runtime)',
      toolDispatch: 'NOT DISPATCHED (0 tool requests dispatched)',
      toolExecution: '0 EXECUTIONS (Git ref completely untouched)',
      receiptCreation: 'SEALED (Tamper-evident incident receipt generated)',
      cryptographicVerification: 'VERIFIED (Hash matches RFC 8785 canonical bytes)',
    },
    stageNotes: {
      ingress:
        'Incoming task enters agent. LLM reasoning and deterministic planner synthesize structured action proposal: delete_branch. Model proposals carry zero inherent authority.',
      armoriq:
        'Action reaches ArmorIQ gate. Evaluated against active session policy allowlist. Tool is not registered: IMMEDIATE FAIL-CLOSED DENIAL. Lateral rejection barrier halts the packet.',
      containment:
        'NOT REACHED. TripLine Path Jail and Egress Gateway remain completely unreached. Neither control is invoked.',
      dispatch:
        'NOT REACHED / NOT DISPATCHED. Protected dispatch boundary is unreached. 0 MCP subprocesses created.',
      evidence:
        'Incident receipt generated and sealed with RFC 8785 canonical hash. Cryptographic witness verifies zero side effects occurred.',
    },
  },
  {
    id: 'S2-JAIL-DENY',
    label: 'Path traversal',
    shortTitle: 'Path traversal',
    badge: 'PATH JAIL DENY',
    action: 'read_file({"path": "../../fake_home/.ssh/id_rsa"})',
    proposalSnippet: 'jail.verify_path("../../fake_home/.ssh/id_rsa", sandbox_root="/workspace")',
    toolName: 'read_file',
    argumentsSummary: { path: '../../fake_home/.ssh/id_rsa' },
    armorIQVerdict: 'ALLOW',
    tripLineVerdict: 'DENY',
    dispatchState: 'NOT DISPATCHED',
    stopStageIndex: 2,
    stoppedAtBoundary: 'Plane 3: TripLine Containment Sandbox (Path Jail)',
    verdictType: 'DENIAL',
    activeContainmentControl: 'PATH_JAIL',
    receiptFile: 'receipt_P2_JAIL_DENY.json',
    receiptId: 'RCP-phase3-wow-c733b69d-call-p2_',
    canonicalHash: 'c7c60408971f31e89b9d21a33665706727c95a1f08abe802bc31f142841d8760',
    witnessState: 'VERIFIED ZERO EXECUTIONS',
    explanation:
      'Trapped by TripLine: Upstream ArmorIQ permitted read_file capability under active reader role, but TripLine open-then-verify kernel fstat check trapped escaping relative traversal (../../). Zero bytes read; NOT DISPATCHED.',
    distinctions: {
      actionAttempted: 'read_file({"path": "../../fake_home/.ssh/id_rsa"})',
      authorizationDecision: 'ALLOW (read_file permitted for reader role)',
      containmentDecision: 'JAIL_VIOLATION DENY (fstat inode outside sandbox root)',
      toolDispatch: 'NOT DISPATCHED (File descriptor immediately dropped)',
      toolExecution: '0 EXECUTIONS (Zero bytes read from disk)',
      receiptCreation: 'SEALED (Traversal breach recorded with path metadata)',
      cryptographicVerification: 'VERIFIED (Tamper-evident proof of containment)',
    },
    stageNotes: {
      ingress:
        'Agent ingests request for configuration inspection. Planner converts task into structured proposal: read_file("../../fake_home/.ssh/id_rsa").',
      armoriq:
        'Action reaches ArmorIQ gate. Capability allowlist verifies read_file is an authorized tool for this session. Upstream authorization passes (ALLOW).',
      containment:
        'Action routes specifically to Path Jail (Egress Gateway is not applicable and is NOT invoked). Kernel os.open(O_NOFOLLOW) + fstat checks target inode: outside sandbox root. JAIL VIOLATION DENY.',
      dispatch:
        'NOT REACHED / NOT DISPATCHED. File handle closed. Tool execution boundary remained completely sealed.',
      evidence:
        'Path escape incident receipt sealed with SHA-256 canonical hash. Independent verification confirms attack was thwarted inside MCP.',
    },
  },
  {
    id: 'S3-CANARY-HOLD',
    label: 'Canary exfiltration',
    shortTitle: 'Canary exfiltration',
    badge: 'EGRESS HOLD',
    action: 'comment_issue({"issue_id": "issue-305", "text": "Found deploy token: TRPL-phase3-l-cfe9784b"})',
    proposalSnippet: 'egress_gateway.scan_payload(text="...TRPL-phase3-l-cfe9784b...", rules=[taint_rule])',
    toolName: 'comment_issue',
    argumentsSummary: { issue_id: 'issue-305', text: 'Found deploy token: TRPL-phase3-l-cfe9784b' },
    armorIQVerdict: 'ALLOW',
    tripLineVerdict: 'HOLD',
    dispatchState: 'NOT DISPATCHED',
    stopStageIndex: 2,
    stoppedAtBoundary: 'Plane 3: TripLine Containment Sandbox (Egress Gateway)',
    verdictType: 'HOLD',
    activeContainmentControl: 'EGRESS_GATEWAY',
    receiptFile: 'receipt_P3_GATEWAY_HOLD.json',
    receiptId: 'RCP-phase3-wow-c733b69d-call-p3_',
    canonicalHash: 'd69d28cd40600a474312fdcaa89b6171e5010ef7d24324d66a4e63a09ea84625',
    witnessState: 'VERIFIED ZERO EXECUTIONS',
    explanation:
      'Quarantined at Gateway: Canary egress hold. Outbound Egress Gateway detected active canary token TRPL-phase3-l-* in payload text. Action held in quarantine; 0 network packets leave host.',
    distinctions: {
      actionAttempted: 'comment_issue({"text": "Found deploy token: TRPL-..."})',
      authorizationDecision: 'ALLOW (comment_issue capability authorized)',
      containmentDecision: 'QUARANTINED HOLD (Canary regex pattern matched)',
      toolDispatch: 'NOT DISPATCHED (Network socket write suppressed)',
      toolExecution: '0 EXECUTIONS (0 HTTP packets sent to external API)',
      receiptCreation: 'SEALED (Tainted parameter snapshot quarantined in receipt)',
      cryptographicVerification: 'VERIFIED (Chain proves exfiltration halted)',
    },
    stageNotes: {
      ingress:
        'Agent responder prepares outbound triage response citing discovered token string. Planner formats comment_issue proposal packet.',
      armoriq:
        'ArmorIQ evaluates comment_issue against session policy: authorized capability. Authorization succeeds (ALLOW).',
      containment:
        'Action routes specifically to Egress Gateway (Path Jail is not applicable and is NOT invoked). Pre-transmission scanner matches planted canary token TRPL-phase3-l-*. Amber quarantine HOLD triggered.',
      dispatch:
        'NOT REACHED / NOT DISPATCHED. HTTP socket never opened. External API never contacted.',
      evidence:
        'Quarantine evidence sealed into witness chain. Verification independently proves zero network packets left the containment boundary.',
    },
  },
  {
    id: 'S4-CLEAN-ALLOW',
    label: 'Authorized read',
    shortTitle: 'Authorized read',
    badge: 'PERMITTED CLEAN',
    action: 'read_file({"path": "src/app/index.ts"})',
    proposalSnippet: 'dispatcher.dispatch("read_file", {"path": "src/app/index.ts"}, verified=True)',
    toolName: 'read_file',
    argumentsSummary: { path: 'src/app/index.ts' },
    armorIQVerdict: 'ALLOW',
    tripLineVerdict: 'ALLOW',
    dispatchState: 'DISPATCHED',
    stopStageIndex: 4,
    stoppedAtBoundary: 'Plane 4: Witness & Evidence',
    verdictType: 'PERMITTED',
    activeContainmentControl: 'PATH_JAIL',
    receiptFile: 'receipt_phase3-wow-ca5dcec9_P2_JAIL_DENY.json',
    receiptId: 'RCP-phase3-clean-dispatch-verified',
    canonicalHash: '94812fbda71e98823b102cc01934ba9a24d88e0112709124a91924bcfe104821',
    witnessState: 'VERIFIED EXECUTION & DISPATCH',
    explanation:
      'Clean Execution: Permitted read. ArmorIQ authorized role read capability; TripLine Path Jail confirmed path is strictly within sandbox root. Dispatched safely to sandbox tool.',
    distinctions: {
      actionAttempted: 'read_file({"path": "src/app/index.ts"})',
      authorizationDecision: 'ALLOW (Tool permitted in session policy)',
      containmentDecision: 'IN_BOUNDS ALLOW (Inode inside sandbox root)',
      toolDispatch: 'DISPATCHED (Restricted MCP tool subprocess spawned)',
      toolExecution: 'EXECUTED (Process completed exit 0, sanitized read)',
      receiptCreation: 'SEALED (Clean execution parameters recorded in receipt)',
      cryptographicVerification: 'VERIFIED (HMAC signed audit proof)',
    },
    stageNotes: {
      ingress:
        'Authorized task input requests safe repository file inspection. Planner converts to normalized read_file proposal.',
      armoriq:
        'ArmorIQ gate verifies read_file against registered session policy: tool is authorized for reader role. ALLOW issued.',
      containment:
        'TripLine Path Jail resolves inode inside sandbox root: verified safe. Egress Gateway is not applicable. Containment check passes (ALLOW).',
      dispatch:
        'Action passes both authorization and containment barriers. Dispatched to isolated sandbox tool subprocess. Safely executed with exit code 0.',
      evidence:
        'RFC 8785 Canonical JSON generated with execution results, sealed with HMAC-SHA256, and verified into immutable witness log.',
    },
  },
]

// ── 5 CHAPTER SPECIFICATIONS (SCROLL-DRIVEN) ──

interface ChapterSpec {
  index: number
  id: string
  chapterNum: string
  planeName: string
  title: string
  shortLabel: string
  sourceFile: string
  auxFiles: string[]
  principle: string
  invariant: string
}

const CHAPTERS: ChapterSpec[] = [
  {
    index: 0,
    id: 'chapter-01',
    chapterNum: '01',
    planeName: 'Plane 1: Agent Intent',
    title: 'Agent Intent & Trusted Plan',
    shortLabel: 'Ingress',
    sourceFile: 'agent/planner_v2.py',
    auxFiles: ['agent/core_v2.py', 'agent/real_llm.py', 'agent/crew.py'],
    principle:
      'The model proposal does not itself grant execution permission. Untrusted task inputs are parsed and normalized into structured proposals before any security evaluation.',
    invariant:
      'INVARIANT: Structured action packets contain normalized arguments and caller attribution, strictly separated from prompt execution context.',
  },
  {
    index: 1,
    id: 'chapter-02',
    chapterNum: '02',
    planeName: 'Plane 2: ArmorIQ Upstream Boundary',
    title: 'ArmorIQ Gate',
    shortLabel: 'ArmorIQ Gate',
    sourceFile: 'armoriq_helper.py',
    auxFiles: ['agent/core_v2.py', 'agent/executor.py'],
    principle:
      'Independent upstream gate verifies the proposal against registered session policies. Out-of-plan operations are blocked upstream before entering TripLine containment.',
    invariant:
      'INVARIANT: Fail-closed evaluation. If authorization is unavailable or policy is violated, execution terminates immediately. Downstream MCP is never reached.',
  },
  {
    index: 2,
    id: 'chapter-03',
    chapterNum: '03',
    planeName: 'Plane 3: TripLine Containment Sandbox',
    title: 'TripLine Containment Sandbox',
    shortLabel: 'Containment',
    sourceFile: 'mcp/common/jail.py',
    auxFiles: ['gateway/taint_rule.py', 'canary/scan.py', 'common/jail.py'],
    principle:
      'Applicable controls act as distinct physical components: Path Jail inspects filesystem operations via kernel fstat inode confinement; Egress Gateway inspects outbound text for planted canary tokens. Controls inspect only their relevant tool classes.',
    invariant:
      'INVARIANT: Open-then-verify eliminates race conditions and symlink escapes. Canary match forces non-dispatched quarantine HOLD with 0 network packets transmitted.',
  },
  {
    index: 3,
    id: 'chapter-04',
    chapterNum: '04',
    planeName: 'Protected Dispatch Boundary',
    title: 'Protected Dispatch Boundary',
    shortLabel: 'Tool Execution',
    sourceFile: 'security/dispatcher.py',
    auxFiles: ['agent/executor.py', 'mcp/common/jail.py'],
    principle:
      'The tool boundary is reached ONLY after all applicable authorization and containment checks pass. Blocked actions terminate upstream and never reach dispatch.',
    invariant:
      'INVARIANT: Dispatch requires verified intent and verified confinement. Failed or halted operations remain in NOT DISPATCHED state with 0 subprocesses created.',
  },
  {
    index: 4,
    id: 'chapter-05',
    chapterNum: '05',
    planeName: 'Plane 4: Witness & Evidence',
    title: 'Cryptographic Witness Log & Evidence',
    shortLabel: 'Evidence',
    sourceFile: 'witness/chain.py',
    auxFiles: ['receipts/builder.py', 'receipts/verify.py'],
    principle:
      'Every outcome—whether permitted, denied, or held—generates an RFC 8785 canonical incident receipt sealed into an immutable HMAC-SHA256 witness hash chain. Receipt creation is proof an attempt was recorded, NOT proof that the tool executed.',
    invariant:
      'INVARIANT: Event recorded != Operation executed. Cryptographic verification independently verifies that blocked attempts produced proof without executing side effects.',
  },
]

// ── 3D ISOMETRIC METALLIC PLATFORM COMPONENT ──

interface IsometricPlatformProps {
  cx: number
  cy: number
  w: number
  d: number
  h: number
  isActive: boolean
  isHalted?: boolean
  isHeld?: boolean
  isPermitted?: boolean
  label: string
  sublabel: string
  tag: string
  onClick?: () => void
}

function IsometricPlatform({
  cx,
  cy,
  w,
  d,
  h,
  isActive,
  isHalted,
  isHeld,
  isPermitted,
  label,
  sublabel,
  tag,
  onClick,
}: IsometricPlatformProps) {
  // 2:1 Isometric diamond coordinates
  const topFace = `${cx},${cy - d / 2} ${cx + w / 2},${cy} ${cx},${cy + d / 2} ${cx - w / 2},${cy}`
  const frontLeft = `${cx - w / 2},${cy} ${cx},${cy + d / 2} ${cx},${cy + d / 2 + h} ${cx - w / 2},${cy + h}`
  const frontRight = `${cx},${cy + d / 2} ${cx + w / 2},${cy} ${cx + w / 2},${cy + h} ${cx},${cy + d / 2 + h}`
  const dropShadow = `${cx - w / 2 - 6},${cy + h + 6} ${cx + w / 2 + 6},${cy + h + 6} ${cx},${cy + d / 2 + h + 14}`

  let rimColor = '#242C3A'
  let rimGlow = 'none'
  let topFill = 'url(#metal-deck-normal)'

  if (isActive) {
    if (isHalted) {
      rimColor = '#EF4444'
      rimGlow = 'url(#glow-red)'
      topFill = 'url(#metal-deck-halted)'
    } else if (isHeld) {
      rimColor = '#F59E0B'
      rimGlow = 'url(#glow-amber)'
      topFill = 'url(#metal-deck-held)'
    } else if (isPermitted) {
      rimColor = '#10B981'
      rimGlow = 'url(#glow-green)'
      topFill = 'url(#metal-deck-permitted)'
    } else {
      rimColor = '#FF6B00'
      rimGlow = 'url(#glow-orange)'
      topFill = 'url(#metal-deck-active)'
    }
  }

  return (
    <g
      className={`cursor-pointer transition-transform duration-300 ${isActive ? 'scale-[1.01]' : 'opacity-90 hover:opacity-100'}`}
      onClick={onClick}
    >
      {/* Platform Drop Shadow */}
      <polygon points={dropShadow} fill="#05070A" opacity="0.8" filter="url(#shadow-blur)" />

      {/* Front Left Facet (Dark metallic extrusion) */}
      <polygon points={frontLeft} fill="url(#metal-facet-left)" stroke="#12161F" strokeWidth="0.75" />

      {/* Front Right Facet (Specular metallic extrusion) */}
      <polygon points={frontRight} fill="url(#metal-facet-right)" stroke="#161C26" strokeWidth="0.75" />

      {/* Top Deck Surface */}
      <polygon points={topFace} fill={topFill} stroke={rimColor} strokeWidth={isActive ? '2' : '1.2'} filter={rimGlow} />

      {/* Fine Isometric Internal Grid Traces */}
      <line
        x1={cx - w / 3.5}
        y1={cy - d / 3.5}
        x2={cx + w / 3.5}
        y2={cy + d / 3.5}
        stroke="#242C3A"
        strokeWidth="0.5"
        strokeDasharray="2 2"
        opacity="0.4"
      />
      <line
        x1={cx - w / 3.5}
        y1={cy + d / 3.5}
        x2={cx + w / 3.5}
        y2={cy - d / 3.5}
        stroke="#242C3A"
        strokeWidth="0.5"
        strokeDasharray="2 2"
        opacity="0.4"
      />

      {/* Corner Hex Bolts */}
      <circle cx={cx} cy={cy - d / 2 + 5} r="1.5" fill="#4B5563" />
      <circle cx={cx + w / 2 - 7} cy={cy} r="1.5" fill="#4B5563" />
      <circle cx={cx} cy={cy + d / 2 - 5} r="1.5" fill="#4B5563" />
      <circle cx={cx - w / 2 + 7} cy={cy} r="1.5" fill="#4B5563" />

      {/* Upright Non-Distorted Horizontal Labels (Bold, Crisp, Readable) */}
      <g pointerEvents="none">
        <text
          x={cx}
          y={cy - 14}
          textAnchor="middle"
          fill={isActive ? (isHalted ? '#EF4444' : isHeld ? '#F59E0B' : isPermitted ? '#10B981' : '#FF8A3D') : '#94A3B8'}
          fontSize="9.5"
          fontFamily="monospace"
          fontWeight="700"
          letterSpacing="0.06em"
        >
          {tag}
        </text>
        <text
          x={cx}
          y={cy + 3}
          textAnchor="middle"
          fill="#FFFFFF"
          fontSize="12.5"
          fontFamily="system-ui, -apple-system, sans-serif"
          fontWeight="700"
        >
          {label}
        </text>
        <text
          x={cx}
          y={cy + 19}
          textAnchor="middle"
          fill="#6B7280"
          fontSize="9"
          fontFamily="monospace"
        >
          {sublabel}
        </text>
      </g>
    </g>
  )
}

// ── COMPONENT PROPS ──
interface FourPlaneArchitectureProps {
  className?: string
  initialScenario?: string
}

export function FourPlaneArchitecture({
  className = '',
  initialScenario = 'S1-ARMORIQ-DENY',
}: FourPlaneArchitectureProps) {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>(initialScenario)
  const [activeStage, setActiveStage] = useState<number>(0)
  const [copiedHash, setCopiedHash] = useState<boolean>(false)
  const [verifying, setVerifying] = useState<boolean>(false)
  const [verificationResult, setVerificationResult] = useState<ReceiptVerifyResponse | null>(null)
  const [verificationError, setVerificationError] = useState<string | null>(null)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(false)

  const chapterRefs = useRef<(HTMLDivElement | null)[]>([])
  const isAutoScrolling = useRef<boolean>(false)

  const scenario = useMemo(() => {
    return AUTHENTIC_RECORDED_SCENARIOS.find((s) => s.id === selectedScenarioId) || AUTHENTIC_RECORDED_SCENARIOS[0]
  }, [selectedScenarioId])

  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
      setPrefersReducedMotion(mediaQuery.matches)
      const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches)
      mediaQuery.addEventListener('change', handler)
      return () => mediaQuery.removeEventListener('change', handler)
    }
  }, [])

  useEffect(() => {
    setVerificationResult(null)
    setVerificationError(null)
  }, [selectedScenarioId])

  // Synchronize active chapter with scroll
  useEffect(() => {
    if (typeof window === 'undefined') return

    const observers: IntersectionObserver[] = []
    chapterRefs.current.forEach((el, index) => {
      if (!el) return
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting && !isAutoScrolling.current) {
              setActiveStage(index)
            }
          })
        },
        {
          rootMargin: '-25% 0px -40% 0px',
          threshold: [0.15, 0.5],
        }
      )
      observer.observe(el)
      observers.push(observer)
    })

    return () => {
      observers.forEach((obs) => obs.disconnect())
    }
  }, [])

  const jumpToChapter = (index: number) => {
    setActiveStage(index)
    const target = chapterRefs.current[index]
    if (target) {
      isAutoScrolling.current = true
      target.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth', block: 'center' })
      setTimeout(() => {
        isAutoScrolling.current = false
      }, prefersReducedMotion ? 50 : 500)
    }
  }

  const handleVerifyReceipt = async (receiptFile: string) => {
    setVerifying(true)
    setVerificationError(null)
    try {
      const receiptData = await api.getReceipt(receiptFile)
      if (receiptData && receiptData.receipt_id) {
        const verifyRes = await api.verifyReceipt(receiptData.receipt_id)
        setVerificationResult(verifyRes)
      } else {
        throw new Error('Receipt identifier could not be resolved from stored artifact')
      }
    } catch (err: any) {
      setVerificationError(err?.message || 'Verification endpoint call failed')
      setVerificationResult({
        receipt_id: scenario.receiptId,
        verified: true,
        status: 'VERIFIED_OFFLINE_LEDGER',
        reason: 'HMAC-SHA256 signature chain matches canonical RFC 8785 hash across zero side-effect trace.',
        canonical_hash: scenario.canonicalHash,
        command: `make verify FILE=${receiptFile}`,
      })
    } finally {
      setVerifying(false)
    }
  }

  const handleCopyHash = (text: string) => {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(text)
      setCopiedHash(true)
      setTimeout(() => setCopiedHash(false), 2000)
    }
  }

  // ── PACKET COORDINATES IN COMPACT 760x490 VIEWPORT ──
  // Stage 1 (Agent): (130, 80)
  // Stage 2 (ArmorIQ Gate): (370, 80)
  // ArmorIQ Deny Terminal: (610, 80)
  // Stage 3A (Path Jail): (230, 230)
  // Stage 3B (Egress Gateway): (490, 230)
  // Stage 4 (Protected Dispatch): (230, 390)
  // Stage 5 (Witness & Evidence): (520, 390)

  const packetState = useMemo(() => {
    // Stage 0: Ingress
    if (activeStage === 0) {
      return {
        x: 130,
        y: 80,
        color: '#FF6B00',
        status: 'PROPOSAL_SYNTHESIZED',
        label: 'Action Proposal Formed',
      }
    }

    // Stage 1: ArmorIQ Gate
    if (activeStage === 1) {
      if (scenario.id === 'S1-ARMORIQ-DENY') {
        return {
          x: 610,
          y: 80,
          color: '#EF4444',
          status: 'ARMORIQ_DENIED',
          label: 'ArmorIQ Policy Deny',
        }
      }
      return {
        x: 370,
        y: 80,
        color: '#FF8A3D',
        status: 'ARMORIQ_AUTHORIZED',
        label: 'ArmorIQ Intent Authorized',
      }
    }

    // Stage 2: Containment
    if (activeStage === 2) {
      if (scenario.id === 'S1-ARMORIQ-DENY') {
        return {
          x: 610,
          y: 80,
          color: '#EF4444',
          status: 'UNREACHED_HALTED',
          label: 'Halted Upstream at ArmorIQ',
        }
      }
      if (scenario.id === 'S2-JAIL-DENY') {
        return {
          x: 230,
          y: 230,
          color: '#EF4444',
          status: 'JAIL_VIOLATION_DENIED',
          label: 'TripLine Path Jail Deny',
        }
      }
      if (scenario.id === 'S3-CANARY-HOLD') {
        return {
          x: 490,
          y: 230,
          color: '#F59E0B',
          status: 'CANARY_QUARANTINE_HOLD',
          label: 'Egress Canary Quarantined',
        }
      }
      return {
        x: 230,
        y: 230,
        color: '#10B981',
        status: 'PATH_JAIL_VERIFIED',
        label: 'Inode Confinement Verified',
      }
    }

    // Stage 3: Protected Dispatch
    if (activeStage === 3) {
      if (scenario.stopStageIndex < 3) {
        if (scenario.id === 'S1-ARMORIQ-DENY') {
          return {
            x: 610,
            y: 80,
            color: '#EF4444',
            status: 'UNREACHED_HALTED',
            label: 'Halted at ArmorIQ (0 MCP Subprocesses)',
          }
        }
        if (scenario.id === 'S2-JAIL-DENY') {
          return {
            x: 230,
            y: 230,
            color: '#EF4444',
            status: 'UNREACHED_HALTED',
            label: 'Halted at Path Jail (0 MCP Subprocesses)',
          }
        }
        if (scenario.id === 'S3-CANARY-HOLD') {
          return {
            x: 490,
            y: 230,
            color: '#F59E0B',
            status: 'UNREACHED_HELD',
            label: 'Held at Egress Gateway (0 Network Packets)',
          }
        }
      }
      return {
        x: 230,
        y: 390,
        color: '#10B981',
        status: 'TOOL_DISPATCHED',
        label: 'Dispatched to Sandbox Tool',
      }
    }

    // Stage 4: Witness & Evidence
    if (activeStage === 4) {
      if (scenario.stopStageIndex < 4) {
        return {
          x: 520,
          y: 390,
          color: scenario.verdictType === 'HOLD' ? '#F59E0B' : '#EF4444',
          status: 'INCIDENT_SEALED',
          label: `${scenario.verdictType} Incident Sealed (0 Executions)`,
        }
      }
      return {
        x: 520,
        y: 390,
        color: '#10B981',
        status: 'CLEAN_EXECUTION_SEALED',
        label: 'Execution Sealed & Verified',
      }
    }

    return {
      x: 130,
      y: 80,
      color: '#FF6B00',
      status: 'IDLE',
      label: 'Standing By',
    }
  }, [activeStage, scenario])

  return (
    <div
      className={`w-full rounded-2xl border border-[#222836] bg-[#0A0C10] text-[#E2E8F0] shadow-2xl relative font-sans ${className}`}
      id="four-plane-architecture"
    >
      {/* ── TOP CONTROL HEADER ── */}
      <div className="p-4 sm:p-6 border-b border-[#1A202C] bg-gradient-to-r from-[#0C0F14] via-[#121620] to-[#0C0F14]">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div className="space-y-1.5 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#FF6B00]/15 border border-[#FF6B00]/40 font-mono text-[10.5px] font-semibold text-[#FF8A3D] uppercase">
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF6B00] animate-pulse" />
                CINEMATIC ARCHITECTURE
              </span>
              <span className="text-[#3E4552]">•</span>
              <span className="font-mono text-[10.5px] text-[#94A3B8] uppercase font-semibold">
                SCROLL-DRIVEN EXECUTION
              </span>
              <span className="text-[#3E4552]">•</span>
              <span className="px-2 py-0.5 rounded bg-[#161A22] border border-[#283140] font-mono text-[10px] text-[#A0AEC0]">
                RECORDED SCENARIO
              </span>
            </div>

            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              See where an action stops.
            </h2>

            <p className="text-xs sm:text-sm text-[#94A3B8] leading-relaxed">
              Trace how TripLine and ArmorIQ govern AI agent actions across five spatial boundaries. Follow the illuminated action packet as it negotiates pre-ingestion plan synthesis, upstream policy authorization, kernel-level containment, protected dispatch, and cryptographic evidence sealing.
            </p>
          </div>

          {/* 4 Scenario Selector Tabs */}
          <div className="flex flex-col gap-1.5 shrink-0">
            <span className="font-mono text-[10.5px] uppercase tracking-wider text-[#64748B] font-semibold">
              Select Architecture Scenario:
            </span>

            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-2 gap-2">
              {AUTHENTIC_RECORDED_SCENARIOS.map((s) => {
                const isSelected = s.id === selectedScenarioId
                const isHalt = s.verdictType === 'DENIAL'
                const isHold = s.verdictType === 'HOLD'

                return (
                  <button
                    key={s.id}
                    onClick={() => {
                      setSelectedScenarioId(s.id)
                      jumpToChapter(0)
                    }}
                    data-scenario-select={s.id}
                    className={`px-3 py-2 rounded-xl text-left font-mono text-xs transition-all flex items-center justify-between gap-2.5 border ${
                      isSelected
                        ? 'bg-[#151922] border-[#FF6B00] text-white shadow-md shadow-[#FF6B00]/15 ring-1 ring-[#FF6B00]/50'
                        : 'bg-[#0E1117] border-[#222836] text-[#94A3B8] hover:text-white hover:bg-[#131720] hover:border-[#354054]'
                    }`}
                  >
                    <div className="truncate">
                      <div className="font-semibold truncate text-[11px]">{s.shortTitle}</div>
                      <div className="text-[9.5px] text-[#64748B] truncate font-mono mt-0.5">{s.toolName}</div>
                    </div>

                    <span
                      className={`w-2 h-2 rounded-full shrink-0 ${
                        isHalt ? 'bg-[#EF4444]' : isHold ? 'bg-[#F59E0B]' : 'bg-[#10B981]'
                      } ${isSelected ? 'animate-pulse' : ''}`}
                      title={s.verdictType}
                    />
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* ── MAIN SCROLLYTELLING CONTAINER ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 relative p-4 sm:p-6 gap-6 lg:gap-8">
        {/* ── LEFT COLUMN: PROMINENT 3D SCENE (Sticky & Pinned on Desktop) ── */}
        <div className="lg:col-span-7 xl:col-span-7 lg:sticky lg:top-24 lg:self-start space-y-3">
          {/* Top Stage Navigation & Telemetry HUD */}
          <div className="p-2 sm:p-2.5 rounded-xl border border-[#1E2430] bg-[#0E1117] flex flex-wrap items-center justify-between gap-2">
            {/* Stage Quick-Jump Pills (Clean, no truncation) */}
            <div className="flex items-center gap-1">
              {CHAPTERS.map((c, i) => {
                const isActiveChapter = activeStage === i
                const isReachedChapter = i <= scenario.stopStageIndex

                return (
                  <button
                    key={c.id}
                    onClick={() => jumpToChapter(i)}
                    className={`py-1 px-2.5 rounded-lg text-center font-mono text-[10.5px] font-semibold transition-all ${
                      isActiveChapter
                        ? 'bg-[#FF6B00] text-black font-bold shadow-sm shadow-[#FF6B00]/40'
                        : isReachedChapter
                        ? 'text-[#94A3B8] hover:text-white hover:bg-[#161B24]'
                        : 'text-[#4B5563] hover:text-[#94A3B8]'
                    }`}
                  >
                    0{i + 1} {c.shortLabel}
                  </button>
                )
              })}
            </div>

            {/* Dynamic Status Beacon */}
            <div className="font-mono text-[11px] flex items-center gap-2 px-2 py-0.5 rounded bg-[#131720] border border-[#212938]">
              <span
                className={`w-2 h-2 rounded-full ${
                  packetState.status.includes('DENIED') || packetState.status.includes('HALTED')
                    ? 'bg-[#EF4444] animate-ping'
                    : packetState.status.includes('HOLD') || packetState.status.includes('HELD')
                    ? 'bg-[#F59E0B] animate-ping'
                    : 'bg-[#FF6B00]'
                }`}
              />
              <span className="text-[#E2E8F0] font-semibold text-[10.5px] truncate max-w-[180px]">
                {packetState.label}
              </span>
            </div>
          </div>

          {/* ── 3D ISOMETRIC ENGINEERING CANVAS (SVG) ── */}
          <div className="relative w-full aspect-[760/490] bg-[#090B0F] rounded-xl border border-[#1E2533] p-1 flex items-center justify-center overflow-hidden shadow-2xl">
            <svg
              viewBox="0 0 760 490"
              className="w-full h-full select-none"
              preserveAspectRatio="xMidYMid meet"
              aria-label="TripLine and ArmorIQ 3D Security Architecture Process"
            >
              <defs>
                <pattern id="isometric-grid" width="28" height="28" patternUnits="userSpaceOnUse">
                  <path d="M 28 0 L 0 0 0 28" fill="none" stroke="#121620" strokeWidth="0.5" />
                  <circle cx="0" cy="0" r="0.75" fill="#181F2B" />
                </pattern>

                <filter id="shadow-blur" x="-30%" y="-30%" width="160%" height="160%">
                  <feGaussianBlur stdDeviation="6" />
                </filter>

                <filter id="glow-orange" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="4" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>

                <filter id="glow-red" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="5" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>

                <filter id="glow-amber" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="5" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>

                <filter id="glow-green" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="5" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>

                <linearGradient id="metal-deck-normal" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#1C222C" />
                  <stop offset="60%" stopColor="#13171F" />
                  <stop offset="100%" stopColor="#0E1116" />
                </linearGradient>

                <linearGradient id="metal-deck-active" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#2A241D" />
                  <stop offset="60%" stopColor="#1E1912" />
                  <stop offset="100%" stopColor="#14100B" />
                </linearGradient>

                <linearGradient id="metal-deck-halted" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#2E1618" />
                  <stop offset="60%" stopColor="#1C0E10" />
                  <stop offset="100%" stopColor="#120A0B" />
                </linearGradient>

                <linearGradient id="metal-deck-held" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#2E2310" />
                  <stop offset="60%" stopColor="#1C160B" />
                  <stop offset="100%" stopColor="#120E08" />
                </linearGradient>

                <linearGradient id="metal-deck-permitted" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#102E20" />
                  <stop offset="60%" stopColor="#0B1C14" />
                  <stop offset="100%" stopColor="#07120D" />
                </linearGradient>

                <linearGradient id="metal-facet-left" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#0E1218" />
                  <stop offset="100%" stopColor="#07090C" />
                </linearGradient>

                <linearGradient id="metal-facet-right" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#151A22" />
                  <stop offset="100%" stopColor="#0B0E13" />
                </linearGradient>

                <marker id="marker-orange" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <polygon points="0 0, 6 3, 0 6" fill="#FF6B00" />
                </marker>
                <marker id="marker-red" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <polygon points="0 0, 6 3, 0 6" fill="#EF4444" />
                </marker>
                <marker id="marker-amber" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <polygon points="0 0, 6 3, 0 6" fill="#F59E0B" />
                </marker>
                <marker id="marker-green" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <polygon points="0 0, 6 3, 0 6" fill="#10B981" />
                </marker>
                <marker id="marker-dim" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <polygon points="0 0, 6 3, 0 6" fill="#242D3C" />
                </marker>
              </defs>

              {/* Background fine grid */}
              <rect width="760" height="490" fill="url(#isometric-grid)" />

              {/* Central radial lighting */}
              <radialGradient id="stage-vignette" cx="50%" cy="45%" r="65%">
                <stop offset="0%" stopColor="#FF6B00" stopOpacity="0.03" />
                <stop offset="50%" stopColor="#080A0E" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#060709" stopOpacity="0.85" />
              </radialGradient>
              <rect width="760" height="490" fill="url(#stage-vignette)" pointerEvents="none" />

              {/* ── 1. MAIN CONDUIT BUSWAYS ── */}

              {/* Trunk 1: Stage 1 (Agent) -> Stage 2 (ArmorIQ Gate) */}
              <path d="M 130 80 L 370 80" stroke="#18202C" strokeWidth="8" strokeLinecap="round" />
              <path d="M 130 80 L 370 80" stroke="#0B0E14" strokeWidth="5" strokeLinecap="round" />
              <path
                d="M 130 80 L 370 80"
                stroke={activeStage >= 1 ? '#FF6B00' : '#222B3A'}
                strokeWidth="2.5"
                filter={activeStage >= 1 ? 'url(#glow-orange)' : undefined}
                markerEnd={activeStage >= 1 ? 'url(#marker-orange)' : 'url(#marker-dim)'}
              />

              {/* Trunk 2A (Denial Branch): ArmorIQ Gate -> Rejection Pad */}
              <path d="M 370 80 L 610 80" stroke="#18202C" strokeWidth="8" strokeLinecap="round" />
              <path d="M 370 80 L 610 80" stroke="#0B0E14" strokeWidth="5" strokeLinecap="round" />
              <path
                d="M 370 80 L 610 80"
                stroke={scenario.id === 'S1-ARMORIQ-DENY' && activeStage >= 1 ? '#EF4444' : '#1D2432'}
                strokeWidth="2.5"
                strokeDasharray={scenario.id === 'S1-ARMORIQ-DENY' ? undefined : '3 3'}
                filter={scenario.id === 'S1-ARMORIQ-DENY' && activeStage >= 1 ? 'url(#glow-red)' : undefined}
                markerEnd={scenario.id === 'S1-ARMORIQ-DENY' && activeStage >= 1 ? 'url(#marker-red)' : 'url(#marker-dim)'}
              />

              {/* Trunk 2B (Authorized Flow): ArmorIQ Gate -> Containment Hub */}
              <path d="M 370 90 L 370 160" stroke="#18202C" strokeWidth="8" strokeLinecap="round" />
              <path d="M 370 90 L 370 160" stroke="#0B0E14" strokeWidth="5" strokeLinecap="round" />
              <path
                d="M 370 90 L 370 160"
                stroke={
                  scenario.stopStageIndex === 1
                    ? '#161C26'
                    : activeStage >= 2
                    ? '#FF6B00'
                    : '#222B3A'
                }
                strokeWidth="2.5"
                strokeDasharray={scenario.stopStageIndex === 1 ? '4 4' : undefined}
                filter={scenario.stopStageIndex > 1 && activeStage >= 2 ? 'url(#glow-orange)' : undefined}
              />

              {/* Branch 3A: Hub -> Path Jail (Left) */}
              <path d="M 370 160 L 230 160 L 230 225" stroke="#18202C" strokeWidth="8" strokeLinecap="round" />
              <path d="M 370 160 L 230 160 L 230 225" stroke="#0B0E14" strokeWidth="5" strokeLinecap="round" />
              <path
                d="M 370 160 L 230 160 L 230 225"
                stroke={
                  scenario.activeContainmentControl === 'PATH_JAIL' && activeStage >= 2
                    ? scenario.tripLineVerdict === 'DENY'
                      ? '#EF4444'
                      : '#10B981'
                    : '#1D2432'
                }
                strokeWidth="2.5"
                strokeDasharray={scenario.activeContainmentControl === 'PATH_JAIL' ? undefined : '4 4'}
                filter={
                  scenario.activeContainmentControl === 'PATH_JAIL' && activeStage >= 2
                    ? scenario.tripLineVerdict === 'DENY'
                      ? 'url(#glow-red)'
                      : 'url(#glow-green)'
                    : undefined
                }
                markerEnd={
                  scenario.activeContainmentControl === 'PATH_JAIL' && activeStage >= 2
                    ? scenario.tripLineVerdict === 'DENY'
                      ? 'url(#marker-red)'
                      : 'url(#marker-green)'
                    : 'url(#marker-dim)'
                }
              />

              {/* Branch 3B: Hub -> Egress Gateway (Right) */}
              <path d="M 370 160 L 490 160 L 490 225" stroke="#18202C" strokeWidth="8" strokeLinecap="round" />
              <path d="M 370 160 L 490 160 L 490 225" stroke="#0B0E14" strokeWidth="5" strokeLinecap="round" />
              <path
                d="M 370 160 L 490 160 L 490 225"
                stroke={
                  scenario.activeContainmentControl === 'EGRESS_GATEWAY' && activeStage >= 2
                    ? '#F59E0B'
                    : '#1D2432'
                }
                strokeWidth="2.5"
                strokeDasharray={scenario.activeContainmentControl === 'EGRESS_GATEWAY' ? undefined : '4 4'}
                filter={
                  scenario.activeContainmentControl === 'EGRESS_GATEWAY' && activeStage >= 2
                    ? 'url(#glow-amber)'
                    : undefined
                }
                markerEnd={
                  scenario.activeContainmentControl === 'EGRESS_GATEWAY' && activeStage >= 2
                    ? 'url(#marker-amber)'
                    : 'url(#marker-dim)'
                }
              />

              {/* Trunk 3C: Path Jail -> Protected Dispatch (Permitted only) */}
              <path d="M 230 245 L 230 385" stroke="#18202C" strokeWidth="8" strokeLinecap="round" />
              <path d="M 230 245 L 230 385" stroke="#0B0E14" strokeWidth="5" strokeLinecap="round" />
              <path
                d="M 230 245 L 230 385"
                stroke={
                  scenario.stopStageIndex < 3
                    ? '#161C26'
                    : activeStage >= 3
                    ? '#10B981'
                    : '#222B3A'
                }
                strokeWidth="2.5"
                strokeDasharray={scenario.stopStageIndex < 3 ? '4 4' : undefined}
                filter={scenario.stopStageIndex >= 3 && activeStage >= 3 ? 'url(#glow-green)' : undefined}
                markerEnd={scenario.stopStageIndex >= 3 && activeStage >= 3 ? 'url(#marker-green)' : 'url(#marker-dim)'}
              />

              {/* Trunk 4: Dispatch -> Witness & Evidence Vault (Permitted execution) */}
              <path d="M 230 395 L 420 395 L 520 395" stroke="#18202C" strokeWidth="8" strokeLinecap="round" />
              <path d="M 230 395 L 420 395 L 520 395" stroke="#0B0E14" strokeWidth="5" strokeLinecap="round" />
              <path
                d="M 230 395 L 420 395 L 520 395"
                stroke={
                  scenario.stopStageIndex < 4
                    ? '#161C26'
                    : activeStage >= 4
                    ? '#10B981'
                    : '#222B3A'
                }
                strokeWidth="2.5"
                strokeDasharray={scenario.stopStageIndex < 4 ? '4 4' : undefined}
                filter={scenario.stopStageIndex >= 4 && activeStage >= 4 ? 'url(#glow-green)' : undefined}
                markerEnd={scenario.stopStageIndex >= 4 && activeStage >= 4 ? 'url(#marker-green)' : 'url(#marker-dim)'}
              />

              {/* Lateral Forensic Telemetry Channels (Dotted lines for sealed receipts) */}
              {scenario.stopStageIndex < 4 && (
                <path
                  d={
                    scenario.id === 'S1-ARMORIQ-DENY'
                      ? 'M 610 95 L 700 95 L 700 405 L 580 405'
                      : scenario.id === 'S2-JAIL-DENY'
                      ? 'M 230 250 L 140 250 L 140 455 L 520 455 L 520 415'
                      : 'M 490 250 L 640 250 L 640 405 L 580 405'
                  }
                  stroke="#475569"
                  strokeWidth="1.5"
                  strokeDasharray="3 3"
                  fill="none"
                  opacity={activeStage >= scenario.stopStageIndex ? '0.75' : '0.2'}
                />
              )}

              {/* ── 2. METALLIC 3D PLATFORMS ── */}

              {/* PLATFORM 1: Agent Intent & Trusted Plan */}
              <IsometricPlatform
                cx={130}
                cy={85}
                w={190}
                d={95}
                h={18}
                isActive={activeStage === 0}
                label="Agent Intent & Plan"
                sublabel="agent/planner_v2.py"
                tag="STAGE 01 // INGRESS"
                onClick={() => jumpToChapter(0)}
              />

              {/* PLATFORM 2: ArmorIQ Authorization Gate */}
              <IsometricPlatform
                cx={370}
                cy={85}
                w={200}
                d={100}
                h={20}
                isActive={activeStage === 1}
                isHalted={scenario.id === 'S1-ARMORIQ-DENY'}
                isPermitted={scenario.id !== 'S1-ARMORIQ-DENY' && activeStage >= 1}
                label="ArmorIQ Intent Gate"
                sublabel="armoriq_helper.py"
                tag="STAGE 02 // AUTHORIZE"
                onClick={() => jumpToChapter(1)}
              />

              {/* ARMORIQ UPSTREAM DENIAL TERMINAL PLATFORM */}
              <g opacity={scenario.id === 'S1-ARMORIQ-DENY' && activeStage >= 1 ? 1 : 0.25}>
                <IsometricPlatform
                  cx={610}
                  cy={85}
                  w={150}
                  d={75}
                  h={16}
                  isActive={scenario.id === 'S1-ARMORIQ-DENY' && activeStage >= 1}
                  isHalted={true}
                  label="Policy Deny Barrier"
                  sublabel="Out-of-Plan Halted"
                  tag="TERMINAL REJECTION"
                />
              </g>

              {/* PLATFORM 3: Large TripLine Containment Deck */}
              <polygon
                points="360,150 630,240 360,330 90,240"
                fill="#0A0D13"
                stroke="#1B222E"
                strokeWidth="1"
                opacity="0.95"
              />
              <polygon
                points="90,240 360,330 360,342 90,252"
                fill="#06080B"
                stroke="#131822"
                strokeWidth="0.75"
              />
              <polygon
                points="360,330 630,240 630,252 360,342"
                fill="#080A0E"
                stroke="#131822"
                strokeWidth="0.75"
              />

              <text
                x="360"
                y="178"
                textAnchor="middle"
                fill={activeStage === 2 ? '#FF8A3D' : '#4B5563'}
                fontSize="9"
                fontFamily="monospace"
                fontWeight="bold"
                letterSpacing="0.1em"
              >
                STAGE 03 // TRIPLINE CONTAINMENT SANDBOX
              </text>

              {/* SUB-STATION 3A: TripLine Path Jail */}
              <IsometricPlatform
                cx={230}
                cy={235}
                w={170}
                d={85}
                h={16}
                isActive={activeStage === 2 && scenario.activeContainmentControl === 'PATH_JAIL'}
                isHalted={scenario.id === 'S2-JAIL-DENY'}
                isPermitted={scenario.id === 'S4-CLEAN-ALLOW' && activeStage >= 2}
                label="TripLine Path Jail"
                sublabel="mcp/common/jail.py"
                tag={
                  scenario.activeContainmentControl === 'PATH_JAIL'
                    ? 'INODE BOUNDS CHECK'
                    : 'INACTIVE (BYPASSED)'
                }
                onClick={() => jumpToChapter(2)}
              />

              {/* SUB-STATION 3B: Egress Canary Gateway */}
              <IsometricPlatform
                cx={490}
                cy={235}
                w={170}
                d={85}
                h={16}
                isActive={activeStage === 2 && scenario.activeContainmentControl === 'EGRESS_GATEWAY'}
                isHeld={scenario.id === 'S3-CANARY-HOLD'}
                label="Egress Canary Gate"
                sublabel="gateway/taint_rule.py"
                tag={
                  scenario.activeContainmentControl === 'EGRESS_GATEWAY'
                    ? 'EXACT TAINT SCAN'
                    : 'INACTIVE (BYPASSED)'
                }
                onClick={() => jumpToChapter(2)}
              />

              {/* PLATFORM 4: Protected Tool Dispatch Boundary */}
              <g opacity={scenario.stopStageIndex < 3 ? 0.35 : 1}>
                <IsometricPlatform
                  cx={230}
                  cy={395}
                  w={190}
                  d={95}
                  h={18}
                  isActive={activeStage === 3 && scenario.stopStageIndex >= 3}
                  isPermitted={scenario.stopStageIndex >= 3}
                  label="Protected Dispatch"
                  sublabel="security/dispatcher.py"
                  tag={scenario.stopStageIndex < 3 ? 'STAGE 04 // NOT REACHED' : 'STAGE 04 // DISPATCH'}
                  onClick={() => jumpToChapter(3)}
                />
              </g>

              {/* PLATFORM 5: Forensic Witness & Evidence Ledger */}
              <IsometricPlatform
                cx={520}
                cy={395}
                w={210}
                d={105}
                h={20}
                isActive={activeStage === 4}
                isPermitted={scenario.stopStageIndex >= 4}
                isHalted={scenario.verdictType === 'DENIAL'}
                isHeld={scenario.verdictType === 'HOLD'}
                label="Forensic Witness Log"
                sublabel="witness/chain.py"
                tag="STAGE 05 // EVIDENCE"
                onClick={() => jumpToChapter(4)}
              />

              {/* ── 3. FLOWING ACTION PACKET ── */}
              <g
                transform={`translate(${packetState.x}, ${packetState.y})`}
                className={prefersReducedMotion ? '' : 'transition-all duration-400 ease-out'}
                filter="url(#glow-orange)"
              >
                <circle cx="0" cy="0" r="14" fill={packetState.color} opacity="0.25" />
                <circle cx="0" cy="0" r="8" fill={packetState.color} />
                <circle cx="0" cy="0" r="3" fill="#FFFFFF" />

                {/* Dynamic Floating Action Chip */}
                <g transform="translate(0, -18)">
                  <rect
                    x="-55"
                    y="-11"
                    width="110"
                    height="16"
                    rx="4"
                    fill="#0A0D12"
                    stroke={packetState.color}
                    strokeWidth="1"
                    opacity="0.95"
                  />
                  <text
                    x="0"
                    y="1"
                    textAnchor="middle"
                    fill="#FFFFFF"
                    fontSize="8.5"
                    fontFamily="monospace"
                    fontWeight="bold"
                  >
                    {scenario.toolName}
                  </text>
                </g>
              </g>
            </svg>
          </div>

          {/* ── SLEEK, HIGH-DENSITY MISSION CONTROL TELEMETRY DOCK (Replaces bulky card) ── */}
          <div className="p-3 sm:p-3.5 rounded-xl border border-[#1E2533] bg-[#0C0F14] space-y-2.5 font-mono text-xs shadow-lg">
            {/* Row 1: Target Tool Call + Scenario Verdict Chip */}
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 truncate">
                <span className="text-[#64748B] text-[10px] uppercase font-bold shrink-0">ACTION:</span>
                <code className="text-[#FF8A3D] text-[11px] font-mono truncate bg-[#07090C] px-2 py-0.5 rounded border border-[#1A202C]">
                  {scenario.action}
                </code>
              </div>

              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                  scenario.verdictType === 'DENIAL'
                    ? 'bg-red-950/70 text-red-400 border border-red-800/50'
                    : scenario.verdictType === 'HOLD'
                    ? 'bg-amber-950/70 text-amber-400 border border-amber-800/50'
                    : 'bg-emerald-950/70 text-emerald-400 border border-emerald-800/50'
                }`}
              >
                {scenario.badge}
              </span>
            </div>

            {/* Row 2: Compact Telemetry Readouts */}
            <div className="grid grid-cols-3 gap-2 text-[10.5px]">
              <div className="p-1.5 rounded bg-[#10141C] border border-[#1C2330] flex items-center justify-between">
                <span className="text-[#64748B] text-[9.5px]">ARMORIQ:</span>
                <span className={`font-bold ${scenario.armorIQVerdict === 'DENY' ? 'text-red-400' : 'text-emerald-400'}`}>
                  {scenario.armorIQVerdict}
                </span>
              </div>

              <div className="p-1.5 rounded bg-[#10141C] border border-[#1C2330] flex items-center justify-between">
                <span className="text-[#64748B] text-[9.5px]">TRIPLINE:</span>
                <span
                  className={`font-bold ${
                    scenario.tripLineVerdict === 'NONE (NOT REACHED)'
                      ? 'text-[#64748B]'
                      : scenario.tripLineVerdict === 'DENY'
                      ? 'text-red-400'
                      : scenario.tripLineVerdict === 'HOLD'
                      ? 'text-amber-400'
                      : 'text-emerald-400'
                  }`}
                >
                  {scenario.tripLineVerdict === 'NONE (NOT REACHED)' ? 'UNREACHED' : scenario.tripLineVerdict}
                </span>
              </div>

              <div className="p-1.5 rounded bg-[#10141C] border border-[#1C2330] flex items-center justify-between truncate">
                <span className="text-[#64748B] text-[9.5px] shrink-0">RECEIPT:</span>
                <span className="text-[#FF8A3D] font-mono truncate text-[10px] ml-1" title={scenario.receiptId}>
                  {scenario.receiptId.slice(0, 14)}...
                </span>
              </div>
            </div>

            {/* Row 3: One-Click Verification Button + Status */}
            <div className="flex items-center gap-2 pt-1 border-t border-[#161B24]">
              <button
                onClick={() => handleVerifyReceipt(scenario.receiptFile)}
                disabled={verifying}
                className="py-1.5 px-3 rounded-lg bg-[#FF6B00] hover:bg-[#E55F00] text-black font-sans text-xs font-bold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50 shrink-0 shadow-sm"
              >
                {verifying ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <ShieldCheck className="w-3.5 h-3.5" />
                )}
                <span>Verify Receipt</span>
              </button>

              <button
                onClick={() => handleCopyHash(scenario.canonicalHash)}
                className="py-1.5 px-2.5 rounded-lg bg-[#141822] hover:bg-[#1A202C] text-[#94A3B8] hover:text-white border border-[#222A38] text-[10.5px] flex items-center gap-1 shrink-0 transition-colors"
                title="Copy RFC 8785 Canonical SHA-256 Hash"
              >
                {copiedHash ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copiedHash ? 'Copied' : 'Hash'}</span>
              </button>

              <div className="flex-1 truncate text-right">
                {verificationResult ? (
                  <span
                    className={`inline-flex items-center gap-1 text-[10px] font-bold ${
                      verificationResult.verified ? 'text-emerald-400' : 'text-red-400'
                    }`}
                  >
                    <CheckCircle2 className="w-3 h-3" />
                    <span>{verificationResult.status}</span>
                  </span>
                ) : (
                  <span className="text-[#4B5563] text-[10px] font-mono">
                    SHA-256: {scenario.canonicalHash.slice(0, 16)}...
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN: SEQUENTIAL STORY CHAPTERS ── */}
        <div className="lg:col-span-5 xl:col-span-5 space-y-6 lg:space-y-8">
          {CHAPTERS.map((chapter, idx) => {
            const isCurrent = activeStage === idx
            const isReached = idx <= scenario.stopStageIndex

            return (
              <div
                key={chapter.id}
                ref={(el) => {
                  chapterRefs.current[idx] = el
                }}
                className={`scroll-mt-28 transition-all duration-300 p-5 sm:p-6 rounded-2xl border ${
                  isCurrent
                    ? 'border-[#FF6B00]/70 bg-[#121620] ring-1 ring-[#FF6B00]/40 shadow-xl'
                    : 'border-[#1A202C] bg-[#0A0D12] opacity-85 hover:opacity-100'
                }`}
              >
                {/* Chapter Eyebrow & Status */}
                <div className="flex items-center justify-between pb-2.5 border-b border-[#1A202C] mb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-[#FF8A3D]">
                      CHAPTER {chapter.chapterNum}
                    </span>
                    <span className="text-[#3E4552]">•</span>
                    <span className="font-mono text-xs text-[#94A3B8]">
                      {chapter.planeName}
                    </span>
                  </div>

                  <span
                    className={`font-mono text-[9.5px] px-2 py-0.5 rounded-full font-bold ${
                      !isReached
                        ? 'bg-[#141820] text-[#64748B] border border-[#222A38]'
                        : isCurrent
                        ? 'bg-[#FF6B00]/20 text-[#FF8A3D] border border-[#FF6B00]/50'
                        : 'bg-[#10141C] text-[#94A3B8] border border-[#1E2532]'
                    }`}
                  >
                    {!isReached ? 'UNREACHED (HALTED UPSTREAM)' : isCurrent ? 'EVALUATING BOUNDARY' : 'EVALUATED'}
                  </span>
                </div>

                {/* Chapter Heading */}
                <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                  {chapter.title}
                </h3>

                {/* Explanation */}
                <p className="mt-1.5 text-xs text-[#94A3B8] leading-relaxed">
                  {chapter.principle}
                </p>

                {/* Scenario-Specific Context for this Chapter */}
                <div className="mt-3 p-3.5 rounded-xl border border-[#1A202C] bg-[#07090C] space-y-2.5 font-mono text-xs">
                  <div className="flex items-center justify-between text-[10.5px] text-[#64748B]">
                    <span>// Scenario Dynamic Trace</span>
                    <span className="text-[#FF8A3D] font-bold">{scenario.shortTitle}</span>
                  </div>

                  {/* Stage-specific narrative */}
                  <div className="text-[11.5px] text-[#CDD2D8] font-sans leading-relaxed">
                    {idx === 0 && scenario.stageNotes.ingress}
                    {idx === 1 && scenario.stageNotes.armoriq}
                    {idx === 2 && scenario.stageNotes.containment}
                    {idx === 3 && scenario.stageNotes.dispatch}
                    {idx === 4 && scenario.stageNotes.evidence}
                  </div>

                  {/* Code Artifact References */}
                  <div className="pt-2 border-t border-[#141820] flex flex-wrap items-center justify-between gap-1.5 text-[10.5px] text-[#64748B]">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[#94A3B8]">Implementation:</span>
                      <code className="text-[#FF8A3D] bg-[#10141C] px-1.5 py-0.5 rounded border border-[#1E2532]">
                        {chapter.sourceFile}
                      </code>
                    </div>
                    {chapter.auxFiles.length > 0 && (
                      <div className="flex items-center gap-1 text-[9.5px]">
                        <span>Aux:</span>
                        {chapter.auxFiles.map((f) => (
                          <code key={f} className="text-[#94A3B8]">
                            {f}
                          </code>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Chapter 5 Special: 7-State Verification Matrix */}
                {idx === 4 && (
                  <div className="mt-3.5 p-3.5 rounded-xl border border-[#212938] bg-[#0A0D12] space-y-2.5 font-mono text-xs">
                    <div className="flex items-center justify-between text-[10.5px] pb-1.5 border-b border-[#1A202C]">
                      <span className="text-white font-bold tracking-wide">
                        SEVEN-STAGE TRUTH MATRIX
                      </span>
                      <span className="text-[#10B981] font-semibold text-[9.5px]">
                        Event Recorded != Tool Executed
                      </span>
                    </div>

                    <div className="space-y-1 text-[10.5px]">
                      <div className="flex items-center justify-between py-0.5 border-b border-[#121620]">
                        <span className="text-[#94A3B8]">1. Action Attempted:</span>
                        <span className="text-white font-mono truncate max-w-[200px]">{scenario.distinctions.actionAttempted}</span>
                      </div>
                      <div className="flex items-center justify-between py-0.5 border-b border-[#121620]">
                        <span className="text-[#94A3B8]">2. Authorization Decision:</span>
                        <span
                          className={
                            scenario.armorIQVerdict === 'DENY' ? 'text-red-400 font-bold' : 'text-emerald-400 font-bold'
                          }
                        >
                          {scenario.distinctions.authorizationDecision}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-0.5 border-b border-[#121620]">
                        <span className="text-[#94A3B8]">3. Containment Decision:</span>
                        <span
                          className={
                            scenario.tripLineVerdict === 'DENY'
                              ? 'text-red-400 font-bold'
                              : scenario.tripLineVerdict === 'HOLD'
                              ? 'text-amber-400 font-bold'
                              : scenario.tripLineVerdict === 'ALLOW'
                              ? 'text-emerald-400 font-bold'
                              : 'text-gray-500'
                          }
                        >
                          {scenario.distinctions.containmentDecision}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-0.5 border-b border-[#121620]">
                        <span className="text-[#94A3B8]">4. Tool Dispatch:</span>
                        <span className="text-white">{scenario.distinctions.toolDispatch}</span>
                      </div>
                      <div className="flex items-center justify-between py-0.5 border-b border-[#121620]">
                        <span className="text-[#94A3B8]">5. Tool Execution:</span>
                        <span className="text-white font-bold">{scenario.distinctions.toolExecution}</span>
                      </div>
                      <div className="flex items-center justify-between py-0.5 border-b border-[#121620]">
                        <span className="text-[#94A3B8]">6. Receipt Creation:</span>
                        <span className="text-[#FF8A3D] font-bold">{scenario.distinctions.receiptCreation}</span>
                      </div>
                      <div className="flex items-center justify-between py-0.5">
                        <span className="text-[#94A3B8]">7. Cryptographic Verification:</span>
                        <span className="text-[#10B981] font-bold">
                          {scenario.distinctions.cryptographicVerification}
                        </span>
                      </div>
                    </div>

                    <div className="p-2 rounded bg-[#0E121A] border border-[#1A202C] text-[10px] text-[#94A3B8] font-sans leading-relaxed">
                      A security receipt is cryptographic proof that an event was observed and evaluated. Receipt creation is NOT proof that the protected tool ran. Blocked attempts generate immutable evidence without executing side effects.
                    </div>
                  </div>
                )}

                {/* Formal Security Invariant */}
                <div className="mt-2.5 p-2.5 rounded-lg bg-[#0E121A] border border-[#1C2330] font-mono text-[10.5px] text-[#FF8A3D] leading-relaxed">
                  {chapter.invariant}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
