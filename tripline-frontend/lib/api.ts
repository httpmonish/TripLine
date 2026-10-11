/**
 * tripline-frontend/lib/api.ts
 * Authoritative, strongly-typed API client for Tripline backend.
 * Never performs fake timeouts or mock simulations.
 */

export interface HealthInfo {
  status: string
  time: string
  git_commit: string
  branch: string
  dirty: boolean
}

export interface EnvInfo {
  armoriq_sdk_version: string
  armoriq_key_present: boolean
  armoriq_key_prefix: string | null
  llm_key_present: boolean
  llm_provider: string
  llm_model: string
  enforcement_mode: string
  live_runs_enabled: boolean
  python_version: string
  repo_relative_paths: Record<string, string>
}

export interface RunSummary {
  run_id: string
  date: string
  model_id: string
  prompt_rung: number
  outcome_summary: string
  attack_class?: string
  tripline_decision?: string
  armoriq_decision?: string
  executed: number
}

export interface RunDetail {
  run_id: string
  date: string
  model_id: string
  prompt_rung: number
  records: Array<{
    issue?: string
    action?: string
    armoriq?: string
    tripline?: string
    outcome?: string
    receipt?: string
    [key: string]: any
  }>
  events: Array<{
    stage?: number
    stage_name?: string
    event?: string
    timestamp?: string
    [key: string]: any
  }>
  receipt?: any
}

export interface RunTranscript {
  run_id: string
  transcript: string | null
  message?: string | null
}

export interface AttributionLayer {
  layer: string
  name: string
  boundary: string
  mechanism: string
  decision_type: string
  stops: string[]
  receipt_coverage: string
}

export interface AttributionResponse {
  title: string
  layers: AttributionLayer[]
  summary: string
}

export interface JailBurstProbe {
  attempt: string
  path: string
  armoriq_decision: string
  jail_decision: string
  fake_key_bytes: number
  verdict: string
}

export interface JailBurstResponse {
  total_probes: number
  passed_probes: number
  probe_scope: string
  reconciliation_note: string
  probes: JailBurstProbe[]
}

export interface MeasuredRow {
  arm: string
  attack: string
  k: number
  attempted_ratio: string
  executed_ratio: string
  decided_by: string
  wilson_ci_95: string
  refusal_rate: string
  protection_rate: string
}

export interface MeasuredResponse {
  status: string
  manifest: Record<string, any>
  rows: MeasuredRow[]
}

export interface AuditLinkEntry {
  receipt_id: string
  receipt_hash: string
  armoriq_ref: Record<string, any>
  prev_hash: string
  link_hash: string
}

export interface AuditLinksResponse {
  valid: bool
  chain_length: number
  reason: string
  links: AuditLinkEntry[]
}

export interface ReceiptSummary {
  receipt_id: string
  run_id: string
  tool: string
  tripline_decision: string
  armoriq_decision: string
  canonical_hash: string
  created_at: string
}

export interface ReceiptDetail {
  receipt_id: string
  data: Record<string, any>
  raw_json: string
  armoriq_ref?: Record<string, any> | null
  sidecar_link_hash?: string | null
}

export interface ReceiptVerifyResponse {
  receipt_id: string
  verified: boolean
  status: string
  reason: string
  canonical_hash?: string
  command: string
}

export interface ReceiptTamperResponse {
  receipt_id: string
  tampered_field: string
  original_value: any
  tampered_value: any
  tamper_detected: boolean
  status: string
  verifier_reason: string
  original_file_untouched: boolean
}

export interface WitnessSummary {
  total_records: number
  mcp_logs: Record<string, number>
  execution_counts: Record<string, number>
  chain_status: string
}

export interface WitnessVerifyResponse {
  valid: boolean
  reason: string
  log_name: string
  inspected_records: number
}

export interface WitnessTamperResponse {
  tamper_detected: boolean
  status: string
  verifier_reason: string
  original_log_untouched: boolean
}

export interface JobRecord {
  job_id: string
  kind: string
  params: Record<string, any>
  live: boolean
  status: string
  started_at?: string | null
  finished_at?: string | null
  exit_code?: number | null
  output_preview: string[]
}

export interface EvidenceItem {
  path: string
  size_bytes: number
  sha256: string
  claims_supported: string[]
}

export interface EvidenceIndexResponse {
  total_files: number
  items: EvidenceItem[]
}

export interface DocItem {
  name: string
  title: string
  size_bytes: number
}

export interface DocDetailResponse {
  name: string
  title: string
  content: string
}

export interface ClaimsItem {
  id: string
  claim: string
  verdict: string
  evidence_path: string
  notes?: string
}

export interface ClaimsLedgerResponse {
  total_claims: number
  verified_count: number
  unverified_count: number
  failed_count: number
  items: ClaimsItem[]
}

export interface PlatformChecklistItem {
  item_id: string
  title: string
  status: string
  evidence_file?: string | null
  instruction: string
}

export interface PlatformChecklistResponse {
  platform_url: string
  agent_id: string
  items: PlatformChecklistItem[]
}

let cachedCsrfToken: string | null = null

async function getCsrfToken(): Promise<string> {
  if (cachedCsrfToken) return cachedCsrfToken
  try {
    const res = await fetch('/api/csrf-token')
    if (res.ok) {
      const data = await res.json()
      cachedCsrfToken = data.csrf_token
      return cachedCsrfToken || ''
    }
  } catch {
    // fallback
  }
  return ''
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {})

  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes((options.method || 'GET').toUpperCase())) {
    headers.set('Content-Type', 'application/json')
    const token = await getCsrfToken()
    if (token) {
      headers.set('X-CSRF-Token', token)
    }
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorDetail = response.statusText
    try {
      const errJson = await response.json()
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail
      }
    } catch {
      // not json
    }
    throw new Error(`[HTTP ${response.status}] ${errorDetail}`)
  }

  return response.json()
}

export const api = {
  getHealth: () => request<HealthInfo>('/api/health'),
  getEnv: () => request<EnvInfo>('/api/env'),
  getRuns: () => request<RunSummary[]>('/api/runs'),
  getRun: (id: string) => request<RunDetail>(`/api/runs/${encodeURIComponent(id)}`),
  getLatestRun: () => request<RunDetail>('/api/runs/latest'),
  getRunTranscript: (id: string) => request<RunTranscript>(`/api/runs/${encodeURIComponent(id)}/transcript`),
  getAttribution: () => request<AttributionResponse>('/api/attribution'),
  getJailBurst: () => request<JailBurstResponse>('/api/jail-burst'),
  getMeasured: () => request<MeasuredResponse>('/api/measured'),
  getAuditLinks: () => request<AuditLinksResponse>('/api/audit-links'),
  getReceipts: () => request<ReceiptSummary[]>('/api/receipts'),
  getReceipt: (id: string) => request<ReceiptDetail>(`/api/receipts/${encodeURIComponent(id)}`),
  verifyReceipt: (id: string) => request<ReceiptVerifyResponse>(`/api/receipts/${encodeURIComponent(id)}/verify`, { method: 'POST' }),
  tamperReceipt: (id: string) => request<ReceiptTamperResponse>(`/api/receipts/${encodeURIComponent(id)}/tamper-check`, { method: 'POST' }),
  getWitness: () => request<WitnessSummary>('/api/witness'),
  verifyWitness: () => request<WitnessVerifyResponse>('/api/witness/verify', { method: 'POST' }),
  tamperWitness: () => request<WitnessTamperResponse>('/api/witness/tamper-check', { method: 'POST' }),
  listJobs: () => request<JobRecord[]>('/api/jobs'),
  getJob: (id: string) => request<JobRecord>(`/api/jobs/${encodeURIComponent(id)}`),
  createJob: (kind: string, params: Record<string, any> = {}, confirmToken?: string) =>
    request<JobRecord>('/api/jobs', {
      method: 'POST',
      body: JSON.stringify({ kind, params, confirm_token: confirmToken }),
    }),
  cancelJob: (id: string) => request<{ status: string; job_id: string }>(`/api/jobs/${encodeURIComponent(id)}/cancel`, { method: 'POST' }),
  getEvidenceIndex: () => request<EvidenceIndexResponse>('/api/evidence'),
  getDocs: () => request<DocItem[]>('/api/docs'),
  getDoc: (name: string) => request<DocDetailResponse>(`/api/docs/${encodeURIComponent(name)}`),
  getClaims: () => request<ClaimsLedgerResponse>('/api/claims'),
  getPlatformChecklist: () => request<PlatformChecklistResponse>('/api/platform-checklist'),
  getSummary: () => request<Record<string, any>>('/api/summary'),
}
