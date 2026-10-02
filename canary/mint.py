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
    short_run_id = run_id[:8] if len(run_id) > 8 else run_id
    canary_id = f"TRPL-{short_run_id}-{hex_id}"
    
    return CanaryRecord(
        run_id=run_id,
        canary_id=canary_id,
        tier=tier,
        intended_placement=intended_placement,
        created_at=time.time()
    )
