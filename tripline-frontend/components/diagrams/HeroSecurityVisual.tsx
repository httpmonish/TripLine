'use client'

import React, { useState } from 'react'
import { ShieldCheck, ShieldAlert, CheckCircle2, XCircle, ArrowRight, KeyRound, Lock, FileCode, Play, RotateCcw } from 'lucide-react'
import { TripLineLogo } from '../brand/TripLineLogo'

export function HeroSecurityVisual() {
  const [mode, setMode] = useState<'safe' | 'blocked'>('blocked')
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false)

  const handleToggle = (nextMode: 'safe' | 'blocked') => {
    setMode(nextMode)
    setIsEvaluating(true)
    setTimeout(() => {
      setIsEvaluating(false)
    }, 450)
  }

  return (
    <div className="relative w-full max-w-[500px] mx-auto lg:mx-0 bg-[#FFFFFF] border border-[#E2DFD6] rounded-2xl p-6 sm:p-7 shadow-sm overflow-hidden">
      {/* Subtle background wash */}
      <div className="absolute top-0 right-0 w-48 h-48 bg-[#0D7A73]/5 rounded-full blur-2xl pointer-events-none" />

      {/* Top Bar: Interactive Scenario Switch */}
      <div className="flex items-center justify-between pb-4 border-b border-[#EDEAE1] mb-6">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#0D7A73] animate-pulse" />
          <span className="font-mono text-[11px] text-[#0D7A73] uppercase tracking-wider font-semibold">
            Live Boundary Intercept
          </span>
        </div>
        <div className="flex items-center gap-1 p-0.5 rounded-lg bg-[#F5F3EC] border border-[#E2DFD6] text-xs font-sans">
          <button
            onClick={() => handleToggle('blocked')}
            data-local="toggle-hero-blocked"
            className={`px-2.5 py-1 rounded text-[11px] transition-all font-medium ${
              mode === 'blocked'
                ? 'bg-[#DC2626] text-white shadow-xs'
                : 'text-[#4D535F] hover:text-[#191C21]'
            }`}
          >
            Blocked Attack
          </button>
          <button
            onClick={() => handleToggle('safe')}
            data-local="toggle-hero-safe"
            className={`px-2.5 py-1 rounded text-[11px] transition-all font-medium ${
              mode === 'safe'
                ? 'bg-[#16A34A] text-white shadow-xs'
                : 'text-[#4D535F] hover:text-[#191C21]'
            }`}
          >
            Permitted Read
          </button>
        </div>
      </div>

      {/* Centerpiece: The TripLine Brand Mark & Intercept Plane */}
      <div className="relative flex flex-col items-center justify-center py-4">
        {/* Interactive Logo Mark with 3D tilt */}
        <div className="relative z-10 p-3 transition-transform duration-300">
          <TripLineLogo
            size="hero"
            variant="light"
            showWordmark={false}
            animated={true}
            interactive={true}
          />
        </div>

        {/* Dynamic Status Beacon */}
        <div className="mt-4 flex flex-col items-center text-center">
          {isEvaluating ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#FAF8F2] border border-[#E2DFD6] text-xs font-mono text-[#0D7A73] animate-pulse">
              <span className="w-2 h-2 rounded-full bg-[#0D7A73] animate-ping" />
              <span>Evaluating session plan...</span>
            </div>
          ) : mode === 'blocked' ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#FEF2F2] border border-[#FECACA] text-xs font-mono text-[#DC2626] font-medium">
              <XCircle className="w-3.5 h-3.5" />
              <span>VERDICT: DENIED (Out of plan: delete_branch)</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F0FDF4] border border-[#BBF7D0] text-xs font-mono text-[#16A34A] font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>VERDICT: AUTHORIZED (In plan: read_file)</span>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Process Strip: Request -> Gate -> MCP -> Evidence */}
      <div className="mt-6 pt-5 border-t border-[#EDEAE1] grid grid-cols-3 gap-2 text-center font-mono text-[11px]">
        <div className="p-2.5 rounded-lg bg-[#FAF8F2] border border-[#EDEAE1]">
          <span className="text-[#6E7687] block text-[9px] uppercase">01 Ingress</span>
          <span className="text-[#191C21] font-semibold block truncate mt-0.5">
            {mode === 'blocked' ? 'delete_branch' : 'read_file'}
          </span>
        </div>

        <div className="p-2.5 rounded-lg bg-[#FAF8F2] border border-[#EDEAE1]">
          <span className="text-[#6E7687] block text-[9px] uppercase">02 ArmorIQ Gate</span>
          <span
            className={`font-semibold block truncate mt-0.5 ${
              mode === 'blocked' ? 'text-[#DC2626]' : 'text-[#16A34A]'
            }`}
          >
            {mode === 'blocked' ? 'DENY (Out of Plan)' : 'ALLOW (In Plan)'}
          </span>
        </div>

        <div className="p-2.5 rounded-lg bg-[#FAF8F2] border border-[#EDEAE1]">
          <span className="text-[#6E7687] block text-[9px] uppercase">03 Evidence</span>
          <span className="text-[#0D7A73] font-semibold block truncate mt-0.5">
            {mode === 'blocked' ? 'Signed Receipt' : 'Clean Dispatch'}
          </span>
        </div>
      </div>
    </div>
  )
}
