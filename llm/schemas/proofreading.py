"""JSON Schema for proofreading errors validation."""

# Schema for structured AI output
PROOFREADING_SCHEMA = {
    "type": "object",
    "properties": {
        "errors": {
            "type": "array",
            "description": "List of proofreading errors found in the text",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["grammar", "spelling", "punctuation", "style", "clarity", "syntax", "coherence"],
                        "description": "Type of language error found"
                    },
                    "original": {
                        "type": "string",
                        "description": "The exact text containing the error"
                    },
                    "suggestion": {
                        "type": "string", 
                        "description": "The corrected version of the text"
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Brief explanation of why this is an error"
                    },
                    "importance": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Importance level of the error"
                    }
                },
                "required": ["type", "original", "suggestion", "explanation", "importance"]
            }
        }
    },
    "required": ["errors"]
}


def get_proofreading_schema():
    """Get JSON schema for proofreading structured output."""
    return PROOFREADING_SCHEMA


def validate_proofreading_response(response_data):
    """Validate response matches proofreading schema."""
    if not isinstance(response_data, dict):
        return False, []
    
    # Check for forbidden fields (wrong response type)
    forbidden_fields = ["title", "authors", "journal", "volume", "issue", "pages", "doi", "abstract", "date"]
    if any(field in response_data for field in forbidden_fields):
        return False, []
    
    if "errors" not in response_data:
        return False, []
    
    errors = response_data["errors"]
    if not isinstance(errors, list):
        return False, []
    
    normalized_errors = []
    valid_types = {"grammar", "spelling", "punctuation", "style", "clarity", "syntax", "coherence"}
    valid_importance = {"high", "medium", "low"}
    
    for error in errors:
        if not isinstance(error, dict):
            continue
        
        # Check required fields
        required_fields = ["type", "original", "explanation"]
        if not all(field in error for field in required_fields):
            continue
        
        error_type = error.get("type", "").lower()
        if error_type not in valid_types:
            continue
        
        original = error.get("original", "").strip()
        suggestion = error.get("suggestion", "").strip()
        explanation = error.get("explanation", "").strip()
        importance = error.get("importance", "medium").lower()
        
        # Validate fields
        if not original or not explanation:
            continue
        
        if importance not in valid_importance:
            importance = "medium"
        
        # Allow empty suggestion for deletions (coherence errors)
        if not suggestion and error_type != "coherence":
            continue
        
        # Skip if suggestion is identical to original
        if original == suggestion:
            continue
        
        # Create normalized error
        normalized_error = {
            "type": error_type,
            "original": original,
            "suggestion": suggestion,
            "explanation": explanation,
            "importance": importance,
            "start": error.get("start", 0),
            "end": error.get("end", 0),
            "context": error.get("context", original)
        }
        
        normalized_errors.append(normalized_error)
    
    return True, normalized_errors