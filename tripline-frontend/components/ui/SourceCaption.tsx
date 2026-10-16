'use client'

import React from 'react'

export interface SourceCaptionProps {
  source: string
  className?: string
}

export function SourceCaption({ source, className = '' }: SourceCaptionProps) {
  if (!source) return null
  return (
    <div
      className={`font-mono text-[11px] tracking-wider text-[var(--text-faint-on-dark)] dark:text-[var(--text-faint-on-dark)] opacity-75 mt-2 flex items-center gap-1 select-all ${className}`}
    >
      <span className="opacity-60">// source:</span>
      <span className="underline decoration-dotted underline-offset-2">{source}</span>
    </div>
  )
}
