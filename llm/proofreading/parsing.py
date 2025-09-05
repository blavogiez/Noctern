"""
Robust parsing for AI responses - multiple fallback strategies.
"""

import json
import re
from typing import Dict, Any, Optional
from llm import utils
from utils import logs_console


def parse_ai_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Parse AI response using multiple fallback strategies."""
    
    logs_console.log(f"Parsing AI response ({len(response_text)} chars)", level='DEBUG')
    
    # Strategy 1: Direct JSON parsing (structured output)
    try:
        data = json.loads(response_text)
        logs_console.log("Parsed via direct JSON", level='DEBUG')
        return data
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: JSON extraction 
    try:
        cleaned = utils.extract_json_from_llm_response(response_text)
        data = json.loads(cleaned)
        logs_console.log("Parsed via JSON extraction", level='DEBUG')
        return data
    except (ValueError, json.JSONDecodeError):
        pass
    
    # Strategy 3: Multiple JSON objects
    try:
        data = _extract_multiple_json(response_text)
        if data.get("errors"):
            logs_console.log(f"Parsed via multi-JSON ({len(data['errors'])} errors)", level='DEBUG')
            return data
    except Exception:
        pass
    
    # Strategy 4: Text parsing (last resort)
    try:
        data = _parse_from_text(response_text)
        if data.get("errors"):
            logs_console.log(f"Parsed via text parsing ({len(data['errors'])} errors)", level='DEBUG')
            return data
    except Exception:
        pass
    
    logs_console.log("All parsing strategies failed", level='WARNING')
    return None


def _extract_multiple_json(text: str) -> Dict[str, Any]:
    """Find and combine multiple JSON objects."""
    json_pattern = r'\{[^{}]*(?:"[^"]*"[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    all_errors = []
    for match in matches:
        try:
            obj = json.loads(match)
            if isinstance(obj, dict):
                if "errors" in obj:
                    all_errors.extend(obj["errors"])
                elif any(key in obj for key in ["type", "original"]):
                    all_errors.append(obj)
        except json.JSONDecodeError:
            continue
    
    return {"errors": all_errors}


def _parse_from_text(text: str) -> Dict[str, Any]:
    """Extract errors from plain text (fallback)."""
    errors = []
    
    # Look for error patterns
    patterns = [
        r'([a-zA-Z]+)\s*error[:\s]+"([^"]+)"\s*→\s*"([^"]*)"',
        r'Type[:\s]+([^,\n]+)[,\s]+Original[:\s]+"([^"]+)"\s*[,\s]*Suggestion[:\s]+"([^"]*)"',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            if len(match) >= 3:
                error_type = match[0].lower().strip()
                original = match[1].strip()
                suggestion = match[2].strip()
                
                # Map to valid type
                if "grammar" in error_type or "grammatical" in error_type:
                    error_type = "grammar"
                elif "spell" in error_type:
                    error_type = "spelling" 
                elif "punct" in error_type:
                    error_type = "punctuation"
                else:
                    error_type = "grammar"
                
                if original:
                    errors.append({
                        "type": error_type,
                        "original": original,
                        "suggestion": suggestion,
                        "explanation": f"Extracted {error_type} issue",
                        "importance": "medium"
                    })
    
    return {"errors": errors}