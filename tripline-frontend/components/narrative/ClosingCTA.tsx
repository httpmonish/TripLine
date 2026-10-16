'use client'

import React from 'react'
import { Button } from '../ui/Button'
import { ShieldCheck, Layers } from 'lucide-react'

export function ClosingCTA({ className = '' }: { className?: string }) {
  return (
    <div
      className={`text-center max-w-3xl mx-auto py-8 ${className}`}
      data-testid="closing-cta"
    >
      <div className="font-mono text-xs uppercase tracking-[0.14em] text-[var(--text-muted-on-dark)] mb-4">
        // FORENSIC CERTAINTY FOR AUTONOMOUS AGENTS
      </div>

      <h2 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-white mb-6 leading-tight">
        ArmorIQ decides.{' '}
        <span className="text-[var(--accent)]">Tripline proves.</span>
      </h2>

      <p className="text-base sm:text-lg text-[var(--text-muted-on-dark)] max-w-xl mx-auto mb-10 leading-relaxed font-normal">
        Turn guardrail verdicts into tamper-evident forensic receipts. Independently verifiable offline with zero external network dependencies.
      </p>

      <div className="flex flex-wrap items-center justify-center gap-4">
        <Button
          variant="primary"
          href="/receipts"
          size="lg"
          icon={<ShieldCheck className="w-4 h-4" />}
        >
          Inspect receipts
        </Button>
        <Button
          variant="secondary"
          href="/layers"
          size="lg"
          icon={<Layers className="w-4 h-4" />}
        >
          View verification suite
        </Button>
      </div>

      <div className="mt-12 text-[11px] font-mono text-[var(--text-faint-on-dark)]">
        // Built for the ArmorIQ Flow State 2026 Hackathon
      </div>
    </div>
  )
}
