'use client'

import React from 'react'
import {
  Check,
  X,
  Pause,
  RotateCw,
  ShieldCheck,
  AlertTriangle,
  Circle,
} from 'lucide-react'

export type SecurityState =
  | 'allow'
  | 'deny'
  | 'hold'
  | 'evaluating'
  | 'verified'
  | 'tamper'
  | 'tamper-detected'
  | 'idle'

export interface BadgeProps {
  state: SecurityState
  label?: string
  variant?: 'badge' | 'pill'
  size?: 'sm' | 'md'
  className?: string
}

export function getStateConfig(state: SecurityState) {
  switch (state) {
    case 'allow':
      return {
        label: 'ALLOW',
        icon: Check,
        color: 'var(--state-allow)',
        bgDark: 'rgba(47, 191, 113, 0.12)',
        bgLight: 'rgba(47, 191, 113, 0.10)',
        border: 'rgba(47, 191, 113, 0.35)',
      }
    case 'deny':
      return {
        label: 'DENY',
        icon: X,
        color: 'var(--state-deny)',
        bgDark: 'rgba(229, 72, 77, 0.12)',
        bgLight: 'rgba(229, 72, 77, 0.10)',
        border: 'rgba(229, 72, 77, 0.35)',
      }
    case 'hold':
      return {
        label: 'HOLD',
        icon: Pause,
        color: 'var(--state-hold)',
        bgDark: 'rgba(245, 165, 36, 0.12)',
        bgLight: 'rgba(245, 165, 36, 0.10)',
        border: 'rgba(245, 165, 36, 0.35)',
      }
    case 'evaluating':
      return {
        label: 'EVALUATING',
        icon: RotateCw,
        color: 'var(--state-evaluating)',
        bgDark: 'rgba(76, 141, 255, 0.12)',
        bgLight: 'rgba(76, 141, 255, 0.10)',
        border: 'rgba(76, 141, 255, 0.35)',
        animate: true,
      }
    case 'verified':
      return {
        label: 'VERIFIED',
        icon: ShieldCheck,
        color: 'var(--state-verified)',
        bgDark: 'rgba(47, 191, 113, 0.14)',
        bgLight: 'rgba(47, 191, 113, 0.12)',
        border: 'rgba(47, 191, 113, 0.40)',
      }
    case 'tamper':
    case 'tamper-detected':
      return {
        label: 'TAMPER_DETECTED',
        icon: AlertTriangle,
        color: 'var(--state-tamper)',
        bgDark: 'rgba(229, 72, 77, 0.14)',
        bgLight: 'rgba(229, 72, 77, 0.12)',
        border: 'rgba(229, 72, 77, 0.40)',
      }
    case 'idle':
    default:
      return {
        label: 'IDLE',
        icon: Circle,
        color: 'var(--state-idle)',
        bgDark: 'rgba(107, 107, 115, 0.10)',
        bgLight: 'rgba(107, 107, 115, 0.08)',
        border: 'rgba(107, 107, 115, 0.25)',
      }
  }
}

export function Badge({
  state,
  label,
  variant = 'badge',
  size = 'md',
  className = '',
}: BadgeProps) {
  const config = getStateConfig(state)
  const Icon = config.icon
  const displayLabel = label || config.label

  const radius = variant === 'pill' ? 'rounded-full' : 'rounded-[2px]'
  const sizeClasses =
    size === 'sm'
      ? 'text-[11px] px-1.5 py-0.5 gap-1'
      : 'text-xs px-2 py-0.5 gap-1.5'

  return (
    <span
      className={`inline-flex items-center font-mono font-medium tracking-wide uppercase border ${radius} ${sizeClasses} ${className}`}
      style={{
        color: config.color,
        borderColor: config.border,
        backgroundColor: 'var(--badge-bg, rgba(120, 120, 120, 0.08))',
      }}
      role="status"
    >
      <Icon
        className={`w-3 h-3 shrink-0 ${
          'animate' in config && config.animate ? 'animate-spin' : ''
        }`}
        aria-hidden="true"
      />
      <span>{displayLabel}</span>
    </span>
  )
}

export function StatusPill(props: Omit<BadgeProps, 'variant'>) {
  return <Badge {...props} variant="pill" />
}
