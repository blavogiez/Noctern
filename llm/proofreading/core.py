"""
Core classes for proofreading - simplified and production-ready.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class ProofreadingError:
    """Single proofreading error - simplified."""
    type: str
    original: str
    suggestion: str
    explanation: str
    importance: str = "medium"
    is_approved: bool = False
    is_applied: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProofreadingError':
        """Create error from API response data."""
        return cls(
            type=data.get('type', 'grammar'),
            original=data.get('original', ''),
            suggestion=data.get('suggestion', ''),
            explanation=data.get('explanation', ''),
            importance=data.get('importance', 'medium')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'type': self.type,
            'original': self.original,
            'suggestion': self.suggestion,
            'explanation': self.explanation,
            'importance': self.importance,
            'is_approved': self.is_approved,
            'is_applied': self.is_applied
        }


class ProofreadingSession:
    """Manages proofreading session - simplified."""
    
    def __init__(self, text: str, custom_instructions: str = ""):
        self.original_text = text
        self.custom_instructions = custom_instructions
        self.errors: List[ProofreadingError] = []
        self.current_error_index = 0
        self.is_processing = False
        self.status = "Ready"
        self.created_at = datetime.now().isoformat()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # UI callbacks - None by default, set by panel
        self.on_status_change = None
        self.on_progress_change = None
        self.on_errors_found = None
        self.on_error = None
    
    def get_current_error(self) -> Optional[ProofreadingError]:
        """Get currently selected error."""
        if 0 <= self.current_error_index < len(self.errors):
            return self.errors[self.current_error_index]
        return None
    
    def apply_correction(self, editor, error: ProofreadingError) -> bool:
        """Apply correction to editor."""
        try:
            content = editor.get("1.0", "end-1c")
            if error.original in content and not error.is_applied:
                updated = content.replace(error.original, error.suggestion, 1)
                editor.delete("1.0", "end")
                editor.insert("1.0", updated)
                error.is_applied = True
                return True
            return False
        except:
            return False
    
    def go_to_previous_error(self) -> bool:
        """Navigate to previous error."""
        if self.current_error_index > 0:
            self.current_error_index -= 1
            return True
        return False
    
    def go_to_next_error(self) -> bool:
        """Navigate to next error."""
        if self.current_error_index < len(self.errors) - 1:
            self.current_error_index += 1
            return True
        return False
    
    def approve_current_correction(self) -> bool:
        """Approve the current error correction."""
        current_error = self.get_current_error()
        if current_error and not current_error.is_applied:
            current_error.is_approved = True
            return True
        return False
    
    def reject_current_correction(self) -> bool:
        """Reject the current error correction."""
        current_error = self.get_current_error()
        if current_error and not current_error.is_applied:
            current_error.is_approved = False
            return True
        return False
    
    def apply_current_correction(self, editor) -> bool:
        """Apply the current error correction to editor."""
        current_error = self.get_current_error()
        if current_error and current_error.is_approved:
            return self.apply_correction(editor, current_error)
        return False