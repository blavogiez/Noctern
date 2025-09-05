"""Backward compatibility for proofreading schema."""

from llm.proofreading.validation import validate_proofreading_response

# JSON Schema for structured AI output
PROOFREADING_SCHEMA = {
    "type": "object",
    "properties": {
        "errors": {
            "type": "array",
            "description": "List of proofreading errors found in the text",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["grammar", "spelling", "punctuation", "style", "clarity", "syntax", "coherence"]},
                    "original": {"type": "string"},
                    "suggestion": {"type": "string"}, 
                    "explanation": {"type": "string"},
                    "importance": {"type": "string", "enum": ["high", "medium", "low"]}
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