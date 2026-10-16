'use client'

import React from 'react'
import { SourceCaption } from './SourceCaption'

export interface StatItem {
  label: string
  value: string | number
  sublabel?: string
  source?: string
}

export interface StatRowProps {
  stats: StatItem[]
  source?: string
  className?: string
  tone?: 'dark' | 'light'
}

export function StatRow({
  stats,
  source,
  className = '',
  tone = 'dark',
}: StatRowProps) {
  const isDark = tone === 'dark'

  return (
    <div className={`w-full ${className}`}>
      <div
        className={`grid grid-cols-2 md:grid-cols-4 gap-6 py-6 border-y ${
          isDark
            ? 'border-[var(--border-dark)] bg-transparent text-[var(--text-on-dark)]'
            : 'border-[var(--border-light)] bg-transparent text-[var(--text-on-light)]'
        }`}
      >
        {stats.map((stat, idx) => (
          <div key={idx} className="flex flex-col">
            <span
              className={`font-mono text-xs uppercase tracking-wider mb-1 ${
                isDark
                  ? 'text-[var(--text-muted-on-dark)]'
                  : 'text-[var(--text-muted-on-light)]'
              }`}
            >
              // {stat.label}
            </span>
            <span className="font-mono text-3xl md:text-4xl font-bold tracking-tight">
              {stat.value}
            </span>
            {stat.sublabel && (
              <span
                className={`text-xs mt-1 ${
                  isDark
                    ? 'text-[var(--text-faint-on-dark)]'
                    : 'text-[var(--text-faint-on-light)]'
                }`}
              >
                {stat.sublabel}
              </span>
            )}
            {stat.source && (
              <SourceCaption source={stat.source} className="mt-1" />
            )}
          </div>
        ))}
      </div>
      {source && <SourceCaption source={source} className="mt-2" />}
    </div>
  )
}
