'use client'

import React, { useState } from 'react'
import { SectionHeader } from '../ui/SectionHeader'
import { CodeBlock } from '../ui/CodeBlock'
import { VerifyStrip } from '../diagrams/VerifyStrip'
import { verifyReceiptLocally } from '../../lib/data'
import { ShieldCheck, Play, RotateCw } from 'lucide-react'

export interface NonRepudiationBandProps {
  receipt?: any
  className?: string
}

export function NonRepudiationBand({ receipt, className = '' }: NonRepudiationBandProps) {
  const [verifyStatus, setVerifyStatus] = useState<'VERIFIED' | 'TAMPER_DETECTED' | 'IDLE' | 'VERIFYING'>('VERIFIED')
  const [computedHash, setComputedHash] = useState<string>(
    receipt?.canonical_hash || '84d707a125166845b8aaba424c23b3b77b758dad0c2bdbb3d3739e8f8dc449ec'
  )

  const handleRunVerify = async () => {
    if (!receipt) return
    setVerifyStatus('VERIFYING')
    setTimeout(async () => {
      const res = await verifyReceiptLocally(receipt)
      setVerifyStatus(res.status)
      setComputedHash(res.computed_hash)
    }, 400)
  }

  const cliOutput = `make verify FILE=results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json
[OK] Receipt RCP-phase3-wow-ca5dcec9-call-p1_ verified: VERIFIED
     Canonical Hash: 84d707a125166845b8aaba424c23b3b77b758dad0c2bdbb3d3739e8f8dc449ec
     Signature:      eedc5214f6314bf44881a0a785dada909d60312795c4042bd8f073442180dfd7`

  return (
    <div className={`w-full ${className}`}>
      <SectionHeader
        eyebrow="// OFFLINE CRYPTOGRAPHIC VERIFICATION"
        title="Four steps to forensic non-repudiation."
        accentWord="non-repudiation."
        description="Every incident receipt can be independently recomputed and verified offline without trusting Tripline, the LLM, or the hosting environment."
        tone="light"
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-8">
        {/* Left: CLI Command Block (5 cols) */}
        <div className="lg:col-span-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="font-mono text-xs uppercase tracking-wider text-[var(--text-muted-on-light)] font-medium">
              // REPOSITORY VERIFICATION COMMAND
            </span>
            <button
              onClick={handleRunVerify}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[2px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[#0B0B0C] font-mono text-xs font-semibold cursor-pointer"
              type="button"
            >
              <RotateCw className="w-3 h-3" />
              <span>RE-RUN IN BROWSER</span>
            </button>
          </div>

          <CodeBlock
            code={cliOutput}
            language="bash"
            source="receipts/verify.py & results/phase3/scenario/"
            filename="Terminal Shell"
            highlightLines={[2]}
          />
        </div>

        {/* Right: D5 Verify Strip Stage (7 cols) */}
        <div className="lg:col-span-7">
          <VerifyStrip
            status={verifyStatus}
            canonicalHash={receipt?.canonical_hash || '84d707a125166845b8aaba424c23b3b77b758dad0c2bdbb3d3739e8f8dc449ec'}
            computedHash={computedHash}
          />
        </div>
      </div>
    </div>
  )
}
