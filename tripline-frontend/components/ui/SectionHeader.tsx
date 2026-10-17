'use client'

import React from 'react'

export interface SectionHeaderProps {
  eyebrow?: string
  title: string
  accentWord?: string
  description?: string
  tone?: 'dark' | 'light'
  size?: 'hero' | 'section'
  className?: string
}

export function SectionHeader({
  eyebrow,
  title,
  accentWord,
  description,
  tone = 'dark',
  size = 'section',
  className = '',
}: SectionHeaderProps) {
  const isDark = tone === 'dark'

  // Render headline with one emphasized word in accent color if provided
  let formattedTitle = <>{title}</>
  if (accentWord && title.includes(accentWord)) {
    const parts = title.split(accentWord)
    formattedTitle = (
      <>
        {parts[0]}
        <span className="text-[var(--accent)]">{accentWord}</span>
        {parts.slice(1).join(accentWord)}
      </>
    )
  }

  const eyebrowColor = isDark
    ? 'text-[#9EA8B6]'
    : 'text-[#59636E]'

  const titleColor = isDark
    ? 'text-[#F4F5F6]'
    : 'text-[#20252B]'

  const descColor = isDark
    ? 'text-[#9EA8B6]'
    : 'text-[#59636E]'

  return (
    <div className={`mb-12 ${className}`}>
      {eyebrow && (
        <div
          className={`font-mono text-xs uppercase tracking-[0.12em] font-medium mb-3 ${eyebrowColor}`}
        >
          {eyebrow.startsWith('//') ? eyebrow : `// ${eyebrow}`}
        </div>
      )}

      {size === 'hero' ? (
        <h1
          className={`text-5xl sm:text-6xl md:text-7xl lg:text-[84px] font-bold leading-[0.96] tracking-[-0.04em] ${titleColor}`}
        >
          {formattedTitle}
        </h1>
      ) : (
        <h2
          className={`text-3xl sm:text-4xl md:text-5xl font-semibold leading-[1.08] tracking-[-0.025em] ${titleColor}`}
        >
          {formattedTitle}
        </h2>
      )}

      {description && (
        <p
          className={`mt-6 text-lg sm:text-xl leading-[1.55] font-normal max-w-[62ch] ${descColor}`}
        >
          {description}
        </p>
      )}
    </div>
  )
}
