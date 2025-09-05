"""
Validation for proofreading responses - simplified but robust.
"""

from typing import Dict, Any, List, Tuple
from utils import logs_console


def validate_proofreading_response(response_data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
    """Validate and normalize proofreading response - relaxed validation."""
    
    if not isinstance(response_data, dict) or "errors" not in response_data:
        return False, []
    
    errors = response_data["errors"]
    if not isinstance(errors, list):
        return False, []
    
    logs_console.log(f"Validating {len(errors)} potential errors", level='DEBUG')
    
    normalized_errors = []
    rejected_count = 0
    
    # Valid types with mapping
    type_mapping = {
        "grammatical": "grammar", "misspelling": "spelling", "typo": "spelling",
        "punctuation error": "punctuation", "styling": "style", "unclear": "clarity",
        "syntax error": "syntax", "coherence error": "coherence"
    }
    valid_types = {"grammar", "spelling", "punctuation", "style", "clarity", "syntax", "coherence"}
    valid_importance = {"high", "medium", "low"}
    
    for i, error in enumerate(errors):
        if not isinstance(error, dict):
            rejected_count += 1
            continue
        
        # Required fields check - minimal
        if not error.get("type") or not error.get("original"):
            rejected_count += 1
            continue
        
        # Normalize type
        error_type = error["type"].lower().strip()
        if error_type in type_mapping:
            error_type = type_mapping[error_type]
        elif error_type not in valid_types:
            # Try partial matching
            for valid_type in valid_types:
                if valid_type in error_type:
                    error_type = valid_type
                    break
            else:
                rejected_count += 1
                continue
        
        # Normalize fields
        original = error.get("original", "").strip()
        suggestion = error.get("suggestion", "").strip()
        explanation = error.get("explanation", "No explanation provided")
        importance = error.get("importance", "medium").lower()
        
        if importance not in valid_importance:
            importance = "medium"
        
        # Create normalized error - very permissive
        if original:  # Only requirement
            normalized_errors.append({
                "type": error_type,
                "original": original,
                "suggestion": suggestion,
                "explanation": explanation,
                "importance": importance
            })
        else:
            rejected_count += 1
    
    accepted = len(normalized_errors)
    logs_console.log(f"Validation: {accepted} accepted, {rejected_count} rejected", level='INFO')
    
    return True, normalized_errors