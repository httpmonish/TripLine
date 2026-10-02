import re
import urllib.parse
from typing import Dict, Optional, Any
from .models import ContextItem
from .ledger import get_run_context

def normalize_content(content: str) -> str:
    """
    Normalizes string content for C1 matching.
    Applies url decoding, whitespace stripping, and lowercasing.
    """
    if not isinstance(content, str):
        return ""
        
    # URL / Percent decoding
    content = urllib.parse.unquote(content)
    # Replace escaped forward slashes (e.g. \/ -> /)
    content = content.replace('\\/', '/')
    # Replace escaped backward slashes (e.g. \\ -> \)
    content = content.replace('\\\\', '\\')
    # Collapse whitespace
    content = re.sub(r'\s+', ' ', content).strip()
    # Lowercase
    content = content.lower()
    return content

def find_c1_match(proposal_text: str, run_id: str) -> Optional[Dict[str, Any]]:
    """
    Checks if normalized proposal text matches any T3 ContextItems.
    Returns C1 evidence if match found, else None.
    """
    items = get_run_context(run_id)
    t3_items = [i for i in items if i.trust_level == "T3"]
    
    normalized_proposal = normalize_content(proposal_text)
    
    # Avoid matching very short generic strings
    if len(normalized_proposal) < 10:
        return None
        
    # Benign overlap mitigation:
    # If the proposal is entirely alphanumeric words and spaces, 
    # we require it to be significantly long to avoid false positives 
    # on generic troubleshooting phrases like "review the file handling code".
    # But if it contains paths or special chars (~ / % \), it's more specific.
    has_special = bool(re.search(r'[/~\\%_.-]', normalized_proposal))
    if not has_special and len(normalized_proposal) < 40:
        return None
        
    for item in t3_items:
        if not item.normalized_content:
            continue
            
        # Check if proposal is in the source, or source is in the proposal
        if normalized_proposal in item.normalized_content:
            return {
                "confidence": "C1",
                "source_item_id": item.id,
                "source": item.source_id,
                "matched_text": proposal_text,
                "match_type": "normalized_string"
            }
            
        # Optional: check if source is in the proposal (if the proposal is longer)
        if len(item.normalized_content) > 10 and item.normalized_content in normalized_proposal:
            # Same benign check for the source
            s_has_special = bool(re.search(r'[/~\\%_.-]', item.normalized_content))
            if s_has_special or len(item.normalized_content) >= 40:
                return {
                    "confidence": "C1",
                    "source_item_id": item.id,
                    "source": item.source_id,
                    "matched_text": item.normalized_content,
                    "match_type": "normalized_string"
                }
            
    return None

def check_c0_association(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Checks if ANY T3 content was ingested during this run.
    """
    items = get_run_context(run_id)
    t3_items = [i for i in items if i.trust_level == "T3"]
    if t3_items:
        # Just return the first one for C0 context or all of them
        sources = list(set([i.source_id for i in t3_items]))
        return {
            "confidence": "C0",
            "source": sources[0] if len(sources) == 1 else ",".join(sources),
            "basis": "source was present in context"
        }
    return None
