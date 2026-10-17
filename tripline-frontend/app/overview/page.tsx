'use client'

import React, { useEffect, useState } from 'react'
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
import { api } from '@/lib/api'

export default function OverviewPage() {
  const initialStats = getSummaryStats()
  const initialReceipts = getReceipts()
  const [stats, setStats] = useState(initialStats)
  const [receipts, setReceipts] = useState<any[]>(initialReceipts)

  useEffect(() => {
    let mounted = true
    Promise.allSettled([api.getSummary(), api.getReceipts()]).then(([sumRes, recRes]) => {
      if (!mounted) return
      if (sumRes.status === 'fulfilled' && sumRes.value) {
        const s = sumRes.value
        setStats(prev => ({
          ...prev,
          recorded_runs: s.total_runs ?? s.runs ?? prev.recorded_runs,
          signed_receipts: s.total_receipts ?? s.receipts ?? prev.signed_receipts,
          witness_records: s.witness_records ?? prev.witness_records,
          jail_probes: s.probes_total ? `${s.probes_passed}/${s.probes_total}` : prev.jail_probes,
          source: 'Live API /api/summary'
        }))
      }
      if (recRes.status === 'fulfilled' && recRes.value && recRes.value.length > 0) {
        const first = recRes.value[0]
        api.getReceipt(first.receipt_id).then(full => {
          if (!mounted) return
          setReceipts(prev => [full, ...prev.slice(1)])
        }).catch(() => {})
      }
    })
    return () => { mounted = false }
  }, [])

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
