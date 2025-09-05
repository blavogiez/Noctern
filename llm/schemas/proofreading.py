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
    from utils import logs_console
    
    if not isinstance(response_data, dict):
        logs_console.log("Response data is not a dictionary", level='DEBUG')
        return False, []
    
    # Check for forbidden fields (wrong response type)
    forbidden_fields = ["title", "authors", "journal", "volume", "issue", "pages", "doi", "abstract", "date"]
    if any(field in response_data for field in forbidden_fields):
        logs_console.log("Found forbidden fields - likely wrong response type", level='DEBUG')
        return False, []
    
    if "errors" not in response_data:
        logs_console.log("No 'errors' field found in response", level='DEBUG')
        return False, []
    
    errors = response_data["errors"]
    if not isinstance(errors, list):
        logs_console.log("Errors field is not a list", level='DEBUG')
        return False, []
    
    logs_console.log(f"Starting validation of {len(errors)} potential errors", level='INFO')
    
    normalized_errors = []
    rejected_errors = []
    valid_types = {"grammar", "spelling", "punctuation", "style", "clarity", "syntax", "coherence"}
    valid_importance = {"high", "medium", "low"}
    
    # Map similar/alternative error types to valid ones
    type_mapping = {
        "grammatical": "grammar",
        "grammatical error": "grammar",
        "misspelling": "spelling",
        "typo": "spelling", 
        "punctuation error": "punctuation",
        "styling": "style",
        "stylistic": "style",
        "unclear": "clarity",
        "ambiguous": "clarity",
        "confusing": "clarity",
        "syntax error": "syntax",
        "word order": "syntax",
        "coherence error": "coherence",
        "logic": "coherence",
        "logical": "coherence"
    }
    
    for i, error in enumerate(errors):
        if not isinstance(error, dict):
            rejected_errors.append(f"Error {i+1}: Not a dictionary")
            continue
        
        # Check required fields - be more lenient
        required_fields = ["type", "original"]
        missing_fields = [field for field in required_fields if field not in error or not str(error[field]).strip()]
        if missing_fields:
            rejected_errors.append(f"Error {i+1}: Missing required fields: {missing_fields}")
            continue
        
        original_type = error.get("type", "").lower().strip()
        error_type = original_type
        
        # Try to map similar types
        if error_type not in valid_types and error_type in type_mapping:
            error_type = type_mapping[error_type]
        
        # If still not valid, try partial matching
        if error_type not in valid_types:
            for valid_type in valid_types:
                if valid_type in error_type or error_type in valid_type:
                    error_type = valid_type
                    break
        
        if error_type not in valid_types:
            rejected_errors.append(f"Error {i+1}: Invalid type '{original_type}' (mapped to '{error_type}')")
            continue
        
        original = error.get("original", "").strip()
        suggestion = error.get("suggestion", "").strip()
        explanation = error.get("explanation", "").strip()
        importance = error.get("importance", "medium").lower().strip()
        
        # Validate fields - be more lenient
        if not original:
            rejected_errors.append(f"Error {i+1}: Empty original text")
            continue
        
        # Allow missing explanation but warn
        if not explanation:
            explanation = "No explanation provided"
            logs_console.log(f"Error {i+1}: No explanation provided, using default", level='WARNING')
        
        if importance not in valid_importance:
            logs_console.log(f"Error {i+1}: Invalid importance '{importance}', defaulting to 'medium'", level='WARNING')
            importance = "medium"
        
        # Be more lenient with empty suggestions
        # Allow empty suggestions for more error types (deletion, formatting, etc.)
        deletion_types = {"coherence", "style", "clarity", "punctuation"}
        if not suggestion and error_type not in deletion_types:
            # For non-deletion types, warn but don't reject entirely
            logs_console.log(f"Error {i+1}: Empty suggestion for type '{error_type}' - keeping for review", level='WARNING')
        
        # Don't automatically reject identical original/suggestion - could be formatting/context errors
        if original == suggestion and error_type not in {"punctuation", "style"}:
            logs_console.log(f"Error {i+1}: Identical original and suggestion - keeping for review", level='WARNING')
        
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
    
    # Log filtering results
    accepted_count = len(normalized_errors)
    rejected_count = len(rejected_errors)
    logs_console.log(f"Validation complete: {accepted_count} errors accepted, {rejected_count} rejected", level='INFO')
    
    if rejected_errors:
        logs_console.log("Rejected errors details:", level='DEBUG')
        for rejection in rejected_errors[:10]:  # Limit to first 10 to avoid spam
            logs_console.log(f"  - {rejection}", level='DEBUG')
        if len(rejected_errors) > 10:
            logs_console.log(f"  - ... and {len(rejected_errors) - 10} more", level='DEBUG')
    
    return True, normalized_errors