'use client'

import React from 'react'
import { AlertCircle, Terminal } from 'lucide-react'

export interface EmptyStateProps {
  title: string
  description?: string
  command?: string
  source?: string
  className?: string
}

export function EmptyState({
  title,
  description,
  command,
  source,
  className = '',
}: EmptyStateProps) {
  return (
    <div
      className={`rounded-[4px] border border-dashed border-[var(--border-dark)] p-8 text-center bg-white/[0.02] ${className}`}
      data-testid="empty-state"
    >
      <div className="w-10 h-10 mx-auto mb-3 rounded-full bg-white/5 flex items-center justify-center text-[var(--text-muted-on-dark)]">
        <AlertCircle className="w-5 h-5 opacity-70" />
      </div>
      <h3 className="font-mono text-sm uppercase tracking-wider font-semibold text-white mb-1">
        {title}
      </h3>
      {description && (
        <p className="text-sm text-[var(--text-muted-on-dark)] max-w-md mx-auto mb-3 leading-relaxed">
          {description}
        </p>
      )}
      {command && (
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-[2px] bg-[#0A0A0C] border border-[var(--border-dark)] text-xs font-mono text-emerald-400">
          <Terminal className="w-3.5 h-3.5 opacity-60" />
          <code>{command}</code>
        </div>
      )}
      {source && (
        <div className="mt-3 text-[11px] font-mono text-[var(--text-faint-on-dark)]">
          // source: {source}
        </div>
      )}
    </div>
  )
}
