'use client'

import React, { useState, useEffect } from 'react'
import { RotateCcw, ShieldCheck, X, Check, Pause, Info } from 'lucide-react'

export interface HeroInterceptProps {
  receipt?: any
  onReplay?: () => void
  className?: string
}

export function HeroIntercept({ receipt, className = '' }: HeroInterceptProps) {
  // Animation stage: 0=init/draw, 1=packet to gate, 2=evaluating, 3=denied, 4=receipt reveal, 5=complete
  const [stage, setStage] = useState<number>(0)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)
    if (mediaQuery.matches) {
      setStage(5)
      return
    }

    const t1 = setTimeout(() => setStage(1), 500)
    const t2 = setTimeout(() => setStage(2), 1400)
    const t3 = setTimeout(() => setStage(3), 2100)
    const t4 = setTimeout(() => setStage(4), 2800)
    const t5 = setTimeout(() => setStage(5), 3600)

    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
      clearTimeout(t3)
      clearTimeout(t4)
      clearTimeout(t5)
    }
  }, [])

  const handleReplay = () => {
    if (prefersReducedMotion) return
    setStage(0)
    setTimeout(() => setStage(1), 300)
    setTimeout(() => setStage(2), 1200)
    setTimeout(() => setStage(3), 1900)
    setTimeout(() => setStage(4), 2600)
    setTimeout(() => setStage(5), 3400)
  }

  // Node metadata for interactive inspection
  const nodeInfo: Record<string, { title: string; role: string; event: string; source: string }> = {
    agent: {
      title: 'Triage Agent (LLM Loop)',
      role: 'Autonomous tool-calling loop parsing untrusted inbound issues.',
      event: 'Proposed action: delete_branch("stale/old-experiment")',
      source: 'results/phase3/scenario/phase3-wow-ca5dcec9.jsonl',
    },
    plan: {
      title: 'Intent Plan + Token',
      role: 'ArmorIQ SDK plan capture boundary: capture_plan(), get_intent_token().',
      event: 'Session plan initialized with registered tool allowlist.',
      source: 'docs/ARCHITECTURE.md',
    },
    gate: {
      title: 'ArmorIQ Policy Gate',
      role: 'Intent-assurance checkpoint evaluating tool permission against active session policy.',
      event: 'VERDICT: DENY (reason: tool_not_in_allowlist). Action never reached MCP.',
      source: 'results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json',
    },
    interceptor: {
      title: 'Tripline Containment',
      role: 'In-MCP path jail (fstat inode verification) and egress canary gate.',
      event: 'Unreached for delete_branch due to upstream platform policy denial.',
      source: 'docs/phase3_layer_attribution.md',
    },
    mcp: {
      title: 'MCP Tools (repo-mcp & issues-mcp)',
      role: 'Protected execution endpoints with local witness recording middleware.',
      event: '0 EXECUTIONS — Verified zero side-effects on local git repository.',
      source: '.tripline/witness/repo-mcp.jsonl',
    },
    receipt: {
      title: 'Signed Incident Receipt',
      role: 'Canonical JSON (RFC 8785) signed with local witness HMAC-SHA256.',
      event: `Receipt ID: ${receipt?.receipt_id || 'RCP-phase3-wow-ca5dcec9-call-p1_'} | VERIFIED`,
      source: receipt?.source_file || 'results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json',
    },
  }

  // Real receipt data bindings
  const receiptId = receipt?.receipt_id || 'RCP-phase3-wow-ca5dcec9-call-p1_'
  const canonicalHash = receipt?.canonical_hash || '84d707a125166845b8aaba424c23b3b77b758dad0c2bdbb3d3739e8f8dc449ec'
  const hashPrefix = canonicalHash.slice(0, 12) + '…'
  const verStatus = receipt?.verification_status || 'VERIFIED'

  // Gate state
  const isEvaluating = stage === 2
  const isDenied = stage >= 3

  return (
    <div
      className={`relative w-full rounded-[4px] border border-[var(--border-dark)] bg-[#0A0A0C] p-4 sm:p-6 overflow-hidden ${className}`}
      data-testid="hero-intercept-diagram"
    >
      {/* Top Diagram Controls */}
      <div className="flex items-center justify-between pb-3 mb-2 border-b border-[var(--border-dark)] text-xs font-mono text-[var(--text-muted-on-dark)]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[var(--accent)]" />
          <span className="uppercase tracking-wider">
            SCENARIO RUN: delete_branch INTERCEPTION
          </span>
        </div>
        <button
          onClick={handleReplay}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[2px] border border-[var(--border-dark)] hover:bg-white/5 text-[var(--text-on-dark)] transition-colors cursor-pointer focus-ring"
          type="button"
          aria-label="Replay interception sequence"
        >
          <RotateCcw className="w-3 h-3" />
          <span>REPLAY</span>
        </button>
      </div>

      {/* SVG Diagram Canvas */}
      <div className="relative w-full overflow-x-auto">
        <svg
          viewBox="0 0 1200 520"
          className="w-full h-auto min-w-[700px] select-none"
          role="img"
          aria-label="Tripline and ArmorIQ Interception Architecture Diagram showing delete_branch blocked at ArmorIQ policy gate and generating signed forensic receipt with 0 MCP executions"
        >
          <defs>
            {/* Arrow marker */}
            <marker
              id="arrowhead"
              markerWidth="8"
              markerHeight="8"
              refX="6"
              refY="4"
              orient="auto"
            >
              <polygon points="0 0, 8 4, 0 8" fill="#4B4B52" />
            </marker>

            {/* Accent arrow marker */}
            <marker
              id="arrowhead-accent"
              markerWidth="8"
              markerHeight="8"
              refX="6"
              refY="4"
              orient="auto"
            >
              <polygon points="0 0, 8 4, 0 8" fill="#FF4F1A" />
            </marker>

            {/* Deny arrow marker */}
            <marker
              id="arrowhead-deny"
              markerWidth="8"
              markerHeight="8"
              refX="6"
              refY="4"
              orient="auto"
            >
              <polygon points="0 0, 8 4, 0 8" fill="#E5484D" />
            </marker>
          </defs>

          {/* Connectors */}
          {/* C1: Agent -> Plan */}
          <line
            x1="160"
            y1="230"
            x2="240"
            y2="230"
            stroke={stage >= 1 ? '#FF4F1A' : '#2A2A2E'}
            strokeWidth="2"
            strokeDasharray={stage === 1 ? '4 6' : undefined}
            markerEnd="url(#arrowhead)"
            className="transition-colors duration-300"
          />

          {/* C2: Plan -> ArmorIQ Gate */}
          <line
            x1="400"
            y1="230"
            x2="480"
            y2="230"
            stroke={stage >= 2 ? (isDenied ? '#E5484D' : '#4C8DFF') : '#2A2A2E'}
            strokeWidth="2"
            markerEnd="url(#arrowhead)"
            className="transition-colors duration-300"
          />

          {/* C3: ArmorIQ Gate -> Tripline Containment */}
          <line
            x1="600"
            y1="230"
            x2="680"
            y2="230"
            stroke="#2A2A2E"
            strokeWidth="1.5"
            strokeDasharray="4 6"
            markerEnd="url(#arrowhead)"
            opacity={isDenied ? '0.25' : '1'}
          />

          {/* C4a: Tripline -> repo-mcp */}
          <path
            d="M 880 230 L 920 230 L 920 150 L 960 150"
            fill="none"
            stroke="#2A2A2E"
            strokeWidth="1.5"
            strokeDasharray="4 6"
            markerEnd="url(#arrowhead)"
            opacity="0.25"
          />

          {/* C4b: Tripline -> issues-mcp */}
          <path
            d="M 880 230 L 920 230 L 920 310 L 960 310"
            fill="none"
            stroke="#2A2A2E"
            strokeWidth="1.5"
            strokeDasharray="4 6"
            markerEnd="url(#arrowhead)"
            opacity="0.25"
          />

          {/* C5: ArmorIQ Gate -> Receipt Node (Dashed on Deny) */}
          <path
            d="M 540 290 L 540 430 L 680 430"
            fill="none"
            stroke={stage >= 4 ? '#E5484D' : '#2A2A2E'}
            strokeWidth="2"
            strokeDasharray="5 5"
            markerEnd={stage >= 4 ? 'url(#arrowhead-deny)' : 'url(#arrowhead)'}
            opacity={stage >= 4 ? '1' : '0.1'}
            className="transition-all duration-500"
          />

          {/* ======================================================== */}
          {/* Node 1: Triage Agent */}
          {/* ======================================================== */}
          <g
            onClick={() => setSelectedNode('agent')}
            className="cursor-pointer focus-ring"
            tabIndex={0}
            role="button"
            aria-label="Node: Triage Agent"
          >
            <rect
              x="20"
              y="190"
              width="140"
              height="80"
              rx="4"
              fill="#141416"
              stroke={selectedNode === 'agent' ? 'var(--accent)' : '#2A2A2E'}
              strokeWidth="1.5"
            />
            <text x="35" y="224" fill="#F3F1EA" fontSize="13" fontWeight="600" fontFamily="monospace">
              Triage Agent
            </text>
            <text x="35" y="246" fill="#9A9AA2" fontSize="11" fontFamily="monospace">
              LLM tool loop
            </text>
          </g>

          {/* ======================================================== */}
          {/* Node 2: Intent Plan + Token */}
          {/* ======================================================== */}
          <g
            onClick={() => setSelectedNode('plan')}
            className="cursor-pointer focus-ring"
            tabIndex={0}
            role="button"
            aria-label="Node: Intent Plan and Token"
          >
            <rect
              x="240"
              y="190"
              width="160"
              height="80"
              rx="4"
              fill="#141416"
              stroke={selectedNode === 'plan' ? 'var(--accent)' : '#2A2A2E'}
              strokeWidth="1.5"
            />
            <text x="255" y="222" fill="#F3F1EA" fontSize="12" fontWeight="600" fontFamily="monospace">
              Plan + Token
            </text>
            <text x="255" y="242" fill="#9A9AA2" fontSize="10" fontFamily="monospace">
              capture_plan()
            </text>
            <text x="255" y="258" fill="#6B6B73" fontSize="9" fontFamily="monospace">
              get_intent_token()
            </text>
          </g>

          {/* ======================================================== */}
          {/* Node 3: ArmorIQ Gate (Diamond / Rounded Rect) */}
          {/* ======================================================== */}
          <g
            onClick={() => setSelectedNode('gate')}
            className="cursor-pointer focus-ring"
            tabIndex={0}
            role="button"
            aria-label="Node: ArmorIQ Policy Gate"
          >
            {isEvaluating ? (
              // Evaluating Diamond Shape
              <polygon
                points="540,170 600,230 540,290 480,230"
                fill="#141416"
                stroke="#4C8DFF"
                strokeWidth="2"
                className="animate-pulse"
              />
            ) : (
              // Standard Rounded Rect
              <rect
                x="470"
                y="180"
                width="140"
                height="100"
                rx="4"
                fill={isDenied ? 'rgba(229, 72, 77, 0.12)' : '#141416'}
                stroke={isDenied ? '#E5484D' : '#2A2A2E'}
                strokeWidth={isDenied ? '2' : '1.5'}
              />
            )}

            <text
              x="540"
              y={isEvaluating ? '226' : '218'}
              textAnchor="middle"
              fill="#F3F1EA"
              fontSize="12"
              fontWeight="600"
              fontFamily="monospace"
            >
              ArmorIQ Gate
            </text>

            <text
              x="540"
              y={isEvaluating ? '242' : '236'}
              textAnchor="middle"
              fill={isDenied ? '#E5484D' : isEvaluating ? '#4C8DFF' : '#9A9AA2'}
              fontSize="11"
              fontWeight="600"
              fontFamily="monospace"
            >
              {isDenied ? 'DENIED' : isEvaluating ? 'EVALUATING' : 'Policy Check'}
            </text>

            {isDenied && (
              <text
                x="540"
                y="256"
                textAnchor="middle"
                fill="#9A9AA2"
                fontSize="9"
                fontFamily="monospace"
              >
                tool_not_in_allowlist
              </text>
            )}
          </g>

          {/* ======================================================== */}
          {/* Node 4: Tripline Interceptor (Downstream Containment) */}
          {/* ======================================================== */}
          <g
            onClick={() => setSelectedNode('interceptor')}
            className="cursor-pointer focus-ring"
            tabIndex={0}
            role="button"
            aria-label="Node: Tripline Containment"
            opacity={isDenied ? '0.35' : '1'}
          >
            <rect
              x="680"
              y="180"
              width="200"
              height="100"
              rx="4"
              fill="#141416"
              stroke="#2A2A2E"
              strokeWidth="1.5"
            />
            <text x="700" y="214" fill="#F3F1EA" fontSize="12" fontWeight="600" fontFamily="monospace">
              Tripline Containment
            </text>
            <text x="700" y="234" fill="#9A9AA2" fontSize="10" fontFamily="monospace">
              L1 Path Jail (fstat check)
            </text>
            <text x="700" y="252" fill="#9A9AA2" fontSize="10" fontFamily="monospace">
              L2 Canary Egress Gate
            </text>
          </g>

          {/* ======================================================== */}
          {/* Node 5: MCP Tools (repo-mcp & issues-mcp) */}
          {/* ======================================================== */}
          <g
            onClick={() => setSelectedNode('mcp')}
            className="cursor-pointer focus-ring"
            tabIndex={0}
            role="button"
            aria-label="Node: MCP Tools"
            opacity={isDenied ? '0.35' : '1'}
          >
            {/* repo-mcp */}
            <rect
              x="960"
              y="110"
              width="180"
              height="70"
              rx="4"
              fill="#141416"
              stroke="#2A2A2E"
              strokeWidth="1.5"
            />
            <text x="980" y="142" fill="#F3F1EA" fontSize="12" fontWeight="600" fontFamily="monospace">
              repo-mcp (:8000)
            </text>
            <text x="980" y="162" fill="#6B6B73" fontSize="10" fontFamily="monospace">
              read, write, delete
            </text>

            {/* issues-mcp */}
            <rect
              x="960"
              y="270"
              width="180"
              height="70"
              rx="4"
              fill="#141416"
              stroke="#2A2A2E"
              strokeWidth="1.5"
            />
            <text x="980" y="302" fill="#F3F1EA" fontSize="12" fontWeight="600" fontFamily="monospace">
              issues-mcp (:8001)
            </text>
            <text x="980" y="322" fill="#6B6B73" fontSize="10" fontFamily="monospace">
              comment, label, read
            </text>

            {/* Zero Executions Callout Banner */}
            {isDenied && (
              <g opacity="1">
                <rect
                  x="960"
                  y="190"
                  width="180"
                  height="40"
                  rx="2"
                  fill="#0B0B0C"
                  stroke="#2FBF71"
                  strokeWidth="1"
                />
                <text
                  x="1050"
                  y="215"
                  textAnchor="middle"
                  fill="#2FBF71"
                  fontSize="11"
                  fontWeight="600"
                  fontFamily="monospace"
                >
                  0 MCP EXECUTIONS
                </text>
              </g>
            )}
          </g>

          {/* ======================================================== */}
          {/* Node 6: Signed Forensic Receipt Node */}
          {/* ======================================================== */}
          <g
            onClick={() => setSelectedNode('receipt')}
            className="cursor-pointer focus-ring"
            tabIndex={0}
            role="button"
            aria-label="Node: Signed Incident Receipt"
            opacity={stage >= 4 ? '1' : '0'}
            className="transition-opacity duration-500"
          >
            <rect
              x="680"
              y="380"
              width="460"
              height="100"
              rx="4"
              fill="#121215"
              stroke="#2A2A2E"
              strokeWidth="1.5"
            />

            {/* Receipt Header */}
            <text x="700" y="410" fill="#F3F1EA" fontSize="12" fontWeight="700" fontFamily="monospace">
              SIGNED INCIDENT RECEIPT
            </text>

            <rect x="910" y="396" width="90" height="20" rx="2" fill="rgba(229, 72, 77, 0.15)" stroke="rgba(229, 72, 77, 0.4)" />
            <text x="955" y="410" textAnchor="middle" fill="#E5484D" fontSize="10" fontWeight="600" fontFamily="monospace">
              DENIED
            </text>

            <rect x="1010" y="396" width="110" height="20" rx="2" fill="rgba(47, 191, 113, 0.15)" stroke="rgba(47, 191, 113, 0.4)" />
            <text x="1065" y="410" textAnchor="middle" fill="#2FBF71" fontSize="10" fontWeight="600" fontFamily="monospace">
              ✓ {verStatus}
            </text>

            {/* Receipt Details */}
            <text x="700" y="438" fill="#9A9AA2" fontSize="11" fontFamily="monospace">
              ID: {receiptId}
            </text>

            <text x="700" y="458" fill="#2FBF71" fontSize="11" fontFamily="monospace">
              SHA-256: {hashPrefix}
            </text>

            <text x="960" y="458" fill="#9A9AA2" fontSize="10" fontFamily="monospace">
              // make verify
            </text>
          </g>

          {/* ======================================================== */}
          {/* Animated Packet */}
          {/* ======================================================== */}
          {stage === 1 && (
            <circle cx="200" cy="230" r="6" fill="#FF4F1A">
              <animate attributeName="cx" from="100" to="520" dur="1s" fill="freeze" />
            </circle>
          )}

          {stage >= 2 && stage < 4 && (
            <g transform="translate(540, 230)">
              <circle cx="0" cy="0" r="7" fill={isDenied ? '#E5484D' : '#4C8DFF'} />
              <circle cx="0" cy="0" r="14" fill="none" stroke={isDenied ? '#E5484D' : '#4C8DFF'} strokeWidth="1.5" opacity="0.6">
                <animate attributeName="r" values="7;18" dur="0.8s" repeatCount="1" />
                <animate attributeName="opacity" values="0.8;0" dur="0.8s" repeatCount="1" />
              </circle>
            </g>
          )}
        </svg>
      </div>

      {/* Interactive Detail Drawer / Callout when a node is selected */}
      {selectedNode && (
        <div className="mt-4 p-4 rounded-[4px] bg-[#141417] border border-[var(--border-dark)] font-mono text-xs flex items-start justify-between gap-4">
          <div>
            <div className="text-white font-semibold flex items-center gap-2 mb-1">
              <Info className="w-3.5 h-3.5 text-[var(--accent)]" />
              <span>{nodeInfo[selectedNode]?.title}</span>
            </div>
            <div className="text-[var(--text-muted-on-dark)] mb-2 leading-relaxed">
              {nodeInfo[selectedNode]?.role}
            </div>
            <div className="text-emerald-400 text-[11px] mb-1">
              &gt; {nodeInfo[selectedNode]?.event}
            </div>
            <div className="text-[var(--text-faint-on-dark)] text-[10px]">
              // source: {nodeInfo[selectedNode]?.source}
            </div>
          </div>
          <button
            onClick={() => setSelectedNode(null)}
            className="p-1 rounded hover:bg-white/10 text-[var(--text-faint-on-dark)] hover:text-white cursor-pointer"
            aria-label="Close details"
            type="button"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Caption rail footer */}
      <div className="mt-3 pt-3 border-t border-[var(--border-dark)] flex items-center justify-between text-[11px] font-mono text-[var(--text-faint-on-dark)]">
        <div>
          // Click any node to inspect role &amp; trace event. Reduced-motion honored.
        </div>
        <div>
          source: results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json
        </div>
      </div>
    </div>
  )
}
