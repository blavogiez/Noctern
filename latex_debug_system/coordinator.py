"""Orchestrate debug functionality with SOLID design principles."""

import threading
from typing import Optional, Callable
from utils import logs_console
from latex_debug_system.core import DebugContext, AnalysisResult
from latex_debug_system.error_parser import LaTeXErrorParser
from latex_debug_system.llm_analyzer import LLMAnalyzer
from latex_debug_system.diff_service import CachedDiffGenerator
from latex_debug_system.debug_ui import TabbedDebugUI


class DebugCoordinator:
    """Coordinate all debug functionality components."""
    
    def __init__(self, debug_ui: TabbedDebugUI, on_goto_line: Optional[Callable[[int], None]] = None):
        """Initialize debug coordinator with required components."""
        self.debug_ui = debug_ui
        self.on_goto_line = on_goto_line
        
        # Setup core debug system components
        self.error_parser = LaTeXErrorParser()
        self.llm_analyzer = LLMAnalyzer()
        from latex_debug_system.legacy_fix_applicator import LegacyFixApplicator
        self.fix_applicator = LegacyFixApplicator()
        self.diff_generator = CachedDiffGenerator()
        
        # Current state
        self.current_context: Optional[DebugContext] = None
        self.current_analysis: Optional[AnalysisResult] = None
        self._is_analyzing: bool = False
        
        # Configuration
        self.auto_fix_threshold = 0.9
        
        # Connect UI callbacks
        self._connect_ui_callbacks()
        
        logs_console.log("Debug coordinator initialized", level='DEBUG')
    
    def _connect_ui_callbacks(self):
        """Connect UI callbacks to coordinator methods."""
        self.debug_ui.on_request_analysis = self._handle_analysis_request
        self.debug_ui.on_apply_correction = self._handle_correction_application
        self.debug_ui.on_compare_versions = self._handle_version_comparison
    
    def handle_compilation_result(self, success: bool, log_content: str, file_path: str, current_content: str):
        """Handle compilation result and update UI accordingly."""
        logs_console.log(f"Handling compilation result - Success: {success}", level='INFO')
        
        # Create context
        context = DebugContext(
            current_file_path=file_path,
            current_content=current_content,
            log_content=log_content
        )
        
        self.current_context = context
        
        if success:
            # Clear errors for successful compilation
            self.debug_ui.clear_display()
            logs_console.log("Compilation successful - cleared error display", level='INFO')
        else:
            # Update UI with errors
            self.debug_ui.update_compilation_errors(log_content, file_path, current_content)
            
            
            logs_console.log("LLM analysis available via 'Analyze with AI' button", level='INFO')
    
    def set_current_document(self, file_path: str, content: str):
        """Set the current document information."""
        self.current_context = DebugContext(
            current_file_path=file_path,
            current_content=content
        )
        
        logs_console.log(f"Updated current document: {file_path}", level='DEBUG')
    
    def store_successful_compilation(self, file_path: str, content: str):
        """Store successful compilation (handled by existing cache system)."""
        logs_console.log(f"Successful compilation stored for {file_path}", level='DEBUG')
    
    def get_error_panel(self):
        """Get the debug UI widget."""
        return self.debug_ui
    
    def auto_fix_if_possible(self, context: DebugContext) -> bool:
        """Attempt automatic fixing - disabled after quickfix removal."""
        logs_console.log("Auto-fix disabled - quickfix system removed", level='INFO')
        return False
    
    
    def _handle_analysis_request(self):
        """Handle user request for AI analysis asynchronously (non-blocking)."""
        if self._is_analyzing:
            logs_console.log("Analysis already in progress; ignoring duplicate request", level='INFO')
            return

        if not self.current_context:
            logs_console.log("No context available for analysis", level='WARNING')
            # Inform UI so it can re-enable controls gracefully
            try:
                self.debug_ui.display_analysis_message("No document context available for analysis.")
            except Exception:
                pass
            return

        # Prepare context with diff before starting the worker
        try:
            has_previous, diff_content, last_content = self.diff_generator.analyze_current_vs_last_successful(
                self.current_context.current_file_path,
                self.current_context.current_content
            )
            if has_previous and diff_content:
                self.current_context.diff_content = diff_content
                self.current_context.last_successful_content = last_content
        except Exception as e:
            logs_console.log(f"Diff preparation failed: {e}", level='WARNING')

        # Start worker thread
        self._is_analyzing = True
        threading.Thread(target=self._run_analysis_worker, daemon=True).start()

    def _run_analysis_worker(self):
        """Background worker to run AI analysis and update UI safely."""
        try:
            # Validate if analysis is needed/possible
            if not self.current_context or not self.current_context.has_analyzable_content():
                reason = self.current_context.get_analysis_reason() if self.current_context else "No document context"
                logs_console.log(f"Analysis skipped: {reason}", level='INFO')
                try:
                    # Schedule UI update on main thread
                    self.debug_ui.after(0, lambda: self.debug_ui.display_analysis_message(reason, is_success=True))
                except Exception:
                    pass
                return

            # Log what we're analyzing
            analysis_reason = self.current_context.get_analysis_reason()
            logs_console.log(f"Starting AI analysis - {analysis_reason}", level='INFO')

            # Perform analysis (blocking in worker thread)
            analysis_result = self.llm_analyzer.analyze_errors(self.current_context)
            self.current_analysis = analysis_result

            # Display results on UI thread
            try:
                self.debug_ui.after(0, lambda r=analysis_result: self.debug_ui.display_analysis_result(r))
            except Exception:
                pass

            logs_console.log(f"Analysis completed with {analysis_result.confidence:.1%} confidence", level='SUCCESS')

        except Exception as e:
            logs_console.log(f"Error during AI analysis: {e}", level='ERROR')
            # Surface error to UI and restore button state on main thread
            try:
                self.debug_ui.after(0, lambda: self.debug_ui.display_analysis_message(f"Analysis error: {e}", is_success=False))
            except Exception:
                pass
        finally:
            self._is_analyzing = False
    
    def _handle_correction_application(self, corrected_code: str):
        """Handle application of LLM correction."""
        if self.current_context:
            success = self.fix_applicator.apply_corrected_code(corrected_code, self.current_context)
            if success:
                logs_console.log("LLM correction applied successfully", level='SUCCESS')
                
                # Update context with new content
                try:
                    from app import state
                    current_tab = state.get_current_tab()
                    if current_tab and hasattr(current_tab, 'editor'):
                        self.current_context.current_content = current_tab.editor.get("1.0", "end-1c")
                except:
                    pass
            else:
                logs_console.log("Failed to apply LLM correction", level='ERROR')
    
    
    def _handle_version_comparison(self):
        """Handle version comparison request."""
        if not self.current_context:
            logs_console.log("No context for version comparison", level='WARNING')
            return
        
        try:
            has_previous, diff_content, last_content = self.diff_generator.analyze_current_vs_last_successful(
                self.current_context.current_file_path,
                self.current_context.current_content
            )
            
            if has_previous and diff_content:
                # Get parent window for diff viewer
                try:
                    parent_window = self.debug_ui.winfo_toplevel()
                    self.diff_generator.display_diff(diff_content, parent_window)
                except:
                    self.diff_generator.display_diff(diff_content)
                
                logs_console.log("Version comparison displayed", level='SUCCESS')
            else:
                logs_console.log("No previous version available for comparison", level='INFO')
                
        except Exception as e:
            logs_console.log(f"Error during version comparison: {e}", level='ERROR')


def create_debug_system(parent_window, on_goto_line: Optional[Callable[[int], None]] = None):
    """Create the complete debug system with UI and coordinator.
    
    Returns:
        tuple: (coordinator, debug_ui_widget)
    """
    logs_console.log("Creating debug system", level='INFO')
    
    # Create debug UI
    debug_ui = TabbedDebugUI(parent_window, on_goto_line)
    
    # Create coordinator
    coordinator = DebugCoordinator(debug_ui, on_goto_line)
    
    logs_console.log("Debug system created successfully", level='SUCCESS')
    
    return coordinator, debug_ui
