"""
Integrated proofreading panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents

from llm.proofreading import get_proofreading_service, ProofreadingError, ProofreadingSession
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
        
        # New widgets for context and explanation display
        self.context_text: Optional[tk.Text] = None
        self.explanation_label: Optional[tk.Label] = None
        self.error_type_label: Optional[tk.Label] = None
        
    def get_panel_title(self) -> str:
        return "Document Proofreading"
    
    def get_layout_style(self) -> PanelStyle:
        """Use split layout for better space utilization like generation panel."""
        return PanelStyle.SPLIT
    
    def get_critical_action_buttons(self) -> list:
        """Get critical action buttons that must always be visible."""
        return [
            ("Approve", self._approve_current_correction, "success"),
            ("Reject", self._reject_current_correction, "secondary"),
            ("Apply", self._apply_current_correction, "primary"),
            ("Apply All Approved", self._apply_all_corrections, "success")
        ]
    
    def create_content(self):
        """Create the proofreading panel using split layout like generation panel."""
        # main_container is a PanedWindow for split layout
        paned_window = self.main_container
        
        # Control and analysis section (top - more space for analysis)
        self._create_main_section(paned_window)
        
        # Navigation section (bottom - for error navigation)  
        self._create_navigation_section(paned_window)
    
    def _create_main_section(self, parent):
        """Create the main section with control and analysis (top pane)."""
        main_frame = ttk.Frame(parent)
        parent.add(main_frame, weight=2)  # Give more space like generation panel
        
        # Main content with padding like generation panel
        content_frame = ttk.Frame(main_frame, padding=StandardComponents.PADDING)
        content_frame.pack(fill="both", expand=True)
        
        # Control section
        self._create_control_section(content_frame)
        
        # Analysis section  
        self._create_analysis_section(content_frame)
        
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
        
        # Bind keyboard shortcuts for the panel
        self._bind_keyboard_shortcuts()
        
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
        """Create error navigation section (bottom pane)."""
        nav_frame = ttk.Frame(parent)
        parent.add(nav_frame, weight=1)  # Less space like generation panel
        
        # Main content with padding like generation panel
        content_frame = ttk.Frame(nav_frame, padding=StandardComponents.PADDING)
        content_frame.pack(fill="both", expand=True)
        
        self.navigation_frame = StandardComponents.create_section(content_frame, "Error Navigation")
        self.navigation_frame.pack(fill="both", expand=True)  # Always visible now
        
        # Navigation controls
        nav_controls = ttk.Frame(self.navigation_frame)
        nav_controls.pack(fill="x", pady=(0, StandardComponents.PADDING))
        
        # Navigation buttons - Previous left, Next right (logical order)
        nav_buttons = [
            ("Previous", self._go_previous, "secondary"),
            ("Next", self._go_next, "secondary")
        ]
        nav_button_row = StandardComponents.create_button_row(nav_controls, nav_buttons)
        nav_button_row.pack(side="left")
        
        # Store button references - Previous is left (0), Next is right (1)
        buttons = nav_button_row.winfo_children()
        self.prev_button = buttons[0]  # Previous button (left)
        self.next_button = buttons[1]  # Next button (right)
        
        # Counter label
        self.counter_label = StandardComponents.create_info_label(
            nav_controls, 
            "", 
            "body"
        )
        self.counter_label.pack(side="right")
        self.counter_label.config(textvariable=self.error_counter_var)
        
        # Error type and details section
        details_frame = StandardComponents.create_section(self.navigation_frame, "Error Details")
        details_frame.pack(fill="x", pady=(0, StandardComponents.PADDING))
        
        # Error type
        type_frame = ttk.Frame(details_frame)
        type_frame.pack(fill="x", pady=(0, StandardComponents.PADDING//2))
        
        ttk.Label(type_frame, text="Type:").pack(side="left")
        self.error_type_label = StandardComponents.create_info_label(
            type_frame,
            "",
            "body"
        )
        self.error_type_label.pack(side="left", padx=(10, 0))
        
        # Original error text
        error_label = StandardComponents.create_info_label(
            details_frame, 
            "Original:", 
            "body"
        )
        error_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        self.current_error_text = StandardComponents.create_text_input(
            details_frame,
            "Error text will appear here...",
            height=2
        )
        self.current_error_text.pack(fill="x", pady=(0, StandardComponents.PADDING//2))
        self.current_error_text.config(state="disabled")
        
        # Explanation
        explanation_label = StandardComponents.create_info_label(
            details_frame, 
            "Explanation:", 
            "body"
        )
        explanation_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        self.explanation_label = StandardComponents.create_info_label(
            details_frame,
            "Explanation will appear here...",
            "small"
        )
        self.explanation_label.pack(anchor="w", fill="x", pady=(0, StandardComponents.PADDING))
        self.explanation_label.config(wraplength=400)
        
        # Suggestion
        suggestion_label = StandardComponents.create_info_label(
            details_frame, 
            "Suggestion:", 
            "body"
        )
        suggestion_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        self.suggestion_text = StandardComponents.create_text_input(
            details_frame,
            "Suggestion will appear here...",
            height=2
        )
        self.suggestion_text.pack(fill="x", pady=(0, StandardComponents.PADDING))
        self.suggestion_text.config(state="disabled")
        
        # Context display section - positioned above the action buttons
        context_section = StandardComponents.create_section(self.navigation_frame, "Context")
        context_section.pack(fill="both", expand=True, pady=(0, StandardComponents.PADDING))
        
        # Limit height to ensure buttons remain visible, add scrollbar if needed
        context_frame = ttk.Frame(context_section)
        context_frame.pack(fill="both", expand=True)
        
        self.context_text = StandardComponents.create_text_input(
            context_frame,
            "Context will appear here...",
            height=3  # Reduced from 4 to save space for buttons
        )
        
        # Add scrollbar for context if it gets too long
        context_scrollbar = ttk.Scrollbar(context_frame, orient="vertical", command=self.context_text.yview)
        self.context_text.configure(yscrollcommand=context_scrollbar.set)
        
        self.context_text.pack(side="left", fill="both", expand=True)
        context_scrollbar.pack(side="right", fill="y")
        
        self.context_text.config(state="disabled")
        
        # Configure text highlighting tags
        self.context_text.tag_configure("error_highlight", 
                                       background="#ffcccc", 
                                       foreground="#990000")
        
        # Critical action buttons are now handled by BasePanel automatically
        # Initialize button references that will be populated after panel creation
        self.approve_button = None
        self.reject_button = None 
        self.apply_button = None
        self.apply_all_button = None
    
    def _link_critical_button_references(self):
        """Link critical button references after creation."""
        if hasattr(self, 'critical_action_buttons') and len(self.critical_action_buttons) >= 4:
            # Buttons are created in order: Approve, Reject, Apply, Apply All Approved
            # But packed right-to-left, so reverse order in the children list
            buttons = self.critical_action_buttons
            self.approve_button = buttons[-1]  # First defined, last in children
            self.reject_button = buttons[-2]   # Second defined, second-to-last in children
            self.apply_button = buttons[-3]    # Third defined, third-to-last in children
            self.apply_all_button = buttons[-4]  # Last defined, first in children
            
            # Set initial state
            if self.apply_button:
                self.apply_button.config(state="disabled")
        
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.instructions_entry:
            self.instructions_entry.focus_set()
            # Enable keyboard shortcuts when panel has focus
            self.panel_frame.focus_set()
    
    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts for navigation and actions."""
        # Bind to the panel frame to capture keyboard events
        self.panel_frame.bind("<Left>", lambda e: self._go_previous())
        self.panel_frame.bind("<Right>", lambda e: self._go_next())
        self.panel_frame.bind("<KeyPress-a>", lambda e: self._approve_current_correction())
        self.panel_frame.bind("<KeyPress-r>", lambda e: self._reject_current_correction())
        
        # Make sure the panel can receive focus for keyboard events
        self.panel_frame.config(takefocus=True)
        
        # Also bind to main container for broader capture
        if hasattr(self, 'main_container'):
            self.main_container.bind("<Left>", lambda e: self._go_previous())
            self.main_container.bind("<Right>", lambda e: self._go_next())
            self.main_container.bind("<KeyPress-a>", lambda e: self._approve_current_correction())
            self.main_container.bind("<KeyPress-r>", lambda e: self._reject_current_correction())
    
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
            # Navigation section is already visible with SPLIT layout
            self._update_error_navigation()
    
    def _on_analysis_error(self, error_msg: str):
        """Handle analysis error."""
        if self.analyze_button and self.analyze_button.winfo_exists():
            self.analyze_button.config(state="normal", text="Retry Analysis")
            self.status_indicator.config(text="Analysis failed", foreground=self.get_theme_color("danger", "#cc0000"))
            messagebox.showerror("Proofreading Analysis Error", f"Failed to analyze document:\n{error_msg}", parent=self.panel_frame)
    
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
            messagebox.showwarning("Correction Not Approved", "Please approve this correction before applying it.", parent=self.panel_frame)
            return
            
        if self.session.apply_current_correction(self.editor):
            self.apply_button.config(state="disabled", text="Applied")
            # Auto-advance to next error
            self.panel_frame.after(1000, self._go_next)
        else:
            messagebox.showwarning("Apply Correction Failed", 
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
        """Update error navigation display with context and explanation."""
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
        
        # Update error type with color coding
        if hasattr(current_error, 'type') and current_error.type:
            error_type_text = current_error.type.value.title() if hasattr(current_error.type, 'value') else str(current_error.type)
            self.error_type_label.config(text=error_type_text)
            # Set color based on error type
            type_colors = {
                'grammar': self.get_theme_color("danger", "#cc0000"),
                'spelling': self.get_theme_color("warning", "#ff6600"),
                'punctuation': self.get_theme_color("primary", "#6600cc"),
                'style': self.get_theme_color("info", "#0066cc"),
                'clarity': self.get_theme_color("success", "#006600"),
                'syntax': self.get_theme_color("danger", "#990000"),
                'coherence': self.get_theme_color("warning", "#cc6600")
            }
            error_type_lower = error_type_text.lower()
            color = type_colors.get(error_type_lower, self.get_theme_color("text", "#000000"))
            self.error_type_label.config(foreground=color)
        
        # Update error display
        self.current_error_text.config(state="normal")
        self.current_error_text.delete("1.0", "end")
        self.current_error_text.insert("1.0", current_error.original)
        self.current_error_text.config(state="disabled")
        
        # Update explanation
        explanation_text = getattr(current_error, 'explanation', '') or "No explanation provided"
        self.explanation_label.config(text=explanation_text)
        
        # Update suggestion
        self.suggestion_text.config(state="normal")
        self.suggestion_text.delete("1.0", "end")
        suggestion_text = current_error.suggestion if current_error.suggestion else "[DELETE]"
        self.suggestion_text.insert("1.0", suggestion_text)
        self.suggestion_text.config(state="disabled")
        
        # Update context with highlighting
        self.context_text.config(state="normal")
        self.context_text.delete("1.0", "end")
        
        context = getattr(current_error, 'context', '') or current_error.original
        self.context_text.insert("1.0", context)
        
        # Highlight the original error text in the context
        if current_error.original and current_error.original in context:
            start_pos = context.find(current_error.original)
            if start_pos != -1:
                # Calculate Text widget positions
                lines_before = context[:start_pos].count('\n')
                char_pos = len(context[:start_pos].split('\n')[-1])
                
                start_index = f"{lines_before + 1}.{char_pos}"
                end_index = f"{lines_before + 1}.{char_pos + len(current_error.original)}"
                
                # Apply highlight
                self.context_text.tag_add("error_highlight", start_index, end_index)
        
        self.context_text.config(state="disabled")
        
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
        
        # Ensure the panel can receive keyboard focus
        self.panel_frame.focus_set()