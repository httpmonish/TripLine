'use client'

import React from 'react'
import Link from 'next/link'
import { SectionHeader } from '../ui/SectionHeader'
import { ArrowRight, FileCheck, Terminal, ShieldAlert, Layers, BarChart, Scale } from 'lucide-react'

export function EvidenceIndex({ className = '' }: { className?: string }) {
  const views = [
    {
      title: '// RECEIPTS',
      name: 'Incident Receipts Registry',
      desc: 'Canonical JSON (RFC 8785) signed receipts for all denied or held actions with offline verification.',
      href: '/receipts',
      source: 'results/phase3/scenario/*.json',
      icon: FileCheck,
    },
    {
      title: '// CONSOLE',
      name: 'Agent Execution Trace',
      desc: 'Raw event timeline of the autonomous Claude 3.5 Sonnet loop processing issues 301 to 305.',
      href: '/console',
      source: 'results/demo/events.jsonl',
      icon: Terminal,
    },
    {
      title: '// JAIL BURST',
      name: 'Path Jail Burst Matrix',
      desc: 'Deterministic path-traversal evaluation proving 0 leaked bytes across 8 adversarial encoding vectors.',
      href: '/jail-burst',
      source: 'docs/phase3_layer_attribution.md Sec. 2',
      icon: ShieldAlert,
    },
    {
      title: '// WITNESS',
      name: 'Witness Hash Chain Ledger',
      desc: 'Append-only HMAC chain logs recording exact MCP received, started, and completed states.',
      href: '/witness',
      source: '.tripline/witness/repo-mcp.jsonl',
      icon: Layers,
    },
    {
      title: '// MEASURED',
      name: 'Empirical Overhead & Protection',
      desc: 'Measured protection rate, model refusal rate, and code growth metrics backed by repository files.',
      href: '/measured',
      source: 'results/phase3/measured/summary.md',
      icon: BarChart,
    },
    {
      title: '// CLAIMS & LIMITS',
      name: 'Truth Audit & Known Residuals',
      desc: 'Strict Rule 10 claims verification matrix and explicit acknowledged limits (e.g., exact-match canary).',
      href: '/claims',
      source: 'docs/FINAL_CLAIMS_AUDIT.md',
      icon: Scale,
    },
  ]

  return (
    <div className={`w-full ${className}`}>
      <SectionHeader
        eyebrow="// TRACEABLE EVIDENCE REGISTRY"
        title="Complete Evidence Views Index"
        accentWord="Index"
        description="Every claim in Tripline is backed by recorded files in the repository. Select any view below to inspect raw evidence directly."
        tone="light"
      />

      {/* Ruled list (no card boxes, elegant ruled rows) */}
      <div className="divide-y divide-[var(--border-light)] border-y border-[var(--border-light)]">
        {views.map((v) => {
          const Icon = v.icon
          return (
            <Link
              key={v.title}
              href={v.href}
              className="py-5 px-3 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-black/[0.02] transition-colors focus-ring rounded-[2px] group"
            >
              <div className="flex items-start sm:items-center gap-4">
                <div className="w-8 h-8 rounded-[2px] bg-black/5 flex items-center justify-center text-[var(--text-on-light)] shrink-0">
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs uppercase font-bold text-[var(--accent)]">
                      {v.title}
                    </span>
                    <span className="font-semibold text-sm text-[var(--text-on-light)]">
                      — {v.name}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-muted-on-light)] mt-0.5 max-w-2xl">
                    {v.desc}
                  </p>
                </div>
              </div>

              <div className="shrink-0 flex items-center gap-4">
                <span className="font-mono text-[11px] text-[var(--text-faint-on-light)] hidden md:inline">
                  // {v.source}
                </span>
                <span className="font-mono text-xs text-[var(--text-on-light)] group-hover:translate-x-1 transition-transform flex items-center gap-1 font-semibold">
                  <span>VIEW</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
