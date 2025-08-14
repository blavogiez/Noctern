"""
TeXstudio-style Debug Coordinator.
Integrates TeXstudio-style error display with existing compilation system.
"""

from typing import Optional, Callable
from utils import debug_console
from debug_system.ui.texstudio_error_panel import TeXstudioErrorPanelFactory


class ICompilationErrorHandler:
    """Interface for handling compilation errors."""
    
    def handle_compilation_result(self, success: bool, log_content: str, file_path: str, current_content: str):
        """Handle compilation result and display errors."""
        raise NotImplementedError


class TeXstudioDebugCoordinator(ICompilationErrorHandler):
    """
    Coordinator that manages TeXstudio-style error display and version comparison.
    Integrates with existing compiler.py diff mechanisms.
    """
    
    def __init__(self, error_panel, on_goto_line: Optional[Callable[[int], None]] = None):
        self.error_panel = error_panel
        self.on_goto_line = on_goto_line
        self.current_file_path: Optional[str] = None
        self.current_content: Optional[str] = None
        debug_console.log("TeXstudio debug coordinator initialized", level='DEBUG')
    
    def handle_compilation_result(self, success: bool, log_content: str, file_path: str, current_content: str):
        """
        Handle compilation result and update error display.
        
        Args:
            success: Whether compilation was successful
            log_content: LaTeX compilation log content
            file_path: Path to the compiled file
            current_content: Current file content
        """
        debug_console.log(f"Handling compilation result - Success: {success}", level='INFO')
        
        if success:
            self.error_panel.clear_display()
            debug_console.log("Compilation successful - cleared error display", level='INFO')
        else:
            # Display compilation errors in TeXstudio style
            self.error_panel.update_compilation_errors(log_content, file_path, current_content)
            debug_console.log("Updated error display with compilation errors", level='INFO')
    
    def store_successful_compilation(self, file_path: str, content: str):
        """
        Store successful compilation version.
        This integrates with the existing cache mechanism in compiler.py.
        """
        # The storage is handled by compiler.py's existing cache mechanism
        # This method exists for interface compatibility
        debug_console.log(f"Successful compilation stored for {file_path}", level='DEBUG')
    
    def set_current_document(self, file_path: str, content: str):
        """
        Set the current document information for the debug system.
        This method is called by the application when the active document changes.
        
        Args:
            file_path: Path to the current file
            content: Current file content
        """
        self.current_file_path = file_path
        self.current_content = content
        
        # Update the error panel with current document info
        if hasattr(self.error_panel, 'current_file_path'):
            self.error_panel.current_file_path = file_path
            self.error_panel.current_content = content
        
        debug_console.log(f"Debug system updated with document: {file_path}", level='DEBUG')
    
    def get_error_panel(self):
        """Get the error panel widget."""
        return self.error_panel


class TeXstudioDebugCoordinatorFactory:
    """Factory for creating TeXstudio debug coordinator instances."""
    
    @staticmethod
    def create_default_coordinator(parent_window, on_goto_line: Optional[Callable[[int], None]] = None):
        """
        Create a TeXstudio debug coordinator with default configuration.
        
        Args:
            parent_window: Parent widget for the error panel
            on_goto_line: Callback for line navigation
            
        Returns:
            tuple: (coordinator, error_panel_widget)
        """
        debug_console.log("Creating TeXstudio debug coordinator", level='DEBUG')
        
        # Create error panel
        error_panel = TeXstudioErrorPanelFactory.create_panel(parent_window, on_goto_line)
        
        # Create coordinator
        coordinator = TeXstudioDebugCoordinator(error_panel, on_goto_line)
        
        debug_console.log("TeXstudio debug coordinator created successfully", level='INFO')
        
        return coordinator, error_panel
    
    @staticmethod
    def create_with_custom_panel(error_panel, on_goto_line: Optional[Callable[[int], None]] = None):
        """Create coordinator with a custom error panel."""
        return TeXstudioDebugCoordinator(error_panel, on_goto_line)