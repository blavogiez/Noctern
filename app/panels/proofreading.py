"""
Integrated proofreading panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents

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
    
    def get_layout_style(self) -> PanelStyle:
        """Use scrollable layout for comprehensive proofreading interface."""
        return PanelStyle.SCROLLABLE
    
    def create_content(self):
        """Create the proofreading panel content using standardized components."""
        # main_container is a tuple for scrollable: (scrollable_frame, canvas)
        scrollable_frame, canvas = self.main_container
        
        # Main content in scrollable area
        main_frame = ttk.Frame(scrollable_frame, padding=StandardComponents.PADDING)
        main_frame.pack(fill="both", expand=True)
        
        # Create content sections using standardized components
        self._create_control_section(main_frame)
        self._create_analysis_section(main_frame)
        self._create_navigation_section(main_frame)
        
    def _create_control_section(self, parent):
        """Create the control section with instructions and analyze button."""
        control_section = StandardComponents.create_section(parent, "Analysis Control")
        control_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Status indicator
        self.status_indicator = StandardComponents.create_info_label(
            control_section,
            "Ready to analyze",
            "body"
        )
        self.status_indicator.pack(anchor="w", pady=(0, StandardComponents.PADDING))
        
        # Instructions
        instructions_label = StandardComponents.create_info_label(
            control_section, 
            "Custom instructions (optional):", 
            "body"
        )
        instructions_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        self.instructions_entry = StandardComponents.create_entry_input(
            control_section, 
            "Add specific instructions for analysis..."
        )
        self.instructions_entry.pack(fill="x", pady=(0, StandardComponents.PADDING))
        
        # Set as main widget for focus
        self.main_widget = self.instructions_entry
        
        # Analyze button
        analyze_buttons = [(
            "Start Analysis", 
            self._start_proofreading, 
            "primary"
        )]
        analyze_row = StandardComponents.create_button_row(control_section, analyze_buttons)
        analyze_row.pack(fill="x", pady=(0, StandardComponents.PADDING))
        self.analyze_button = analyze_row.winfo_children()[0]  # Get the button reference
        
        # Progress display
        progress_label = StandardComponents.create_info_label(
            control_section, 
            "", 
            "small"
        )
        progress_label.pack(anchor="w")
        # Update the textvariable after creation
        progress_label.config(textvariable=self.progress_var)
        
    def _create_analysis_section(self, parent):
        """Create the analysis display section."""
        analysis_section = StandardComponents.create_section(parent, "Analysis Results")
        analysis_section.pack(fill="both", expand=True, pady=(0, StandardComponents.SECTION_SPACING))
        
        # Original text display
        original_label = StandardComponents.create_info_label(
            analysis_section, 
            "Original Text (preview):", 
            "body"
        )
        original_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        self.original_text_widget = StandardComponents.create_text_input(
            analysis_section,
            "Original text will appear here...",
            height=4
        )
        self.original_text_widget.pack(fill="x", pady=(0, StandardComponents.PADDING))
        
        # Show original text (disabled for readonly)
        self.original_text_widget.config(state="normal")
        self.original_text_widget.delete("1.0", "end")
        self.original_text_widget.insert("1.0", self.initial_text[:500] + ("..." if len(self.initial_text) > 500 else ""))
        self.original_text_widget.config(state="disabled")
        
        # Analysis output
        analysis_label = StandardComponents.create_info_label(
            analysis_section, 
            "Analysis:", 
            "body"
        )
        analysis_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        self.analysis_text_widget = StandardComponents.create_text_input(
            analysis_section,
            "Analysis results will appear here...",
            height=6
        )
        self.analysis_text_widget.pack(fill="x")
        self.analysis_text_widget.config(state="disabled")
        
    def _create_navigation_section(self, parent):
        """Create error navigation section (hidden initially)."""
        self.navigation_frame = StandardComponents.create_section(parent, "Error Navigation")
        # Don't pack initially - will be shown when errors are found
        
        # Navigation controls
        nav_controls = ttk.Frame(self.navigation_frame)
        nav_controls.pack(fill="x", pady=(0, StandardComponents.PADDING))
        
        # Navigation buttons
        nav_buttons = [
            ("Previous", self._go_previous, "secondary"),
            ("Next", self._go_next, "secondary")
        ]
        nav_button_row = StandardComponents.create_button_row(nav_controls, nav_buttons)
        nav_button_row.pack(side="left")
        
        # Store button references
        buttons = nav_button_row.winfo_children()
        self.prev_button = buttons[0]
        self.next_button = buttons[1]
        
        # Counter label
        self.counter_label = StandardComponents.create_info_label(
            nav_controls, 
            "", 
            "body"
        )
        self.counter_label.pack(side="right")
        self.counter_label.config(textvariable=self.error_counter_var)
        
        # Current error display
        error_label = StandardComponents.create_info_label(
            self.navigation_frame, 
            "Current Error:", 
            "body"
        )
        error_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        self.current_error_text = StandardComponents.create_text_input(
            self.navigation_frame,
            "Error text will appear here...",
            height=3
        )
        self.current_error_text.pack(fill="x", pady=(0, StandardComponents.PADDING//2))
        self.current_error_text.config(state="disabled")
        
        suggestion_label = StandardComponents.create_info_label(
            self.navigation_frame, 
            "Suggestion:", 
            "body"
        )
        suggestion_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        self.suggestion_text = StandardComponents.create_text_input(
            self.navigation_frame,
            "Suggestion will appear here...",
            height=3
        )
        self.suggestion_text.pack(fill="x", pady=(0, StandardComponents.PADDING))
        self.suggestion_text.config(state="disabled")
        
        # Action buttons
        action_buttons = [
            ("✓ Approve", self._approve_current_correction, "success"),
            ("✗ Reject", self._reject_current_correction, "secondary"),
            ("Apply", self._apply_current_correction, "primary"),
            ("Apply All Approved", self._apply_all_corrections, "success")
        ]
        action_row = StandardComponents.create_button_row(self.navigation_frame, action_buttons)
        action_row.pack(fill="x")
        
        # Store button references
        action_buttons_widgets = action_row.winfo_children()
        self.approve_button = action_buttons_widgets[0]
        self.reject_button = action_buttons_widgets[1]
        self.apply_button = action_buttons_widgets[2]
        self.apply_all_button = action_buttons_widgets[3]
        
        # Set initial state
        self.apply_button.config(state="disabled")
        
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
            self.navigation_frame.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
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