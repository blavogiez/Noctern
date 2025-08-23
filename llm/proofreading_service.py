"""Proofreading service with AI-powered text analysis."""
import json
import os
from datetime import datetime
from typing import List, Optional, Callable

from llm import state
from llm import utils
from llm.streaming_service import start_streaming_request
from llm.schemas.proofreading import get_proofreading_schema, validate_proofreading_response


class ErrorType:
    """Proofreading error types."""
    GRAMMAR = "grammar"
    SPELLING = "spelling"
    PUNCTUATION = "punctuation"
    STYLE = "style"
    CLARITY = "clarity"
    SYNTAX = "syntax"
    COHERENCE = "coherence"


class ProofreadingError:
    """Single proofreading error with context and correction."""
    def __init__(self, error_type, original, suggestion, explanation, importance="medium"):
        """Initialize proofreading error."""
        self.type = error_type
        self.original = original
        self.suggestion = suggestion
        self.explanation = explanation
        self.importance = importance
        self.start_pos = 0
        self.end_pos = 0
        self.context = ""
        self.is_applied = False
        self.is_approved = False
    
    @classmethod
    def from_dict(cls, data, full_text=""):
        """Create error from dictionary data."""
        error_type = data.get('type', 'grammar')
        original_text = data.get('original', '')
        
        if full_text and original_text:
            context = cls.create_context(original_text, full_text)
        else:
            context = original_text
        
        error = cls(
            error_type=error_type,
            original=original_text,
            suggestion=data.get('suggestion', ''),
            explanation=data.get('explanation', ''),
            importance=data.get('importance', 'medium')
        )
        
        error.context = context
        error.is_approved = data.get('is_approved', False)
        error.is_applied = data.get('is_applied', False)
        
        return error
    
    @staticmethod
    def create_context(original_text, full_text, words_before=10, words_after=10):
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
    
    def to_dict(self):
        return {
            'type': self.type,
            'original': self.original,
            'suggestion': self.suggestion,
            'explanation': self.explanation,
            'importance': self.importance,
            'start': self.start_pos,
            'end': self.end_pos,
            'context': self.context,
            'is_applied': self.is_applied,
            'is_approved': self.is_approved
        }


class ProofreadingSession:
    """Manages proofreading session with errors and state."""
    def __init__(self, text, custom_instructions=""):
        """Initialize proofreading session."""
        self.original_text = text
        self.custom_instructions = custom_instructions
        self.errors = []
        self.current_error_index = 0
        self.is_processing = False
        self.status = "Ready"
        self.created_at = datetime.now().isoformat()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.on_status_change = None
        self.on_progress_change = None
        self.on_errors_found = None
        self.on_chunk_received = None
        self.on_error = None
    
    def get_error_summary(self):
        summary = {}
        for error in self.errors:
            summary[error.type] = summary.get(error.type, 0) + 1
        return summary
    
    def get_current_error(self):
        if 0 <= self.current_error_index < len(self.errors):
            return self.errors[self.current_error_index]
        return None
    
    def navigate_to_error(self, index):
        if 0 <= index < len(self.errors):
            self.current_error_index = index
            return True
        return False
    
    def go_to_next_error(self):
        if self.current_error_index < len(self.errors) - 1:
            self.current_error_index += 1
            return True
        return False
    
    def go_to_previous_error(self):
        if self.current_error_index > 0:
            self.current_error_index -= 1
            return True
        return False
    
    def apply_current_correction(self, editor):
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
    
    def get_applied_corrections_count(self):
        return sum(1 for error in self.errors if error.is_applied)
    
    def get_approved_corrections_count(self):
        return sum(1 for error in self.errors if error.is_approved)
    
    def approve_current_correction(self):
        current_error = self.get_current_error()
        if current_error and not current_error.is_approved:
            current_error.is_approved = True
            return True
        return False
    
    def reject_current_correction(self):
        current_error = self.get_current_error()
        if current_error:
            current_error.is_approved = False
            return True
        return False
    
    def get_approved_errors(self):
        return [error for error in self.errors if error.is_approved and not error.is_applied]
    
    def save_to_cache(self, filepath=None):
        return ProofreadingCache.save_session(self, filepath)
    
    def to_dict(self):
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
    def from_dict(cls, data):
        session = cls(data['original_text'], data.get('custom_instructions', ''))
        session.session_id = data.get('session_id', session.session_id)
        session.created_at = data.get('created_at', session.created_at)
        session.status = data.get('status', 'Ready')
        session.current_error_index = data.get('current_error_index', 0)
        
        for error_data in data.get('errors', []):
            error = ProofreadingError.from_dict(error_data, session.original_text)
            session.errors.append(error)
        
        return session


class ProofreadingCache:
    """Session caching and persistence."""
    @staticmethod
    def get_cache_dir(filepath=None):
        if filepath and os.path.exists(filepath):
            base_dir = os.path.dirname(filepath)
            filename = os.path.splitext(os.path.basename(filepath))[0]
            cache_dir = os.path.join(base_dir, f"{filename}.cache", "proofreading")
        else:
            cache_dir = os.path.join(os.getcwd(), "proofreading_cache")
        
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
    
    @staticmethod
    def save_session(session, filepath=None):
        try:
            cache_dir = ProofreadingCache.get_cache_dir(filepath)
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
        except:
            return ""
    
    @staticmethod
    def load_session(session_file):
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ProofreadingSession.from_dict(data)
        except:
            return None
    
    @staticmethod
    def list_sessions(filepath=None):
        try:
            cache_dir = ProofreadingCache.get_cache_dir(filepath)
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


class ProofreadingService:
    """Main proofreading service with AI integration."""
    def __init__(self):
        self.current_session = None
    
    def start_proofreading_session(self, text, custom_instructions=""):
        self.current_session = ProofreadingSession(text, custom_instructions)
        return self.current_session
    
    def analyze_text(self, session, editor):
        if not session or session.is_processing:
            return
        
        session.is_processing = True
        session.status = "Analyzing text..."
        
        if session.on_status_change:
            session.on_status_change(session.status)
        
        if session.on_progress_change:
            session.on_progress_change("Preparing AI analysis...")
        
        prompt_template = state._global_default_prompts.get("proofreading")
        if not prompt_template:
            session.is_processing = False
            session.status = "Error: Template not found"
            if session.on_error:
                session.on_error("Proofreading prompt template not configured")
            return
        
        instructions_part = f"Additional instructions: {session.custom_instructions}" if session.custom_instructions.strip() else ""
        full_prompt = prompt_template.format(
            text_to_check=session.original_text,
            custom_instructions=instructions_part
        )
        
        accumulated_response = ""
        
        def on_chunk(chunk):
            nonlocal accumulated_response
            accumulated_response += chunk
            if session.on_chunk_received:
                session.on_chunk_received(accumulated_response)
        
        def on_success(final_text):
            session.is_processing = False
            
            try:
                cleaned_response = utils.clean_full_llm_response(final_text)
                errors_data = json.loads(cleaned_response)
                
                is_valid, normalized_errors = validate_proofreading_response(errors_data)
                
                if not is_valid:
                    if isinstance(errors_data, list):
                        is_valid, normalized_errors = validate_proofreading_response({"errors": errors_data})
                    
                    if not is_valid:
                        session.status = "AI analysis failed"
                        if session.on_error:
                            session.on_error("The AI response does not match the expected format.")
                        return
                
                session.errors = [ProofreadingError.from_dict(error_data, session.original_text) for error_data in normalized_errors]
                session.current_error_index = 0
                
                error_count = len(session.errors)
                if error_count == 0:
                    session.status = "No errors found"
                    if session.on_progress_change:
                        session.on_progress_change("Analysis complete - text looks good!")
                else:
                    session.status = f"Found {error_count} errors"
                    if session.on_progress_change:
                        session.on_progress_change(f"Analysis complete - {error_count} errors to review")
                
                if session.on_status_change:
                    session.on_status_change(session.status)
                
                if session.on_errors_found:
                    session.on_errors_found(session.errors)
                
                try:
                    current_filepath = state.get_active_filepath()
                    session.save_to_cache(current_filepath)
                except:
                    pass
                
            except json.JSONDecodeError:
                session.status = "Invalid AI response"
                if session.on_error:
                    session.on_error("The AI response is not valid JSON.")
            except Exception as e:
                session.status = "Analysis failed"
                if session.on_error:
                    session.on_error(f"Failed to process AI response: {str(e)}")
        
        def on_error(error_msg):
            session.is_processing = False
            session.status = "Analysis failed"
            
            enhanced_error = error_msg
            if "filtered by safety settings" in error_msg.lower():
                enhanced_error = "Content was filtered by safety settings. Try using a different model or smaller text sections."
            elif "empty response" in error_msg.lower():
                enhanced_error = "Received empty response. Content may have been filtered by safety settings."
            
            if session.on_error:
                session.on_error(enhanced_error)
        
        json_schema = get_proofreading_schema()
        start_streaming_request(
            editor=editor,
            prompt=full_prompt,
            model_name=state.model_proofreading,
            on_chunk=on_chunk,
            on_success=on_success,
            on_error=on_error,
            task_type="proofreading",
            json_schema=json_schema
        )
    
    def get_current_session(self):
        return self.current_session


proofreading_service = ProofreadingService()


def get_proofreading_service():
    """Get global proofreading service instance."""
    return proofreading_service