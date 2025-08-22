"""
JSON schemas for structured LLM outputs.
"""

from .proofreading import get_proofreading_schema, validate_proofreading_response

__all__ = [
    "get_proofreading_schema",
    "validate_proofreading_response"
]