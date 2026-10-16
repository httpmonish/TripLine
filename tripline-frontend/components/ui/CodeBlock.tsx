'use client'

import React, { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { SourceCaption } from './SourceCaption'

export interface CodeBlockProps {
  code: string
  language?: string
  source?: string
  filename?: string
  highlightLines?: number[]
  className?: string
}

export function CodeBlock({
  code,
  language = 'json',
  source,
  filename,
  highlightLines = [],
  className = '',
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1400)
    } catch {
      // ignore
    }
  }

  const lines = code.split('\n')

  return (
    <div
      className={`rounded-[4px] border border-[var(--border-dark)] bg-[#0A0A0C] text-[#F3F1EA] overflow-hidden ${className}`}
    >
      {(filename || source) && (
        <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-dark)] bg-[#121214] text-xs font-mono text-[var(--text-muted-on-dark)]">
          <span className="truncate">{filename || source}</span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2 py-0.5 rounded-[2px] hover:bg-white/10 text-xs text-[var(--text-on-dark)] transition-colors focus-ring cursor-pointer"
            title="Copy code"
            type="button"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-[var(--state-allow)]" />
                <span className="text-[var(--state-allow)]">COPIED</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 opacity-70" />
                <span>COPY</span>
              </>
            )}
          </button>
        </div>
      )}

      <div className="relative p-4 overflow-x-auto text-[13px] leading-[1.6] font-mono">
        {!filename && !source && (
          <button
            onClick={handleCopy}
            className="absolute top-3 right-3 p-1.5 rounded-[2px] bg-white/5 hover:bg-white/15 text-[var(--text-on-dark)] transition-colors focus-ring cursor-pointer"
            title="Copy code"
            type="button"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-[var(--state-allow)]" />
            ) : (
              <Copy className="w-3.5 h-3.5 opacity-70" />
            )}
          </button>
        )}
        <pre className="m-0 font-mono">
          {lines.map((line, idx) => {
            const lineNum = idx + 1
            const isHighlighted = highlightLines.includes(lineNum)
            return (
              <div
                key={idx}
                className={`${
                  isHighlighted
                    ? 'bg-[var(--accent-soft-on-dark)] -mx-4 px-4 border-l-2 border-[var(--accent)]'
                    : ''
                }`}
              >
                <code>{line || ' '}</code>
              </div>
            )
          })}
        </pre>
      </div>

      {source && (
        <div className="px-4 pb-3">
          <SourceCaption source={source} />
        </div>
      )}
    </div>
  )
}
