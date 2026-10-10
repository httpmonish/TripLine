import hashlib
import pathlib

evidence_files = [
    ('Layer 1 ArmorIQ Deny Receipt', 'results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json'),
    ('Layer 2 Path Jail Deny Receipt', 'results/phase3/scenario/receipt_P2_JAIL_DENY.json'),
    ('Layer 3 Egress Hold Receipt', 'results/phase3/scenario/receipt_P3_GATEWAY_HOLD.json'),
    ('ArmorIQ Sidecar Audit Links', 'results/phase3/armoriq_links.jsonl'),
    ('Measured Runs Summary', 'results/phase3/measured/summary.md'),
    ('Measured Runs JSONL', 'results/phase3/measured/measured_runs.jsonl'),
    ('Layer Attribution Matrix', 'docs/phase3_layer_attribution.md'),
    ('In-Window Development Ledger', 'docs/IN_WINDOW_LEDGER.md'),
    ('Pre-existing Code Disclosure', 'docs/PREEXISTING_CODE.md'),
    ('System Limitations & Residual', 'docs/limitations.md'),
    ('Architecture Specification', 'docs/ARCHITECTURE.md'),
    ('Demo Video MP4 (1080p)', 'video/out/tripline_demo_90s.mp4'),
    ('Demo Video Low-Bitrate', 'video/out/tripline_demo_90s_lowbitrate.mp4'),
    ('Video Captions SRT', 'video/captions.srt'),
    ('Video Storyboard JSON', 'video/storyboard.json'),
    ('Witness HMAC Key', '.tripline/witness_key.txt'),
    ('Repo MCP Witness Log', '.tripline/witness/repo-mcp.jsonl'),
]

lines = [
    '# Tripline Cryptographic Evidence Index',
    '',
    '**Freeze Snapshot**: 2026-10-10',
    '**Purpose**: Cryptographic SHA-256 integrity manifest for all verified evidence artifacts.',
    '',
    '> **Note for Auditors & Evaluators**: These hashes reflect the exact artifact state at submission freeze. This enables judges to independently detect post-submission modifications. Note that any actor with write access to the repository could regenerate hashes; this ledger represents self-consistent author attestation, not third-party notarization.',
    '',
    '| Artifact Category | Relative File Path | SHA-256 Digest | Size (Bytes) |',
    '|---|---|---|---|',
]

for desc, rel in evidence_files:
    p = pathlib.Path(rel)
    if p.exists():
        data = p.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        lines.append(f"| **{desc}** | `{rel}` | `{sha}` | {len(data)} |")
    else:
        lines.append(f"| **{desc}** | `{rel}` | `MISSING` | 0 |")

out = '\n'.join(lines) + '\n'
pathlib.Path('docs/EVIDENCE_INDEX.md').write_text(out)
print(f'[+] Created docs/EVIDENCE_INDEX.md with {len(evidence_files)} artifacts.')
