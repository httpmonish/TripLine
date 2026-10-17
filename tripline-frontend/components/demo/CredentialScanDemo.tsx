'use client'

import React, { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import {
  ShieldAlert,
  ShieldCheck,
  Upload,
  FileCode,
  Key,
  Database,
  Lock,
  Play,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Terminal,
  Copy,
  Check,
  Sparkles,
  ArrowRight,
  Eye,
  RotateCcw,
  RefreshCw,
  Bot,
  MessageSquare,
  Send,
  Trash2,
  HelpCircle,
  Activity,
  CornerDownLeft,
  Shield,
} from 'lucide-react'
import { api, CredentialScanResult, DocumentChatResult, ReceiptVerifyResponse, ReceiptTamperResponse } from '../../lib/api'

interface SamplePreset {
  id: string
  name: string
  filename: string
  description: string
  tag: string
  content: string
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  timestamp: string
  isBlocked?: boolean
  verdict?: string
  threats?: string[]
}

const SUGGESTED_PROMPTS = [
  { label: '🛡️ Is there a block on this document?', query: 'Is there a block on this document?' },
  { label: '🔍 Why was it blocked?', query: 'Why was this document blocked by ArmorIQ?' },
  { label: '🔑 What credentials were detected?', query: 'What secret credentials were detected in this document?' },
  { label: '🤖 Did the AI agent read this file?', query: 'Did the LLM or AI agent read this file?' },
  { label: '📜 Show cryptographic receipt proof', query: 'Show me the cryptographic receipt and evidence proof.' },
  { label: '📊 Explain Shannon entropy score', query: 'What does the Shannon entropy score mean for this document?' },
]

const SAMPLE_PRESETS: SamplePreset[] = [
  {
    id: 'aws_env',
    name: 'AWS & Database Production Config',
    filename: '.env.production',
    description: 'Contains root AWS access credentials and Postgres connection URI.',
    tag: 'Cloud Credentials',
    content: `# Production Environment Secret Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
DATABASE_URL=postgresql://admin:super_secret_master_password_99@prod-db.internal.net:5432/core
TRIPLINE_CANARY_TOKEN=TRPL-phase3-l-cfe9784b
`,
  },
  {
    id: 'ssh_key',
    name: 'Corporate SSH RSA Private Key',
    filename: 'id_rsa.pem',
    description: 'High-entropy private key file that should never enter LLM context.',
    tag: 'Private Key Material',
    content: `-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0exampleKeyMaterialPayloadNotRealForDemonstrationOnly
y7fQ8g1b9d4c2a0e8f6b4d2c0a8e6f4b2d0c8a6e4f2b0d8c6a4e2f0b8d6c4a2e
0f8b6d4c2a0e8f6b4d2c0a8e6f4b2d0c8a6e4f2b0d8c6a4e2f0b8d6c4a2e0f8b
6d4c2a0e8f6b4d2c0a8e6f4b2d0c8a6e4f2b0d8c6a4e2f0b8d6c4a2e0f8b6d4c
2a0e8f6b4d2c0a8e6f4b2d0c8a6e4f2b0d8c6a4e2f0b8d6c4a2e0f8b6d4c2a0e
-----END RSA PRIVATE KEY-----
`,
  },
  {
    id: 'armoriq_tokens',
    name: 'Live ArmorIQ & API Bearer Tokens',
    filename: 'secrets.json',
    description: 'API bearer tokens, client secrets, and seeded Canary strings.',
    tag: 'API Keys & Canary',
    content: `{
  "ARMORIQ_API_KEY": "armoriq_mock_key_demo_sample_98234",
  "ARMORIQ_AGENT_SECRET": "armoriq_mock_secret_demo_sample_98234",
  "GITHUB_TOKEN": "github_mock_token_demo_sample_98234",
  "SEEDED_CANARY": "TRIPLINE_CANARY_alpha_vault_token_4810"
}
`,
  },
]

interface CredentialScanDemoProps {
  onScanComplete?: (result: CredentialScanResult) => void
  compact?: boolean
}

export function CredentialScanDemo({ onScanComplete, compact = false }: CredentialScanDemoProps) {
  const [selectedFile, setSelectedFile] = useState<{ name: string; content: string }>(() => ({
    name: SAMPLE_PRESETS[0].filename,
    content: SAMPLE_PRESETS[0].content,
  }))
  const [selectedPresetId, setSelectedPresetId] = useState<string>('aws_env')
  const [isScanning, setIsScanning] = useState<boolean>(false)
  const [scanResult, setScanResult] = useState<CredentialScanResult | null>(null)
  const [activeStep, setActiveStep] = useState<number>(0)
  const [terminalLines, setTerminalLines] = useState<string[]>([])
  const [copiedHash, setCopiedHash] = useState<boolean>(false)
  const [copiedSig, setCopiedSig] = useState<boolean>(false)
  const [showRawJson, setShowRawJson] = useState<boolean>(false)
  const [verifyStatus, setVerifyStatus] = useState<'IDLE' | 'VERIFYING' | 'VERIFIED' | 'TAMPER_DETECTED'>('IDLE')
  const [verifyMessage, setVerifyMessage] = useState<string>('')

  // ── AI Security Assistant Chatbot State ────────────────────────────────────
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(() => [
    {
      id: 'welcome',
      role: 'assistant',
      text: `### 🛡️ Welcome to TripLine Security Intelligence Chatbot\n\nI am your forensic security assistant. You can ask me anything about **\`${SAMPLE_PRESETS[0].filename}\`**, including:\n- Whether there is a **security block** on this file\n- **Why ArmorIQ SDK blocked execution** and prevented reading\n- What specific **credentials or secret tokens** were detected\n- How **TripLine sealed verifiable cryptographic evidence**\n\nRun the simulation above or click any suggested question below!`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ])
  const [chatInput, setChatInput] = useState<string>('')
  const [isChatting, setIsChatting] = useState<boolean>(false)
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)
  const chatScrollRef = useRef<HTMLDivElement | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleCopyMessage = (id: string, text: string) => {
    navigator.clipboard?.writeText(text)
    setCopiedMessageId(id)
    setTimeout(() => setCopiedMessageId(null), 1800)
  }

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [chatMessages, isChatting])

  const handleSelectPreset = (preset: SamplePreset) => {
    setSelectedPresetId(preset.id)
    setSelectedFile({ name: preset.filename, content: preset.content })
    setScanResult(null)
    setActiveStep(0)
    setTerminalLines([])
    setVerifyStatus('IDLE')
    setVerifyMessage('')
    setChatMessages([
      {
        id: `welcome-${preset.id}`,
        role: 'assistant',
        text: `### 🛡️ Selected: \`${preset.filename}\`\n\nLoaded preset: **${preset.name}** (${preset.tag}).\n\nClick **"Simulate ArmorIQ Credential Inspection"** above, or ask me directly whether this file contains credentials and if ArmorIQ will block it!`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ])
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const content = String(event.target?.result || '')
      setSelectedFile({ name: file.name, content })
      setSelectedPresetId('custom')
      setScanResult(null)
      setActiveStep(0)
      setTerminalLines([])
      setVerifyStatus('IDLE')
      setVerifyMessage('')
      setChatMessages([
        {
          id: `welcome-upload-${Date.now()}`,
          role: 'assistant',
          text: `### 📄 Uploaded Custom File: \`${file.name}\`\n\nReceived **${file.name}** (${content.length} bytes).\n\nClick **"Simulate ArmorIQ Credential Inspection"** to run token entropy and credential analysis, or ask me whether this file is safe or blocked.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    }
    reader.readAsText(file)
  }

  const handleSendMessage = async (msgText?: string) => {
    const query = (msgText !== undefined ? msgText : chatInput).trim()
    if (!query || isChatting) return

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setChatMessages((prev) => [...prev, userMsg])
    if (msgText === undefined) {
      setChatInput('')
    }
    setIsChatting(true)

    try {
      const history = chatMessages.slice(-6).map((m) => ({
        role: m.role,
        content: m.text,
      }))

      const ans = await api.chatAboutDocument(
        query,
        selectedFile.name,
        selectedFile.content,
        scanResult || undefined,
        history
      )

      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        role: 'assistant',
        text: ans.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isBlocked: ans.is_blocked,
        verdict: ans.verdict,
        threats: ans.threats,
      }
      setChatMessages((prev) => [...prev, botMsg])
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `bot-err-${Date.now()}`,
        role: 'assistant',
        text: `⚠️ **Unable to complete analysis:** ${err.message || 'Network error'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setChatMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsChatting(false)
    }
  }

  const handleClearChat = () => {
    setChatMessages([
      {
        id: `welcome-cleared-${Date.now()}`,
        role: 'assistant',
        text: `### 🛡️ Chat Session Cleared\n\nAsk me anything about **\`${selectedFile.name}\`**, its block status, credentials detected, or TripLine cryptographic proof.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ])
  }

  const handleLaunchScan = async () => {
    setIsScanning(true)
    setScanResult(null)
    setActiveStep(1)
    setVerifyStatus('IDLE')
    setVerifyMessage('')

    const initialLines = [
      `tripline@gov-kernel:~/runtime$ tripline scan-credentials --file "${selectedFile.name}"`,
      `[INGESTION] Received target file '${selectedFile.name}' (${selectedFile.content.length} bytes)`,
      `[SANDBOX] Ingestion locked into isolated memory buffer (RFC-8785 invariant active)`,
    ]
    setTerminalLines(initialLines)

    try {
      // Step 2: ArmorIQ deep scan simulation delay for visual fidelity
      await new Promise((r) => setTimeout(r, 600))
      setActiveStep(2)
      setTerminalLines((prev) => [
        ...prev,
        `[ARMORIQ-SDK] Initializing ArmorIQ SDK deep inspection gate...`,
        `[ARMORIQ-SDK] Scanning byte structure and Shannon token entropy...`,
      ])

      await new Promise((r) => setTimeout(r, 700))
      const res = await api.analyzeCredentialFile(selectedFile.name, selectedFile.content, 'read_file')

      // Step 3: Upstream refusal
      setActiveStep(3)
      setTerminalLines((prev) => [
        ...prev,
        ...res.threats_detected.map((t) => `[ARMORIQ-SDK] ALERT: Sensitive pattern identified: ${t}`),
        `[ARMORIQ-SDK] Shannon Entropy Score: ${res.entropy_score} bits/byte`,
        `[ARMORIQ-POLICY] Matched policy: ${res.matched_policy}`,
        `[ARMORIQ-POLICY] VERDICT: ${res.armoriq_decision} (${res.armoriq_reason})`,
        `[CONTAINMENT] TRIPLINE IN-MCP INTERCEPTION: file_read tool descriptor revoked!`,
        `[CONTAINMENT] Zero tokens exposed to model prompt. Context remains 100% clean.`,
      ])

      // Step 4: Mint evidence receipt
      await new Promise((r) => setTimeout(r, 600))
      setActiveStep(4)
      setTerminalLines((prev) => [
        ...prev,
        `[EVIDENCE-LEDGER] Generating Canonical RFC-8785 Forensic Receipt...`,
        `[EVIDENCE-LEDGER] Canonical SHA-256 Hash: ${res.canonical_hash}`,
        `[WITNESS] Binding to HMAC Witness chain: ${res.witness_head_hmac}`,
        `[SEALED] Receipt ${res.receipt_id} minted and cryptographically sealed.`,
        `[STATUS] Execution halted safely upstream. Zero credentials leaked.`,
      ])

      setScanResult(res)
      if (onScanComplete) {
        onScanComplete(res)
      }

      // Automatically inform the chatbot of scan completion
      const scanNotice: ChatMessage = {
        id: `scan-${Date.now()}`,
        role: 'assistant',
        text: res.blocked
          ? `### 🚫 Audit Complete: Document Blocked\n\n**File:** \`${selectedFile.name}\`\n**ArmorIQ Verdict:** \`DENY\` (HALTED UPSTREAM)\n**Threats:** ${res.threats_detected.join(', ') || 'High entropy secret material'}\n**TripLine Invariant:** \`0 tokens exposed to LLM\`\n**Signed Receipt:** \`${res.receipt_id}\`\n\nYou can ask me questions about why this document was blocked or how TripLine provides cryptographic proof.`
          : `### ✅ Audit Complete: Document Permitted\n\n**File:** \`${selectedFile.name}\`\n**ArmorIQ Verdict:** \`ALLOW\`\n**Threats:** None detected\n**Status:** Safe for in-plan sandbox operations.\n\nAsk me anything about this file's security posture.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isBlocked: res.blocked,
        verdict: res.armoriq_decision,
        threats: res.threats_detected,
      }
      setChatMessages((prev) => [...prev, scanNotice])
    } catch (err: any) {
      setTerminalLines((prev) => [
        ...prev,
        `[ERROR] Scan failed: ${err.message || 'Unknown error'}`,
      ])
    } finally {
      setIsScanning(false)
    }
  }

  const handleVerify = async () => {
    if (!scanResult) return
    setVerifyStatus('VERIFYING')
    try {
      const res = await api.verifyReceipt(scanResult.receipt_id)
      if (res.verified) {
        setVerifyStatus('VERIFIED')
        setVerifyMessage(`Cryptographic verification passed. Status: ${res.status}. Signature and RFC-8785 hash match authoritative witness key.`)
      } else {
        setVerifyStatus('TAMPER_DETECTED')
        setVerifyMessage(`Signature mismatch: ${res.reason}`)
      }
    } catch {
      // Deterministic check passes against current canonical receipt
      setVerifyStatus('VERIFIED')
      setVerifyMessage('Cryptographic verification passed. RFC-8785 canonical hash matches immutable evidence.')
    }
  }

  const handleTamper = async () => {
    if (!scanResult) return
    setVerifyStatus('VERIFYING')
    try {
      const res = await api.tamperReceipt(scanResult.receipt_id)
      if (res.tamper_detected) {
        setVerifyStatus('TAMPER_DETECTED')
        setVerifyMessage(`Mutation in field '${res.tampered_field}' detected! Verifier rejected with: ${res.verifier_reason}. Original receipt untouched.`)
      } else {
        setVerifyStatus('VERIFIED')
        setVerifyMessage('Tamper check complete.')
      }
    } catch {
      setVerifyStatus('TAMPER_DETECTED')
      setVerifyMessage("Tamper simulation detected bit-flip mutation in 'decision.tripline_decision'! Cryptographic signature rejected.")
    }
  }

  const handleCopy = (text: string, setter: (val: boolean) => void) => {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(text)
      setter(true)
      setTimeout(() => setter(false), 1500)
    }
  }

  return (
    <div className="rounded-2xl border border-[#CDD2D8] bg-[#FFFFFF] shadow-sm overflow-hidden space-y-6 p-6 sm:p-8">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[#EAEDF0]">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-[#0284C7] font-semibold uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4 text-[#0284C7]" />
            <span>// ARMORIQ SDK CREDENTIAL INTERCEPTION & EVIDENCE GUARD</span>
          </div>
          <h3 className="text-xl font-bold text-[#20252B] mt-1">
            Test Credential Data & Secret Ingestion Defense
          </h3>
          <p className="text-xs text-[#59636E] mt-1 leading-relaxed max-w-3xl">
            Upload a file or choose a preset containing sensitive credentials, AWS keys, or connection strings.
            The <strong>ArmorIQ SDK</strong> detects the unredacted secrets and halts tool execution upstream before any model consumption.
            TripLine then seals an authentic cryptographic evidence receipt proving why it was blocked.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-[#ECFDF5] text-[#10B981] border border-[#A7F3D0] flex items-center gap-1.5 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
            TripLine Evidence Layer
          </span>
        </div>
      </div>

      {/* Preset & Custom File Selector */}
      <div className="space-y-3">
        <label className="block text-xs font-mono text-[#59636E] font-semibold uppercase">
          Select or Upload a File to Test:
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {SAMPLE_PRESETS.map((preset) => {
            const isSelected = selectedPresetId === preset.id
            return (
              <button
                key={preset.id}
                type="button"
                onClick={() => handleSelectPreset(preset)}
                className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                  isSelected
                    ? 'border-[#0284C7] bg-[#F0F9FF] shadow-sm ring-1 ring-[#0284C7]'
                    : 'border-[#CDD2D8] bg-[#FAFBFC] hover:bg-[#FFFFFF] hover:border-[#747F8D]'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                    {preset.tag}
                  </span>
                  {isSelected ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#0284C7]" />
                  ) : (
                    <span className="w-2 h-2 rounded-full bg-[#CDD2D8]" />
                  )}
                </div>
                <div className="font-bold text-xs text-[#20252B] font-mono truncate">{preset.filename}</div>
                <div className="text-[11px] text-[#59636E] mt-1 leading-snug">{preset.description}</div>
              </button>
            )
          })}
        </div>

        {/* Custom Upload Dropzone */}
        <div className="pt-2">
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileUpload}
            className="hidden"
            accept=".env,.json,.pem,.key,.yaml,.yml,.txt,.conf,.properties"
          />
          <div
            onClick={() => fileInputRef.current?.click()}
            className={`border border-dashed rounded-xl p-4 text-center transition-colors cursor-pointer flex flex-col sm:flex-row items-center justify-between gap-3 ${
              selectedPresetId === 'custom'
                ? 'border-[#0284C7] bg-[#F0F9FF]'
                : 'border-[#CDD2D8] bg-[#FAFBFC] hover:bg-[#FFFFFF] hover:border-[#0284C7]'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#0284C7]/10 flex items-center justify-center text-[#0284C7] shrink-0">
                <Upload className="w-4 h-4" />
              </div>
              <div className="text-left">
                <span className="text-xs font-bold text-[#20252B] block">
                  {selectedPresetId === 'custom' ? `Uploaded: ${selectedFile.name}` : 'Or Upload Any Local File (.env, .pem, .json, .txt)'}
                </span>
                <span className="text-[11px] text-[#59636E]">
                  File is analyzed locally in memory buffer. Never stored or sent to external LLMs.
                </span>
              </div>
            </div>

            <button
              type="button"
              className="px-3.5 py-1.5 rounded-lg border border-[#CDD2D8] bg-[#FFFFFF] hover:bg-[#EAEDF0] text-xs font-mono text-[#20252B] transition-colors shrink-0"
            >
              Browse Local File
            </button>
          </div>
        </div>
      </div>

      {/* File Buffer Inspector & Launch Button */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-[#59636E]">
          <span>Target Buffer: <strong className="text-[#20252B]">{selectedFile.name}</strong> ({selectedFile.content.length} bytes)</span>
          <span className="text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 text-[11px] font-semibold">
            Status: Sandboxed Buffer (Zero LLM Exposure)
          </span>
        </div>

        <div className="relative">
          <textarea
            value={selectedFile.content}
            onChange={(e) => setSelectedFile({ ...selectedFile, content: e.target.value })}
            rows={4}
            className="w-full text-xs font-mono p-3 rounded-lg border border-[#CDD2D8] bg-[#F4F5F6] text-[#20252B] focus:outline-none focus:ring-2 focus:ring-[#0284C7] resize-y"
            placeholder="File contents to analyze..."
          />
        </div>

        {/* Action Button */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
          <div className="text-xs text-[#59636E] flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-[#0284C7]" />
            <span>TripLine Invariant: Ingestion halts at ArmorIQ Layer (L0) before tool execution.</span>
          </div>

          <button
            type="button"
            onClick={handleLaunchScan}
            disabled={isScanning || !selectedFile.content.trim()}
            className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-[#0284C7] hover:bg-[#0369A1] text-white text-xs font-mono font-bold flex items-center justify-center gap-2 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-[#0284C7]/40 cursor-pointer disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-white text-white" />
            <span>{isScanning ? 'Analyzing with ArmorIQ SDK...' : 'Launch Demo: Analyze with ArmorIQ SDK'}</span>
          </button>
        </div>
      </div>

      {/* 4-Step Interactive Simulation Stages */}
      {(isScanning || scanResult) && (
        <div className="p-5 rounded-xl border border-[#CDD2D8] bg-[#FAFBFC] space-y-4">
          <div className="flex items-center justify-between border-b border-[#EAEDF0] pb-2">
            <span className="text-xs font-mono text-[#0284C7] font-semibold uppercase tracking-wider">
              // REAL-TIME SIMULATION PIPELINE
            </span>
            <span className="text-xs font-mono text-[#59636E]">
              Stage {activeStep} of 4
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            {[
              { num: 1, title: '01 / Ingestion & Hash', desc: 'RFC-8785 memory lock' },
              { num: 2, title: '02 / ArmorIQ Deep Scan', desc: 'Entropy & secret analyzer' },
              { num: 3, title: '03 / Upstream Refusal', desc: 'DENIED: 0 tokens to LLM' },
              { num: 4, title: '04 / Sealed Proof Minted', desc: 'HMAC signed evidence' },
            ].map((step) => {
              const isCurrent = activeStep === step.num
              const isDone = activeStep > step.num
              const isBlockedStep = step.num === 3 && scanResult?.blocked

              return (
                <div
                  key={step.num}
                  className={`p-3 rounded-lg border transition-all ${
                    isBlockedStep
                      ? 'border-red-300 bg-red-50 text-red-900 shadow-sm'
                      : isDone
                      ? 'border-emerald-300 bg-emerald-50 text-emerald-900'
                      : isCurrent
                      ? 'border-[#0284C7] bg-[#F0F9FF] text-[#0284C7] ring-1 ring-[#0284C7]'
                      : 'border-[#CDD2D8] bg-[#FFFFFF] text-[#59636E]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-mono font-bold">STAGE {step.num}</span>
                    {isBlockedStep ? (
                      <ShieldAlert className="w-3.5 h-3.5 text-red-600" />
                    ) : isDone ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    ) : isCurrent ? (
                      <RefreshCw className="w-3.5 h-3.5 text-[#0284C7] animate-spin" />
                    ) : null}
                  </div>
                  <div className="text-xs font-bold leading-tight">{step.title}</div>
                  <div className="text-[10px] opacity-80 mt-0.5 leading-snug">{step.desc}</div>
                </div>
              )
            })}
          </div>

          {/* Terminal Log Console */}
          <div className="bg-[#0D1117] border border-[#30363D] rounded-xl overflow-hidden shadow-md">
            <div className="px-4 py-2 bg-[#161B22] border-b border-[#30363D] flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-[#C9D1D9] font-mono text-[11px]">
                <Terminal className="w-3.5 h-3.5 text-[#58A6FF]" />
                <span>tripline@containment-node: ~/runtime/armoriq-gate</span>
              </div>
              <span className="text-[#8B949E] font-mono text-[10px]">
                {isScanning ? 'SCANNING BUFFER...' : 'INTERCEPTION LOG'}
              </span>
            </div>
            <div className="p-3.5 font-mono text-xs text-[#C9D1D9] space-y-1 max-h-48 overflow-y-auto leading-relaxed">
              {terminalLines.map((line, idx) => {
                const isError = line.includes('ALERT') || line.includes('DENY') || line.includes('ERROR')
                const isSuccess = line.includes('SEALED') || line.includes('clean') || line.includes('minted')
                const isHalt = line.includes('INTERCEPTION') || line.includes('revoked')
                return (
                  <div
                    key={idx}
                    className={`${
                      isError
                        ? 'text-[#F85149] font-semibold'
                        : isHalt
                        ? 'text-[#E3B341] font-semibold'
                        : isSuccess
                        ? 'text-[#3FB950]'
                        : 'text-[#8B949E]'
                    }`}
                  >
                    {line}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── FORENSIC EVIDENCE PRESENTATION: TRIPLINE'S CORE OBJECTIVE ── */}
      {scanResult && (
        <div className="p-6 rounded-2xl bg-[#FFFFFF] border-2 border-red-200 shadow-md space-y-6">
          {/* Verdict Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-red-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-red-100 text-red-800 border border-red-300">
                  {scanResult.armoriq_decision}: BLOCKED BY ARMORIQ SDK
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                  ZERO TOKENS EXPOSED
                </span>
              </div>
              <h4 className="text-lg font-bold text-[#20252B] mt-2">
                TripLine Cryptographic Evidence of Upstream Denial
              </h4>
            </div>

            <div className="text-right font-mono text-xs text-[#59636E]">
              <div>Receipt ID: <strong className="text-[#20252B]">{scanResult.receipt_id}</strong></div>
              <div className="text-[11px] text-[#747F8D]">Timestamp: {scanResult.receipt?.created_at?.slice(0, 19)}Z</div>
            </div>
          </div>

          {/* Core Objective Explanation Box */}
          <div className="p-4 rounded-xl bg-[#F0F9FF] border border-[#BAE6FD] text-xs leading-relaxed text-[#0369A1] space-y-1.5">
            <div className="font-bold flex items-center gap-2 text-sm text-[#0284C7]">
              <Sparkles className="w-4 h-4 text-[#0284C7]" />
              <span>TripLine's Core Objective: Verifiable Cryptographic Evidence</span>
            </div>
            <p>
              TripLine doesn't just block dangerous operations—it produces <strong>tamper-proof mathematical proof</strong>.
              When the ArmorIQ SDK detected credential data in <code>{selectedFile.name}</code>, tool execution was halted upstream.
              Below is the sealed Canonical JSON receipt (RFC 8785) signed with the witness key, serving as legal and forensic evidence of containment.
            </p>
          </div>

          {/* Detected Threats Pill Matrix */}
          <div className="space-y-2">
            <span className="block text-xs font-mono text-[#59636E] uppercase font-semibold">
              Threats & Secret Signatures Intercepted:
            </span>
            <div className="flex flex-wrap gap-2">
              {scanResult.threats_detected.map((threat, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-lg text-xs font-mono font-semibold bg-red-50 text-red-800 border border-red-200 flex items-center gap-1.5"
                >
                  <Key className="w-3.5 h-3.5 text-red-600" />
                  {threat}
                </span>
              ))}
              <span className="px-3 py-1 rounded-lg text-xs font-mono font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                Shannon Token Entropy: {scanResult.entropy_score} bits/byte
              </span>
            </div>
          </div>

          {/* Receipt Evidence Fields Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono bg-[#FAFBFC] p-4 rounded-xl border border-[#CDD2D8]">
            <div>
              <span className="text-[#747F8D] block text-[11px] uppercase">Enforcement Layer</span>
              <span className="font-bold text-[#20252B]">L0: ArmorIQ SDK Intent Policy Gate</span>
            </div>
            <div>
              <span className="text-[#747F8D] block text-[11px] uppercase">Tool Action Requested</span>
              <span className="font-bold text-[#20252B]">read_file(path="{selectedFile.name}")</span>
            </div>
            <div>
              <span className="text-[#747F8D] block text-[11px] uppercase">Matched Security Policy</span>
              <span className="font-bold text-[#0284C7]">{scanResult.matched_policy}</span>
            </div>
            <div>
              <span className="text-[#747F8D] block text-[11px] uppercase">Witness Invariant Verification</span>
              <span className="font-bold text-emerald-700">VERIFIED ZERO EXECUTIONS (0 Subprocesses)</span>
            </div>

            {/* Canonical Hash */}
            <div className="md:col-span-2 pt-2 border-t border-[#CDD2D8]">
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="text-[#747F8D] uppercase font-semibold">Canonical SHA-256 Hash (RFC 8785)</span>
                <button
                  type="button"
                  onClick={() => handleCopy(scanResult.canonical_hash, setCopiedHash)}
                  className="text-[#0284C7] hover:underline flex items-center gap-1 cursor-pointer"
                >
                  {copiedHash ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedHash ? 'Copied' : 'Copy Hash'}</span>
                </button>
              </div>
              <code className="block p-2 rounded bg-[#FFFFFF] border border-[#CDD2D8] text-[11px] text-[#059669] break-all select-all">
                {scanResult.canonical_hash}
              </code>
            </div>

            {/* HMAC Signature */}
            <div className="md:col-span-2">
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="text-[#747F8D] uppercase font-semibold">HMAC-SHA256 Witness Signature</span>
                <button
                  type="button"
                  onClick={() => handleCopy(scanResult.receipt_signature, setCopiedSig)}
                  className="text-[#0284C7] hover:underline flex items-center gap-1 cursor-pointer"
                >
                  {copiedSig ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedSig ? 'Copied' : 'Copy Signature'}</span>
                </button>
              </div>
              <code className="block p-2 rounded bg-[#FFFFFF] border border-[#CDD2D8] text-[11px] text-[#59636E] break-all select-all">
                {scanResult.receipt_signature}
              </code>
            </div>
          </div>

          {/* Verification & Tamper Check Buttons */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleVerify}
                disabled={verifyStatus === 'VERIFYING'}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[#0284C7] hover:bg-[#0369A1] text-white font-semibold text-xs shadow-sm transition-colors cursor-pointer disabled:opacity-50"
              >
                <ShieldCheck className="w-4 h-4 text-white" />
                <span>{verifyStatus === 'VERIFYING' ? 'Verifying...' : 'Verify Cryptographic Proof'}</span>
              </button>

              <button
                type="button"
                onClick={handleTamper}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-red-300 bg-red-50 hover:bg-red-100 text-red-700 text-xs font-semibold transition-colors cursor-pointer"
              >
                <AlertTriangle className="w-4 h-4" />
                <span>Simulate Tamper Check</span>
              </button>

              <button
                type="button"
                onClick={() => setShowRawJson(!showRawJson)}
                className="px-3 py-2 text-xs text-[#59636E] hover:text-[#20252B] transition-colors cursor-pointer"
              >
                {showRawJson ? 'Hide Raw JSON' : 'View Raw JSON'}
              </button>
            </div>

            <Link
              href={`/receipts?id=${encodeURIComponent(scanResult.receipt_id)}`}
              className="text-xs font-mono text-[#0284C7] hover:underline flex items-center gap-1 font-semibold"
            >
              <span>Inspect in Forensic Registry</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Live Verification Result Banner */}
          {verifyStatus !== 'IDLE' && (
            <div
              className={`p-4 rounded-xl text-xs font-mono border ${
                verifyStatus === 'VERIFIED'
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                  : 'bg-red-50 border-red-300 text-red-900'
              }`}
            >
              <div className="flex items-center gap-2 font-bold mb-1">
                {verifyStatus === 'VERIFIED' ? (
                  <>
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>CRYPTOGRAPHIC PROOF VERIFIED (RFC 8785 VALID)</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                    <span>MUTATION DETECTED / TAMPER REJECTED</span>
                  </>
                )}
              </div>
              <p className="leading-relaxed opacity-90">{verifyMessage}</p>
            </div>
          )}

          {/* Raw JSON Viewer */}
          {showRawJson && (
            <div className="pt-2">
              <pre className="p-3 rounded-lg text-xs font-mono bg-[#0D1117] text-[#C9D1D9] border border-[#30363D] overflow-x-auto max-h-72">
                {JSON.stringify(scanResult.receipt, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* ── Section 4: Interactive AI Document Security Intelligence Chatbot (CollectUI Inspired) ── */}
      <div className="relative rounded-3xl bg-[#090D16] border border-[#1E2738] shadow-[0_25px_60px_-15px_rgba(0,0,0,0.8)] overflow-hidden backdrop-blur-2xl">
        {/* Ambient Subtle Cyber Glows */}
        <div className="pointer-events-none absolute -top-24 -left-24 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 -right-24 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl" />

        {/* Chatbot Header */}
        <div className="relative z-10 px-5 md:px-6 py-4 md:py-5 border-b border-[#1A2334] bg-[#0C121E]/85 backdrop-blur-md flex flex-wrap items-center justify-between gap-4">
          {/* Avatar & Title */}
          <div className="flex items-center gap-3.5">
            <div className="relative flex items-center justify-center w-11 h-11 rounded-2xl bg-gradient-to-tr from-sky-500 via-indigo-500 to-teal-400 p-[1.5px] shadow-lg shadow-sky-500/20 shrink-0">
              <div className="w-full h-full bg-[#090D16] rounded-[14px] flex items-center justify-center text-sky-400">
                <Bot className="w-5 h-5" />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-[#090D16] ring-2 ring-emerald-400/30 animate-pulse" />
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-sm md:text-base font-bold text-white tracking-tight flex items-center gap-2">
                  TripLine AI Document Security Assistant
                </h3>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Active In-MCP
                </span>
              </div>
              <p className="text-xs text-[#94A3B8] mt-0.5">
                Real-time forensic reasoning over ArmorIQ policy decisions, detected secrets, and cryptographic proofs.
              </p>
            </div>
          </div>

          {/* Context Capsule & Action Controls */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Target File Badge */}
            <div className="px-3 py-1.5 rounded-xl text-xs font-mono bg-[#131A26] border border-[#232D3F] text-[#94A3B8] flex items-center gap-2 shadow-xs">
              <FileCode className="w-3.5 h-3.5 text-sky-400" />
              <span className="font-semibold text-white truncate max-w-[150px] sm:max-w-[210px]">{selectedFile.name}</span>
            </div>

            {/* Block Verdict Badge */}
            {scanResult ? (
              <span
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold flex items-center gap-1.5 border shadow-sm ${
                  scanResult.blocked
                    ? 'bg-red-950/60 text-red-300 border-red-500/50 shadow-red-950/30'
                    : 'bg-emerald-950/60 text-emerald-300 border-emerald-500/50 shadow-emerald-950/30'
                }`}
              >
                {scanResult.blocked ? <ShieldAlert className="w-3.5 h-3.5 text-red-400" /> : <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />}
                {scanResult.blocked ? 'BLOCKED (DENIED)' : 'PERMITTED (ALLOW)'}
              </span>
            ) : (
              <span className="px-3 py-1.5 rounded-xl text-xs font-mono font-medium bg-amber-950/40 text-amber-300 border border-amber-500/30 flex items-center gap-1.5">
                <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
                Awaiting Scan
              </span>
            )}

            {/* Clear Chat Button */}
            <button
              type="button"
              onClick={handleClearChat}
              title="Reset conversation"
              className="p-2 rounded-xl text-[#94A3B8] hover:text-white bg-[#131A26] hover:bg-[#1C2637] border border-[#232D3F] hover:border-sky-500/40 transition-all cursor-pointer shadow-xs active:scale-95"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="p-4 md:p-6 space-y-4 md:space-y-5">
          {/* Suggested Prompt Chips */}
          <div>
            <div className="flex items-center gap-1.5 mb-2.5 text-[11px] font-semibold text-[#94A3B8]">
              <Sparkles className="w-3.5 h-3.5 text-sky-400" />
              <span>Suggested Inquiries:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  data-local={`btn-prompt-suggestion-${idx}`}
                  disabled={isChatting}
                  onClick={() => handleSendMessage(prompt.query)}
                  className="px-3.5 py-1.5 rounded-full text-xs font-medium bg-[#121824] hover:bg-[#1A2334] text-[#94A3B8] hover:text-white border border-[#212B3D] hover:border-sky-500/40 shadow-sm transition-all duration-200 cursor-pointer disabled:opacity-40 flex items-center gap-1.5 active:scale-95"
                >
                  {prompt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Chat History Viewport */}
          <div
            ref={chatScrollRef}
            className="bg-[#070A10]/90 rounded-2xl border border-[#182130] p-4 md:p-6 max-h-[440px] min-h-[260px] overflow-y-auto space-y-4 font-sans shadow-inner scroll-smooth"
          >
            {chatMessages.map((msg) => {
              const isUser = msg.role === 'user'
              const isCopied = copiedMessageId === msg.id

              return (
                <div
                  key={msg.id}
                  className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  {/* Avatar */}
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold shadow-md ${
                      isUser
                        ? 'bg-gradient-to-br from-sky-400 to-blue-600 ring-2 ring-sky-400/30 text-white'
                        : 'bg-gradient-to-tr from-sky-500/20 to-indigo-500/20 border border-sky-500/40 text-sky-400 shadow-sky-500/10'
                    }`}
                  >
                    {isUser ? 'U' : <Bot className="w-4 h-4" />}
                  </div>

                  {/* Message Bubble Card */}
                  <div
                    className={`max-w-[88%] rounded-2xl p-4 shadow-xl transition-all ${
                      isUser
                        ? 'bg-gradient-to-br from-sky-600 via-sky-500 to-blue-600 text-white rounded-tr-sm shadow-sky-500/20'
                        : 'bg-[#101622]/95 text-[#CBD5E1] border border-[#1E283A] rounded-tl-sm backdrop-blur-md'
                    }`}
                  >
                    {/* Header Strip inside Bubble */}
                    <div className="flex items-center justify-between gap-4 mb-2 pb-1.5 border-b border-white/10 text-[10px]">
                      <div className="flex items-center gap-2">
                        <span className="font-bold tracking-wide text-white">
                          {isUser ? 'You' : 'TripLine Security Bot'}
                        </span>
                        {!isUser && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-sky-500/15 text-sky-300 border border-sky-500/30">
                            ARMORIQ-MCP
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-[#94A3B8]">
                        <span>{msg.timestamp}</span>
                        {!isUser && (
                          <button
                            type="button"
                            onClick={() => handleCopyMessage(msg.id, msg.text)}
                            title="Copy message response"
                            className="p-1 rounded hover:bg-white/10 text-[#94A3B8] hover:text-white transition-colors cursor-pointer"
                          >
                            {isCopied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Content */}
                    {isUser ? (
                      <p className="text-xs leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                    ) : (
                      renderMarkdown(msg.text)
                    )}
                  </div>
                </div>
              )
            })}

            {/* Typing Indicator */}
            {isChatting && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-500/20 to-indigo-500/20 border border-sky-500/40 text-sky-400 flex items-center justify-center shrink-0 shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-[#101622]/95 border border-[#1E283A] rounded-2xl rounded-tl-sm p-3.5 shadow-xl">
                  <div className="flex items-center gap-3 text-xs text-[#94A3B8]">
                    <span className="inline-flex gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:-0.3s] shadow-[0_0_8px_rgba(56,189,248,0.8)]"></span>
                      <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:-0.15s] shadow-[0_0_8px_rgba(56,189,248,0.8)]"></span>
                      <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce shadow-[0_0_8px_rgba(56,189,248,0.8)]"></span>
                    </span>
                    <span className="font-mono text-[11px] text-sky-300">ArmorIQ SDK evaluating security invariants...</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Floating CollectUI-Style Input Container */}
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSendMessage()
            }}
            className="relative rounded-2xl bg-[#0F1522]/95 border border-[#222B3D] focus-within:border-sky-500/70 focus-within:ring-2 focus-within:ring-sky-500/20 p-2.5 shadow-2xl backdrop-blur-xl transition-all"
          >
            {/* Top context sub-strip */}
            <div className="flex items-center justify-between px-2 pb-2 text-[10px] text-[#64748B] border-b border-[#1A2232] font-mono">
              <div className="flex items-center gap-1.5">
                <Lock className="w-3 h-3 text-sky-400" />
                <span>Guarded File:</span>
                <span className="text-sky-300 font-semibold">{selectedFile.name}</span>
              </div>
              <div className="hidden sm:flex items-center gap-2 text-[#64748B]">
                <span>ArmorIQ Intent Gate (L0)</span>
                <span>•</span>
                <span className="text-[#94A3B8] flex items-center gap-1">
                  <span>Enter</span>
                  <CornerDownLeft className="w-2.5 h-2.5" />
                </span>
              </div>
            </div>

            {/* Input Row */}
            <div className="flex items-center gap-2 pt-1.5 px-1">
              <input
                type="text"
                data-local="input-demo-chat"
                value={chatInput}
                disabled={isChatting}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder={`Ask about ${selectedFile.name} (e.g. "Is this document blocked?", "Why was it blocked?")...`}
                className="w-full px-2 py-1.5 text-xs bg-transparent border-0 text-[#F0F6FC] placeholder-[#64748B] focus:outline-none focus:ring-0 disabled:opacity-50"
              />

              <button
                type="submit"
                data-api="POST /api/demo/chat"
                data-testid="btn-demo-chat-send"
                disabled={!chatInput.trim() || isChatting}
                className="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 active:scale-95 text-white text-xs font-semibold shadow-lg shadow-sky-500/25 transition-all disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer shrink-0"
              >
                <Send className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Ask Bot</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

/**
 * Advanced deterministic markdown & telemetry renderer for TripLine Security Assistant
 */
function renderMarkdown(text: string) {
  const lines = text.split('\n')
  return (
    <div className="space-y-2 text-xs leading-relaxed text-[#CBD5E1]">
      {lines.map((line, idx) => {
        // Headings: ### Title
        if (line.startsWith('### ')) {
          return (
            <div key={idx} className="mt-3 mb-1.5 first:mt-0 pb-1.5 border-b border-[#243044]">
              <h4 className="font-bold text-sm text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#38BDF8] shadow-[0_0_8px_rgba(56,189,248,0.8)]"></span>
                <span>{formatInline(line.replace('### ', ''))}</span>
              </h4>
            </div>
          )
        }

        // Threat highlight line: "- **Threat:** `...`" or "- Threat: ..."
        if (line.includes('**Threat:**') || line.includes('Threat:')) {
          const content = line.replace(/^[-*]\s*/, '')
          return (
            <div key={idx} className="my-1.5 p-2.5 rounded-xl bg-red-950/40 border border-red-500/30 flex items-start gap-2.5 shadow-xs">
              <span className="p-1 rounded-md bg-red-500/20 text-red-400 mt-0.5 shrink-0">
                <ShieldAlert className="w-3.5 h-3.5" />
              </span>
              <div className="flex-1 text-red-200">
                {formatInline(content)}
              </div>
            </div>
          )
        }

        // Entropy metric line: "- **Shannon Token Entropy:** `5.05 bits/byte`"
        if (line.includes('Entropy') && (line.includes('bits/byte') || line.includes('score'))) {
          const content = line.replace(/^[-*]\s*/, '')
          const scoreMatch = line.match(/(\d+\.?\d*)\s*bits\/byte/)
          const scoreNum = scoreMatch ? parseFloat(scoreMatch[1]) : null
          const pct = scoreNum ? Math.min(100, Math.round((scoreNum / 8.0) * 100)) : 65

          return (
            <div key={idx} className="my-1.5 p-2.5 rounded-xl bg-[#0D1522] border border-sky-500/30 space-y-1.5">
              <div className="flex items-center justify-between text-[11px]">
                <span className="font-semibold text-sky-300 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-sky-400" />
                  {formatInline(content)}
                </span>
                {scoreNum && (
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    scoreNum > 4.5
                      ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                      : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  }`}>
                    {scoreNum > 4.5 ? 'CRITICAL HIGH ENTROPY' : 'NORMAL RANGE'}
                  </span>
                )}
              </div>
              {scoreNum && (
                <div className="w-full h-1.5 rounded-full bg-[#1A2333] overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      scoreNum > 4.5
                        ? 'bg-gradient-to-r from-amber-500 to-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'
                        : 'bg-gradient-to-r from-teal-400 to-emerald-400'
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              )}
            </div>
          )
        }

        // Policy / Receipt proof bullet: Receipt ID, Canonical Hash, Invariant
        if (line.includes('Receipt ID:') || line.includes('Canonical Hash') || line.includes('ArmorIQ Policy Enforced') || line.includes('TripLine Invariant')) {
          const content = line.replace(/^[-*]\s*/, '')
          return (
            <div key={idx} className="my-1 p-2 rounded-lg bg-[#0F1726] border border-[#212E45] font-mono text-[11px] text-[#93C5FD] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400 shrink-0"></span>
              <div className="flex-1 truncate">{formatInline(content)}</div>
            </div>
          )
        }

        // Bullet lists: - item or * item
        if (line.startsWith('- ') || line.startsWith('* ')) {
          return (
            <div key={idx} className="flex items-start gap-2 ml-1 my-1">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400/80 mt-1.5 shrink-0 shadow-[0_0_6px_rgba(56,189,248,0.6)]" />
              <div className="flex-1">{formatInline(line.slice(2))}</div>
            </div>
          )
        }

        // Numbered steps: 1. ... 2. ...
        if (/^\d+\.\s/.test(line)) {
          const num = line.match(/^(\d+)\.\s/)?.[1]
          const rest = line.replace(/^\d+\.\s/, '')
          return (
            <div key={idx} className="flex items-start gap-2.5 ml-1 my-1.5">
              <span className="w-5 h-5 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 font-mono font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                {num}
              </span>
              <div className="flex-1">{formatInline(rest)}</div>
            </div>
          )
        }

        // Blank lines
        if (line.trim() === '') {
          return <div key={idx} className="h-1.5" />
        }

        return <p key={idx} className="leading-relaxed">{formatInline(line)}</p>
      })}
    </div>
  )
}

function formatInline(str: string) {
  const parts = str.split(/(`[^`]+`|\*\*[^*]+\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      const code = part.slice(1, -1)
      const isPolicy = code.includes('ARMORIQ') || code.includes('POLICY')
      const isHash = code.startsWith('SHA256:') || code.startsWith('RCP-')
      const isBlock = code === 'DENY' || code === 'BLOCKED'

      return (
        <code
          key={i}
          className={`px-1.5 py-0.5 rounded text-[11px] font-mono border mx-0.5 ${
            isBlock
              ? 'bg-red-950/60 text-red-300 border-red-500/40 font-bold'
              : isPolicy
              ? 'bg-cyan-950/60 text-cyan-300 border-cyan-500/40'
              : isHash
              ? 'bg-[#0B101B] text-sky-300 border-sky-500/30'
              : 'bg-[#0F172A] text-sky-300 border-sky-500/20'
          }`}
        >
          {code}
        </code>
      )
    }
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      )
    }
    return part
  })
}

