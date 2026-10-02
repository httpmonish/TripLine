import hashlib
import time
import dataclasses

@dataclasses.dataclass(frozen=True)
class ContextItem:
    id: str
    run_id: str
    source_type: str
    source_id: str
    trust_level: str
    content: str
    normalized_content: str
    content_hash: str
    created_at: float

def generate_content_hash(canonical_content: str) -> str:
    """Generates a SHA-256 hash of the normalized/canonical content."""
    return hashlib.sha256(canonical_content.encode('utf-8')).hexdigest()

def verify_context_item(item: ContextItem) -> bool:
    """Validates the integrity of the content hash."""
    return item.content_hash == generate_content_hash(item.normalized_content)
