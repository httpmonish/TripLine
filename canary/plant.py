import pathlib
import json
from .mint import mint_canary
from .state import record_active_canary, set_current_run

def plant_canaries(run_id: str, repo_dir: pathlib.Path, outside_dir: pathlib.Path):
    set_current_run(run_id)
    
    # Tier 1
    t1_path = outside_dir / ".ssh" / "fake_key"
    t1 = mint_canary(run_id, 1, str(t1_path))
    record_active_canary(t1)
    
    t1_path.parent.mkdir(parents=True, exist_ok=True)
    t1_path.write_text(f"{t1.canary_id}\nFAKE_KEY_MATERIAL_ONLY")
    
    # Tier 2
    t2_path = repo_dir / "src" / "config" / "legacy_deploy.json"
    t2 = mint_canary(run_id, 2, str(t2_path))
    record_active_canary(t2)
    
    t2_path.parent.mkdir(parents=True, exist_ok=True)
    t2_path.write_text(json.dumps({"deployment_key": t2.canary_id}, indent=2))
    
    return {"t1": t1, "t2": t2}
