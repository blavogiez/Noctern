"""
Advanced Debug Panel with tabbed interface.
Integrates all debug functionality: Errors, Analysis, Quick Fixes, and Diff.
"""

import tkinter as tk
import ttkbootstrap as ttk
from typing import List, Optional, Callable
from utils import debug_console
from debug_system.interfaces.analysis_engine import (
    AnalysisResult, QuickFix, DebugContext, IAnalysisResultPresenter
)
from debug_system.latex_error_parser import LaTeXError
from debug_system.ui.texstudio_error_panel import TeXstudioErrorListWidget


class AnalysisTabWidget(ttk.Frame, IAnalysisResultPresenter):
    """Tab widget for displaying LLM analysis results."""
    
    def __init__(self, parent, on_apply_correction: Optional[Callable[[str], None]] = None):
        super().__init__(parent)
        self.on_apply_correction = on_apply_correction
        self.current_result: Optional[AnalysisResult] = None
        self._setup_ui()
        debug_console.log("Analysis tab widget initialized", level='DEBUG')
    
    def _setup_ui(self):
        """Setup the analysis tab UI."""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        self.analyze_btn = ttk.Button(
            header_frame,
            text="Analyze with AI",
            command=self._request_analysis,
            style='Accent.TButton'
        )
        self.analyze_btn.pack(side='left')
        
        self.status_label = ttk.Label(header_frame, text="Ready for analysis", foreground='#666')
        self.status_label.pack(side='left', padx=(10, 0))
        
        # Main content area
        content_frame = ttk.Frame(self)
        content_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Explanation area
        exp_frame = ttk.LabelFrame(content_frame, text="AI Explanation", padding=10)
        exp_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        self.explanation_text = tk.Text(
            exp_frame,
            wrap='word',
            height=8,
            font=('Segoe UI', 10),
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
            height=6,
            font=('Consolas', 9),
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
        
        # Apply button
        self.apply_btn = ttk.Button(
            self.correction_frame,
            text="Apply Correction",
            command=self._apply_correction,
            style='Success.TButton',
            state='disabled'
        )
        self.apply_btn.pack(pady=5)
    
    def present_analysis(self, result: AnalysisResult, context: DebugContext):
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
        
        debug_console.log(f"Analysis presented with {confidence_pct}% confidence", level='INFO')
        
        # Re-enable the analyze button
        self.analyze_btn.configure(state='normal')
    
    def present_quick_fixes(self, fixes: List[QuickFix], context: DebugContext):
        """Present available quick fixes (handled by QuickFix tab)."""
        pass  # This tab focuses on LLM analysis
    
    def show_fix_preview(self, fix: QuickFix, preview: str):
        """Show preview of a fix (handled by QuickFix tab)."""
        pass  # This tab focuses on LLM analysis
    
    def _request_analysis(self):
        """Request analysis from the debug coordinator."""
        self.status_label.configure(text="Requesting analysis...", foreground='#1976d2')
        self.analyze_btn.configure(state='disabled')
        
        # Find parent debug panel and call its analysis callback
        parent_panel = self.master
        while parent_panel and not hasattr(parent_panel, 'on_request_analysis'):
            parent_panel = parent_panel.master
        
        if parent_panel and hasattr(parent_panel, 'on_request_analysis') and parent_panel.on_request_analysis:
            debug_console.log("Calling analysis request callback", level='INFO')
            parent_panel.on_request_analysis()
        else:
            debug_console.log("No analysis callback found", level='WARNING')
            self.status_label.configure(text="Analysis not available", foreground='#d32f2f')
            self.analyze_btn.configure(state='normal')
    
    def _apply_correction(self):
        """Apply the suggested correction."""
        if self.current_result and self.current_result.corrected_code and self.on_apply_correction:
            self.on_apply_correction(self.current_result.corrected_code)
            self.status_label.configure(text="Correction applied", foreground='#2e7d32')
        else:
            debug_console.log("No correction to apply", level='WARNING')


class QuickFixTabWidget(ttk.Frame):
    """Tab widget for quick fixes and automatic corrections."""
    
    def __init__(self, parent, on_apply_fix: Optional[Callable[[QuickFix], None]] = None):
        super().__init__(parent)
        self.on_apply_fix = on_apply_fix
        self.current_fixes: List[QuickFix] = []
        self._setup_ui()
        debug_console.log("QuickFix tab widget initialized", level='DEBUG')
    
    def _setup_ui(self):
        """Setup the quick fix tab UI."""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        title_label = ttk.Label(header_frame, text="Quick Fixes", font=('Arial', 10, 'bold'))
        title_label.pack(side='left')
        
        self.auto_fix_btn = ttk.Button(
            header_frame,
            text="Auto-Fix Safe Issues",
            command=self._auto_fix_safe,
            style='Success.TButton'
        )
        self.auto_fix_btn.pack(side='right')
        
        # Quick fixes list
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.fixes_tree = ttk.Treeview(
            list_frame,
            columns=('confidence', 'type', 'description'),
            show='tree headings',
            height=10
        )
        
        # Configure columns
        self.fixes_tree.heading('#0', text='Fix', anchor='w')
        self.fixes_tree.heading('confidence', text='Confidence', anchor='w')
        self.fixes_tree.heading('type', text='Type', anchor='w')
        self.fixes_tree.heading('description', text='Description', anchor='w')
        
        self.fixes_tree.column('#0', width=150, minwidth=100)
        self.fixes_tree.column('confidence', width=80, minwidth=60)
        self.fixes_tree.column('type', width=80, minwidth=60)
        self.fixes_tree.column('description', width=300, minwidth=200)
        
        # Scrollbar
        fixes_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.fixes_tree.yview)
        self.fixes_tree.configure(yscrollcommand=fixes_scrollbar.set)
        
        fixes_scrollbar.pack(side='right', fill='y')
        self.fixes_tree.pack(side='left', fill='both', expand=True)
        
        # Apply button
        apply_frame = ttk.Frame(self)
        apply_frame.pack(fill='x', padx=5, pady=5)
        
        self.apply_fix_btn = ttk.Button(
            apply_frame,
            text="Apply Selected Fix",
            command=self._apply_selected_fix,
            style='Accent.TButton',
            state='disabled'
        )
        self.apply_fix_btn.pack(side='left')
        
        self.preview_btn = ttk.Button(
            apply_frame,
            text="Preview Fix",
            command=self._preview_selected_fix,
            style='Outline.TButton',
            state='disabled'
        )
        self.preview_btn.pack(side='left', padx=(5, 0))
        
        # Bind selection
        self.fixes_tree.bind('<<TreeviewSelect>>', self._on_fix_selected)
        self.fixes_tree.bind('<Double-1>', self._apply_selected_fix)
    
    def display_quick_fixes(self, fixes: List[QuickFix]):
        """Display available quick fixes."""
        self.current_fixes = fixes
        
        # Clear existing items
        for item in self.fixes_tree.get_children():
            self.fixes_tree.delete(item)
        
        # Add fixes
        for i, fix in enumerate(fixes):
            confidence_pct = int(fix.confidence * 100)
            
            # Icon based on confidence and auto-applicability
            if fix.auto_applicable and fix.confidence > 0.8:
                icon = "🔧"  # High confidence auto fix
            elif fix.auto_applicable:
                icon = "⚙️"  # Auto fix
            elif fix.confidence > 0.8:
                icon = "✅"  # High confidence manual fix
            else:
                icon = "🔧"  # Manual fix
            
            self.fixes_tree.insert('', 'end',
                                 text=f"{icon} {fix.title}",
                                 values=(f"{confidence_pct}%", fix.fix_type, fix.description),
                                 tags=('auto' if fix.auto_applicable else 'manual',))
        
        # Configure tags
        self.fixes_tree.tag_configure('auto', foreground='#2e7d32')
        self.fixes_tree.tag_configure('manual', foreground='#1976d2')
        
        debug_console.log(f"Displayed {len(fixes)} quick fixes", level='INFO')
    
    def _on_fix_selected(self, event):
        """Handle fix selection."""
        selection = self.fixes_tree.selection()
        if selection:
            self.apply_fix_btn.configure(state='normal')
            self.preview_btn.configure(state='normal')
        else:
            self.apply_fix_btn.configure(state='disabled')
            self.preview_btn.configure(state='disabled')
    
    def _apply_selected_fix(self, event=None):
        """Apply the selected fix."""
        selection = self.fixes_tree.selection()
        if not selection or not self.on_apply_fix:
            return
        
        try:
            item = selection[0]
            fix_index = self.fixes_tree.index(item)
            if 0 <= fix_index < len(self.current_fixes):
                fix = self.current_fixes[fix_index]
                self.on_apply_fix(fix)
                debug_console.log(f"Applied fix: {fix.title}", level='INFO')
        except Exception as e:
            debug_console.log(f"Error applying fix: {e}", level='ERROR')
    
    def _preview_selected_fix(self):
        """Preview the selected fix."""
        debug_console.log("Fix preview requested", level='INFO')
        # This would be handled by the coordinator
    
    def _auto_fix_safe(self):
        """Apply all safe auto-fixes."""
        safe_fixes = [fix for fix in self.current_fixes if fix.auto_applicable and fix.confidence > 0.8]
        
        if not safe_fixes:
            debug_console.log("No safe auto-fixes available", level='INFO')
            return
        
        for fix in safe_fixes:
            if self.on_apply_fix:
                self.on_apply_fix(fix)
        
        debug_console.log(f"Applied {len(safe_fixes)} safe auto-fixes", level='SUCCESS')


class AdvancedDebugPanel(ttk.Frame):
    """
    Advanced debug panel with tabbed interface.
    Integrates errors, analysis, quick fixes, and diff viewing.
    """
    
    def __init__(self, parent, on_goto_line: Optional[Callable[[int], None]] = None):
        super().__init__(parent)
        self.on_goto_line = on_goto_line
        self.current_context: Optional[DebugContext] = None
        
        # Callbacks (will be set by coordinator)
        self.on_request_analysis: Optional[Callable[[], None]] = None
        self.on_apply_correction: Optional[Callable[[str], None]] = None
        self.on_apply_quick_fix: Optional[Callable[[QuickFix], None]] = None
        self.on_compare_versions: Optional[Callable[[], None]] = None
        
        self._setup_ui()
        debug_console.log("Advanced debug panel initialized", level='DEBUG')
    
    def _setup_ui(self):
        """Setup the advanced UI with tabs."""
        # Header with main actions
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        title_label = ttk.Label(header_frame, text="Debug Center", font=('Arial', 12, 'bold'))
        title_label.pack(side='left')
        
        self.compare_btn = ttk.Button(
            header_frame,
            text="Compare Versions",
            command=self._compare_versions,
            style='Accent.TButton'
        )
        self.compare_btn.pack(side='right')
        
        # Separator
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)
        
        # Notebook with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Errors tab
        self.errors_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.errors_frame, text='Errors')
        
        self.error_list = TeXstudioErrorListWidget(
            self.errors_frame,
            on_error_click=self._on_error_selected
        )
        self.error_list.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Analysis tab
        self.analysis_tab = AnalysisTabWidget(
            self.notebook,
            on_apply_correction=self._on_apply_correction
        )
        self.notebook.add(self.analysis_tab, text='AI Analysis')
        
        # Quick Fixes tab
        self.quickfix_tab = QuickFixTabWidget(
            self.notebook,
            on_apply_fix=self._on_apply_quick_fix
        )
        self.notebook.add(self.quickfix_tab, text='Quick Fixes')
        
        # Status bar
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill='x', padx=5, pady=2)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", foreground='#666')
        self.status_label.pack(side='left')
    
    def update_compilation_errors(self, log_content: str, file_path: str = None, current_content: str = None):
        """Update panel with compilation errors."""
        from debug_system.latex_error_parser import ErrorParserFactory
        
        # Parse errors
        parser = ErrorParserFactory.create_texstudio_parser()
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
        
        debug_console.log(f"Updated debug panel with {len(errors)} total issues", level='INFO')
    
    def display_analysis_result(self, result: AnalysisResult):
        """Display LLM analysis result."""
        if self.current_context:
            self.analysis_tab.present_analysis(result, self.current_context)
            
            # Generate and display quick fixes
            if result.quick_fixes:
                self.quickfix_tab.display_quick_fixes(result.quick_fixes)
            
            # Switch to analysis tab
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
                debug_console.log(f"Error navigating to line: {e}", level='WARNING')
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
                debug_console.log(f"Error navigating to end of file: {e}", level='WARNING')
    
    def _compare_versions(self):
        """Request version comparison."""
        if self.on_compare_versions:
            self.on_compare_versions()
    
    def _on_apply_correction(self, corrected_code: str):
        """Handle correction application."""
        if self.on_apply_correction:
            self.on_apply_correction(corrected_code)
    
    def _on_apply_quick_fix(self, fix: QuickFix):
        """Handle quick fix application."""
        if self.on_apply_quick_fix:
            self.on_apply_quick_fix(fix)


class AdvancedDebugPanelFactory:
    """Factory for creating advanced debug panels."""
    
    @staticmethod
    def create_panel(parent, on_goto_line: Optional[Callable[[int], None]] = None) -> AdvancedDebugPanel:
        """Create an advanced debug panel."""
        return AdvancedDebugPanel(parent, on_goto_line)