"""
TeXstudio-style Error Panel UI Component.
Displays compilation errors in a TeXstudio-like interface using SOLID principles.
"""

import tkinter as tk
import ttkbootstrap as ttk
from typing import List, Callable, Optional
from utils import debug_console
from debug_system.latex_error_parser import LaTeXError, ErrorParserFactory
from debug_system.diff_service import DiffServiceFactory


class IErrorDisplay:
    """Interface for error display components."""
    
    def display_errors(self, errors: List[LaTeXError]):
        """Display a list of errors."""
        raise NotImplementedError
    
    def clear_errors(self):
        """Clear all displayed errors."""
        raise NotImplementedError


class TeXstudioErrorListWidget(ttk.Treeview, IErrorDisplay):
    """TeXstudio-style error list widget."""
    
    def __init__(self, parent, on_error_click: Optional[Callable[[LaTeXError], None]] = None):
        super().__init__(parent, columns=('severity', 'line', 'message', 'error_index'), show='tree headings', height=8)
        
        self.on_error_click = on_error_click
        self.errors: List[LaTeXError] = []
        
        # Configure columns
        self.heading('#0', text='Type', anchor='w')
        self.heading('severity', text='Severity', anchor='w')
        self.heading('line', text='Line', anchor='w')
        self.heading('message', text='Message', anchor='w')
        # Hide error_index column - it's only for internal use
        self.heading('error_index', text='')
        
        self.column('#0', width=50, minwidth=40)
        self.column('severity', width=80, minwidth=60)
        self.column('line', width=60, minwidth=50)
        self.column('message', width=400, minwidth=300)
        self.column('error_index', width=0, minwidth=0, stretch=False)  # Hidden column
        
        # Configure tags for different error types
        self.tag_configure('error', foreground='#d32f2f')
        self.tag_configure('warning', foreground='#f57c00')
        self.tag_configure('info', foreground='#1976d2')
        
        # Bind events
        self.bind('<Double-1>', self._on_item_double_click)
        self.bind('<Return>', self._on_item_activate)
        
        debug_console.log("TeXstudio error list widget initialized", level='DEBUG')
    
    def display_errors(self, errors: List[LaTeXError]):
        """Display errors in TeXstudio style."""
        self.clear_errors()
        self.errors = errors
        
        debug_console.log(f"Displaying {len(errors)} errors in TeXstudio style", level='INFO')
        
        for i, error in enumerate(errors):
            # Error type icon
            icon = {'Error': '❌', 'Warning': '⚠️', 'Info': 'ℹ️'}.get(error.severity, '•')
            
            # Insert item
            item_id = self.insert('', 'end', 
                                text=icon,
                                values=(error.severity, 
                                       str(error.line_number) if error.line_number > 0 else '',
                                       error.message,
                                       str(i)),  # error_index in the values
                                tags=(error.severity.lower(),))
    
    def clear_errors(self):
        """Clear all errors from display."""
        for item in self.get_children():
            self.delete(item)
        self.errors.clear()
        debug_console.log("Cleared error display", level='DEBUG')
    
    def _on_item_double_click(self, event):
        """Handle double-click on error item."""
        self._activate_selected_error()
    
    def _on_item_activate(self, event):
        """Handle Enter key on error item."""
        self._activate_selected_error()
    
    def _activate_selected_error(self):
        """Activate the selected error (navigate to line)."""
        selection = self.selection()
        if not selection or not self.on_error_click:
            return
        
        try:
            item = selection[0]
            error_index = int(self.set(item, 'error_index'))
            if 0 <= error_index < len(self.errors):
                error = self.errors[error_index]
                self.on_error_click(error)
                debug_console.log(f"Navigating to error at line {error.line_number}", level='INFO')
        except (ValueError, IndexError) as e:
            debug_console.log(f"Error activating error item: {e}", level='WARNING')


class TeXstudioErrorPanel(ttk.Frame):
    """
    Main TeXstudio-style error panel combining error display and diff functionality.
    Follows Single Responsibility and Dependency Inversion principles.
    """
    
    def __init__(self, parent, on_goto_line: Optional[Callable[[int], None]] = None):
        super().__init__(parent)
        
        self.on_goto_line = on_goto_line
        self.current_file_path: Optional[str] = None
        self.current_content: Optional[str] = None
        
        # Initialize services
        self.error_parser = ErrorParserFactory.create_texstudio_parser()
        self.diff_service = DiffServiceFactory.create_with_existing_cache()
        
        self._setup_ui()
        debug_console.log("TeXstudio error panel initialized", level='DEBUG')
    
    def _setup_ui(self):
        """Setup the UI components."""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=5, pady=2)
        
        title_label = ttk.Label(header_frame, text="Debug", font=('Arial', 10, 'bold'))
        title_label.pack(side='left')
        
        # Compare button
        self.compare_btn = ttk.Button(
            header_frame, 
            text="Compare with last version",
            command=self._compare_with_last_version,
            style='Accent.TButton'
        )
        self.compare_btn.pack(side='right')
        
        # Separator
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=2)
        
        # Error display area
        error_frame = ttk.Frame(self)
        error_frame.pack(fill='both', expand=True, padx=5, pady=2)
        
        # Error list with scrollbar
        list_frame = ttk.Frame(error_frame)
        list_frame.pack(fill='both', expand=True)
        
        self.error_list = TeXstudioErrorListWidget(
            list_frame,
            on_error_click=self._on_error_selected
        )
        self.error_list.pack(side='left', fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.error_list.yview)
        scrollbar.pack(side='right', fill='y')
        self.error_list.configure(yscrollcommand=scrollbar.set)
        
        # Status label
        self.status_label = ttk.Label(self, text="Ready", foreground='#666')
        self.status_label.pack(side='bottom', fill='x', padx=5, pady=2)
    
    def update_compilation_errors(self, log_content: str, file_path: str = None, current_content: str = None):
        """
        Update panel with compilation errors from log content.
        
        Args:
            log_content: LaTeX compilation log content
            file_path: Path to the current file
            current_content: Current file content
        """
        self.current_file_path = file_path
        self.current_content = current_content
        
        debug_console.log(f"Updating compilation errors for {file_path or 'unnamed'}", level='INFO')
        
        try:
            # Parse errors from log
            errors = self.error_parser.parse_log_content(log_content, file_path)
            
            # Display errors
            self.error_list.display_errors(errors)
            
            # Update status
            if errors:
                error_count = len([e for e in errors if e.severity == 'Error'])
                warning_count = len([e for e in errors if e.severity == 'Warning'])
                status_text = f"{error_count} errors, {warning_count} warnings"
                self.status_label.configure(text=status_text, foreground='#d32f2f' if error_count > 0 else '#f57c00')
            else:
                self.status_label.configure(text="No errors found", foreground='#2e7d32')
                
        except Exception as e:
            debug_console.log(f"Error updating compilation errors: {e}", level='ERROR')
            self.status_label.configure(text="Error parsing log", foreground='#d32f2f')
    
    def _compare_with_last_version(self):
        """Compare current version with last successful compilation."""
        if not self.current_file_path or not self.current_content:
            debug_console.log("No current file or content for comparison", level='WARNING')
            self.status_label.configure(text="No file to compare", foreground='#f57c00')
            return
        
        try:
            debug_console.log("Starting comparison with last successful version", level='INFO')
            self.status_label.configure(text="Comparing...", foreground='#1976d2')
            
            # Analyze diff using existing mechanism
            has_previous, diff_content, last_content = self.diff_service.analyze_current_vs_last_successful(
                self.current_file_path, 
                self.current_content
            )
            
            if not has_previous:
                self.status_label.configure(text="No previous version found", foreground='#f57c00')
                return
            
            if not diff_content:
                self.status_label.configure(text="No differences found", foreground='#2e7d32')
                return
            
            # Display diff in viewer window
            self.diff_service.trigger_diff_display(diff_content, self.winfo_toplevel())
            self.status_label.configure(text="Diff displayed", foreground='#2e7d32')
            
        except Exception as e:
            debug_console.log(f"Error during comparison: {e}", level='ERROR')
            self.status_label.configure(text="Comparison failed", foreground='#d32f2f')
    
    def _on_error_selected(self, error: LaTeXError):
        """Handle error selection for navigation."""
        if not self.on_goto_line:
            debug_console.log("No goto_line callback available", level='WARNING')
            return
            
        try:
            if error.line_number > 0:
                # Navigate to specific line
                self.on_goto_line(error.line_number)
                debug_console.log(f"Navigated to line {error.line_number}", level='INFO')
            elif error.line_number == -1:
                # For "end of file" errors, navigate to the last line
                # We need to get current tab to find the last line
                from app import state
                current_tab = state.get_current_tab()
                if current_tab and hasattr(current_tab, 'editor'):
                    # Get total number of lines
                    last_line = int(current_tab.editor.index('end-1c').split('.')[0])
                    self.on_goto_line(last_line)
                    debug_console.log(f"Navigated to end of file (line {last_line}) for end-of-file error", level='INFO')
                else:
                    debug_console.log("Cannot navigate to end of file: no active editor", level='WARNING')
            else:
                debug_console.log(f"Cannot navigate: invalid line number {error.line_number}", level='WARNING')
        except Exception as e:
            debug_console.log(f"Error navigating to line {error.line_number}: {e}", level='WARNING')
    
    def clear_display(self):
        """Clear the error display."""
        self.error_list.clear_errors()
        self.status_label.configure(text="Ready", foreground='#666')
        debug_console.log("Error panel display cleared", level='DEBUG')


class TeXstudioErrorPanelFactory:
    """Factory for creating TeXstudio error panel instances."""
    
    @staticmethod
    def create_panel(parent, on_goto_line: Optional[Callable[[int], None]] = None) -> TeXstudioErrorPanel:
        """Create a TeXstudio-style error panel."""
        return TeXstudioErrorPanel(parent, on_goto_line)