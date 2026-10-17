'use client'

import React, { useState } from 'react'
import { ShieldCheck, ShieldAlert, CheckCircle2, XCircle, KeyRound, Lock, FileText, Sparkles, Terminal } from 'lucide-react'
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
    <div className="relative w-full max-w-[500px] mx-auto lg:mx-0 bg-[#121418] border border-[#262B34] rounded-2xl p-6 sm:p-7 shadow-2xl overflow-hidden font-sans text-white">
      {/* Subtle brushed metal highlight */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-[#F97316]/5 rounded-full blur-3xl pointer-events-none" />

      {/* Top Bar: Interactive Scenario Switch */}
      <div className="flex items-center justify-between pb-4 border-b border-[#20242C] mb-6">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#F97316] animate-pulse" />
          <span className="font-mono text-[11px] text-[#F97316] uppercase tracking-wider font-semibold">
            Live Boundary Intercept
          </span>
        </div>
        <div className="flex items-center gap-1 p-0.5 rounded-lg bg-[#181B22] border border-[#2B303C] text-xs font-mono">
          <button
            onClick={() => handleToggle('blocked')}
            data-local="toggle-hero-blocked"
            className={`px-2.5 py-1 rounded text-[11px] transition-all font-medium ${
              mode === 'blocked'
                ? 'bg-[#EF4444] text-white shadow-sm'
                : 'text-[#8C96A5] hover:text-white'
            }`}
          >
            Blocked Attack
          </button>
          <button
            onClick={() => handleToggle('safe')}
            data-local="toggle-hero-safe"
            className={`px-2.5 py-1 rounded text-[11px] transition-all font-medium ${
              mode === 'safe'
                ? 'bg-[#10B981] text-white shadow-sm'
                : 'text-[#8C96A5] hover:text-white'
            }`}
          >
            Permitted Read
          </button>
        </div>
      </div>

      {/* Centerpiece: The TripLine Brand Mark & Intercept Plane */}
      <div className="relative flex flex-col items-center justify-center py-5">
        {/* Interactive Logo Mark with 3D tilt */}
        <div className="relative z-10 p-4 rounded-2xl bg-gradient-to-b from-[#181B22] to-[#121418] border border-[#2A303D] shadow-inner transition-transform duration-300">
          <TripLineLogo
            size="hero"
            variant="dark"
            showWordmark={false}
            animated={true}
            interactive={true}
          />
        </div>

        {/* Dynamic Status Beacon */}
        <div className="mt-5 flex flex-col items-center text-center">
          {isEvaluating ? (
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#181B22] border border-[#2E3543] text-xs font-mono text-[#F97316] animate-pulse">
              <span className="w-2 h-2 rounded-full bg-[#F97316] animate-ping" />
              <span>Evaluating session plan...</span>
            </div>
          ) : mode === 'blocked' ? (
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-red-950/40 border border-red-800/60 text-xs font-mono text-red-400 font-medium">
              <XCircle className="w-3.5 h-3.5 text-red-400" />
              <span>VERDICT: DENIED (Out of plan: delete_branch)</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-950/40 border border-emerald-800/60 text-xs font-mono text-emerald-400 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>VERDICT: AUTHORIZED (In plan: read_file)</span>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Process Strip: Request -> Gate -> MCP -> Evidence */}
      <div className="mt-6 pt-5 border-t border-[#20242C] grid grid-cols-3 gap-2 text-center font-mono text-[11px]">
        <div className="p-2.5 rounded-xl bg-[#16181E] border border-[#242933]">
          <span className="text-[#64748B] block text-[9px] uppercase tracking-wider">01 Ingress</span>
          <span className="text-white font-semibold block truncate mt-0.5">
            {mode === 'blocked' ? 'delete_branch' : 'read_file'}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-[#16181E] border border-[#242933]">
          <span className="text-[#64748B] block text-[9px] uppercase tracking-wider">02 ArmorIQ Gate</span>
          <span
            className={`font-semibold block truncate mt-0.5 ${
              mode === 'blocked' ? 'text-red-400' : 'text-emerald-400'
            }`}
          >
            {mode === 'blocked' ? 'DENY (Out of Plan)' : 'ALLOW (In Plan)'}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-[#16181E] border border-[#242933]">
          <span className="text-[#64748B] block text-[9px] uppercase tracking-wider">03 Evidence</span>
          <span className="text-[#F97316] font-semibold block truncate mt-0.5">
            {mode === 'blocked' ? 'Signed Receipt' : 'Clean Dispatch'}
          </span>
        </div>
      </div>
    </div>
  )
}
