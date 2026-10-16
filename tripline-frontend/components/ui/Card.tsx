'use client'

import React from 'react'
import { SourceCaption } from './SourceCaption'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'outlined' | 'filled' | 'ruled-top'
  padding?: 'compact' | 'feature' | 'none'
  source?: string
  accentColor?: string
  tone?: 'dark' | 'light'
}

export function Card({
  children,
  variant = 'filled',
  padding = 'compact',
  source,
  accentColor,
  tone,
  className = '',
  ...props
}: CardProps) {
  const padClass = {
    compact: 'p-6',
    feature: 'p-8',
    none: 'p-0',
  }[padding]

  let variantStyle = ''
  if (variant === 'outlined') {
    variantStyle =
      'bg-transparent border border-[var(--border-dark)] dark:border-[var(--border-dark)]'
  } else if (variant === 'filled') {
    variantStyle =
      'bg-[var(--surface-dark)] border border-[var(--border-dark)]'
  } else if (variant === 'ruled-top') {
    variantStyle =
      'bg-[var(--surface-dark)] border border-[var(--border-dark)] border-t-2'
  }

  return (
    <div
      className={`rounded-[4px] relative transition-colors duration-160 ${padClass} ${variantStyle} ${className}`}
      style={
        variant === 'ruled-top' && accentColor
          ? { borderTopColor: accentColor }
          : undefined
      }
      {...props}
    >
      {children}
      {source && <SourceCaption source={source} />}
    </div>
  )
}
