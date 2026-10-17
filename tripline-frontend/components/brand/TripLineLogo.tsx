'use client'

import React, { useRef, useState, useEffect } from 'react'

export interface TripLineLogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'hero' | number
  variant?: 'dark' | 'light' | 'mono' | 'brand'
  showWordmark?: boolean
  animated?: boolean
  interactive?: boolean
  className?: string
  priority?: boolean
}

export function TripLineLogo({
  size = 'md',
  variant = 'dark',
  showWordmark = true,
  animated = false,
  interactive = false,
  className = '',
}: TripLineLogoProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [tilt, setTilt] = useState({ rx: 0, ry: 0 })
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
      setPrefersReducedMotion(mq.matches)
      const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches)
      mq.addEventListener('change', handler)
      return () => mq.removeEventListener('change', handler)
    }
  }, [])

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!interactive || prefersReducedMotion || !containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width - 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5
    setTilt({
      rx: -y * 22,
      ry: x * 26,
    })
  }

  const handlePointerLeave = () => {
    if (!interactive) return
    setTilt({ rx: 0, ry: 0 })
  }

  // Dimensions
  let markHeight = 32
  let textClass = 'text-xl'
  let gapClass = 'gap-2.5'

  if (typeof size === 'number') {
    markHeight = size
    textClass = size > 48 ? 'text-4xl' : size > 32 ? 'text-2xl' : 'text-lg'
  } else {
    switch (size) {
      case 'xs':
        markHeight = 20
        textClass = 'text-sm'
        gapClass = 'gap-1.5'
        break
      case 'sm':
        markHeight = 28
        textClass = 'text-lg'
        gapClass = 'gap-2'
        break
      case 'md':
        markHeight = 36
        textClass = 'text-2xl'
        gapClass = 'gap-3'
        break
      case 'lg':
        markHeight = 54
        textClass = 'text-4xl'
        gapClass = 'gap-3.5'
        break
      case 'hero':
        markHeight = 96
        textClass = 'text-5xl sm:text-6xl'
        gapClass = 'gap-5'
        break
    }
  }

  // Width is proportional to viewBox (212 x 264 => ratio ~ 0.803)
  const markWidth = Math.round(markHeight * (212 / 264))

  // Color tokens
  const isDark = variant === 'dark' || variant === 'brand'
  const isLight = variant === 'light'
  const isMono = variant === 'mono'

  const topFace = isMono ? 'currentColor' : isLight ? '#0F1228' : '#ECEEF6'
  const leftFace = isMono ? 'currentColor' : isLight ? '#6B6E7A' : '#565A6B'
  const rightFace = isMono ? 'currentColor' : isLight ? '#AEB1BA' : '#8A8FA3'
  const gapStroke = isLight ? '#FFFFFF' : '#090A14'
  const stubColor = isMono ? 'currentColor' : isLight ? '#0F1228' : '#ECEEF6'
  const nodeFill = isLight ? '#FFFFFF' : '#090A14'
  const accentColor = isDark ? '#9A8CFF' : '#5B4BFF'
  const textColor = isLight ? 'text-[#0F1228]' : 'text-[#F4F5FB]'

  return (
    <div
      ref={containerRef}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      className={`inline-flex items-center select-none ${gapClass} ${className}`}
      style={{ perspective: interactive ? 800 : undefined }}
      role="img"
      aria-label="TripLine"
    >
      <div
        className="relative transition-transform duration-150 ease-out shrink-0"
        style={{
          width: markWidth,
          height: markHeight,
          transform:
            interactive && !prefersReducedMotion
              ? `rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)`
              : undefined,
          transformStyle: 'preserve-3d',
        }}
      >
        <svg
          viewBox="94 52 212 264"
          className="w-full h-full overflow-visible"
          aria-hidden="true"
        >
          <defs>
            <filter id={`tl-glow-${variant}`} x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <linearGradient id={`tl-shade-${variant}`} gradientUnits="userSpaceOnUse" x1="200" y1="90" x2="200" y2="310">
              <stop offset="0" stopColor="#FFFFFF" stopOpacity="0.16" />
              <stop offset="1" stopColor="#000000" stopOpacity="0.25" />
            </linearGradient>
            <clipPath id={`tl-hex-${variant}`}>
              <path d="M200 90L295.26 145V255L200 310L104.74 255V145Z" />
            </clipPath>
          </defs>

          {/* Left Face */}
          <path
            d="M104.74 145L200 200V310L104.74 255Z"
            fill={leftFace}
            fillOpacity={isMono ? 0.6 : 1}
            stroke={gapStroke}
            strokeWidth="3"
            strokeLinejoin="round"
          />

          {/* Right Face */}
          <path
            d="M200 200L295.26 145V255L200 310Z"
            fill={rightFace}
            fillOpacity={isMono ? 0.3 : 1}
            stroke={gapStroke}
            strokeWidth="3"
            strokeLinejoin="round"
          />

          {/* Top Face */}
          <path
            d="M200 90L295.26 145L200 200L104.74 145Z"
            fill={topFace}
            stroke={gapStroke}
            strokeWidth="3"
            strokeLinejoin="round"
          />

          {/* Shading overlay */}
          {!isMono && (
            <path
              d="M200 90L295.26 145V255L200 310L104.74 255V145Z"
              fill={`url(#tl-shade-${variant})`}
              pointerEvents="none"
            />
          )}

          {/* Apex tripwire stub */}
          <path
            d="M200 90V62"
            stroke={stubColor}
            strokeWidth="2.6"
            strokeLinecap="round"
            fill="none"
          />

          {/* Live tripwire tip */}
          <circle
            cx="200"
            cy="62"
            r="3.2"
            fill={accentColor}
            filter={`url(#tl-glow-${variant})`}
            className={animated && !prefersReducedMotion ? 'animate-pulse' : ''}
          />

          {/* Center inspection node */}
          <circle
            cx="200"
            cy="200"
            r="5.8"
            fill={nodeFill}
            stroke={stubColor}
            strokeWidth="2.4"
          />

          {/* Subtle animated tripwire pulses along edges when animated=true */}
          {animated && !prefersReducedMotion && (
            <g opacity="0.8">
              <path
                d="M104.74 145L200 200"
                stroke={accentColor}
                strokeWidth="2"
                strokeDasharray="12 40"
                className="animate-[dash_3s_linear_infinite]"
              />
              <path
                d="M295.26 145L200 200"
                stroke={accentColor}
                strokeWidth="2"
                strokeDasharray="12 40"
                className="animate-[dash_3s_linear_infinite_0.8s]"
              />
              <path
                d="M200 200V310"
                stroke={accentColor}
                strokeWidth="2"
                strokeDasharray="12 40"
                className="animate-[dash_3s_linear_infinite_1.6s]"
              />
            </g>
          )}
        </svg>
      </div>

      {showWordmark && (
        <span
          className={`font-sans font-extrabold tracking-[-0.04em] leading-none ${textClass} ${textColor}`}
          style={{ letterSpacing: '-0.04em' }}
        >
          TripLine
        </span>
      )}
    </div>
  )
}
