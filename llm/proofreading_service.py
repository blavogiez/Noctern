"""Proofreading service - AI analysis and error management."""
import json
import os
import threading
from datetime import datetime
from typing import List, Optional, Dict, Any

from llm import state, utils, api_client
from llm.schemas.proofreading import get_proofreading_schema, validate_proofreading_response
from utils import logs_console


class ProofreadingError:
    """Single proofreading error."""
    def __init__(self, error_type: str, original: str, suggestion: str, 
                 explanation: str, importance: str = "medium"):
        self.type = error_type
        self.original = original
        self.suggestion = suggestion
        self.explanation = explanation
        self.importance = importance
        self.context = ""
        self.is_approved = False
        self.is_applied = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], full_text: str = ""):
        """Create error from API response data."""
        error = cls(
            error_type=data.get('type', 'grammar'),
            original=data.get('original', ''),
            suggestion=data.get('suggestion', ''),
            explanation=data.get('explanation', ''),
            importance=data.get('importance', 'medium')
        )
        
        # Generate context around error
        if full_text and error.original:
            error.context = create_error_context(error.original, full_text)
        else:
            error.context = error.original
        
        return error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'type': self.type,
            'original': self.original,
            'suggestion': self.suggestion,
            'explanation': self.explanation,
            'importance': self.importance,
            'context': self.context,
            'is_approved': self.is_approved,
            'is_applied': self.is_applied
        }


class ProofreadingSession:
    """Manages proofreading session state."""
    def __init__(self, text: str, custom_instructions: str = ""):
        self.original_text = text
        self.custom_instructions = custom_instructions
        self.errors = []
        self.current_error_index = 0
        self.is_processing = False
        self.status = "Ready"
        self.created_at = datetime.now().isoformat()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Callbacks for UI updates
        self.on_status_change = None
        self.on_progress_change = None
        self.on_errors_found = None
        self.on_error = None
    
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
    
    def approve_current_correction(self) -> bool:
        """Approve current error correction."""
        current_error = self.get_current_error()
        if current_error and not current_error.is_approved:
            current_error.is_approved = True
            return True
        return False
    
    def reject_current_correction(self) -> bool:
        """Reject current error correction."""
        current_error = self.get_current_error()
        if current_error:
            current_error.is_approved = False
            return True
        return False
    
    def apply_current_correction(self, editor) -> bool:
        """Apply current correction to editor."""
        current_error = self.get_current_error()
        if not current_error or current_error.is_applied:
            return False
        
        try:
            editor_content = editor.get("1.0", "end-1c")
            
            if current_error.original in editor_content:
                updated_content = editor_content.replace(
                    current_error.original, 
                    current_error.suggestion, 
                    1
                )
                
                editor.delete("1.0", "end")
                editor.insert("1.0", updated_content)
                
                current_error.is_applied = True
                return True
            
            return False
        except:
            return False
    
    def get_approved_errors(self) -> List[ProofreadingError]:
        """Get all approved but not applied errors."""
        return [error for error in self.errors if error.is_approved and not error.is_applied]
    
    def get_applied_corrections_count(self) -> int:
        """Count applied corrections."""
        return sum(1 for error in self.errors if error.is_applied)
    
    def get_approved_corrections_count(self) -> int:
        """Count approved corrections."""
        return sum(1 for error in self.errors if error.is_approved)
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get error count by type."""
        summary = {}
        for error in self.errors:
            summary[error.type] = summary.get(error.type, 0) + 1
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for storage."""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at,
            'original_text': self.original_text,
            'custom_instructions': self.custom_instructions,
            'status': self.status,
            'current_error_index': self.current_error_index,
            'errors': [error.to_dict() for error in self.errors]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create session from stored dictionary."""
        session = cls(data['original_text'], data.get('custom_instructions', ''))
        session.session_id = data.get('session_id', session.session_id)
        session.created_at = data.get('created_at', session.created_at)
        session.status = data.get('status', 'Ready')
        session.current_error_index = data.get('current_error_index', 0)
        
        for error_data in data.get('errors', []):
            error = ProofreadingError.from_dict(error_data, session.original_text)
            session.errors.append(error)
        
        return session


# Global service instance
proofreading_service = None


def get_proofreading_service():
    """Get singleton proofreading service."""
    global proofreading_service
    if proofreading_service is None:
        proofreading_service = ProofreadingService()
    return proofreading_service


class ProofreadingService:
    """Main proofreading service."""
    def __init__(self):
        self.current_session = None
    
    def start_session(self, text: str, custom_instructions: str = "") -> ProofreadingSession:
        """Start new proofreading session."""
        self.current_session = ProofreadingSession(text, custom_instructions)
        return self.current_session
    
    def analyze_text(self, session: ProofreadingSession, editor):
        """Analyze text for errors using AI."""
        if not session or session.is_processing:
            logs_console.log("Skipping analysis - session busy", level='WARNING')
            return
        
        logs_console.log(f"Starting proofreading analysis: {len(session.original_text)} chars", level='INFO')
        
        session.is_processing = True
        update_session_status(session, "Contacting LLM...")
        
        # Get prompt template
        prompt_template = state._global_default_prompts.get("proofreading")
        if not prompt_template:
            logs_console.log("Proofreading prompt template not found", level='ERROR')
            finish_session_with_error(session, "Proofreading prompt template not configured")
            return
        
        # Build full prompt
        full_prompt = build_proofreading_prompt(prompt_template, session)
        logs_console.log(f"Built prompt: {len(full_prompt)} chars", level='INFO')
        
        # Start analysis in background thread
        thread = threading.Thread(target=run_ai_analysis, args=(session, editor, full_prompt))
        thread.daemon = True
        thread.start()


# Helper functions

def create_error_context(original_text: str, full_text: str, words_before: int = 10, words_after: int = 10) -> str:
    """Create context around error text."""
    if not original_text or not full_text:
        return original_text
    
    error_pos = full_text.find(original_text)
    if error_pos == -1:
        return original_text
    
    text_before = full_text[:error_pos]
    text_after = full_text[error_pos + len(original_text):]
    
    words_before_list = text_before.split()[-words_before:]
    words_after_list = text_after.split()[:words_after]
    
    context_parts = []
    if len(text_before.split()) > words_before:
        context_parts.append("...")
    context_parts.extend(words_before_list)
    context_parts.append(original_text)
    context_parts.extend(words_after_list)
    if len(text_after.split()) > words_after:
        context_parts.append("...")
    
    return " ".join(context_parts)


def update_session_status(session: ProofreadingSession, message: str):
    """Update session status and notify UI."""
    session.status = message
    if session.on_status_change:
        session.on_status_change(message)
    if session.on_progress_change:
        session.on_progress_change(message)


def finish_session_with_error(session: ProofreadingSession, error_message: str):
    """Finish session with error state."""
    session.is_processing = False
    session.status = "Analysis failed"
    if session.on_error:
        session.on_error(error_message)


def build_proofreading_prompt(template: str, session: ProofreadingSession) -> str:
    """Build complete prompt for AI analysis."""
    instructions_part = ""
    if session.custom_instructions.strip():
        instructions_part = f"Additional instructions: {session.custom_instructions}"
    
    return template.format(
        text_to_check=session.original_text,
        custom_instructions=instructions_part
    )


def run_ai_analysis(session: ProofreadingSession, editor, full_prompt: str):
    """Run AI analysis in background thread."""
    try:
        logs_console.log("Starting AI analysis", level='INFO')
        
        # Call AI with structured output
        json_schema = get_proofreading_schema()
        generator = api_client.generate_with_structured_output(
            full_prompt, 
            json_schema, 
            model_name=state.model_proofreading, 
            stream=False, 
            task_type="proofreading"
        )
        
        # Get response
        response = next(generator)
        logs_console.log(f"AI response received: {response.get('success')}", level='INFO')
        
        if not response.get("success"):
            error_msg = response.get("error", "Unknown AI error")
            logs_console.log(f"AI analysis failed: {error_msg}", level='ERROR')
            editor.after(0, finish_session_with_error, session, error_msg)
            return
        
        # Process successful response
        process_ai_response(session, editor, response.get("data", ""))
        
    except Exception as e:
        logs_console.log(f"Analysis error: {e}", level='ERROR')
        editor.after(0, finish_session_with_error, session, f"Analysis failed: {str(e)}")


def process_ai_response(session: ProofreadingSession, editor, response_text: str):
    """Process AI response and create error objects."""
    try:
        logs_console.log(f"Processing AI response: {len(response_text)} chars", level='INFO')
        
        # Update status
        editor.after(0, update_session_status, session, "Formatting JSON...")
        
        # Clean and parse JSON
        cleaned_response = utils.clean_full_llm_response(response_text)
        errors_data = json.loads(cleaned_response)
        
        # Validate response format
        is_valid, normalized_errors = validate_proofreading_response(errors_data)
        if not is_valid:
            # Try fallback format
            if isinstance(errors_data, list):
                is_valid, normalized_errors = validate_proofreading_response({"errors": errors_data})
            
            if not is_valid:
                logs_console.log("Response validation failed", level='ERROR')
                editor.after(0, finish_session_with_error, session, "Invalid AI response format")
                return
        
        # Create error objects
        editor.after(0, update_session_status, session, "Processing errors...")
        logs_console.log(f"Creating {len(normalized_errors)} error objects", level='INFO')
        
        session.errors = []
        for i, error_data in enumerate(normalized_errors):
            try:
                error = ProofreadingError.from_dict(error_data, session.original_text)
                session.errors.append(error)
            except Exception as e:
                logs_console.log(f"Failed to create error {i+1}: {e}", level='WARNING')
        
        # Finish processing
        finish_successful_analysis(session, editor)
        
    except json.JSONDecodeError as e:
        logs_console.log(f"JSON parsing failed: {e}", level='ERROR')
        editor.after(0, finish_session_with_error, session, "Invalid AI response format")
    except Exception as e:
        logs_console.log(f"Response processing failed: {e}", level='ERROR')
        editor.after(0, finish_session_with_error, session, f"Failed to process response: {str(e)}")


def finish_successful_analysis(session: ProofreadingSession, editor):
    """Complete successful analysis."""
    session.current_error_index = 0
    error_count = len(session.errors)
    session.is_processing = False
    
    logs_console.log(f"Analysis complete: {error_count} errors found", level='INFO')
    
    # Update status
    if error_count == 0:
        session.status = "No errors found"
        message = "Analysis complete - text looks good!"
    else:
        session.status = f"Found {error_count} errors"
        message = f"Analysis complete - {error_count} errors to review"
    
    editor.after(0, update_session_status, session, message)
    
    # Notify UI about errors found
    if session.on_errors_found:
        editor.after(0, session.on_errors_found, session.errors)
    
    # Save to cache
    try:
        current_filepath = state.get_active_filepath()
        save_session_to_cache(session, current_filepath)
    except:
        pass  # Cache saving is optional


def save_session_to_cache(session: ProofreadingSession, filepath: Optional[str] = None) -> str:
    """Save session to cache directory."""
    try:
        # Determine cache directory
        if filepath and os.path.exists(filepath):
            base_dir = os.path.dirname(filepath)
            filename = os.path.splitext(os.path.basename(filepath))[0]
            cache_dir = os.path.join(base_dir, f"{filename}.cache", "proofreading")
        else:
            cache_dir = os.path.join(os.getcwd(), "proofreading_cache")
        
        os.makedirs(cache_dir, exist_ok=True)
        
        # Save session data
        session_file = os.path.join(cache_dir, f"proofreading_{session.session_id}.json")
        session_data = session.to_dict()
        session_data['metadata'] = {
            'original_filepath': filepath,
            'total_errors': len(session.errors),
            'approved_errors': session.get_approved_corrections_count(),
            'applied_errors': session.get_applied_corrections_count(),
            'error_summary': session.get_error_summary()
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return session_file
    except Exception as e:
        logs_console.log(f"Cache save failed: {e}", level='WARNING')
        return ""


def load_session_from_cache(session_file: str) -> Optional[ProofreadingSession]:
    """Load session from cache file."""
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return ProofreadingSession.from_dict(data)
    except Exception as e:
        logs_console.log(f"Cache load failed: {e}", level='WARNING')
        return None


def list_cached_sessions(filepath: Optional[str] = None) -> List[Dict[str, Any]]:
    """List available cached sessions."""
    try:
        # Determine cache directory
        if filepath and os.path.exists(filepath):
            base_dir = os.path.dirname(filepath)
            filename = os.path.splitext(os.path.basename(filepath))[0]
            cache_dir = os.path.join(base_dir, f"{filename}.cache", "proofreading")
        else:
            cache_dir = os.path.join(os.getcwd(), "proofreading_cache")
        
        sessions = []
        if os.path.exists(cache_dir):
            for filename in os.listdir(cache_dir):
                if filename.startswith("proofreading_") and filename.endswith(".json"):
                    session_file = os.path.join(cache_dir, filename)
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        sessions.append({
                            'file': session_file,
                            'session_id': data.get('session_id', ''),
                            'created_at': data.get('created_at', ''),
                            'status': data.get('status', ''),
                            'total_errors': data.get('metadata', {}).get('total_errors', 0),
                            'approved_errors': data.get('metadata', {}).get('approved_errors', 0),
                            'error_summary': data.get('metadata', {}).get('error_summary', {})
                        })
                    except:
                        continue
        
        sessions.sort(key=lambda x: x['created_at'], reverse=True)
        return sessions
    except:
        return []