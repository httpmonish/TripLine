'use client'

import React, { useState } from 'react'

export interface TooltipProps {
  content: React.ReactNode
  source?: string
  children: React.ReactNode
  className?: string
}

export function Tooltip({
  content,
  source,
  children,
  className = '',
}: TooltipProps) {
  const [visible, setVisible] = useState(false)

  return (
    <div
      className={`relative inline-block ${className}`}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
      tabIndex={0}
      role="tooltip"
    >
      {children}
      {visible && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 pointer-events-none w-max max-w-xs p-2.5 rounded-[2px] bg-[#1B1B1E] text-[#F3F1EA] text-xs font-mono shadow-[0_8px_24px_rgba(0,0,0,0.35)] border border-[var(--border-dark)] leading-snug">
          <div>{content}</div>
          {source && (
            <div className="mt-1 pt-1 border-t border-[var(--border-dark)] text-[10px] text-[var(--text-faint-on-dark)]">
              // source: {source}
            </div>
          )}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-[#1B1B1E]" />
        </div>
      )}
    </div>
  )
}
