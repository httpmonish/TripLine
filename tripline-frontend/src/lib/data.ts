import summaryStatsJson from '../data/generated/summary_stats.json'
import receiptsJson from '../data/generated/receipts.json'
import jailBurstJson from '../data/generated/jail_burst.json'
import layersJson from '../data/generated/layers.json'
import measuredJson from '../data/generated/measured.json'
import claimsJson from '../data/generated/claims.json'
import witnessJson from '../data/generated/witness.json'

export interface SummaryStats {
  recorded_runs: number
  signed_receipts: number
  jail_probes: string
  protection_rate: string
  witness_records: number
  primary_receipt: any | null
  source: string
}

export interface ReceiptRecord {
  receipt_id: string
  incident_id?: string
  run_id?: string
  created_at: string
  action: string
  layer: string
  verdict: string
  canonical_hash: string
  receipt_signature: string
  witness_head_hmac?: string
  verification_status: 'VERIFIED' | 'TAMPER_DETECTED'
  source_file: string
  proposal?: any
  decision?: any
  witness?: any
  confidence?: any
  raw_json: string
}

export interface JailBurstData {
  total_probes: number
  passed_probes: number
  leaked_bytes: number
  source: string
  probes: Array<{
    attempt: string
    path: string
    armoriq_decision: string
    jail_decision: string
    bytes_returned: number
    verdict: string
  }>
}

export interface LayerItem {
  id: string
  name: string
  boundary: string
  mechanism: string
  decision_type: string
  stops: string[]
  receipt_coverage: string
}

export interface RecordedAttack {
  id: string
  title: string
  issue: string
  action: string
  armoriq_decision: string
  tripline_decision: string
  final_outcome: string
  stopped_by: string
  receipt_id: string
  source_file: string
}

export interface LayersData {
  title: string
  source: string
  layers: LayerItem[]
  recorded_attacks: RecordedAttack[]
  honest_residuals: Array<{
    technique: string
    payload: string
    armoriq: string
    tripline: string
    outcome: string
    status: string
  }>
}

export interface MeasuredData {
  source: string
  protection_rate: string
  refusal_rate: string
  in_window_growth: string
  rows: Array<{
    metric: string
    condition: string
    value: string
    baseline: string
    status: string
  }>
}

export interface ClaimsData {
  source: string
  claims: Array<{
    id: string
    claim: string
    source: string
    evidence: string
    status: string
  }>
  known_limits: Array<{
    title: string
    description: string
    source: string
  }>
}

export interface WitnessData {
  total_records: number
  mcp_logs: Record<string, number>
  chain_status: string
  source: string
}

export function getSummaryStats(): SummaryStats {
  return summaryStatsJson as SummaryStats
}

export function getReceipts(): ReceiptRecord[] {
  return receiptsJson as ReceiptRecord[]
}

export function getReceipt(receiptId: string): ReceiptRecord | undefined {
  return (receiptsJson as ReceiptRecord[]).find(
    (r) => r.receipt_id === receiptId || r.source_file.includes(receiptId)
  )
}

export function getJailBurst(): JailBurstData {
  return jailBurstJson as JailBurstData
}

export function getLayersData(): LayersData {
  return layersJson as LayersData
}

export function getMeasuredData(): MeasuredData {
  return measuredJson as MeasuredData
}

export function getClaimsData(): ClaimsData {
  return claimsJson as ClaimsData
}

export function getWitnessData(): WitnessData {
  return witnessJson as WitnessData
}

// Client-side Canonical JSON verification
function canonicalSort(obj: any): any {
  if (obj === null || typeof obj !== 'object') return obj
  if (Array.isArray(obj)) return obj.map(canonicalSort)
  const sortedKeys = Object.keys(obj).sort()
  const result: Record<string, any> = {}
  for (const k of sortedKeys) {
    result[k] = canonicalSort(obj[k])
  }
  return result
}

export async function verifyReceiptLocally(receipt: any): Promise<{
  verified: boolean
  status: 'VERIFIED' | 'TAMPER_DETECTED'
  computed_hash: string
  declared_hash: string
  reason: string
}> {
  const evidenceDict: Record<string, any> = {
    receipt_id: receipt.receipt_id,
    incident_id: receipt.incident_id,
    run_id: receipt.run_id,
    created_at: receipt.created_at,
    source: receipt.source,
    proposal: receipt.proposal,
    decision: receipt.decision,
    canary: receipt.canary,
    witness: receipt.witness,
    confidence: receipt.confidence,
  }

  const canonicalObj = canonicalSort(evidenceDict)
  const serialized = JSON.stringify(canonicalObj)
  const enc = new TextEncoder().encode(serialized)
  const hashBuffer = await crypto.subtle.digest('SHA-256', enc)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const computedHash = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')

  const declaredHash = receipt.canonical_hash || ''
  const isMatch = computedHash === declaredHash

  return {
    verified: isMatch,
    status: isMatch ? 'VERIFIED' : 'TAMPER_DETECTED',
    computed_hash: computedHash,
    declared_hash: declaredHash,
    reason: isMatch
      ? 'Canonical SHA-256 hash matches immutable evidence fields.'
      : `TAMPER_DETECTED: canonical_hash mismatch (expected ${computedHash}, got ${declaredHash})`,
  }
}
