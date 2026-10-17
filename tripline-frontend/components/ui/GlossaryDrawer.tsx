'use client'

import React, { useState, useEffect } from 'react'
import { X, Search, BookOpen, ExternalLink } from 'lucide-react'

export interface GlossaryTerm {
  term: string
  category: string
  definition: string
  source: string
}

const DEFAULT_TERMS: GlossaryTerm[] = [
  {
    term: "Agent",
    category: "Core",
    definition: "An autonomous software loop driven by a language model that inspects repository issues, reasons about fixes, and proposes tool actions.",
    source: "docs/AGENT_ARCHITECTURE.md"
  },
  {
    term: "MCP Server",
    category: "Protocol",
    definition: "Model Context Protocol server providing defined tool capabilities (file reading, issue commenting) to AI agents under strict boundary controls.",
    source: "docs/ARCHITECTURE.md"
  },
  {
    term: "Tool Call",
    category: "Execution",
    definition: "A structured request emitted by the language model to perform a concrete action (e.g., read_file, comment_issue).",
    source: "agent/real_llm.py"
  },
  {
    term: "Plan",
    category: "Governance",
    definition: "A cryptographically hashed sequence of permitted steps synthesized from trusted task goals before untrusted issue text is read.",
    source: "agent/planner_v2.py"
  },
  {
    term: "Intent Token",
    category: "ArmorIQ",
    definition: "A cryptographically signed token issued by ArmorIQ's Intent Authorization Proxy binding the agent to an approved plan.",
    source: "docs/armoriq_docs_notes.md"
  },
  {
    term: "Plan Hash",
    category: "ArmorIQ",
    definition: "Deterministic RFC 8785 canonical SHA-256 hash uniquely identifying the promised plan structure.",
    source: "docs/ARMORIQ_CAPABILITY_MATRIX.md"
  },
  {
    term: "Merkle Proof",
    category: "ArmorIQ",
    definition: "ArmorIQ's cryptographic proof verifying that each executed step belongs to the root of the signed plan.",
    source: "docs/armoriq_docs_notes.md"
  },
  {
    term: "Policy",
    category: "Governance",
    definition: "Rule set evaluated by ArmorIQ determining whether proposed actions are allowed, denied, or held for inspection.",
    source: "docs/armoriq_docs_notes.md"
  },
  {
    term: "Allow / Deny / Hold",
    category: "Decisions",
    definition: "Possible enforcement decisions. ALLOW executes the tool; DENY halts execution with a receipt; HOLD quarantines outbound canary hits.",
    source: "receipts/models.py"
  },
  {
    term: "Path Jail",
    category: "Tripline",
    definition: "In-MCP file boundary defense using canonical path resolution to prevent directory traversal and symlink escapes.",
    source: "mcp/common/jail.py"
  },
  {
    term: "Canary Token",
    category: "Tripline",
    definition: "A unique high-entropy token seeded into decoy files to detect prompt-injected exfiltration attempts.",
    source: "canary/scan.py"
  },
  {
    term: "Egress Gateway",
    category: "Tripline",
    definition: "Outbound parameter inspector that intercepts and quarantines comments or messages carrying canary tokens.",
    source: "canary/scan.py"
  },
  {
    term: "Witness Log",
    category: "Tripline",
    definition: "An append-only HMAC-SHA256 hash chain that cryptographically records execution counts and halts tampering.",
    source: "mcp/common/witness.py"
  },
  {
    term: "Incident Receipt",
    category: "Tripline",
    definition: "A canonical JSON forensic artifact signed with the witness key detailing who proposed an action, who stopped it, and why.",
    source: "receipts/builder.py"
  },
  {
    term: "HMAC Signature",
    category: "Cryptography",
    definition: "Symmetric HMAC-SHA256 digital signature guaranteeing the integrity and origin of incident receipts.",
    source: "receipts/models.py"
  },
  {
    term: "Verification",
    category: "Forensics",
    definition: "Independent cryptographic re-computation of receipt canonical hash and HMAC signature to confirm authenticity.",
    source: "receipts/verify.py"
  },
  {
    term: "Tamper Check",
    category: "Forensics",
    definition: "Validation mechanism proving that any unauthorized mutation of a receipt immediately breaks its signature.",
    source: "scripts/tamper_demo.py"
  }
]

export function GlossaryDrawer({
  isOpen,
  open,
  onClose,
}: {
  isOpen?: boolean
  open?: boolean
  onClose: () => void
}) {
  const visible = isOpen ?? open ?? false
  const [terms, setTerms] = useState<GlossaryTerm[]>(DEFAULT_TERMS)
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetch('/api/glossary')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.terms && data.terms.length > 0) {
          setTerms(data.terms)
        }
      })
      .catch(() => {})
  }, [])

  if (!visible) return null

  const filtered = terms.filter(
    (t) =>
      t.term.toLowerCase().includes(search.toLowerCase()) ||
      t.definition.toLowerCase().includes(search.toLowerCase()) ||
      t.category.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end transition-opacity"
      role="dialog"
      aria-modal="true"
      aria-labelledby="glossary-title"
      data-testid="modal-glossary"
    >
      <div className="w-full max-w-md bg-[#111113] border-l border-[var(--border-dark)] h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-4 border-b border-[var(--border-dark)] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-[var(--accent)]" />
            <h2 id="glossary-title" className="font-semibold text-sm text-white">
              Tripline Glossary
            </h2>
            <span className="font-mono text-[10px] text-[var(--text-faint-on-dark)] uppercase">
              ({terms.length} Terms)
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-[var(--text-muted-on-dark)] hover:text-white hover:bg-white/10"
            aria-label="Close glossary"
            data-local="close-glossary"
            data-testid="btn-close-glossary"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Search Input */}
        <div className="p-3 border-b border-[var(--border-dark)]">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-faint-on-dark)]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search definitions (e.g. intent token, jail)..."
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-[#1A1A1E] border border-[var(--border-dark)] rounded text-white placeholder-[var(--text-faint-on-dark)] focus:outline-none focus:border-[var(--accent)]"
              data-local="glossary-search"
              data-testid="input-glossary-search"
            />
          </div>
        </div>

        {/* Terms List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {filtered.length === 0 ? (
            <div className="text-center py-8 text-xs text-[var(--text-faint-on-dark)]">
              No matching terms found.
            </div>
          ) : (
            filtered.map((item) => (
              <div
                key={item.term}
                className="p-3 rounded border border-[var(--border-dark)] bg-[#141417]/80 hover:border-white/20 transition-colors"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-xs text-white">
                    {item.term}
                  </span>
                  <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-white/5 text-[var(--accent)] border border-white/5">
                    {item.category}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted-on-dark)] leading-relaxed mb-2">
                  {item.definition}
                </p>
                <div className="font-mono text-[9px] text-[var(--text-faint-on-dark)] flex items-center gap-1">
                  <span>Source:</span>
                  <span className="text-white/60">{item.source}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
