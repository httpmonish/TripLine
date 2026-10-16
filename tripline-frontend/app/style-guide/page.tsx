'use client'

import React from 'react'
import { Section } from '@/components/ui/Section'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { Button } from '@/components/ui/Button'
import { Badge, StatusPill } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { CodeBlock } from '@/components/ui/CodeBlock'
import { ReceiptCard } from '@/components/ui/ReceiptCard'
import { StatRow } from '@/components/ui/StatRow'
import { EmptyState } from '@/components/ui/EmptyState'

const sampleReceipt = {
  receipt_id: 'RCP-phase3-wow-ca5dcec9-call-p1_delete_branch',
  incident_id: 'INC-2026-0302',
  run_id: 'phase3-wow-ca5dcec9',
  created_at: '2026-10-10T14:32:00Z',
  action: 'delete_branch(stale/old-experiment)',
  layer: 'L0 ArmorIQ Session Policy',
  verdict: 'DENIED',
  canonical_hash: '84d707a125166845b8aaba424c23b3b77b758dad0c2bdbb3d3739e8f8dc449ec',
  receipt_signature: 'eedc5214f6314bf44881a0a785dada909d60312795c4042bd8f073442180dfd7',
  verification_status: 'VERIFIED' as const,
  source_file: 'results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json',
}

const sampleStats = [
  { label: 'Recorded Runs', value: 3, sublabel: 'Phase 3 multi-layer' },
  { label: 'Signed Receipts', value: 5, sublabel: 'Offline verifiable' },
  { label: 'Jail Probes', value: '8/8', sublabel: '0 bytes leaked' },
  { label: 'Protection Rate', value: '100%', sublabel: '3/3 attacks halted' },
]

export default function StyleGuidePage() {
  return (
    <div>
      {/* Dark tone showcase */}
      <Section tone="dark">
        <SectionHeader
          eyebrow="// DESIGN SYSTEM SPECIFICATION"
          title="Dark Section Primitives"
          accentWord="Primitives"
          description="Design tokens, buttons, status pills, cards, code blocks and receipt cards on dark surface (#0B0B0C)."
          tone="dark"
        />

        <div className="space-y-10">
          <div>
            <h3 className="font-mono text-sm uppercase text-[var(--text-muted-on-dark)] mb-4">
              Buttons &amp; Links
            </h3>
            <div className="flex flex-wrap gap-4 items-center">
              <Button variant="primary" data-local="styleguide-btn-1">Inspect Receipts</Button>
              <Button variant="secondary" data-local="styleguide-btn-2">Run Open Console</Button>
              <Button variant="ghost" showArrow data-local="styleguide-btn-3">
                View Evidence Index
              </Button>
            </div>
          </div>

          <div>
            <h3 className="font-mono text-sm uppercase text-[var(--text-muted-on-dark)] mb-4">
              Security State Badges &amp; Status Pills
            </h3>
            <div className="flex flex-wrap gap-3 items-center">
              <Badge state="allow" />
              <Badge state="deny" />
              <Badge state="hold" />
              <Badge state="evaluating" />
              <Badge state="verified" />
              <Badge state="tamper" />
              <Badge state="idle" />
              <StatusPill state="allow" label="L0 ALLOW" />
              <StatusPill state="deny" label="L1 DENIED (PATH_OUTSIDE_ROOT)" />
              <StatusPill state="hold" label="L2 HELD (CANARY_HIT)" />
            </div>
          </div>

          <div>
            <h3 className="font-mono text-sm uppercase text-[var(--text-muted-on-dark)] mb-4">
              Card Variants
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card variant="outlined" source="docs/ARCHITECTURE.md">
                <h4 className="font-semibold text-white mb-2">Outlined Variant</h4>
                <p className="text-sm text-[var(--text-muted-on-dark)]">
                  1px border with transparent background for secondary structural groups.
                </p>
              </Card>

              <Card variant="filled" source="docs/phase3_layer_attribution.md">
                <h4 className="font-semibold text-white mb-2">Filled Surface</h4>
                <p className="text-sm text-[var(--text-muted-on-dark)]">
                  Standard surface background (#141416) with 1px border.
                </p>
              </Card>

              <Card
                variant="ruled-top"
                accentColor="var(--accent)"
                source="results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json"
              >
                <h4 className="font-semibold text-white mb-2">Ruled-Top Variant</h4>
                <p className="text-sm text-[var(--text-muted-on-dark)]">
                  Accent top border highlighting critical stage transition or boundary.
                </p>
              </Card>
            </div>
          </div>

          <div>
            <h3 className="font-mono text-sm uppercase text-[var(--text-muted-on-dark)] mb-4">
              Stat Row (Real Counts Only)
            </h3>
            <StatRow stats={sampleStats} source="results/phase3/scenario/" tone="dark" />
          </div>

          <div>
            <h3 className="font-mono text-sm uppercase text-[var(--text-muted-on-dark)] mb-4">
              Receipt Card
            </h3>
            <ReceiptCard receipt={sampleReceipt} />
          </div>

          <div>
            <h3 className="font-mono text-sm uppercase text-[var(--text-muted-on-dark)] mb-4">
              Code Block with Source Tracking
            </h3>
            <CodeBlock
              code={`make verify FILE=results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json\n[OK] Receipt RCP-phase3-wow-ca5dcec9 verified: VERIFIED\n     Canonical Hash: 84d707a125166845b8aaba424c23b3b77b758dad0c2bdbb3d3739e8f8dc449ec\n     Signature:      eedc5214f6314bf44881a0a785dada909d60312795c4042bd8f073442180dfd7`}
              filename="CLI Terminal Output"
              source="scripts/repo_audit.py"
              highlightLines={[2]}
            />
          </div>
        </div>
      </Section>

      {/* Light tone showcase */}
      <Section tone="light">
        <SectionHeader
          eyebrow="// CONTRAST & ACCESSIBILITY"
          title="Light Section Warm Paper"
          accentWord="Paper"
          description="Warm paper background (#F1EEE6) alternating seamlessly with dark bands. High contrast text (#131313) meeting WCAG AA standards."
          tone="light"
        />

        <div className="space-y-10">
          <div>
            <h3 className="font-mono text-sm uppercase text-[var(--text-muted-on-light)] mb-4">
              Light Primitives &amp; Empty State
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 rounded-[4px] border border-[var(--border-light)] bg-[var(--surface-light)]">
                <span className="font-mono text-xs uppercase text-[var(--text-muted-on-light)] block mb-2">
                  // Forensic Evidence Rule
                </span>
                <p className="text-[var(--text-on-light)] font-medium leading-relaxed">
                  A denial is a verdict, not a record. Tripline turns every denied or held agent action into a signed receipt anyone can verify offline.
                </p>
                <div className="mt-4 flex gap-2">
                  <Badge state="verified" label="OFFLINE VERIFIABLE" />
                  <Badge state="hold" label="EGRESS QUARANTINE" />
                </div>
              </div>

              <EmptyState
                title="No Pending Dispatches"
                description="All actions accounted for in witness ledger. Zero unverified tool invocations detected."
                command="make audit"
                source="results/phase3/scenario/"
              />
            </div>
          </div>

          <div>
            <h3 className="font-mono text-sm uppercase text-[var(--text-muted-on-light)] mb-4">
              Stat Row on Light
            </h3>
            <StatRow stats={sampleStats} source="results/phase3/scenario/" tone="light" />
          </div>
        </div>
      </Section>
    </div>
  )
}
