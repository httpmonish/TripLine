'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  href?: string
  icon?: React.ReactNode
  showArrow?: boolean
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  href,
  icon,
  showArrow = false,
  className = '',
  ...props
}: ButtonProps) {
  const baseStyles =
    'inline-flex items-center justify-center font-mono uppercase tracking-wider transition-colors duration-160 select-none cursor-pointer focus-ring'

  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 gap-1.5 rounded-[2px]',
    md: 'text-[13px] px-4 py-2 gap-2 rounded-[2px]',
    lg: 'text-sm px-6 py-3 gap-2.5 rounded-[2px]',
  }[size]

  const variantStyles = {
    primary:
      'bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[#0B0B0C] font-semibold border border-[var(--accent)]',
    secondary:
      'bg-transparent hover:bg-white/5 border border-current text-inherit font-medium',
    ghost:
      'bg-transparent hover:bg-white/5 text-inherit border-transparent underline-offset-4 hover:underline',
  }[variant]

  const combinedClasses = `${baseStyles} ${sizeStyles} ${variantStyles} ${className}`

  const content = (
    <>
      {icon && <span className="inline-flex shrink-0">{icon}</span>}
      <span>{children}</span>
      {showArrow && <ArrowRight className="w-3.5 h-3.5 shrink-0" />}
    </>
  )

  if (href) {
    return (
      <Link href={href} className={combinedClasses}>
        {content}
      </Link>
    )
  }

  return (
    <button className={combinedClasses} {...props}>
      {content}
    </button>
  )
}

export default Button
