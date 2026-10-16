'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Badge, StatusPill } from '../ui/Badge'
import { SourceCaption } from '../ui/SourceCaption'
import { ShieldCheck, ArrowDown, FileText, CheckCircle2, Lock, AlertTriangle } from 'lucide-react'

export function PinnedDispatchScene() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [activeStep, setActiveStep] = useState<number>(0)
  const [isMobile, setIsMobile] = useState(false)

  const steps = [
    {
      num: 'A',
      title: 'Agent Proposes Action',
      headline: 'Autonomous LLM tool call initiated',
      desc: 'The triage agent parses an adversarial inbound issue (issue-302) and emits a tool invocation: delete_branch("stale/old-experiment").',
      source: 'results/phase3/scenario/phase3-wow-ca5dcec9.jsonl',
      state: 'evaluating' as const,
      stateLabel: 'TOOL PROPOSED',
    },
    {
      num: 'B',
      title: 'ArmorIQ Plan & Token Check',
      headline: 'Platform intent boundary evaluation',
      desc: 'ArmorIQ evaluates the tool against the active agent allowlist policy (cli-tripline-maintainer-tripline-mcp). The requested tool is not permitted.',
      source: 'docs/phase2_report.md & scripts/armoriq_proof.py',
      state: 'evaluating' as const,
      stateLabel: 'POLICY EVALUATING',
    },
    {
      num: 'C',
      title: 'Tripline Interception Boundary',
      headline: 'Multi-layer containment check',
      desc: 'Action delete_branch is halted upstream before touching Tripline MCP servers. For allowed tools like read_file, Tripline checks descriptors via fstat.',
      source: 'docs/phase3_layer_attribution.md Sec. 1',
      state: 'deny' as const,
      stateLabel: 'HALTED UPSTREAM',
    },
    {
      num: 'D',
      title: 'Verdict State Transition',
      headline: 'Cryptographic decision sealed',
      desc: 'ArmorIQ records DENY. Tripline records NONE (NOT REACHED). The attempted action is permanently denied with 0 side-effects.',
      source: 'results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json',
      state: 'deny' as const,
      stateLabel: 'DENIED (ARMORIQ)',
    },
    {
      num: 'E',
      title: 'Witness Ledger Append',
      headline: 'Append-only HMAC hash chain binding',
      desc: 'The MCP middleware records the event into .tripline/witness/repo-mcp.jsonl, proving 0 executions occurred on repository state.',
      source: '.tripline/witness/repo-mcp.jsonl',
      state: 'verified' as const,
      stateLabel: 'WITNESS ATTESTED',
    },
    {
      num: 'F',
      title: 'Forensic Receipt Sealed',
      headline: 'Canonical JSON SHA-256 + HMAC-SHA256',
      desc: 'An Incident Receipt is minted and signed with the local witness key. Any 1-byte tamper in covered fields invalidates verification.',
      source: 'receipts/verify.py & results/phase3/scenario/*.json',
      state: 'verified' as const,
      stateLabel: 'OFFLINE VERIFIED',
    },
  ]

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)

    const handleScroll = () => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const totalScrollable = rect.height - window.innerHeight
      if (totalScrollable <= 0) return

      const progress = Math.min(Math.max(-rect.top / totalScrollable, 0), 1)
      const stepIndex = Math.min(
        Math.floor(progress * steps.length),
        steps.length - 1
      )
      setActiveStep(stepIndex)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      window.removeEventListener('resize', checkMobile)
      window.removeEventListener('scroll', handleScroll)
    }
  }, [steps.length])

  const current = steps[activeStep]

  // If mobile, render simple stacked reveal steps per specification
  if (isMobile) {
    return (
      <div className="w-full space-y-6">
        <div className="font-mono text-xs text-[var(--text-muted-on-light)] uppercase tracking-wider mb-2">
          // SCROLL-DRIVEN INTERCEPTION STORY (STACKED VIEW)
        </div>
        <h2 className="text-3xl font-bold tracking-tight text-[var(--text-on-light)] mb-6">
          The Agent Acts, Interception, Verdict, Evidence.
        </h2>

        {steps.map((step) => (
          <div
            key={step.num}
            className="p-5 rounded-[4px] border border-[var(--border-light)] bg-[var(--surface-light)]"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-xs font-bold text-[var(--accent)]">
                STEP {step.num}
              </span>
              <StatusPill state={step.state} label={step.stateLabel} />
            </div>
            <h3 className="font-mono text-sm font-semibold text-[var(--text-on-light)] mb-1">
              {step.headline}
            </h3>
            <p className="text-xs text-[var(--text-muted-on-light)] leading-relaxed mb-3">
              {step.desc}
            </p>
            <SourceCaption source={step.source} />
          </div>
        ))}
      </div>
    )
  }

  // Desktop Pinned Sticky Scene: 320vh wrapper with sticky inner stage
  return (
    <div
      ref={containerRef}
      className="relative w-full"
      style={{ height: '320vh' }}
      data-testid="pinned-dispatch-scene"
    >
      <div className="sticky top-20 h-[calc(100vh-100px)] flex flex-col justify-center">
        {/* Header */}
        <div className="mb-6">
          <div className="font-mono text-xs text-[var(--text-muted-on-light)] uppercase tracking-wider mb-2">
            // STEP-BY-STEP FORENSIC STORY
          </div>
          <h2 className="text-4xl font-bold tracking-tight text-[var(--text-on-light)]">
            The Agent Acts, Interception, Verdict, Evidence.
          </h2>
        </div>

        {/* 2-column layout: Left caption rail (swapping per step) + Right interactive visual stage */}
        <div className="grid grid-cols-12 gap-8 items-center bg-white border border-[var(--border-light)] rounded-[4px] p-8 shadow-sm">
          {/* Left caption rail: 5 columns */}
          <div className="col-span-5 flex flex-col justify-between h-full min-h-[340px]">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <span className="w-7 h-7 rounded-[2px] bg-[var(--accent)] text-[#0B0B0C] font-mono text-xs font-bold flex items-center justify-center">
                  {current.num}
                </span>
                <span className="font-mono text-xs uppercase tracking-wider text-[var(--text-muted-on-light)]">
                  {current.title}
                </span>
                <StatusPill state={current.state} label={current.stateLabel} />
              </div>

              <h3 className="font-sans text-2xl font-bold text-[var(--text-on-light)] mb-3 leading-tight">
                {current.headline}
              </h3>

              <p className="text-sm text-[var(--text-muted-on-light)] leading-relaxed mb-6">
                {current.desc}
              </p>
            </div>

            <div className="pt-4 border-t border-[var(--border-light)]">
              <SourceCaption source={current.source} />
              <div className="mt-2 flex items-center gap-1.5 font-mono text-[11px] text-[var(--text-faint-on-light)]">
                <span>Scroll progress: Step {activeStep + 1} of {steps.length}</span>
              </div>
            </div>
          </div>

          {/* Right stage: 7 columns visual state monitor */}
          <div className="col-span-7 bg-[#0E0E12] rounded-[4px] border border-[var(--border-dark)] p-6 text-[#F3F1EA] font-mono text-xs">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[var(--border-dark)]">
              <span className="text-[var(--text-muted-on-dark)] uppercase">
                // FORENSIC LIFECYCLE MONITOR
              </span>
              <span className="text-emerald-400 font-semibold">
                ● LIVE STATE: STEP {current.num}
              </span>
            </div>

            {/* Stepper Progress Indicator */}
            <div className="grid grid-cols-6 gap-2 mb-6">
              {steps.map((st, idx) => (
                <div
                  key={st.num}
                  className={`h-2 rounded-[1px] transition-all duration-300 ${
                    idx <= activeStep ? 'bg-[var(--accent)]' : 'bg-[#2A2A2E]'
                  }`}
                  title={`Step ${st.num}: ${st.title}`}
                />
              ))}
            </div>

            {/* Active Trace Box */}
            <div className="p-4 rounded-[2px] bg-[#070709] border border-[#2A2A2E] space-y-2 mb-4">
              <div className="text-[var(--text-faint-on-dark)]">
                $ target: delete_branch(&quot;stale/old-experiment&quot;)
              </div>
              <div className="text-white font-semibold">
                &gt; {current.title.toUpperCase()}
              </div>
              <div className="text-[var(--text-muted-on-dark)]">
                &gt; Status: {current.stateLabel}
              </div>
              {activeStep >= 3 && (
                <div className="text-red-400">
                  &gt; Upstream Block: tool_not_in_allowlist
                </div>
              )}
              {activeStep >= 4 && (
                <div className="text-emerald-400">
                  &gt; Witness Logged: .tripline/witness/repo-mcp.jsonl (0 executions)
                </div>
              )}
              {activeStep >= 5 && (
                <div className="text-blue-300">
                  &gt; Receipt Minted: RCP-phase3-wow-ca5dcec9-call-p1_ (VERIFIED)
                </div>
              )}
            </div>

            {/* Source Callout */}
            <div className="text-[11px] text-[var(--text-faint-on-dark)]">
              // Trace synchronized to active scenario execution run
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
