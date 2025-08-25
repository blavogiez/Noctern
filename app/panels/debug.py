"""
Debug panel that integrates the original perfect debug system into the left sidebar.
Uses the complete debug_system module with TabbedDebugUI for maximum functionality.
"""

import tkinter as tk
from typing import Optional, Callable
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import debug_console


class DebugPanel(BasePanel):
    """
    Debug panel that wraps the original perfect debug system in the sidebar.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter,
                 diff_content: str,
                 log_content: str, 
                 active_editor_getter: Callable,
                 on_goto_line: Optional[Callable[[int], None]] = None,
                 on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        self.diff_content = diff_content
        self.log_content = log_content
        self.active_editor_getter = active_editor_getter
        self.on_goto_line = on_goto_line
        
        # Store debug system components
        self.debug_coordinator = None
        self.debug_ui = None
        
    def get_panel_title(self) -> str:
        return "LaTeX Debugger"
    
    def get_layout_style(self) -> PanelStyle:
        """Use simple layout to embed the original debug UI."""
        return PanelStyle.SIMPLE
        
    def create_content(self):
        """Create the debug panel by embedding the original perfect debug system."""
        try:
            # Import the original debug system
            from debug_system.coordinator import create_debug_system
            
            # Create the original debug system
            self.debug_coordinator, self.debug_ui = create_debug_system(
                self.main_container, 
                self.on_goto_line
            )
            
            # Pack the debug UI into our panel
            self.debug_ui.pack(fill="both", expand=True)
            
            # Parse the compilation results and initialize the debug system
            self._initialize_debug_context()
            
            debug_console.log("Original debug system integrated successfully", level='SUCCESS')
            
        except Exception as e:
            debug_console.log(f"Failed to initialize original debug system: {e}", level='ERROR')
            self._create_fallback_ui()
    
    def _initialize_debug_context(self):
        """Initialize the debug system with the compilation results."""
        try:
            # Get current file content from active editor
            current_content = ""
            editor = self.active_editor_getter() if self.active_editor_getter else None
            if editor:
                current_content = editor.get("1.0", "end-1c")
            
            # Initialize the debug system with compilation results
            if self.debug_coordinator:
                self.debug_coordinator.handle_compilation_result(
                    success=False,  # We're showing debug so there were errors
                    log_content=self.log_content,
                    file_path="current_file.tex",
                    current_content=current_content
                )
                
            # Update the debug UI with compilation errors
            if self.debug_ui:
                self.debug_ui.update_compilation_errors(
                    self.log_content,
                    "current_file.tex",
                    current_content
                )
                
        except Exception as e:
            debug_console.log(f"Error initializing debug context: {e}", level='ERROR')
    
    def _create_fallback_ui(self):
        """Create a simple fallback UI if the original system fails."""
        main_frame = self.main_container
        
        error_section = StandardComponents.create_section(main_frame, "Debug System Error")
        error_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        error_label = StandardComponents.create_info_label(
            error_section,
            "Failed to initialize the original debug system. Using fallback display.",
            "body"
        )
        error_label.pack(anchor="w", pady=(0, StandardComponents.PADDING))
        
        # Show diff if available
        if self.diff_content:
            diff_section = StandardComponents.create_section(main_frame, "Compilation Diff")
            diff_section.pack(fill="both", expand=True, pady=(0, StandardComponents.SECTION_SPACING))
            
            diff_text = StandardComponents.create_text_input(
                diff_section,
                "Diff content...",
                height=10
            )
            diff_text.pack(fill="both", expand=True)
            diff_text.delete("1.0", "end")
            diff_text.insert("1.0", self.diff_content)
            diff_text.config(state="disabled")
        
        # Show log if available
        if self.log_content:
            log_section = StandardComponents.create_section(main_frame, "Compilation Log")
            log_section.pack(fill="both", expand=True)
            
            log_text = StandardComponents.create_text_input(
                log_section,
                "Log content...",
                height=8
            )
            log_text.pack(fill="both", expand=True)
            log_text.delete("1.0", "end")
            log_text.insert("1.0", self.log_content[:2000] + ("..." if len(self.log_content) > 2000 else ""))
            log_text.config(state="disabled")
    
    def focus_main_widget(self):
        """Focus the debug UI."""
        if self.debug_ui:
            # The original debug system should handle focus internally
            try:
                if hasattr(self.debug_ui, 'focus_set'):
                    self.debug_ui.focus_set()
            except:
                pass