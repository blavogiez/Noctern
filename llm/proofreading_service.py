"""
Professional document proofreading service with AI assistance.
Core business logic for grammar, spelling, and style error detection.
"""
import json
from typing import List, Dict, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum

from llm import state as llm_state
from llm import utils as llm_utils
from llm.streaming_service import start_streaming_request
from llm.schemas import get_proofreading_schema, validate_proofreading_response
from utils import debug_console


class ErrorType(Enum):
    """Types of proofreading errors."""
    GRAMMAR = "grammar"
    SPELLING = "spelling"
    PUNCTUATION = "punctuation"
    STYLE = "style"
    CLARITY = "clarity"
    SYNTAX = "syntax"
    COHERENCE = "coherence"


@dataclass
class ProofreadingError:
    """Represents a single proofreading error with correction."""
    type: ErrorType
    original: str
    suggestion: str
    explanation: str
    importance: str = "medium"
    start_pos: int = 0
    end_pos: int = 0
    context: str = ""
    is_applied: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProofreadingError':
        """Create ProofreadingError from dictionary."""
        error_type_str = data.get('type', 'grammar').lower().strip()
        
        # Try to create ErrorType, with fallback
        try:
            error_type = ErrorType(error_type_str)
        except ValueError as e:
            debug_console.log(f"Invalid error type '{error_type_str}', falling back to grammar: {e}", level='WARNING')
            error_type = ErrorType('grammar')
        
        debug_console.log(f"Creating error of type: {error_type.value}", level='DEBUG')
        
        return cls(
            type=error_type,
            original=data.get('original', ''),
            suggestion=data.get('suggestion', ''),
            explanation=data.get('explanation', ''),
            importance=data.get('importance', 'medium'),
            start_pos=data.get('start', 0),
            end_pos=data.get('end', 0),
            context=data.get('context', data.get('original', ''))
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'type': self.type.value,
            'original': self.original,
            'suggestion': self.suggestion,
            'explanation': self.explanation,
            'importance': self.importance,
            'start': self.start_pos,
            'end': self.end_pos,
            'context': self.context
        }


class ProofreadingSession:
    """Manages a single proofreading session."""
    
    def __init__(self, text: str, custom_instructions: str = ""):
        self.original_text = text
        self.custom_instructions = custom_instructions
        self.errors: List[ProofreadingError] = []
        self.current_error_index = 0
        self.is_processing = False
        self.status = "Ready"
        
        # Callbacks for UI updates
        self.on_status_change: Optional[Callable[[str], None]] = None
        self.on_progress_change: Optional[Callable[[str], None]] = None
        self.on_errors_found: Optional[Callable[[List[ProofreadingError]], None]] = None
        self.on_chunk_received: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors by type."""
        summary = {error_type.value: 0 for error_type in ErrorType}
        for error in self.errors:
            summary[error.type.value] += 1
        return summary
    
    def get_current_error(self) -> Optional[ProofreadingError]:
        """Get currently selected error."""
        if 0 <= self.current_error_index < len(self.errors):
            return self.errors[self.current_error_index]
        return None
    
    def navigate_to_error(self, index: int) -> bool:
        """Navigate to specific error by index."""
        if 0 <= index < len(self.errors):
            self.current_error_index = index
            return True
        return False
    
    def go_to_next_error(self) -> bool:
        """Navigate to next error."""
        if self.current_error_index < len(self.errors) - 1:
            self.current_error_index += 1
            return True
        return False
    
    def go_to_previous_error(self) -> bool:
        """Navigate to previous error."""
        if self.current_error_index > 0:
            self.current_error_index -= 1
            return True
        return False
    
    def apply_current_correction(self, editor) -> bool:
        """Apply the current error's correction to the editor."""
        current_error = self.get_current_error()
        if not current_error or current_error.is_applied:
            return False
        
        try:
            # Get current editor content
            editor_content = editor.get("1.0", "end-1c")
            
            # Apply correction
            if current_error.original in editor_content:
                updated_content = editor_content.replace(
                    current_error.original, 
                    current_error.suggestion, 
                    1
                )
                
                # Update editor
                editor.delete("1.0", "end")
                editor.insert("1.0", updated_content)
                
                # Mark as applied
                current_error.is_applied = True
                
                debug_console.log(f"Applied correction: '{current_error.original}' -> '{current_error.suggestion}'", level='INFO')
                return True
            else:
                debug_console.log(f"Original text not found: '{current_error.original}'", level='WARNING')
                return False
                
        except Exception as e:
            debug_console.log(f"Error applying correction: {e}", level='ERROR')
            return False
    
    def get_applied_corrections_count(self) -> int:
        """Get number of applied corrections."""
        return sum(1 for error in self.errors if error.is_applied)


class ProofreadingService:
    """Professional proofreading service with AI assistance."""
    
    def __init__(self):
        self.current_session: Optional[ProofreadingSession] = None
    
    def start_proofreading_session(self, text: str, custom_instructions: str = "") -> ProofreadingSession:
        """Start a new proofreading session."""
        self.current_session = ProofreadingSession(text, custom_instructions)
        return self.current_session
    
    def analyze_text(self, session: ProofreadingSession, editor) -> None:
        """Analyze text for proofreading errors using AI."""
        if not session or session.is_processing:
            return
        
        session.is_processing = True
        session.status = "Analyzing text..."
        
        if session.on_status_change:
            session.on_status_change(session.status)
        
        if session.on_progress_change:
            session.on_progress_change("Preparing AI analysis...")
        
        # Get proofreading prompt template
        prompt_template = llm_state._global_default_prompts.get("proofreading")
        if not prompt_template:
            session.is_processing = False
            session.status = "Error: Template not found"
            if session.on_error:
                session.on_error("Proofreading prompt template not configured")
            return
        
        # Format prompt
        instructions_part = f"Additional instructions: {session.custom_instructions}" if session.custom_instructions.strip() else ""
        full_prompt = prompt_template.format(
            text_to_check=session.original_text,
            custom_instructions=instructions_part
        )
        
        debug_console.log(f"Starting proofreading analysis - Text length: {len(session.original_text)} chars", level='INFO')
        
        # Prepare callbacks
        accumulated_response = ""
        
        def on_chunk(chunk: str):
            nonlocal accumulated_response
            accumulated_response += chunk
            if session.on_chunk_received:
                session.on_chunk_received(accumulated_response)
        
        def on_success(final_text: str):
            session.is_processing = False
            
            try:
                # Clean and parse response
                cleaned_response = llm_utils.clean_full_llm_response(final_text)
                errors_data = json.loads(cleaned_response)
                
                # Validate response
                is_valid, normalized_errors = validate_proofreading_response(errors_data)
                
                if not is_valid:
                    # Handle malformed responses
                    if isinstance(errors_data, list):
                        debug_console.log("Converting direct array response", level='INFO')
                        is_valid, normalized_errors = validate_proofreading_response({"errors": errors_data})
                    
                    if not is_valid:
                        session.status = "AI analysis failed"
                        error_msg = self._get_error_message_for_invalid_response(errors_data)
                        if session.on_error:
                            session.on_error(error_msg)
                        return
                
                # Convert to ProofreadingError objects
                debug_console.log(f"Processing {len(normalized_errors)} normalized errors", level='INFO')
                for i, error_data in enumerate(normalized_errors):
                    debug_console.log(f"Error {i+1}: type='{error_data.get('type')}', original='{error_data.get('original', '')[:50]}...'", level='DEBUG')
                
                session.errors = [ProofreadingError.from_dict(error_data) for error_data in normalized_errors]
                debug_console.log(f"Created {len(session.errors)} ProofreadingError objects", level='INFO')
                session.current_error_index = 0
                
                # Update status
                error_count = len(session.errors)
                if error_count == 0:
                    session.status = "No errors found"
                    if session.on_progress_change:
                        session.on_progress_change("Analysis complete - text looks good!")
                else:
                    session.status = f"Found {error_count} errors"
                    if session.on_progress_change:
                        session.on_progress_change(f"Analysis complete - {error_count} errors to review")
                
                # Notify UI
                if session.on_status_change:
                    session.on_status_change(session.status)
                
                if session.on_errors_found:
                    session.on_errors_found(session.errors)
                
                debug_console.log(f"Proofreading analysis complete: {error_count} errors found", level='SUCCESS')
                
            except json.JSONDecodeError as e:
                session.status = "Invalid AI response"
                error_msg = "The AI response is not valid JSON. This should not happen with structured output."
                debug_console.log(f"JSON parsing error: {e}", level='ERROR')
                debug_console.log(f"Raw response: {cleaned_response}", level='ERROR')
                if session.on_error:
                    session.on_error(error_msg)
                
            except Exception as e:
                session.status = "Analysis failed"
                error_msg = f"Failed to process AI response: {str(e)}"
                debug_console.log(f"Error processing response: {e}", level='ERROR')
                if session.on_error:
                    session.on_error(error_msg)
        
        def on_error(error_msg: str):
            session.is_processing = False
            session.status = "Analysis failed"
            debug_console.log(f"Proofreading request failed: {error_msg}", level='ERROR')
            
            # Provide helpful suggestions for common issues
            enhanced_error = error_msg
            if "filtered by safety settings" in error_msg.lower():
                enhanced_error = ("Content was filtered by Gemini's safety settings.\n\n"
                                "Suggestions:\n"
                                "• Try using a different Gemini model (2.5-flash-lite or 2.0-flash)\n"
                                "• Break your text into smaller sections\n"
                                "• Check for potentially sensitive content\n"
                                "• Use an Ollama model instead")
            elif "empty response" in error_msg.lower():
                enhanced_error = ("Gemini returned an empty response.\n\n"
                                "This usually means:\n"
                                "• Content was filtered by safety settings\n"
                                "• Try a different model or smaller text sections")
            
            if session.on_error:
                session.on_error(enhanced_error)
        
        # Start AI analysis with structured output
        json_schema = get_proofreading_schema()
        start_streaming_request(
            editor=editor,
            prompt=full_prompt,
            model_name=llm_state.model_proofreading,
            on_chunk=on_chunk,
            on_success=on_success,
            on_error=on_error,
            task_type="proofreading",
            json_schema=json_schema
        )
    
    def _get_error_message_for_invalid_response(self, errors_data) -> str:
        """Generate appropriate error message for invalid response."""
        forbidden_fields = ["title", "authors", "journal", "volume", "issue", "pages", "doi", "abstract", "date"]
        
        if isinstance(errors_data, dict) and any(field in errors_data for field in forbidden_fields):
            return ("The AI extracted document metadata instead of finding proofreading errors. "
                   "Please try again with a different model or adjust the instructions.")
        else:
            return ("The AI response does not match the expected format for proofreading errors. "
                   "Please try again or contact support if this persists.")
    
    def get_current_session(self) -> Optional[ProofreadingSession]:
        """Get the current proofreading session."""
        return self.current_session


# Global service instance
_proofreading_service = ProofreadingService()


def get_proofreading_service() -> ProofreadingService:
    """Get the global proofreading service instance."""
    return _proofreading_service