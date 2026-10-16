'use client'

import React from 'react'
import Link from 'next/link'
import { SectionHeader } from '../ui/SectionHeader'
import { Card } from '../ui/Card'
import { ArrowRight, ShieldCheck, Database, BarChart3 } from 'lucide-react'

export interface VerificationModulesProps {
  jailProbes: string
  witnessRecords: number
  protectionRate: string
  className?: string
}

export function VerificationModules({
  jailProbes,
  witnessRecords,
  protectionRate,
  className = '',
}: VerificationModulesProps) {
  const modules = [
    {
      title: 'Jail Burst Probe',
      metric: jailProbes,
      unit: 'probes passed (0 leaked bytes)',
      desc: 'Deterministic path-traversal harness evaluating plain traversal, encoded slashes, and symlinks.',
      href: '/jail-burst',
      icon: ShieldCheck,
      source: 'docs/phase3_layer_attribution.md Sec. 2',
    },
    {
      title: 'Witness Chain Ledger',
      metric: `${witnessRecords} Records`,
      unit: 'HMAC hash-chain attested',
      desc: 'Append-only middleware log (.tripline/witness/) proving exact execution counts and zero untracked state.',
      href: '/witness',
      icon: Database,
      source: '.tripline/witness/repo-mcp.jsonl',
    },
    {
      title: 'Measured Overhead',
      metric: protectionRate,
      unit: 'protection across attacks',
      desc: 'Verified defense rate against adversarial prompt injection, refusal rates, and code footprint growth.',
      href: '/measured',
      icon: BarChart3,
      source: 'results/phase3/measured/summary.md',
    },
  ]

  return (
    <div className={`w-full ${className}`}>
      <SectionHeader
        eyebrow="// VERIFICATION & OBSERVABILITY MODULES"
        title="Explore the Forensic Proof Suite."
        accentWord="Suite."
        description="Inspect raw evidence across containment verification, cryptographic hash chains, and empirical protection measurements."
        tone="dark"
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {modules.map((mod) => {
          const Icon = mod.icon
          return (
            <Link
              key={mod.title}
              href={mod.href}
              className="group block focus-ring rounded-[4px]"
            >
              <Card
                variant="filled"
                source={mod.source}
                className="h-full flex flex-col justify-between border-[var(--border-dark)] group-hover:border-[var(--accent)] transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-8 h-8 rounded-[2px] bg-white/5 flex items-center justify-center text-[var(--accent)]">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="font-mono text-xs text-[var(--accent)] group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                      <span>INSPECT</span>
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>

                  <h3 className="font-mono text-base font-bold text-white mb-2">
                    {mod.title}
                  </h3>

                  <div className="mb-2">
                    <span className="font-mono text-2xl font-bold text-white tracking-tight">
                      {mod.metric}
                    </span>
                    <span className="block text-xs text-emerald-400 font-mono mt-0.5">
                      ✓ {mod.unit}
                    </span>
                  </div>

                  <p className="text-xs text-[var(--text-muted-on-dark)] leading-relaxed">
                    {mod.desc}
                  </p>
                </div>
              </Card>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
