'use client'

import React from 'react'
import { SectionHeader } from '../ui/SectionHeader'
import { Card } from '../ui/Card'
import { CheckpointPipeline } from '../diagrams/CheckpointPipeline'

export function StagesBand({ className = '' }: { className?: string }) {
  const stages = [
    {
      title: '1. Authorize (ArmorIQ)',
      desc: 'Intent assurance at planner boundary: capture_plan, policy match, and token minting. Stops destructive actions upstream before they ever touch infrastructure.',
      accent: 'var(--state-evaluating)',
      source: 'docs/ARCHITECTURE.md Sec. 2',
    },
    {
      title: '2. Contain (Tripline)',
      desc: 'In-MCP boundary protection: fstat descriptor inode verification blocks directory traversal, and exact-match canary scanners quarantine outbound comment exfiltration.',
      accent: 'var(--accent)',
      source: 'mcp/common/jail.py & gateway/taint_rule.py',
    },
    {
      title: '3. Prove (Witness & Receipt)',
      desc: 'Local HMAC-chained witness ledger and Canonical JSON Incident Receipts. Guarantees 0-byte leaks and deterministic tamper detection offline via make verify.',
      accent: 'var(--state-allow)',
      source: 'receipts/verify.py & .tripline/witness/',
    },
  ]

  return (
    <div className={`w-full ${className}`}>
      <SectionHeader
        eyebrow="// ARCHITECTURAL DIVISION OF RESPONSIBILITY"
        title="Authorize, Contain, and Prove."
        accentWord="Prove."
        description="ArmorIQ decides upstream policy intent. Tripline enforces in-MCP parameter containment and mints signed forensic receipts for every denied action."
        tone="dark"
      />

      {/* 3 Ruled-top Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {stages.map((stg) => (
          <Card
            key={stg.title}
            variant="ruled-top"
            accentColor={stg.accent}
            source={stg.source}
          >
            <h3 className="font-mono text-sm uppercase font-semibold text-white mb-2">
              {stg.title}
            </h3>
            <p className="text-xs text-[var(--text-muted-on-dark)] leading-relaxed">
              {stg.desc}
            </p>
          </Card>
        ))}
      </div>

      {/* D2 Diagram Stage */}
      <CheckpointPipeline />
    </div>
  )
}
