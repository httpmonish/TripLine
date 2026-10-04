import hashlib
import dataclasses
import time

@dataclasses.dataclass(frozen=True)
class CanaryRecord:
    run_id: str
    canary_id: str
    tier: int
    intended_placement: str
    created_at: float

def mint_canary(run_id: str, tier: int, intended_placement: str) -> CanaryRecord:
    hasher = hashlib.sha256(f"{run_id}:{tier}:{intended_placement}".encode())
    hex_id = hasher.hexdigest()[:8]
    # Strip leading "TRPL-" from run_id to avoid doubled prefix (e.g. TRPL-TRPL-TRA-...)
    clean_run_id = run_id.removeprefix("TRPL-") if run_id.startswith("TRPL-") else run_id
    short_run_id = clean_run_id[:8] if len(clean_run_id) > 8 else clean_run_id
    canary_id = f"TRPL-{short_run_id}-{hex_id}"
    
    return CanaryRecord(
        run_id=run_id,
        canary_id=canary_id,
        tier=tier,
        intended_placement=intended_placement,
        created_at=time.time()
    )
