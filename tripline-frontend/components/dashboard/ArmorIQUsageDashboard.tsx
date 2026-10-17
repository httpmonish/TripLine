'use client'

import React, { useState } from 'react'
import { Shield, Activity } from 'lucide-react'

interface DayData {
  id: string
  label: string
  date: string
  allowed: number
  held: number
  denied: number
  isSelected?: boolean
}

// Exact timeline matching ArmorIQ control plane telemetry
const ARMORIQ_DECISIONS_DATA: DayData[] = [
  { id: 'sep-18', label: 'Sep 18', date: 'Sep 18', allowed: 0, held: 0, denied: 0 },
  { id: 'sep-21', label: '21', date: 'Sep 21', allowed: 0, held: 0, denied: 0 },
  { id: 'sep-24', label: '24', date: 'Sep 24', allowed: 0, held: 0, denied: 0 },
  { id: 'sep-27', label: '27', date: 'Sep 27', allowed: 0, held: 0, denied: 0 },
  { id: 'sep-30', label: '30', date: 'Sep 30', allowed: 0, held: 0, denied: 0 },
  { id: 'oct-03', label: '03', date: 'Oct 03', allowed: 110, held: 0, denied: 210 },
  { id: 'oct-04', label: '', date: 'Oct 04', allowed: 95, held: 0, denied: 255 },
  { id: 'oct-05', label: '', date: 'Oct 05', allowed: 175, held: 0, denied: 280 },
  { id: 'oct-06', label: '06', date: 'Oct 06', allowed: 0, held: 0, denied: 0 },
  { id: 'oct-09', label: '09', date: 'Oct 09', allowed: 0, held: 0, denied: 0 },
  { id: 'oct-10', label: '', date: 'Oct 10', allowed: 210, held: 0, denied: 360 },
  { id: 'oct-11', label: '', date: 'Oct 11', allowed: 70, held: 0, denied: 85 },
  { id: 'oct-12', label: '12', date: 'Oct 12', allowed: 0, held: 0, denied: 0 },
  { id: 'oct-15', label: '15', date: 'Oct 15', allowed: 0, held: 0, denied: 0 },
  { id: 'oct-16', label: '', date: 'Oct 16', allowed: 0, held: 0, denied: 22 },
  { id: 'oct-17', label: '17', date: 'Oct 17', allowed: 321, held: 0, denied: 527, isSelected: true },
]

const SEVERITY_FINDINGS = [
  { level: 'Critical', color: 'bg-[#DC2626]', count: 0, pct: '0%' },
  { level: 'High', color: 'bg-[#D97706]', count: 0, pct: '0%' },
  { level: 'Medium', color: 'bg-[#A8A29E]', count: 0, pct: '0%' },
  { level: 'Low', color: 'bg-[#16A34A]', count: 0, pct: '0%' },
]

export function ArmorIQUsageDashboard() {
  const [selectedDay, setSelectedDay] = useState<DayData>(
    ARMORIQ_DECISIONS_DATA.find((d) => d.id === 'oct-17') || ARMORIQ_DECISIONS_DATA[ARMORIQ_DECISIONS_DATA.length - 1]
  )
  const [hoveredDay, setHoveredDay] = useState<DayData | null>(null)

  const activeDay = hoveredDay || selectedDay
  const maxVal = 900 // Exact scale from ArmorIQ dashboard

  return (
    <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-6 text-[#1E293B]">
      {/* ── CARD 1: DECISIONS STACKED BAR CHART ── */}
      <div className="bg-white rounded-2xl border border-[#E2E8F0] p-6 sm:p-7 shadow-xs flex flex-col justify-between relative">
        {/* Top Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <h3 className="text-xl font-bold text-[#0F172A] tracking-tight">Decisions</h3>

          {/* Legend */}
          <div className="flex items-center gap-4 text-xs text-[#64748B]">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#D6D3D1]" />
              <span>Allowed</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#EA580C]" />
              <span>Held</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#A13E22]" />
              <span>Denied</span>
            </div>
          </div>
        </div>

        {/* Chart Viewport */}
        <div className="relative h-[230px] w-full flex flex-col justify-between pt-2">
          {/* Background Grid Lines & Y-Labels */}
          <div className="absolute inset-0 flex flex-col justify-between pointer-events-none pb-7">
            {[900, 675, 450, 225, 0].map((val) => (
              <div key={val} className="flex items-center gap-2.5 w-full">
                <span className="w-8 text-right font-sans text-xs text-[#94A3B8] tabular-nums select-none">
                  {val}
                </span>
                <div className="flex-1 border-b border-[#F1F5F9]" />
              </div>
            ))}
          </div>

          {/* Bars Container */}
          <div className="relative pl-10 pr-2 h-[195px] flex items-end justify-between gap-1.5 z-10">
            {ARMORIQ_DECISIONS_DATA.map((day, idx) => {
              const isSelected = activeDay.id === day.id
              const hasActivity = day.allowed > 0 || day.held > 0 || day.denied > 0

              const allowedHeight = (day.allowed / maxVal) * 195
              const heldHeight = (day.held / maxVal) * 195
              const deniedHeight = (day.denied / maxVal) * 195
              const totalHeight = allowedHeight + heldHeight + deniedHeight

              // Right-align tooltip on the last bars so it never clips beyond card
              const isFarRight = idx >= ARMORIQ_DECISIONS_DATA.length - 3

              return (
                <div
                  key={day.id}
                  className="flex-1 flex flex-col items-center justify-end h-full relative group cursor-pointer"
                  onMouseEnter={() => setHoveredDay(day)}
                  onMouseLeave={() => setHoveredDay(null)}
                  onClick={() => setSelectedDay(day)}
                >
                  {/* Tooltip on Active Bar */}
                  {isSelected && (
                    <div
                      className={`absolute -top-[98px] ${
                        isFarRight ? 'right-0 sm:right-auto sm:left-1/2 sm:-translate-x-1/2' : 'left-1/2 -translate-x-1/2'
                      } z-30 pointer-events-none bg-white rounded-lg shadow-xl border border-[#E2E8F0] px-3.5 py-2.5 text-xs min-w-[130px] whitespace-nowrap animate-in fade-in zoom-in-95 duration-150`}
                    >
                      <div className="font-semibold text-[#0F172A] pb-1.5 border-b border-[#F1F5F9] mb-1.5 text-xs">
                        {day.date}
                      </div>
                      <div className="flex items-center justify-between gap-4 text-[#64748B] text-xs">
                        <span className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-[#D6D3D1]" />
                          Allowed
                        </span>
                        <strong className="text-[#0F172A] font-bold">{day.allowed}</strong>
                      </div>
                      <div className="flex items-center justify-between gap-4 text-[#64748B] text-xs">
                        <span className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-[#EA580C]" />
                          Held
                        </span>
                        <strong className="text-[#0F172A] font-bold">{day.held}</strong>
                      </div>
                      <div className="flex items-center justify-between gap-4 text-[#64748B] text-xs">
                        <span className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-[#A13E22]" />
                          Denied
                        </span>
                        <strong className="text-[#0F172A] font-bold">{day.denied}</strong>
                      </div>
                    </div>
                  )}

                  {/* Stacked Bar Pillar */}
                  {hasActivity ? (
                    <div
                      className={`w-full max-w-[18px] flex flex-col-reverse rounded-t-xs overflow-hidden transition-all duration-200 ${
                        isSelected
                          ? 'ring-2 ring-[#EA580C] shadow-sm'
                          : 'hover:opacity-90'
                      }`}
                      style={{ height: `${Math.max(totalHeight, 4)}px` }}
                    >
                      {/* 1. Allowed (Bottom segment) */}
                      {day.allowed > 0 && (
                        <div
                          className="w-full bg-[#D6D3D1]"
                          style={{ height: `${allowedHeight}px` }}
                        />
                      )}
                      {/* 2. Held (Middle segment) */}
                      {day.held > 0 && (
                        <div
                          className="w-full bg-[#EA580C]"
                          style={{ height: `${heldHeight}px` }}
                        />
                      )}
                      {/* 3. Denied (Top segment) */}
                      {day.denied > 0 && (
                        <div
                          className="w-full bg-[#A13E22]"
                          style={{ height: `${deniedHeight}px` }}
                        />
                      )}
                    </div>
                  ) : (
                    <div className="w-full max-w-[18px] h-0" />
                  )}
                </div>
              )
            })}
          </div>

          {/* X-Axis Date Labels: Spaced intervals exactly matching ArmorIQ control plane */}
          <div className="pl-10 pr-2 flex justify-between items-center text-xs text-[#94A3B8] pt-2 select-none">
            {ARMORIQ_DECISIONS_DATA.map((day) => {
              const isSelected = activeDay.id === day.id
              return (
                <div
                  key={day.id}
                  className={`flex-1 text-center font-sans ${
                    isSelected ? 'font-bold text-[#0F172A]' : ''
                  }`}
                >
                  {day.label}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* ── CARD 2: OPEN FINDINGS BY SEVERITY ── */}
      <div className="bg-white rounded-2xl border border-[#E2E8F0] p-6 sm:p-7 shadow-xs flex flex-col justify-between">
        {/* Top Header */}
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-[#F1F5F9] mb-6">
            <h3 className="text-xl font-bold text-[#0F172A] tracking-tight">
              Open findings by severity
            </h3>
            <div className="flex items-center gap-1.5 text-xs text-[#64748B]">
              <Shield className="w-3.5 h-3.5 text-[#94A3B8]" />
              <span>0 open</span>
            </div>
          </div>

          {/* Severity Rows */}
          <div className="space-y-4 pt-1">
            {SEVERITY_FINDINGS.map((sev) => (
              <div key={sev.level} className="flex items-center gap-3 text-xs">
                {/* Dot + Label */}
                <div className="flex items-center gap-2.5 w-24 shrink-0">
                  <span className={`w-2.5 h-2.5 rounded-full ${sev.color} shrink-0`} />
                  <span className="font-medium text-[#1E293B] text-xs">{sev.level}</span>
                </div>

                {/* Segmented Progress Track (24 segments, responsive) */}
                <div className="flex-1 flex items-center gap-[3px] overflow-hidden py-1">
                  {Array.from({ length: 24 }).map((_, idx) => (
                    <div
                      key={idx}
                      className="h-4 w-[6px] rounded-[1px] bg-[#E5E7EB] transition-colors"
                    />
                  ))}
                </div>

                {/* Count & Percentage */}
                <div className="flex items-center gap-3 shrink-0 pl-1">
                  <span className="font-bold text-[#0F172A] w-4 text-right text-xs">{sev.count}</span>
                  <span className="text-[#94A3B8] w-7 text-right text-xs">{sev.pct}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Callout Banner */}
        <div className="mt-6 rounded-xl p-3.5 bg-[#FAF9F6] border border-[#F1E8DC] flex items-start gap-3">
          <Activity className="w-4 h-4 text-[#C2410C] shrink-0 mt-0.5" />
          <p className="text-xs text-[#475569] leading-relaxed">
            Open findings are concentrated in Critical and High severities. Clearing these clusters reduces exposure fastest; Medium and Low await backend aggregation.
          </p>
        </div>
      </div>
    </div>
  )
}
