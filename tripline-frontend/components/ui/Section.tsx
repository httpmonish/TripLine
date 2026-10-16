'use client'

import React from 'react'

export interface SectionProps extends React.HTMLAttributes<HTMLElement> {
  tone?: 'dark' | 'light'
  isHero?: boolean
  isClosing?: boolean
  noPadding?: boolean
  fullBleedContent?: boolean
  id?: string
}

export function Section({
  children,
  tone = 'dark',
  isHero = false,
  isClosing = false,
  noPadding = false,
  fullBleedContent = false,
  id,
  className = '',
  ...props
}: SectionProps) {
  const isDark = tone === 'dark'

  const toneClasses = isDark
    ? 'bg-[#0B0B0C] text-[#F3F1EA] border-[var(--border-dark)]'
    : 'bg-[#F1EEE6] text-[#131313] border-[var(--border-light)]'

  const pyClasses = noPadding
    ? 'py-0'
    : isHero || isClosing
    ? 'py-24 sm:py-32 md:py-40'
    : 'py-20 sm:py-24 md:py-32'

  return (
    <section
      id={id}
      className={`w-full relative border-b last:border-b-0 ${toneClasses} ${pyClasses} ${className}`}
      data-tone={tone}
      {...props}
    >
      {fullBleedContent ? (
        children
      ) : (
        <div className="max-w-[1200px] mx-auto px-4 sm:px-6 w-full">
          {children}
        </div>
      )}
    </section>
  )
}
