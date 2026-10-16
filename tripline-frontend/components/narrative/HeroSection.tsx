'use client'

import React from 'react'
import { Button } from '../ui/Button'
import { StatRow, StatItem } from '../ui/StatRow'
import { HeroIntercept } from '../diagrams/HeroIntercept'
import { ShieldCheck, Terminal } from 'lucide-react'

export interface HeroSectionProps {
  stats: {
    recorded_runs: number
    signed_receipts: number
    jail_probes: string
    protection_rate: string
  }
  primaryReceipt?: any
  source?: string
}

export function HeroSection({
  stats,
  primaryReceipt,
  source = 'results/phase3/scenario/',
}: HeroSectionProps) {
  const statItems: StatItem[] = [
    {
      label: 'RECORDED RUNS',
      value: stats.recorded_runs,
      sublabel: 'Phase 3 multi-layer execution',
      source: 'results/phase3/scenario/',
    },
    {
      label: 'SIGNED RECEIPTS',
      value: stats.signed_receipts,
      sublabel: 'HMAC-SHA256 offline sealed',
      source: 'results/phase3/scenario/*.json',
    },
    {
      label: 'JAIL PROBES',
      value: stats.jail_probes,
      sublabel: '0 bytes leaked across 8 vectors',
      source: 'scripts/jail_burst.py',
    },
    {
      label: 'PROTECTION RATE',
      value: stats.protection_rate,
      sublabel: '3/3 adversarial attacks halted',
      source: 'results/phase3/measured/summary.md',
    },
  ]

  return (
    <section className="relative w-full bg-[#0B0B0C] text-[#F3F1EA] border-b border-[var(--border-dark)] overflow-hidden pt-12 pb-16 md:pt-16 md:pb-24">
      {/* Subtle 48px technical grid background at 4% opacity */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.04]"
        style={{
          backgroundImage:
            'linear-gradient(to right, #F3F1EA 1px, transparent 1px), linear-gradient(to bottom, #F3F1EA 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
        aria-hidden="true"
      />

      <div className="relative max-w-[1200px] mx-auto px-4 sm:px-6 w-full">
        {/* 12-column grid: 5 cols text + 7 cols diagram stage */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-8 items-center mb-16">
          {/* Left Column: 5 columns */}
          <div className="lg:col-span-5 flex flex-col justify-center">
            {/* Eyebrow */}
            <div className="font-mono text-xs uppercase tracking-[0.12em] font-medium text-[var(--text-muted-on-dark)] mb-4">
              // FORENSIC EVIDENCE FOR AI AGENT ACTIONS
            </div>

            {/* Headline Display XL */}
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-[68px] font-bold leading-[0.96] tracking-[-0.04em] text-white mb-6">
              Blocked isn&apos;t{' '}
              <span className="text-[var(--accent)]">evidence.</span>
            </h1>

            {/* Subheadline Body L (max 62ch) */}
            <p className="text-base sm:text-lg md:text-xl leading-[1.55] font-normal text-[var(--text-muted-on-dark)] max-w-[62ch] mb-8">
              A denial is a verdict, not a record. Tripline turns every denied or held agent action into a signed receipt anyone can verify offline.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap gap-4 items-center">
              <Button
                variant="primary"
                href="/receipts"
                size="md"
                icon={<ShieldCheck className="w-4 h-4" />}
              >
                Inspect receipts
              </Button>
              <Button
                variant="secondary"
                href="/console"
                size="md"
                icon={<Terminal className="w-4 h-4" />}
              >
                Run open console
              </Button>
            </div>
          </div>

          {/* Right Column: 7 columns D1 stage */}
          <div className="lg:col-span-7">
            <HeroIntercept receipt={primaryReceipt} />
          </div>
        </div>

        {/* Below fold: StatRow of real counts */}
        <div className="pt-4">
          <StatRow stats={statItems} source={source} tone="dark" />
        </div>
      </div>
    </section>
  )
}
