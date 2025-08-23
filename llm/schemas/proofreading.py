"""JSON Schema for proofreading errors structured output."""


# JSON Schema for proofreading errors (OpenAPI 3.0 subset compatible with Gemini)
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
                        "description": "Importance level of the error for document professionalism"
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
    """Get the JSON schema for proofreading structured output."""
    return PROOFREADING_SCHEMA

def validate_proofreading_response(response_data):
    """Validate response matches proofreading schema."""
    """
    Validate that a response matches the expected proofreading schema.
    
    Args:
        response_data (dict): The parsed JSON response
    
    Returns:
        tuple: (is_valid, normalized_errors)
    """
    if not isinstance(response_data, dict):
        return False, []
    
    # Check for unwanted fields that indicate wrong response type
    forbidden_fields = ["title", "authors", "journal", "volume", "issue", "pages", "doi", "abstract", "date"]
    if any(field in response_data for field in forbidden_fields):
        return False, []
    
    if "errors" not in response_data:
        return False, []
    
    errors = response_data["errors"]
    if not isinstance(errors, list):
        return False, []
    
    normalized_errors = []
    valid_types = ["grammar", "spelling", "punctuation", "style", "clarity", "syntax", "coherence"]
    
    for i, error in enumerate(errors):
        if not isinstance(error, dict):
            continue
        
        # Check for required fields
        required_fields = ["type", "original", "suggestion", "explanation"]
        missing_fields = [field for field in required_fields if field not in error]
        if missing_fields:
            continue
            
        # Validate type
        error_type = error.get("type", "").lower()
        if error_type not in valid_types:
            continue
        
        original = error.get("original", "").strip()
        suggestion = error.get("suggestion", "").strip()
        explanation = error.get("explanation", "").strip()
        importance = error.get("importance", "medium").lower()
        
        # Validate importance level
        if importance not in ["high", "medium", "low"]:
            importance = "medium"
        
        # Skip errors with empty required fields (but allow empty suggestion for deletions)
        if not original or not explanation:
            continue
        
        # For coherence errors, empty suggestion means deletion (which is valid)
        if not suggestion and error_type != "coherence":
            continue
        
        # Skip if suggestion is identical to original (no actual correction)
        if original == suggestion:
            continue
            
        # Normalize error with required fields and defaults
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