'use client'

import React from 'react'
import { Section } from '@/components/ui/Section'
import { HeroSection } from '@/components/narrative/HeroSection'
import { GapComparison } from '@/components/narrative/GapComparison'
import { StagesBand } from '@/components/narrative/StagesBand'
import { PinnedDispatchScene } from '@/components/narrative/PinnedDispatchScene'
import { LayerMatrix } from '@/components/diagrams/LayerMatrix'
import { NonRepudiationBand } from '@/components/narrative/NonRepudiationBand'
import { VerificationModules } from '@/components/narrative/VerificationModules'
import { EvidenceIndex } from '@/components/narrative/EvidenceIndex'
import { ClosingCTA } from '@/components/narrative/ClosingCTA'
import { getSummaryStats, getReceipts } from '@/lib/data'

export default function OverviewPage() {
  const stats = getSummaryStats()
  const receipts = getReceipts()
  const primaryReceipt = stats.primary_receipt || receipts[0]

  return (
    <div className="w-full flex flex-col">
      {/* BAND 1: HERO (DARK) */}
      <HeroSection
        stats={{
          recorded_runs: stats.recorded_runs,
          signed_receipts: stats.signed_receipts,
          jail_probes: stats.jail_probes,
          protection_rate: stats.protection_rate,
        }}
        primaryReceipt={primaryReceipt}
        source={stats.source}
      />

      {/* BAND 2: THE GAP (LIGHT) */}
      <Section tone="light" id="gap">
        <GapComparison receipt={primaryReceipt} />
      </Section>

      {/* BAND 3: THREE STAGES (DARK) */}
      <Section tone="dark" id="stages">
        <StagesBand />
      </Section>

      {/* BAND 4: PINNED DISPATCH STORY (LIGHT) */}
      <Section tone="light" id="narrative">
        <PinnedDispatchScene />
      </Section>

      {/* BAND 5: LAYER EXPLORER (DARK) */}
      <Section tone="dark" id="layers">
        <div className="w-full">
          <div className="font-mono text-xs uppercase tracking-[0.12em] text-[var(--text-muted-on-dark)] mb-3">
            // CONTAINMENT BOUNDARIES
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-semibold leading-[1.08] tracking-[-0.025em] text-white mb-8">
            Which layer stopped which <span className="text-[var(--accent)]">attack.</span>
          </h2>
          <LayerMatrix />
        </div>
      </Section>

      {/* BAND 6: NON-REPUDIATION (LIGHT) */}
      <Section tone="light" id="verification">
        <NonRepudiationBand receipt={primaryReceipt} />
      </Section>

      {/* BAND 7: VERIFICATION MODULES (DARK) */}
      <Section tone="dark" id="modules">
        <VerificationModules
          jailProbes={stats.jail_probes}
          witnessRecords={stats.witness_records}
          protectionRate={stats.protection_rate}
        />
      </Section>

      {/* BAND 8: EVIDENCE VIEWS (LIGHT) */}
      <Section tone="light" id="evidence">
        <EvidenceIndex />
      </Section>

      {/* BAND 9: CLOSING CTA (DARK) */}
      <Section tone="dark" isClosing id="closing">
        <ClosingCTA />
      </Section>
    </div>
  )
}
