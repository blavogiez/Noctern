"""
Ultimate Debug Coordinator - The pinnacle of SOLID LaTeX debugging.
Orchestrates all debug functionality: Analysis, Fixes, UI, and Workflow.
"""

from typing import Optional, Callable, List
from utils import debug_console
from debug_system.interfaces.analysis_engine import (
    IDebugWorkflowOrchestrator, IAnalysisEngine, IQuickFixProvider, 
    IFixApplicator, DebugContext, AnalysisResult, QuickFix
)
from debug_system.analysis.intelligent_engine import AnalysisEngineFactory
from debug_system.fixes.quick_fix_system import QuickFixSystemFactory
from debug_system.diff_service import DiffServiceFactory
from debug_system.ui.advanced_debug_panel import AdvancedDebugPanelFactory
from debug_system.ui.diff_viewer import DiffViewerFactory


class UltimateDebugCoordinator(IDebugWorkflowOrchestrator):
    """
    The ultimate debug coordinator that orchestrates the complete debug workflow.
    Follows SOLID principles and provides seamless integration of all components.
    """
    
    def __init__(self, debug_panel, on_goto_line: Optional[Callable[[int], None]] = None):
        self.debug_panel = debug_panel
        self.on_goto_line = on_goto_line
        
        # Initialize SOLID components
        self.analysis_engine = AnalysisEngineFactory.create_best_available_engine()
        self.quick_fix_provider = QuickFixSystemFactory.create_provider()
        self.fix_applicator = QuickFixSystemFactory.create_applicator()
        self.diff_service = DiffServiceFactory.create_with_existing_cache()
        self.diff_viewer = None  # Created on demand
        
        # Current state
        self.current_context: Optional[DebugContext] = None
        self.current_analysis: Optional[AnalysisResult] = None
        
        # Configuration
        self.auto_analysis_enabled = False  # Only analyze when user requests it
        self.auto_fix_threshold = 0.9
        
        # Connect UI callbacks
        self._connect_ui_callbacks()
        
        debug_console.log("Ultimate Debug Coordinator initialized", level='SUCCESS')
    
    def _connect_ui_callbacks(self):
        """Connect UI callbacks to coordinator methods."""
        if hasattr(self.debug_panel, 'on_request_analysis'):
            self.debug_panel.on_request_analysis = self._handle_analysis_request
        if hasattr(self.debug_panel, 'on_apply_correction'):
            self.debug_panel.on_apply_correction = self._handle_correction_application
        if hasattr(self.debug_panel, 'on_apply_quick_fix'):
            self.debug_panel.on_apply_quick_fix = self._handle_quick_fix_application
        if hasattr(self.debug_panel, 'on_compare_versions'):
            self.debug_panel.on_compare_versions = self._handle_version_comparison
    
    def handle_compilation_failure(self, context: DebugContext):
        """Handle compilation failure with complete analysis workflow."""
        debug_console.log("Handling compilation failure with ultimate workflow", level='INFO')
        
        self.current_context = context
        
        # Update UI with errors
        self.debug_panel.update_compilation_errors(
            context.log_content or "",
            context.current_file_path,
            context.current_content
        )
        
        # Generate quick fixes for immediate errors
        self._generate_quick_fixes_for_errors(context)
        
        # Note: Automatic LLM analysis disabled - only available via "Analyze with AI" button
        debug_console.log("LLM analysis available via 'Analyze with AI' button", level='INFO')
    
    def suggest_improvements(self, context: DebugContext):
        """Suggest improvements even for successful compilation."""
        debug_console.log("Suggesting improvements for successful compilation", level='INFO')
        
        self.current_context = context
        
        # Clear error display but keep panel active
        self.debug_panel.clear_display()
        
        # Note: Analysis only available on demand via button
        debug_console.log("Analysis available via 'Analyze with AI' button for improvements", level='INFO')
    
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
    
    def set_current_document(self, file_path: str, content: str):
        """Set the current document information."""
        self.current_context = DebugContext(
            current_file_path=file_path,
            current_content=content
        )
        
        if hasattr(self.debug_panel, 'current_file_path'):
            self.debug_panel.current_file_path = file_path
            self.debug_panel.current_content = content
        
        debug_console.log(f"Updated current document: {file_path}", level='DEBUG')
    
    def handle_compilation_result(self, success: bool, log_content: str, file_path: str, current_content: str):
        """Handle compilation result and orchestrate appropriate workflow."""
        context = DebugContext(
            current_file_path=file_path,
            current_content=current_content,
            log_content=log_content
        )
        
        if success:
            self.suggest_improvements(context)
        else:
            self.handle_compilation_failure(context)
    
    def store_successful_compilation(self, file_path: str, content: str):
        """Store successful compilation (handled by existing cache system)."""
        debug_console.log(f"Successful compilation stored for {file_path}", level='DEBUG')
    
    def get_error_panel(self):
        """Get the debug panel widget."""
        return self.debug_panel
    
    def _generate_quick_fixes_for_errors(self, context: DebugContext):
        """Generate quick fixes for all errors."""
        if not context.errors:
            return
        
        all_quick_fixes = []
        
        for error in context.errors:
            if self.quick_fix_provider.can_handle_error(error):
                fixes = self.quick_fix_provider.get_quick_fixes(error, context)
                all_quick_fixes.extend(fixes)
        
        if all_quick_fixes and hasattr(self.debug_panel, 'quickfix_tab'):
            self.debug_panel.quickfix_tab.display_quick_fixes(all_quick_fixes)
            debug_console.log(f"Generated {len(all_quick_fixes)} quick fixes", level='INFO')
    
    def _perform_intelligent_analysis(self, context: DebugContext):
        """Perform intelligent LLM analysis."""
        debug_console.log("Starting intelligent analysis", level='INFO')
        
        try:
            # Get diff for analysis if possible
            if hasattr(self, 'diff_service'):
                has_previous, diff_content, last_content = self.diff_service.analyze_current_vs_last_successful(
                    context.current_file_path,
                    context.current_content
                )
                
                if has_previous and diff_content:
                    context.diff_content = diff_content
                    context.last_successful_content = last_content
            
            # Perform analysis
            analysis_result = self.analysis_engine.analyze_errors(context)
            self.current_analysis = analysis_result
            
            # Display results
            if hasattr(self.debug_panel, 'display_analysis_result'):
                self.debug_panel.display_analysis_result(analysis_result)
            
            debug_console.log(f"Analysis completed with {analysis_result.confidence:.1%} confidence", level='SUCCESS')
            
        except Exception as e:
            debug_console.log(f"Error during intelligent analysis: {e}", level='ERROR')
    
    def _handle_analysis_request(self):
        """Handle user request for analysis."""
        if self.current_context:
            self._perform_intelligent_analysis(self.current_context)
        else:
            debug_console.log("No context available for analysis", level='WARNING')
    
    def _handle_correction_application(self, corrected_code: str):
        """Handle application of LLM correction."""
        if self.current_context:
            success = self.fix_applicator.apply_corrected_code(corrected_code, self.current_context)
            if success:
                debug_console.log("LLM correction applied successfully", level='SUCCESS')
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
            has_previous, diff_content, last_content = self.diff_service.analyze_current_vs_last_successful(
                self.current_context.current_file_path,
                self.current_context.current_content
            )
            
            if has_previous and diff_content:
                # Create diff viewer on demand
                if not self.diff_viewer:
                    try:
                        # Get parent window
                        parent_window = self.debug_panel.winfo_toplevel()
                        self.diff_viewer = DiffViewerFactory.create_simple_viewer(parent_window)
                    except:
                        self.diff_viewer = DiffViewerFactory.create_simple_viewer()
                
                self.diff_viewer.show_diff(diff_content, "Compare with Last Successful Version")
                debug_console.log("Version comparison displayed", level='SUCCESS')
            else:
                debug_console.log("No previous version available for comparison", level='INFO')
                
        except Exception as e:
            debug_console.log(f"Error during version comparison: {e}", level='ERROR')


class UltimateDebugCoordinatorFactory:
    """Factory for creating the ultimate debug coordinator."""
    
    @staticmethod
    def create_ultimate_coordinator(parent_window, on_goto_line: Optional[Callable[[int], None]] = None):
        """
        Create the ultimate debug coordinator with advanced UI.
        
        Returns:
            tuple: (coordinator, debug_panel_widget)
        """
        debug_console.log("Creating ultimate debug coordinator", level='INFO')
        
        # Create advanced debug panel
        debug_panel = AdvancedDebugPanelFactory.create_panel(parent_window, on_goto_line)
        
        # Create ultimate coordinator
        coordinator = UltimateDebugCoordinator(debug_panel, on_goto_line)
        
        debug_console.log("Ultimate debug coordinator created successfully", level='SUCCESS')
        
        return coordinator, debug_panel
    
    @staticmethod
    def create_with_simple_ui(parent_window, on_goto_line: Optional[Callable[[int], None]] = None):
        """Create coordinator with simple UI for backward compatibility."""
        from debug_system.texstudio_debug_coordinator import TeXstudioDebugCoordinatorFactory
        return TeXstudioDebugCoordinatorFactory.create_default_coordinator(parent_window, on_goto_line)