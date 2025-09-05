"""
Proofreading service - simplified and production-ready.
"""

import os
import threading
from datetime import datetime
from typing import Optional

from llm import state, api_client
from llm.schemas.proofreading import get_proofreading_schema
from utils import logs_console

from .core import ProofreadingSession, ProofreadingError
from .parsing import parse_ai_response
from .validation import validate_proofreading_response


class ProofreadingService:
    """Main proofreading service - simplified."""
    
    def __init__(self):
        self.current_session: Optional[ProofreadingSession] = None
    
    def start_session(self, text: str, instructions: str = "") -> ProofreadingSession:
        """Start new proofreading session."""
        self.current_session = ProofreadingSession(text, instructions)
        return self.current_session
    
    def analyze_text(self, session: ProofreadingSession, editor=None):
        """Analyze text for errors using AI."""
        if session.is_processing:
            return
        
        logs_console.log(f"Starting analysis: {len(session.original_text)} chars", level='INFO')
        session.is_processing = True
        session.status = "Analyzing..."
        
        # Build prompt
        prompt_template = state._global_default_prompts.get("proofreading")
        if not prompt_template:
            logs_console.log("Proofreading prompt template not found", level='ERROR')
            session.is_processing = False
            session.status = "Error: No prompt template"
            return
        
        full_prompt = self._build_prompt(prompt_template, session)
        
        # Run analysis
        if editor:
            thread = threading.Thread(target=self._run_analysis, args=(session, editor, full_prompt))
            thread.daemon = True
            thread.start()
        else:
            self._run_analysis(session, None, full_prompt)
    
    def _build_prompt(self, template: str, session: ProofreadingSession) -> str:
        """Build complete prompt."""
        instructions = ""
        if session.custom_instructions.strip():
            instructions = f"Additional instructions: {session.custom_instructions}"
        
        return template.format(
            text_to_check=session.original_text,
            custom_instructions=instructions
        )
    
    def _run_analysis(self, session: ProofreadingSession, editor, prompt: str):
        """Run AI analysis."""
        try:
            # Notify UI: Starting AI call
            self._notify_status(session, "Contacting LLM...", editor)
            logs_console.log("Calling AI service", level='DEBUG')
            
            # Call AI
            response_gen = api_client.generate_with_structured_output(
                prompt,
                get_proofreading_schema(),
                model_name=state.model_proofreading,
                stream=False,
                task_type="proofreading"
            )
            
            response = next(response_gen)
            
            if not response.get("success"):
                error_msg = response.get("error", "AI analysis failed")
                logs_console.log(f"AI error: {error_msg}", level='ERROR')
                self._finish_with_error(session, error_msg, editor)
                return
            
            # Notify UI: Processing response
            self._notify_status(session, "Processing response...", editor)
            
            # Process response
            self._process_response(session, response.get("data", ""), editor)
            
        except Exception as e:
            logs_console.log(f"Analysis error: {e}", level='ERROR')
            self._finish_with_error(session, str(e), editor)
    
    def _process_response(self, session: ProofreadingSession, response_text: str, editor):
        """Process AI response."""
        try:
            # Save for debug
            self._save_debug(session, response_text)
            
            # Parse response
            parsed_data = parse_ai_response(response_text)
            if not parsed_data:
                self._finish_with_error(session, "Could not parse AI response", editor)
                return
            
            # Validate errors
            is_valid, normalized_errors = validate_proofreading_response(parsed_data)
            if not is_valid:
                # Try fallback
                if isinstance(parsed_data, list):
                    is_valid, normalized_errors = validate_proofreading_response({"errors": parsed_data})
                
                if not is_valid:
                    normalized_errors = []  # Continue with empty list
            
            # Create error objects
            session.errors = []
            for error_data in normalized_errors:
                try:
                    error = ProofreadingError.from_dict(error_data)
                    session.errors.append(error)
                except Exception as e:
                    logs_console.log(f"Failed to create error: {e}", level='WARNING')
            
            # Finish
            self._finish_success(session, editor)
            
        except Exception as e:
            logs_console.log(f"Response processing error: {e}", level='ERROR')
            self._finish_with_error(session, str(e), editor)
    
    def _save_debug(self, session: ProofreadingSession, response_text: str):
        """Save debug info."""
        try:
            debug_dir = os.path.join(os.getcwd(), "app_logs", "proofreading")
            os.makedirs(debug_dir, exist_ok=True)
            
            debug_file = os.path.join(debug_dir, f"session_{session.session_id}.txt")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"Session: {session.session_id}\n")
                f.write(f"Time: {datetime.now().isoformat()}\n")
                f.write(f"Text length: {len(session.original_text)}\n")
                f.write(f"Response length: {len(response_text)}\n")
                f.write("-" * 40 + "\n")
                f.write(response_text)
        except Exception as e:
            logs_console.log(f"Debug save failed: {e}", level='DEBUG')
    
    def _finish_success(self, session: ProofreadingSession, editor):
        """Finish successful analysis."""
        session.is_processing = False
        error_count = len(session.errors)
        
        if error_count == 0:
            session.status = "No errors found"
        else:
            session.status = f"Found {error_count} errors"
        
        logs_console.log(f"Analysis complete: {error_count} errors", level='INFO')
        
        # Notify UI about completion
        self._notify_status(session, session.status, editor)
        
        # Notify UI about errors found
        if session.on_errors_found and session.errors:
            if editor:
                editor.after(0, lambda: session.on_errors_found(session.errors))
            else:
                session.on_errors_found(session.errors)
    
    def _finish_with_error(self, session: ProofreadingSession, error_msg: str, editor):
        """Finish with error."""
        session.is_processing = False
        session.status = f"Error: {error_msg}"
        logs_console.log(f"Analysis failed: {error_msg}", level='ERROR')
        
        # Notify UI about error
        if session.on_error:
            if editor:
                editor.after(0, lambda: session.on_error(error_msg))
            else:
                session.on_error(error_msg)
    
    def _notify_status(self, session: ProofreadingSession, status: str, editor):
        """Notify UI about status change (thread-safe)."""
        session.status = status
        
        # Thread-safe UI updates
        if session.on_status_change:
            if editor:
                editor.after(0, lambda: session.on_status_change(status))
            else:
                session.on_status_change(status)
        
        if session.on_progress_change:
            if editor:
                editor.after(0, lambda: session.on_progress_change(status))
            else:
                session.on_progress_change(status)