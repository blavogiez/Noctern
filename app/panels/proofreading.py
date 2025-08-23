"""
Integrated proofreading panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from .base_panel import BasePanel

from llm.proofreading_service import get_proofreading_service, ProofreadingError, ProofreadingSession, load_session_from_cache, list_cached_sessions
from llm import state


class ProofreadingPanel(BasePanel):
    """
    Integrated proofreading panel that replaces the dialog window.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter, 
                 editor, initial_text: str, on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        self.editor = editor
        self.initial_text = initial_text
        
        # Services and state
        self.proofreading_service = get_proofreading_service()
        self.session: Optional[ProofreadingSession] = None
        
        # UI components
        self.progress_var = tk.StringVar(value="")
        self.current_error_var = tk.StringVar(value="")
        self.error_counter_var = tk.StringVar(value="")
        
        # Content widgets
        self.instructions_entry: Optional[tk.Entry] = None
        self.analyze_button: Optional[tk.Button] = None
        self.status_indicator: Optional[tk.Label] = None
        self.notebook: Optional[ttk.Notebook] = None
        
    def get_panel_title(self) -> str:
        return "Document Proofreading"
    
    def create_content(self):
        """Create the proofreading panel content."""
        # Main scrollable area
        main_canvas = tk.Canvas(self.content_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create content sections in scrollable frame
        self._create_control_section(scrollable_frame)
        self._create_analysis_section(scrollable_frame)
        self._create_navigation_section(scrollable_frame)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
    def _create_control_section(self, parent):
        """Create the control section with instructions and analyze button."""
        control_frame = ttk.LabelFrame(parent, text=" Analysis Control ", padding="10")
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # Status indicator
        self.status_indicator = ttk.Label(
            control_frame,
            text="Ready to analyze",
            foreground=self.get_theme_color("muted_text", "#666666")
        )
        self.status_indicator.pack(anchor="w", pady=(0, 10))
        
        # Instructions
        ttk.Label(control_frame, text="Instructions (optional):").pack(anchor="w")
        self.instructions_entry = ttk.Entry(control_frame, width=40)
        self.instructions_entry.pack(fill="x", pady=(5, 10))
        
        # Analyze button
        self.analyze_button = ttk.Button(
            control_frame,
            text="Start Analysis",
            command=self._start_proofreading
        )
        self.analyze_button.pack(anchor="w")
        
        # Progress display
        progress_label = ttk.Label(control_frame, textvariable=self.progress_var, wraplength=300)
        progress_label.pack(fill="x", pady=(10, 0))
        
    def _create_analysis_section(self, parent):
        """Create the analysis display section."""
        analysis_frame = ttk.LabelFrame(parent, text=" Analysis Results ", padding="10")
        analysis_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Original text display
        ttk.Label(analysis_frame, text="Original Text:").pack(anchor="w", pady=(0, 5))
        
        original_frame = ttk.Frame(analysis_frame)
        original_frame.pack(fill="x", pady=(0, 10))
        
        self.original_text_widget = tk.Text(
            original_frame,
            height=4,
            wrap="word",
            bg=self.get_theme_color("editor_bg", "#ffffff"),
            fg=self.get_theme_color("editor_fg", "#000000"),
            state="disabled",
            relief="solid",
            borderwidth=1
        )
        self.original_text_widget.pack(fill="x")
        
        # Show original text
        self.original_text_widget.config(state="normal")
        self.original_text_widget.insert("1.0", self.initial_text[:500] + ("..." if len(self.initial_text) > 500 else ""))
        self.original_text_widget.config(state="disabled")
        
        # Analysis output
        ttk.Label(analysis_frame, text="AI Analysis:").pack(anchor="w", pady=(10, 5))
        
        self.analysis_text_widget = tk.Text(
            analysis_frame,
            height=6,
            wrap="word",
            bg="#f8f9fa",
            fg=self.get_theme_color("editor_fg", "#000000"),
            state="disabled",
            relief="solid",
            borderwidth=1
        )
        self.analysis_text_widget.pack(fill="x")
        
    def _create_navigation_section(self, parent):
        """Create error navigation section (hidden initially)."""
        self.navigation_frame = ttk.LabelFrame(parent, text=" Error Navigation ", padding="10")
        # Don't pack initially - will be shown when errors are found
        
        # Navigation controls
        nav_controls = ttk.Frame(self.navigation_frame)
        nav_controls.pack(fill="x", pady=(0, 10))
        
        self.prev_button = ttk.Button(nav_controls, text="Previous", command=self._go_previous)
        self.prev_button.pack(side="left", padx=(0, 5))
        
        self.next_button = ttk.Button(nav_controls, text="Next", command=self._go_next)
        self.next_button.pack(side="left", padx=(0, 10))
        
        self.counter_label = ttk.Label(nav_controls, textvariable=self.error_counter_var)
        self.counter_label.pack(side="left")
        
        # Current error display
        ttk.Label(self.navigation_frame, text="Current Error:").pack(anchor="w", pady=(0, 5))
        
        self.current_error_text = tk.Text(
            self.navigation_frame,
            height=3,
            wrap="word",
            bg="#ffeeee",
            state="disabled",
            relief="solid",
            borderwidth=1
        )
        self.current_error_text.pack(fill="x", pady=(0, 5))
        
        ttk.Label(self.navigation_frame, text="Suggestion:").pack(anchor="w", pady=(5, 5))
        
        self.suggestion_text = tk.Text(
            self.navigation_frame,
            height=3,
            wrap="word",
            bg=self.get_theme_color("editor_bg", "#ffffff"),
            state="disabled",
            relief="solid",
            borderwidth=1
        )
        self.suggestion_text.pack(fill="x", pady=(0, 10))
        
        # Action buttons
        action_frame = ttk.Frame(self.navigation_frame)
        action_frame.pack(fill="x")
        
        self.approve_button = ttk.Button(action_frame, text="✓ Approve", command=self._approve_current_correction)
        self.approve_button.pack(side="left", padx=(0, 5))
        
        self.reject_button = ttk.Button(action_frame, text="✗ Reject", command=self._reject_current_correction)
        self.reject_button.pack(side="left", padx=(0, 5))
        
        self.apply_button = ttk.Button(action_frame, text="Apply", command=self._apply_current_correction, state="disabled")
        self.apply_button.pack(side="left", padx=(0, 10))
        
        # Apply all button
        self.apply_all_button = ttk.Button(action_frame, text="Apply All Approved", command=self._apply_all_corrections)
        self.apply_all_button.pack(side="right")
        
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.instructions_entry:
            self.instructions_entry.focus_set()
    
    # Proofreading methods (simplified from original dialog)
    def _start_proofreading(self):
        """Start proofreading analysis."""
        if self.session and self.session.is_processing:
            return
        
        custom_instructions = self.instructions_entry.get().strip()
        
        # Create new session
        self.session = self.proofreading_service.start_session(
            self.initial_text, 
            custom_instructions
        )
        
        # Setup callbacks
        self.session.on_status_change = self._on_status_change
        self.session.on_progress_change = self._on_progress_change
        self.session.on_errors_found = self._on_errors_found
        self.session.on_error = self._on_analysis_error
        
        # Update UI
        self.analyze_button.config(state="disabled", text="Processing...")
        self.status_indicator.config(text="Processing...", foreground=self.get_theme_color("primary", "#0066cc"))
        
        # Start analysis
        self.proofreading_service.analyze_text(self.session, self.editor)
    
    def _on_status_change(self, status: str):
        """Handle status change."""
        if self.status_indicator and self.status_indicator.winfo_exists():
            if "found" in status.lower():
                self.analyze_button.config(state="normal", text="Restart Analysis")
                self.status_indicator.config(text="Analysis complete", foreground=self.get_theme_color("success", "#006600"))
    
    def _on_progress_change(self, progress: str):
        """Handle progress change."""
        if hasattr(self, 'progress_var'):
            self.progress_var.set(progress)
            if self.analysis_text_widget and self.analysis_text_widget.winfo_exists():
                self.analysis_text_widget.config(state="normal")
                self.analysis_text_widget.delete("1.0", "end")
                self.analysis_text_widget.insert("1.0", progress)
                self.analysis_text_widget.config(state="disabled")
    
    def _on_errors_found(self, errors: List[ProofreadingError]):
        """Handle errors found."""
        if errors:
            # Show navigation section
            self.navigation_frame.pack(fill="x", padx=5, pady=5)
            self._update_error_navigation()
    
    def _on_analysis_error(self, error_msg: str):
        """Handle analysis error."""
        if self.analyze_button and self.analyze_button.winfo_exists():
            self.analyze_button.config(state="normal", text="Retry Analysis")
            self.status_indicator.config(text="Analysis failed", foreground=self.get_theme_color("danger", "#cc0000"))
            messagebox.showerror("Analysis Error", error_msg, parent=self.panel_frame)
    
    def _go_previous(self):
        """Go to previous error."""
        if self.session and self.session.go_to_previous_error():
            self._update_error_navigation()
    
    def _go_next(self):
        """Go to next error."""
        if self.session and self.session.go_to_next_error():
            self._update_error_navigation()
    
    def _approve_current_correction(self):
        """Approve current correction."""
        if self.session and self.session.approve_current_correction():
            self._update_error_navigation()
            # Auto-advance to next error
            self.panel_frame.after(500, self._go_next)
    
    def _reject_current_correction(self):
        """Reject current correction."""
        if self.session and self.session.reject_current_correction():
            self._update_error_navigation()
            # Auto-advance to next error
            self.panel_frame.after(500, self._go_next)
    
    def _apply_current_correction(self):
        """Apply current correction."""
        if not self.session:
            return
            
        current_error = self.session.get_current_error()
        if not current_error or not current_error.is_approved:
            messagebox.showwarning("Not Approved", "Please approve this correction before applying it.", parent=self.panel_frame)
            return
            
        if self.session.apply_current_correction(self.editor):
            self.apply_button.config(state="disabled", text="Applied")
            # Auto-advance to next error
            self.panel_frame.after(1000, self._go_next)
        else:
            messagebox.showwarning("Application Failed", 
                "Could not apply the correction. The original text may have been modified.",
                parent=self.panel_frame)
    
    def _apply_all_corrections(self):
        """Apply all approved corrections."""
        if not self.session or not self.session.errors:
            return
        
        from llm.proofreading_apply import apply_all_corrections
        
        success, corrected_filepath = apply_all_corrections(
            self.session.errors,
            self.initial_text,
            parent_window=self.panel_frame
        )
        
        if success:
            self._update_error_navigation()
    
    def _update_error_navigation(self):
        """Update error navigation display."""
        if not self.session or not self.session.errors:
            return
        
        current_error = self.session.get_current_error()
        if not current_error:
            return
        
        # Update counter
        current_idx = self.session.current_error_index + 1
        total = len(self.session.errors)
        self.error_counter_var.set(f"Error {current_idx} of {total}")
        
        # Update navigation buttons
        self.prev_button.config(state="normal" if self.session.current_error_index > 0 else "disabled")
        self.next_button.config(state="normal" if self.session.current_error_index < total - 1 else "disabled")
        
        # Update error display
        self.current_error_text.config(state="normal")
        self.current_error_text.delete("1.0", "end")
        self.current_error_text.insert("1.0", current_error.original)
        self.current_error_text.config(state="disabled")
        
        self.suggestion_text.config(state="normal")
        self.suggestion_text.delete("1.0", "end")
        suggestion_text = current_error.suggestion if current_error.suggestion else "[DELETE]"
        self.suggestion_text.insert("1.0", suggestion_text)
        self.suggestion_text.config(state="disabled")
        
        # Update button states
        if current_error.is_applied:
            self.approve_button.config(state="disabled", text="Applied")
            self.reject_button.config(state="disabled")
            self.apply_button.config(state="disabled", text="Applied")
        elif current_error.is_approved:
            self.approve_button.config(state="disabled", text="Approved")
            self.reject_button.config(state="normal", text="Reject")
            self.apply_button.config(state="normal", text="Apply")
        else:
            self.approve_button.config(state="normal", text="Approve")
            self.reject_button.config(state="normal", text="Reject")
            self.apply_button.config(state="disabled", text="Apply")