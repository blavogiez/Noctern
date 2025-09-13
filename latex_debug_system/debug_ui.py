"""
Debug user interface with tabbed layout for errors, analysis, and quick fixes.
Provides a clean interface for all debug functionality.
"""

import tkinter as tk
import ttkbootstrap as ttk
from typing import List, Optional, Callable
from utils import logs_console
from latex_debug_system.core import DebugUI, LaTeXError, AnalysisResult, DebugContext


class UltraFineTreeview(ttk.Treeview):
    """Base class for ultra-fine treeviews with theme resistance."""
    
    def __init__(self, parent, **kwargs):
        """Initialize ultra-fine treeview with performance-optimized theme monitoring."""
        super().__init__(parent, **kwargs)
        self._apply_theme_colors()
        self._setup_theme_monitoring()
    
    def _apply_theme_colors(self):
        """Apply theme colors to debug treeview."""
        widget_style = f"Debug{id(self)}.Treeview"
        style = ttk.Style()
        
        # Get colors from theme system to preserve exact debug look
        from app import state
        colors = {
            'bg': state.get_theme_setting('debug_bg', '#ffffff'),
            'fg': state.get_theme_setting('debug_fg', '#333333'),
            'heading_bg': state.get_theme_setting('debug_heading_bg', '#f5f5f5'),
            'heading_fg': state.get_theme_setting('debug_heading_fg', '#666666')
        }
        
        style.configure(widget_style,
                       rowheight=28,
                       font=('Segoe UI', 9),
                       background=colors['bg'],
                       foreground=colors['fg'],
                       fieldbackground=colors['bg'],
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none')
        
        style.configure(widget_style + ".Heading",
                       font=('Segoe UI', 9),
                       background=colors['heading_bg'],
                       foreground=colors['heading_fg'],
                       borderwidth=0,
                       relief='flat',
                       anchor='w')
        
        # Force override global Treeview.Heading to prevent bold
        style.map(widget_style + ".Heading", font=[("", ('Segoe UI', 9))])
        
        self.configure(style=widget_style)
        self._widget_style = widget_style
    
    def _setup_theme_monitoring(self):
        """Setup theme monitoring without polling."""
        # Only event-based, no polling
        self.bind_all('<<ThemeChanged>>', self._on_theme_change)
        
        # Listen for style changes on parent windows
        parent = self.winfo_toplevel()
        if parent:
            parent.bind('<<StyleChanged>>', self._on_theme_change, add='+')
            
    def _on_theme_change(self, event=None):
        """Handle theme change events."""
        try:
            self._apply_theme_colors()
        except:
            pass
            
    
    def _get_debug_colors(self, theme_name):
        """Get debug-specific colors for theme."""
        debug_colors = {
            'darkly': {
                'bg': '#2d2d2d', 'fg': '#ffffff',
                'heading_bg': '#3d3d3d', 'heading_fg': '#cccccc'
            },
            'superhero': {
                'bg': '#2b3e50', 'fg': '#ffffff', 
                'heading_bg': '#34495e', 'heading_fg': '#ecf0f1'
            },
            'solar': {
                'bg': '#002b36', 'fg': '#839496',
                'heading_bg': '#073642', 'heading_fg': '#93a1a1'
            },
            'cyborg': {
                'bg': '#222222', 'fg': '#ffffff',
                'heading_bg': '#2a2a2a', 'heading_fg': '#cccccc'
            },
            'vapor': {
                'bg': '#190a26', 'fg': '#f8f8ff',
                'heading_bg': '#2a1b3d', 'heading_fg': '#e6e6fa'
            }
        }
        
        # Light themes
        light_default = {
            'bg': '#ffffff', 'fg': '#333333',
            'heading_bg': '#f5f5f5', 'heading_fg': '#666666'
        }
        
        return debug_colors.get(theme_name, light_default)
    
    def update_theme_colors(self):
        """Update colors for current theme."""
        self._apply_theme_colors()
        # Also update any existing child widgets
        for child in self.winfo_children():
            if hasattr(child, 'update_theme_colors'):
                child.update_theme_colors()


class ErrorListWidget(UltraFineTreeview):
    """Widget for displaying LaTeX errors in a list format."""
    
    def __init__(self, parent, on_error_click: Optional[Callable[[LaTeXError], None]] = None):
        """Initialize error list widget with theme colors."""
        super().__init__(parent, columns=('severity', 'line', 'message', 'error_index'), 
                        show='tree headings', height=6)
        
        self.on_error_click = on_error_click
        self.errors: List[LaTeXError] = []
        
        # Configure columns with compact headers
        self.heading('#0', text='Type', anchor='w')
        self.heading('severity', text='Level', anchor='w')
        self.heading('line', text='Line', anchor='w')
        self.heading('message', text='Message', anchor='w')
        self.heading('error_index', text='')  # Hidden column
        
        self.column('#0', width=35, minwidth=30)
        self.column('severity', width=60, minwidth=50)
        self.column('line', width=45, minwidth=40)
        self.column('message', width=500, minwidth=350, stretch=True)
        self.column('error_index', width=0, minwidth=0, stretch=False)  # Hidden
        
        # Configure tags with theme colors
        self._update_tag_colors()
        
        # Bind events
        self.bind('<Double-1>', self._on_item_double_click)
        self.bind('<Return>', self._on_item_activate)
        
        logs_console.log("Error list widget initialized", level='DEBUG')
    
    def update_theme_colors(self):
        """Update colors for current theme."""
        super().update_theme_colors()
        self._update_tag_colors()
    
    def _update_tag_colors(self):
        """Update tag colors for current theme."""
        from app import state
        bg_color = state.get_theme_setting('debug_bg', '#ffffff')
        theme_name = state.current_theme if hasattr(state, 'current_theme') else 'litera'
        
        # Dark themes
        if theme_name in ['darkly', 'superhero', 'solar', 'cyborg', 'vapor']:
            error_color = '#ff6b6b'
            warning_color = '#ffa726' 
            info_color = '#64b5f6'
        else:
            error_color = '#c62828'
            warning_color = '#ef6c00'
            info_color = '#1565c0'
            
        self.tag_configure('error', foreground=error_color, background=bg_color)
        self.tag_configure('warning', foreground=warning_color, background=bg_color)
        self.tag_configure('info', foreground=info_color, background=bg_color)
    
    def display_errors(self, errors: List[LaTeXError]):
        """Display errors in the list."""
        self.clear_errors()
        self.errors = errors
        
        logs_console.log(f"Displaying {len(errors)} errors", level='INFO')
        
        for i, error in enumerate(errors):
            # Use simple letter indicators for error types
            icon = {'Error': 'E', 'Warning': 'W', 'Info': 'I'}.get(error.severity, '•')
            
            # Format line number display
            line_display = (str(error.line_number) if error.line_number > 0 
                          else 'EOF' if error.line_number == -1 else '')
            
            # Insert error item with compact formatting
            self.insert('', 'end', 
                       text=icon,
                       values=(error.severity, line_display, error.message, str(i)),
                       tags=(error.severity.lower(),))
        
        # Update colors after adding items
        self._update_tag_colors()
    
    def clear_errors(self):
        """Clear all errors from display."""
        for item in self.get_children():
            self.delete(item)
        self.errors.clear()
        logs_console.log("Cleared error display", level='DEBUG')
    
    def _on_item_double_click(self, event):
        """Handle double-click on error item."""
        self._activate_selected_error()
    
    def _on_item_activate(self, event):
        """Handle Enter key on error item."""
        self._activate_selected_error()
    
    def _activate_selected_error(self):
        """Activate the selected error for navigation."""
        selection = self.selection()
        if not selection or not self.on_error_click:
            return
        
        try:
            item = selection[0]
            error_index = int(self.item(item)['values'][3])  # error_index is 4th value
            if 0 <= error_index < len(self.errors):
                error = self.errors[error_index]
                self.on_error_click(error)
                logs_console.log(f"Navigating to error at line {error.line_number}", level='INFO')
        except (ValueError, IndexError) as e:
            logs_console.log(f"Error activating error item: {e}", level='WARNING')


class AnalysisTab(ttk.Frame):
    """Tab widget for displaying AI analysis results."""
    
    def __init__(self, parent, on_apply_correction: Optional[Callable[[str], None]] = None):
        """Initialize the analysis tab."""
        super().__init__(parent)
        self.on_apply_correction = on_apply_correction
        self.current_result: Optional[AnalysisResult] = None
        self._setup_ui()
        logs_console.log("Analysis tab initialized", level='DEBUG')
    
    def _setup_ui(self):
        """Setup the analysis tab UI."""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        self.analyze_btn = ttk.Button(
            header_frame,
            text="Analyze",
            command=self._request_analysis
        )
        self.analyze_btn.pack(side='left')
        
        self.status_label = ttk.Label(header_frame, text="Ready", font=('Segoe UI', 9), foreground='#666')
        self.status_label.pack(side='left', padx=(8, 0))
        
        # Main content area
        content_frame = ttk.Frame(self)
        content_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Explanation area
        exp_frame = ttk.LabelFrame(content_frame, text="AI Explanation", padding=10)
        exp_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        self.explanation_text = tk.Text(
            exp_frame,
            wrap='word',
            height=6,
            font=('Segoe UI', 9),
            bg='#f8f8f8',
            relief='flat',
            state='disabled'
        )
        
        exp_scrollbar = ttk.Scrollbar(exp_frame, orient='vertical', command=self.explanation_text.yview)
        self.explanation_text.configure(yscrollcommand=exp_scrollbar.set)
        
        exp_scrollbar.pack(side='right', fill='y')
        self.explanation_text.pack(side='left', fill='both', expand=True)
        
        # Correction area
        self.correction_frame = ttk.LabelFrame(content_frame, text="Suggested Correction", padding=10)
        
        self.correction_text = tk.Text(
            self.correction_frame,
            wrap='none',
            height=4,
            font=('Segoe UI', 9),
            bg='#f0f8ff',
            relief='flat',
            state='disabled'
        )
        
        corr_v_scrollbar = ttk.Scrollbar(self.correction_frame, orient='vertical', command=self.correction_text.yview)
        corr_h_scrollbar = ttk.Scrollbar(self.correction_frame, orient='horizontal', command=self.correction_text.xview)
        
        self.correction_text.configure(
            yscrollcommand=corr_v_scrollbar.set,
            xscrollcommand=corr_h_scrollbar.set
        )
        
        corr_v_scrollbar.pack(side='right', fill='y')
        corr_h_scrollbar.pack(side='bottom', fill='x')
        self.correction_text.pack(side='left', fill='both', expand=True)
        
        # Apply button with unified styling
        self.apply_btn = ttk.Button(
            self.correction_frame,
            text="Apply",
            command=self._apply_correction,
            state='disabled'
        )
        self.apply_btn.pack(pady=3)
    
    def present_analysis(self, result: AnalysisResult):
        """Present analysis results to the user."""
        self.current_result = result
        
        # Update explanation
        self.explanation_text.configure(state='normal')
        self.explanation_text.delete('1.0', 'end')
        self.explanation_text.insert('1.0', result.explanation)
        self.explanation_text.configure(state='disabled')
        
        # Update correction if available
        if result.corrected_code:
            self.correction_frame.pack(fill='both', expand=True, pady=(5, 0))
            
            self.correction_text.configure(state='normal')
            self.correction_text.delete('1.0', 'end')
            self.correction_text.insert('1.0', result.corrected_code)
            self.correction_text.configure(state='disabled')
            
            self.apply_btn.configure(state='normal')
        else:
            self.correction_frame.pack_forget()
        
        # Update status
        confidence_pct = int(result.confidence * 100)
        self.status_label.configure(
            text=f"Analysis complete (confidence: {confidence_pct}%)",
            foreground='#2e7d32' if result.confidence > 0.7 else '#f57c00'
        )
        
        # Re-enable the analyze button
        self.analyze_btn.configure(state='normal')
        
        logs_console.log(f"Analysis presented with {confidence_pct}% confidence", level='INFO')
    
    def _request_analysis(self):
        """Request analysis from the debug coordinator."""
        self.status_label.configure(text="Requesting analysis...", foreground='#1976d2')
        self.analyze_btn.configure(state='disabled')
        
        # Find parent debug panel and call its analysis callback
        parent_panel = self.master
        while parent_panel and not hasattr(parent_panel, 'on_request_analysis'):
            parent_panel = parent_panel.master
        
        if parent_panel and hasattr(parent_panel, 'on_request_analysis') and parent_panel.on_request_analysis:
            logs_console.log("Calling analysis request callback", level='INFO')
            parent_panel.on_request_analysis()
        else:
            logs_console.log("No analysis callback found", level='WARNING')
            self.status_label.configure(text="Analysis not available", foreground='#d32f2f')
            self.analyze_btn.configure(state='normal')
    
    def _apply_correction(self):
        """Apply the suggested correction."""
        if self.current_result and self.current_result.corrected_code and self.on_apply_correction:
            self.on_apply_correction(self.current_result.corrected_code)
            self.status_label.configure(text="Correction applied", foreground='#2e7d32')
        else:
            logs_console.log("No correction to apply", level='WARNING')




class TabbedDebugUI(ttk.Frame, DebugUI):
    """Main debug UI with tabbed interface for errors, analysis, and quick fixes."""
    
    def __init__(self, parent, on_goto_line: Optional[Callable[[int], None]] = None):
        """Initialize the tabbed debug UI."""
        super().__init__(parent)
        self.on_goto_line = on_goto_line
        self.current_context: Optional[DebugContext] = None
        
        # Callbacks that will be set by coordinator
        self.on_request_analysis: Optional[Callable[[], None]] = None
        self.on_apply_correction: Optional[Callable[[str], None]] = None
        self.on_compare_versions: Optional[Callable[[], None]] = None
        
        self._setup_ui()
        logs_console.log("Tabbed debug UI initialized", level='DEBUG')
    
    def _setup_ui(self):
        """Setup ultra-fine tabbed UI."""
        # Ultra-compact header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=5, pady=(2, 4))
        
        # Fine title consistent with app style
        title_label = ttk.Label(header_frame, text="Debug Center", font=('Segoe UI', 9))
        title_label.pack(side='left', padx=3)
        
        # Minimal compare button with better positioning
        self.compare_btn = ttk.Button(
            header_frame,
            text="Compare",
            command=self._compare_versions,
            width=9
        )
        self.compare_btn.pack(side='right', padx=(8, 2))
        
        # Ultra-fine notebook with minimal padding
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=3, pady=(0, 2))
        
        # Apply fine styling to notebook
        self._apply_notebook_fine_styling()
        
        # Errors tab
        self.errors_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.errors_frame, text='Errors')
        
        self.error_list = ErrorListWidget(
            self.errors_frame,
            on_error_click=self._on_error_selected
        )
        self.error_list.pack(fill='both', expand=True, padx=3, pady=3)
        
        # Analysis tab
        self.analysis_tab = AnalysisTab(
            self.notebook,
            on_apply_correction=self._on_apply_correction
        )
        self.notebook.add(self.analysis_tab, text='Analyze diff')
        
        
        # Ultra-fine status bar
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill='x', padx=5, pady=(2, 3))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", font=('Segoe UI', 9), foreground='#666')
        self.status_label.pack(side='left', padx=3)
    
    def _apply_notebook_fine_styling(self):
        """Apply fine styling to notebook tabs."""
        style = ttk.Style()
        
        # Create fine notebook style
        notebook_style = f"Fine{id(self)}.TNotebook"
        tab_style = f"Fine{id(self)}.TNotebook.Tab"
        
        # Ultra-fine notebook styling
        style.configure(notebook_style,
                       borderwidth=0,
                       relief='flat')
        
        # Ultra-fine tab styling with unified font
        style.configure(tab_style,
                       font=('Segoe UI', 9),
                       padding=[4, 2],
                       borderwidth=1)
        
        self.notebook.configure(style=notebook_style)
    
    def update_compilation_errors(self, log_content: str, file_path: str = None, current_content: str = None):
        """Update UI with compilation errors."""
        from latex_debug_system.error_parser import LaTeXErrorParser
        
        # Parse errors
        parser = LaTeXErrorParser()
        errors = parser.parse_log_content(log_content, file_path)
        
        # Display in errors tab
        self.error_list.display_errors(errors)
        
        # Update context
        self.current_context = DebugContext(
            current_file_path=file_path or "",
            current_content=current_content or "",
            log_content=log_content,
            errors=errors
        )
        
        # Update status
        error_count = len([e for e in errors if e.severity == 'Error'])
        warning_count = len([e for e in errors if e.severity == 'Warning'])
        
        if error_count > 0:
            self.status_label.configure(text=f"{error_count} errors, {warning_count} warnings", foreground='#d32f2f')
        elif warning_count > 0:
            self.status_label.configure(text=f"{warning_count} warnings", foreground='#f57c00')
        else:
            self.status_label.configure(text="No issues found", foreground='#2e7d32')
        
        logs_console.log(f"Updated debug UI with {len(errors)} total issues", level='INFO')
    
    def display_analysis_result(self, result: AnalysisResult):
        """Display AI analysis result."""
        if self.current_context:
            self.analysis_tab.present_analysis(result)
            
            
            # Switch to analysis tab
            self.notebook.select(self.analysis_tab)
    
    def display_analysis_message(self, message: str, is_success: bool = False):
        """Display simple analysis status message."""
        from latex_debug_system.core import AnalysisResult
        
        # Create a simple result with just the message
        result = AnalysisResult(
            explanation=message,
            confidence=1.0 if is_success else 0.0
        )
        
        # Display using existing analysis display
        self.analysis_tab.present_analysis(result)
        
        # Switch to analysis tab to show message
        self.notebook.select(self.analysis_tab)
    
    def clear_display(self):
        """Clear all displays."""
        self.error_list.clear_errors()
        self.status_label.configure(text="Ready", foreground='#666')
    
    def _on_error_selected(self, error: LaTeXError):
        """Handle error selection for navigation."""
        if self.on_goto_line and error.line_number > 0:
            try:
                self.on_goto_line(error.line_number)
            except Exception as e:
                logs_console.log(f"Error navigating to line: {e}", level='WARNING')
        elif error.line_number == -1:
            # End of file error - navigate to end
            try:
                from app import state
                current_tab = state.get_current_tab()
                if current_tab and hasattr(current_tab, 'editor'):
                    last_line = int(current_tab.editor.index('end-1c').split('.')[0])
                    if self.on_goto_line:
                        self.on_goto_line(last_line)
            except Exception as e:
                logs_console.log(f"Error navigating to end of file: {e}", level='WARNING')
    
    def _compare_versions(self):
        """Request version comparison."""
        if self.on_compare_versions:
            self.on_compare_versions()
    
    def _on_apply_correction(self, corrected_code: str):
        """Handle correction application."""
        if self.on_apply_correction:
            self.on_apply_correction(corrected_code)
    
