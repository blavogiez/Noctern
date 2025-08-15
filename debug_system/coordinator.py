"""
Main debug coordinator that orchestrates all debug functionality.
Follows SOLID principles with clean separation of concerns.
"""

from typing import Optional, Callable
from utils import debug_console
from debug_system.core import DebugContext, AnalysisResult, QuickFix
from debug_system.error_parser import LaTeXErrorParser
from debug_system.llm_analyzer import LLMAnalyzer
from debug_system.quick_fixes import LaTeXQuickFixProvider, EditorFixApplicator
from debug_system.diff_service import CachedDiffGenerator
from debug_system.debug_ui import TabbedDebugUI


class DebugCoordinator:
    """Main coordinator that orchestrates all debug functionality."""
    
    def __init__(self, debug_ui: TabbedDebugUI, on_goto_line: Optional[Callable[[int], None]] = None):
        """Initialize the debug coordinator with all components."""
        self.debug_ui = debug_ui
        self.on_goto_line = on_goto_line
        
        # Initialize core components
        self.error_parser = LaTeXErrorParser()
        self.llm_analyzer = LLMAnalyzer()
        self.quick_fix_provider = LaTeXQuickFixProvider()
        self.fix_applicator = EditorFixApplicator()
        self.diff_generator = CachedDiffGenerator()
        
        # Current state
        self.current_context: Optional[DebugContext] = None
        self.current_analysis: Optional[AnalysisResult] = None
        
        # Configuration
        self.auto_fix_threshold = 0.9
        
        # Connect UI callbacks
        self._connect_ui_callbacks()
        
        debug_console.log("Debug coordinator initialized", level='DEBUG')
    
    def _connect_ui_callbacks(self):
        """Connect UI callbacks to coordinator methods."""
        self.debug_ui.on_request_analysis = self._handle_analysis_request
        self.debug_ui.on_apply_correction = self._handle_correction_application
        self.debug_ui.on_apply_quick_fix = self._handle_quick_fix_application
        self.debug_ui.on_compare_versions = self._handle_version_comparison
    
    def handle_compilation_result(self, success: bool, log_content: str, file_path: str, current_content: str):
        """Handle compilation result and update UI accordingly."""
        debug_console.log(f"Handling compilation result - Success: {success}", level='INFO')
        
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
            debug_console.log("Compilation successful - cleared error display", level='INFO')
        else:
            # Update UI with errors
            self.debug_ui.update_compilation_errors(log_content, file_path, current_content)
            
            # Generate quick fixes for immediate errors
            self._generate_quick_fixes_for_errors(context)
            
            debug_console.log("LLM analysis available via 'Analyze with AI' button", level='INFO')
    
    def set_current_document(self, file_path: str, content: str):
        """Set the current document information."""
        self.current_context = DebugContext(
            current_file_path=file_path,
            current_content=content
        )
        
        debug_console.log(f"Updated current document: {file_path}", level='DEBUG')
    
    def store_successful_compilation(self, file_path: str, content: str):
        """Store successful compilation (handled by existing cache system)."""
        debug_console.log(f"Successful compilation stored for {file_path}", level='DEBUG')
    
    def get_error_panel(self):
        """Get the debug UI widget."""
        return self.debug_ui
    
    def auto_fix_if_possible(self, context: DebugContext) -> bool:
        """Attempt automatic fixing if confidence is high enough."""
        if not context.errors:
            return False
        
        debug_console.log("Attempting automatic fixes", level='INFO')
        
        fixes_applied = 0
        
        for error in context.errors:
            if self.quick_fix_provider.can_handle_error(error):
                quick_fixes = self.quick_fix_provider.get_quick_fixes(error, context)
                
                for fix in quick_fixes:
                    if fix.auto_applicable and fix.confidence >= self.auto_fix_threshold:
                        if self.fix_applicator.apply_quick_fix(fix, context):
                            fixes_applied += 1
                            debug_console.log(f"Auto-applied fix: {fix.title}", level='SUCCESS')
        
        if fixes_applied > 0:
            debug_console.log(f"Successfully applied {fixes_applied} automatic fixes", level='SUCCESS')
            return True
        
        return False
    
    def _generate_quick_fixes_for_errors(self, context: DebugContext):
        """Generate quick fixes for all errors."""
        if not context.errors:
            return
        
        all_quick_fixes = []
        
        for error in context.errors:
            if self.quick_fix_provider.can_handle_error(error):
                fixes = self.quick_fix_provider.get_quick_fixes(error, context)
                all_quick_fixes.extend(fixes)
        
        if all_quick_fixes:
            self.debug_ui.quickfix_tab.display_quick_fixes(all_quick_fixes)
            debug_console.log(f"Generated {len(all_quick_fixes)} quick fixes", level='INFO')
    
    def _handle_analysis_request(self):
        """Handle user request for AI analysis."""
        if not self.current_context:
            debug_console.log("No context available for analysis", level='WARNING')
            return
        
        debug_console.log("Starting AI analysis", level='INFO')
        
        try:
            # Get diff for analysis if possible
            has_previous, diff_content, last_content = self.diff_generator.analyze_current_vs_last_successful(
                self.current_context.current_file_path,
                self.current_context.current_content
            )
            
            if has_previous and diff_content:
                self.current_context.diff_content = diff_content
                self.current_context.last_successful_content = last_content
            
            # Perform analysis
            analysis_result = self.llm_analyzer.analyze_errors(self.current_context)
            self.current_analysis = analysis_result
            
            # Display results
            self.debug_ui.display_analysis_result(analysis_result)
            
            debug_console.log(f"Analysis completed with {analysis_result.confidence:.1%} confidence", level='SUCCESS')
            
        except Exception as e:
            debug_console.log(f"Error during AI analysis: {e}", level='ERROR')
    
    def _handle_correction_application(self, corrected_code: str):
        """Handle application of LLM correction."""
        if self.current_context:
            success = self.fix_applicator.apply_corrected_code(corrected_code, self.current_context)
            if success:
                debug_console.log("LLM correction applied successfully", level='SUCCESS')
                
                # Update context with new content
                try:
                    from app import state
                    current_tab = state.get_current_tab()
                    if current_tab and hasattr(current_tab, 'editor'):
                        self.current_context.current_content = current_tab.editor.get("1.0", "end-1c")
                except:
                    pass
            else:
                debug_console.log("Failed to apply LLM correction", level='ERROR')
    
    def _handle_quick_fix_application(self, fix: QuickFix):
        """Handle application of quick fix."""
        if self.current_context:
            success = self.fix_applicator.apply_quick_fix(fix, self.current_context)
            if success:
                debug_console.log(f"Quick fix '{fix.title}' applied successfully", level='SUCCESS')
                
                # Update context with new content
                try:
                    from app import state
                    current_tab = state.get_current_tab()
                    if current_tab and hasattr(current_tab, 'editor'):
                        self.current_context.current_content = current_tab.editor.get("1.0", "end-1c")
                except:
                    pass
            else:
                debug_console.log(f"Failed to apply quick fix '{fix.title}'", level='ERROR')
    
    def _handle_version_comparison(self):
        """Handle version comparison request."""
        if not self.current_context:
            debug_console.log("No context for version comparison", level='WARNING')
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
                
                debug_console.log("Version comparison displayed", level='SUCCESS')
            else:
                debug_console.log("No previous version available for comparison", level='INFO')
                
        except Exception as e:
            debug_console.log(f"Error during version comparison: {e}", level='ERROR')


def create_debug_system(parent_window, on_goto_line: Optional[Callable[[int], None]] = None):
    """Create the complete debug system with UI and coordinator.
    
    Returns:
        tuple: (coordinator, debug_ui_widget)
    """
    debug_console.log("Creating debug system", level='INFO')
    
    # Create debug UI
    debug_ui = TabbedDebugUI(parent_window, on_goto_line)
    
    # Create coordinator
    coordinator = DebugCoordinator(debug_ui, on_goto_line)
    
    debug_console.log("Debug system created successfully", level='SUCCESS')
    
    return coordinator, debug_ui