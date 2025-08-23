"""
Document proofreading dialog interface.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List

from llm.proofreading_service import get_proofreading_service, ProofreadingError, ProofreadingSession, load_session_from_cache, list_cached_sessions
from llm import state


class ProofreadingDialog:
    """
    Document proofreading dialog interface.
    """
    
    def __init__(self, parent, theme_getter, editor, initial_text: str):
        self.parent = parent
        self.theme_getter = theme_getter
        self.editor = editor
        self.initial_text = initial_text
        
        # Services and state
        self.proofreading_service = get_proofreading_service()
        self.session: Optional[ProofreadingSession] = None
        
        # UI components
        self.window: Optional[tk.Toplevel] = None
        self.progress_var = tk.StringVar(value="")
        self.current_error_var = tk.StringVar(value="")
        self.error_counter_var = tk.StringVar(value="")
        
        # Theme colors
        self._load_theme_colors()
    
    def _load_theme_colors(self):
        """Load color theme settings."""
        self.colors = {
            'bg': self.theme_getter("root_bg", "#ffffff"),
            'surface': self.theme_getter("editor_bg", "#ffffff"),
            'text': self.theme_getter("editor_fg", "#000000"),
            'primary': "#0066cc",
            'success': "#006600",
            'danger': "#cc0000",
            'muted': "#666666",
            'error_bg': "#ffeeee",
            'grammar_color': "#cc0000",
            'spelling_color': "#ff6600",
            'punctuation_color': "#6600cc",
            'style_color': "#0066cc",
            'clarity_color': "#006600",
            'syntax_color': "#990000",
            'coherence_color': "#cc6600"
        }
    
    def show(self):
        """Display proofreading dialog."""
        self._create_window()
        self._setup_layout()
        self._bind_events()
        
        # Show window
        self.window.deiconify()
        self.window.focus_force()
        self.window.wait_window()
    
    def _create_window(self):
        """Create and configure dialog window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Document Proofreading")
        self.window.configure(bg=self.colors['bg'])
        
        # Maximize window
        self.window.state('zoomed')
        self.window.minsize(800, 600)
        self.window.transient(self.parent)
        self.window.grab_set()
        
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
    
    def _setup_layout(self):
        """Create dialog layout."""
        # Main container
        main_container = ttk.Frame(self.window, padding="10")
        main_container.pack(fill="both", expand=True)
        main_container.grid_rowconfigure(2, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Create sections
        self._create_progress_section(main_container)
        self._create_content_area(main_container)
        self._create_footer(main_container)
    
    def _create_progress_section(self, parent):
        """Create progress section."""
        progress_frame = ttk.LabelFrame(parent, text=" Progress ", padding="10")
        progress_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        progress_frame.grid_columnconfigure(1, weight=1)
        
        # Status indicator
        self.status_indicator = ttk.Label(
            progress_frame,
            text="Ready",
            foreground=self.colors['muted']
        )
        self.status_indicator.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        
        # Progress text
        self.progress_label = ttk.Label(
            progress_frame,
            textvariable=self.progress_var
        )
        self.progress_label.grid(row=1, column=0, columnspan=3, sticky="w")
        
        # Instructions and control
        instructions_label = ttk.Label(progress_frame, text="Instructions (leaving blank is fine):")
        instructions_label.grid(row=2, column=0, sticky="w", pady=(10, 5))
        
        self.instructions_entry = ttk.Entry(progress_frame, width=40)
        self.instructions_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        # Warning about processing time
        warning_label = ttk.Label(
            progress_frame, 
            text="Note: Thorough analysis may take a while", 
            foreground=self.colors['muted'],
            font=("Segoe UI", 9)
        )
        warning_label.grid(row=4, column=0, columnspan=3, sticky="w", pady=(5, 0))
        
        self.analyze_button = ttk.Button(
            progress_frame,
            text="Start Analysis",
            command=self._start_proofreading
        )
        self.analyze_button.grid(row=3, column=2, sticky="e", padx=(10, 0))
    
    def _create_content_area(self, parent):
        """Create content area with tabs."""
        # Content tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        
        # Text Analysis Tab
        self._create_text_analysis_tab()
        
        # Error Navigation Tab (initially hidden)
        self.errors_tab_frame = None
        
        # Results Summary Tab (initially hidden)  
        self.summary_tab_frame = None
    
    def _create_text_analysis_tab(self):
        """Create text analysis tab."""
        analysis_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(analysis_frame, text="Text Analysis")
        
        analysis_frame.grid_rowconfigure(1, weight=1)
        analysis_frame.grid_rowconfigure(3, weight=1)
        analysis_frame.grid_columnconfigure(0, weight=1)
        
        # Original text section
        ttk.Label(analysis_frame, text="Original Text").grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        original_frame = ttk.Frame(analysis_frame, relief="solid", borderwidth=1)
        original_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        original_frame.grid_rowconfigure(0, weight=1)
        original_frame.grid_columnconfigure(0, weight=1)
        
        self.original_text_widget = tk.Text(
            original_frame,
            wrap="word",
            bg=self.colors['surface'],
            fg=self.colors['text'],
            state="disabled",
            relief="flat",
            padx=10,
            pady=10
        )
        self.original_text_widget.grid(row=0, column=0, sticky="nsew")
        
        original_scrollbar = ttk.Scrollbar(original_frame, orient="vertical", command=self.original_text_widget.yview)
        original_scrollbar.grid(row=0, column=1, sticky="ns")
        self.original_text_widget.config(yscrollcommand=original_scrollbar.set)
        
        # Show original text
        self.original_text_widget.config(state="normal")
        self.original_text_widget.insert("1.0", self.initial_text)
        self.original_text_widget.config(state="disabled")
        
        # AI Analysis section
        ttk.Label(analysis_frame, text="AI Analysis").grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        analysis_output_frame = ttk.Frame(analysis_frame, relief="solid", borderwidth=1)
        analysis_output_frame.grid(row=3, column=0, sticky="nsew")
        analysis_output_frame.grid_rowconfigure(0, weight=1)
        analysis_output_frame.grid_columnconfigure(0, weight=1)
        
        self.analysis_text_widget = tk.Text(
            analysis_output_frame,
            wrap="word",
            bg="#f8f9fa",
            fg=self.colors['text'],
            state="disabled",
            relief="flat",
            padx=10,
            pady=10
        )
        self.analysis_text_widget.grid(row=0, column=0, sticky="nsew")
        
        analysis_scrollbar = ttk.Scrollbar(analysis_output_frame, orient="vertical", command=self.analysis_text_widget.yview)
        analysis_scrollbar.grid(row=0, column=1, sticky="ns")
        self.analysis_text_widget.config(yscrollcommand=analysis_scrollbar.set)
    
    def _create_error_navigation_tab(self, errors: List[ProofreadingError]):
        """Create error navigation tab."""
        if self.errors_tab_frame:
            self.notebook.forget(self.errors_tab_frame)
        
        self.errors_tab_frame = ttk.Frame(self.notebook, padding="10")
        error_count = len(errors)
        self.notebook.add(self.errors_tab_frame, text=f"Errors ({error_count})")
        self.notebook.select(self.errors_tab_frame)
        
        self.errors_tab_frame.grid_rowconfigure(2, weight=1)
        self.errors_tab_frame.grid_columnconfigure(0, weight=1)
        
        # Navigation header
        nav_header = ttk.Frame(self.errors_tab_frame)
        nav_header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        nav_header.grid_columnconfigure(2, weight=1)
        
        # Navigation buttons
        self.prev_button = ttk.Button(
            nav_header, 
            text="Previous", 
            command=self._go_previous
        )
        self.prev_button.grid(row=0, column=0, padx=(0, 10))
        
        self.next_button = ttk.Button(
            nav_header,
            text="Next",
            command=self._go_next
        )
        self.next_button.grid(row=0, column=1, padx=(0, 20))
        
        # Error counter
        self.counter_label = ttk.Label(
            nav_header,
            textvariable=self.error_counter_var
        )
        self.counter_label.grid(row=0, column=2, sticky="w")
        
        # Quick stats
        stats_text = self._get_error_stats_text(errors)
        stats_label = ttk.Label(
            nav_header,
            text=stats_text,
            foreground=self.colors['muted']
        )
        stats_label.grid(row=0, column=3, sticky="e")
        
        # Current error display
        self._create_error_display_section(self.errors_tab_frame)
        
        # Update navigation
        self._update_error_navigation()
    
    def _create_error_display_section(self, parent):
        """Create error display section."""
        # Error details frame
        details_frame = ttk.LabelFrame(parent, text=" Error Details ", padding="10")
        details_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        details_frame.grid_columnconfigure(1, weight=1)
        
        # Error type
        ttk.Label(details_frame, text="Type:").grid(row=0, column=0, sticky="nw", padx=(0, 10))
        self.error_type_label = ttk.Label(details_frame, text="")
        self.error_type_label.grid(row=0, column=1, sticky="w")
        
        # Original text
        ttk.Label(details_frame, text="Original:").grid(row=1, column=0, sticky="nw", padx=(0, 10), pady=(5, 0))
        
        self.original_error_text = tk.Text(
            details_frame,
            height=2,
            wrap="word",
            bg=self.colors['error_bg'],
            fg=self.colors['text'],
            state="disabled",
            relief="flat",
            padx=5,
            pady=5
        )
        self.original_error_text.grid(row=1, column=1, sticky="ew", pady=(10, 0))
        
        # Suggested correction
        ttk.Label(details_frame, text="Suggestion:").grid(row=2, column=0, sticky="nw", padx=(0, 10), pady=(5, 0))
        
        self.suggested_text = tk.Text(
            details_frame,
            height=2,
            wrap="word",
            bg=self.colors['surface'],
            fg=self.colors['text'],
            state="disabled",
            relief="solid",
            borderwidth=1,
            padx=5,
            pady=5
        )
        self.suggested_text.grid(row=2, column=1, sticky="ew", pady=(10, 0))
        
        # Explanation
        ttk.Label(details_frame, text="Explanation:").grid(row=3, column=0, sticky="nw", padx=(0, 10), pady=(5, 0))
        self.explanation_label = ttk.Label(
            details_frame, 
            text="",
            wraplength=500
        )
        self.explanation_label.grid(row=3, column=1, sticky="w", pady=(10, 0))
        
        # Context display
        context_frame = ttk.LabelFrame(parent, text=" Context ", padding="15")
        context_frame.grid(row=2, column=0, sticky="nsew")
        context_frame.grid_rowconfigure(0, weight=1)
        context_frame.grid_columnconfigure(0, weight=1)
        
        self.context_text = tk.Text(
            context_frame,
            wrap="word",
            bg=self.colors['surface'],
            fg=self.colors['text'],
            state="disabled",
            relief="flat",
            padx=10,
            pady=5
        )
        self.context_text.grid(row=0, column=0, sticky="nsew")
        
        # Action buttons
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=3, column=0, sticky="ew", pady=(15, 0))
        
        # Approval buttons
        self.approve_button = ttk.Button(
            action_frame,
            text="✓ Approve",
            command=self._approve_current_correction
        )
        self.approve_button.pack(side="left", padx=(0, 10))
        
        self.reject_button = ttk.Button(
            action_frame,
            text="✗ Reject",
            command=self._reject_current_correction
        )
        self.reject_button.pack(side="left", padx=(0, 10))
        
        # Individual apply button (for approved corrections)
        self.apply_button = ttk.Button(
            action_frame,
            text="Apply Now",
            command=self._apply_current_correction,
            state="disabled"
        )
        self.apply_button.pack(side="left", padx=(0, 10))
        
        # Progress info
        applied_label = ttk.Label(
            action_frame,
            text="",
            foreground=self.colors['success']
        )
        applied_label.pack(side="right")
        self.applied_label = applied_label
    
    def _create_summary_tab(self):
        """Create summary tab."""
        if self.summary_tab_frame:
            self.notebook.forget(self.summary_tab_frame)
        
        self.summary_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.summary_tab_frame, text="Summary")
        
        # Add summary content here
        summary_text = self._generate_summary_text()
        
        summary_label = ttk.Label(
            self.summary_tab_frame,
            text=summary_text,
            justify="left"
        )
        summary_label.pack(anchor="w")
    
    def _create_footer(self, parent):
        """Create footer buttons."""
        footer_frame = ttk.Frame(parent)
        footer_frame.grid(row=3, column=0, sticky="ew")
        
        ttk.Button(
            footer_frame,
            text="Close",
            command=self._on_close
        ).pack(side="right")
        
        ttk.Button(
            footer_frame,
            text="Restart Analysis", 
            command=self._restart_analysis
        ).pack(side="right", padx=(0, 10))
        
        ttk.Button(
            footer_frame,
            text="Browse History",
            command=self._browse_history
        ).pack(side="right", padx=(0, 10))
        
        # Apply All Approved Corrections button (initially hidden)
        self.apply_all_button = ttk.Button(
            footer_frame,
            text="Apply All Approved & Save Corrected File",
            command=self._apply_all_corrections
        )
        # Don't pack initially - will be shown when errors are found
    
    def _bind_events(self):
        """Bind keyboard shortcuts."""
        self.window.bind("<Escape>", lambda e: self._on_close())
        self.window.bind("<F5>", lambda e: self._restart_analysis())
        self.window.bind("<Left>", lambda e: self._go_previous())
        self.window.bind("<Right>", lambda e: self._go_next())
        self.window.bind("<a>", lambda e: self._approve_current_correction())  # A for Approve
        self.window.bind("<r>", lambda e: self._reject_current_correction())   # R for Reject
        self.window.bind("<Return>", lambda e: self._apply_current_correction())
    
    # Event Handlers
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
        self.session.on_chunk_received = None
        self.session.on_errors_found = self._on_errors_found
        self.session.on_error = self._on_analysis_error
        
        # Update UI
        self.analyze_button.config(state="disabled", text="Processing...")
        self.status_indicator.config(text="Processing", foreground=self.colors['primary'])
        
        # Start analysis
        self.proofreading_service.analyze_text(self.session, self.editor)
        
    
    def _restart_analysis(self):
        """Restart proofreading analysis."""
        # Reset UI
        if hasattr(self, 'errors_tab_frame') and self.errors_tab_frame:
            self.notebook.forget(self.errors_tab_frame)
            self.errors_tab_frame = None
            
        if hasattr(self, 'summary_tab_frame') and self.summary_tab_frame:
            self.notebook.forget(self.summary_tab_frame)
            self.summary_tab_frame = None
        
        # Hide Apply All button
        if hasattr(self, 'apply_all_button'):
            self.apply_all_button.pack_forget()
        
        self.analysis_text_widget.config(state="normal")
        self.analysis_text_widget.delete("1.0", "end")
        self.analysis_text_widget.insert("1.0", "Ready to analyze...")
        self.analysis_text_widget.config(state="disabled")
        
        self.analyze_button.config(state="normal", text="Start Analysis")
        self.status_indicator.config(text="Ready", foreground=self.colors['muted'])
        
        # Start new analysis
        self._start_proofreading()
    
    def _go_previous(self):
        """Go to previous error."""
        if not self._is_window_valid():
            return
        if self.session and self.session.go_to_previous_error():
            self._update_error_navigation()
    
    def _go_next(self):
        """Go to next error."""
        if not self._is_window_valid():
            return
        if self.session and self.session.go_to_next_error():
            self._update_error_navigation()
    
    def _approve_current_correction(self):
        """Approve current correction for later application."""
        if not self._is_window_valid() or not self.session:
            return
            
        try:
            if self.session.approve_current_correction():
                self._update_error_navigation()
                # Auto-advance to next error
                if self._is_window_valid():
                    self.window.after(500, self._go_next)
        except tk.TclError:
            pass
    
    def _reject_current_correction(self):
        """Reject current correction."""
        if not self._is_window_valid() or not self.session:
            return
            
        try:
            if self.session.reject_current_correction():
                self._update_error_navigation()
                # Auto-advance to next error
                if self._is_window_valid():
                    self.window.after(500, self._go_next)
        except tk.TclError:
            pass
    
    def _apply_current_correction(self):
        """Apply current correction immediately (only if approved)."""
        if not self._is_window_valid() or not self.session:
            return
            
        current_error = self.session.get_current_error()
        if not current_error or not current_error.is_approved:
            messagebox.showwarning("Not Approved", "Please approve this correction before applying it.", parent=self.window)
            return
            
        try:
            if self.session.apply_current_correction(self.editor):
                self.applied_label.config(text=f"Correction applied!", foreground=self.colors['success'])
                self.apply_button.config(state="disabled", text="Applied")
                
                # Auto-advance to next error
                if self._is_window_valid():
                    self.window.after(1000, self._go_next)
            else:
                if self._is_window_valid():
                    messagebox.showwarning("Application Failed", 
                        "Could not apply the correction. The original text may have been modified.",
                        parent=self.window)
        except tk.TclError:
            pass
    
    def _update_error_navigation(self):
        """Update error navigation."""
        if not self._is_window_valid() or not self.session or not self.session.errors:
            return
        
        try:
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
            
            # Update error details
            error_color = self.colors.get(f'{current_error.type}_color', self.colors['primary'])
            self.error_type_label.config(text=current_error.type.title(), foreground=error_color)
            
            # Update text widgets
            self.original_error_text.config(state="normal")
            self.original_error_text.delete("1.0", "end")
            self.original_error_text.insert("1.0", current_error.original)
            self.original_error_text.config(state="disabled")
            
            self.suggested_text.config(state="normal")
            self.suggested_text.delete("1.0", "end")
            suggestion_text = current_error.suggestion if current_error.suggestion else "[DELETE]"
            self.suggested_text.insert("1.0", suggestion_text)
            self.suggested_text.config(state="disabled")
            
            self.explanation_label.config(text=current_error.explanation)
            
            self.context_text.config(state="normal")
            self.context_text.delete("1.0", "end")
            self.context_text.insert("1.0", current_error.context)
            
            # Highlight the original error text in the context
            if current_error.original and current_error.original in current_error.context:
                # Find the position of the error in the context
                start_pos = current_error.context.find(current_error.original)
                if start_pos != -1:
                    # Calculate Text widget positions
                    lines_before = current_error.context[:start_pos].count('\n')
                    char_pos = len(current_error.context[:start_pos].split('\n')[-1])
                    
                    start_index = f"{lines_before + 1}.{char_pos}"
                    end_index = f"{lines_before + 1}.{char_pos + len(current_error.original)}"
                    
                    # Configure error highlight tag if not exists
                    self.context_text.tag_configure("error_highlight", 
                                                   background="#ffcccc", 
                                                   foreground="#990000")
                    
                    # Apply highlight
                    self.context_text.tag_add("error_highlight", start_index, end_index)
            
            self.context_text.config(state="disabled")
            
            # Update button states based on approval and application status
            if current_error.is_applied:
                # Already applied
                self.approve_button.config(state="disabled", text="Applied")
                self.reject_button.config(state="disabled")
                self.apply_button.config(state="disabled", text="Applied")
                status_color = self.colors['success']
                status_text = "Already applied"
            elif current_error.is_approved:
                # Approved but not applied
                self.approve_button.config(state="disabled", text="Approved")
                self.reject_button.config(state="normal", text="Reject")
                self.apply_button.config(state="normal", text="Apply Now")
                status_color = self.colors['primary']
                status_text = "Approved - ready to apply"
            else:
                # Not approved yet
                self.approve_button.config(state="normal", text="Approve")
                self.reject_button.config(state="normal", text="Reject") 
                self.apply_button.config(state="disabled", text="Apply Now")
                status_color = self.colors['muted']
                status_text = "Pending approval"
            
            # Update status display
            approved_count = self.session.get_approved_corrections_count()
            applied_count = self.session.get_applied_corrections_count()
            
            if applied_count > 0 or approved_count > 0:
                status_parts = []
                if approved_count > 0:
                    status_parts.append(f"{approved_count} approved")
                if applied_count > 0:
                    status_parts.append(f"{applied_count} applied")
                status_text = f"{', '.join(status_parts)} of {total}"
            
            self.applied_label.config(text=status_text, foreground=status_color)
            
            # Update Apply All button
            self._update_apply_all_button()
            
        except tk.TclError:
            pass
    
    def _update_apply_all_button(self):
        """Update Apply All button visibility and text."""
        if not self._is_window_valid():
            return
            
        try:
            if not self.session or not self.session.errors:
                if hasattr(self, 'apply_all_button'):
                    self.apply_all_button.pack_forget()
                return
            
            # Count approved but unapplied corrections
            approved_unapplied = len([e for e in self.session.errors if e.is_approved and not e.is_applied])
            
            if approved_unapplied > 0:
                # Show button with approved count
                button_text = f"Apply All {approved_unapplied} Approved Corrections & Save"
                self.apply_all_button.config(text=button_text, state="normal")
                if not self.apply_all_button.winfo_viewable():
                    self.apply_all_button.pack(side="left", padx=(0, 10))
            else:
                # Check if there are any approved corrections (all applied)
                approved_count = self.session.get_approved_corrections_count()
                applied_count = self.session.get_applied_corrections_count()
                
                if approved_count > 0 and approved_count == applied_count:
                    # All approved corrections have been applied
                    self.apply_all_button.config(text="All Approved Corrections Applied", state="disabled")
                else:
                    # No approved corrections yet
                    if hasattr(self, 'apply_all_button'):
                        self.apply_all_button.pack_forget()
        except tk.TclError:
            pass
    
    def _is_window_valid(self) -> bool:
        """Check if the window and widgets are still valid."""
        try:
            return self.window and self.window.winfo_exists()
        except tk.TclError:
            return False
    
    # Callback handlers
    def _on_status_change(self, status: str):
        """Handle status change."""
        if not self._is_window_valid():
            return
            
        try:
            if "found" in status.lower():
                # Analysis complete
                self.analyze_button.config(state="normal", text="Restart Analysis")
                self.status_indicator.config(text="Analysis complete", foreground=self.colors['success'])
        except tk.TclError:
            pass
    
    def _on_progress_change(self, progress: str):
        """Handle progress change."""
        if not self._is_window_valid():
            return
            
        try:
            self.progress_var.set(progress)
            # Also update analysis text widget with status
            self.analysis_text_widget.config(state="normal")
            self.analysis_text_widget.delete("1.0", "end")
            self.analysis_text_widget.insert("1.0", progress)
            self.analysis_text_widget.config(state="disabled")
        except tk.TclError:
            pass
    
    
    def _on_errors_found(self, errors: List[ProofreadingError]):
        """Handle errors found."""
        if not self._is_window_valid():
            return
            
        try:
            if errors:
                self._create_error_navigation_tab(errors)
                # Show Apply All button when errors are found
                self.apply_all_button.pack(side="left", padx=(0, 10))
            
            self._create_summary_tab()
            
        except tk.TclError:
            pass
    
    def _on_analysis_error(self, error_msg: str):
        """Handle analysis error."""
        if not self._is_window_valid():
            return
            
        try:
            self.analyze_button.config(state="normal", text="Retry Analysis")
            self.status_indicator.config(text="Analysis failed", foreground=self.colors['danger'])
            
            messagebox.showerror("Analysis Error", error_msg, parent=self.window)
        except tk.TclError:
            pass
    
    # Utility methods
    def _get_error_stats_text(self, errors: List[ProofreadingError]) -> str:
        """Generate error statistics."""
        if not errors:
            return "No errors found"
        
        stats = {}
        for error in errors:
            error_type = error.type
            stats[error_type] = stats.get(error_type, 0) + 1
        
        stats_parts = [f"{count} {error_type}" for error_type, count in stats.items()]
        return " • ".join(stats_parts)
    
    def _generate_summary_text(self) -> str:
        """Generate summary text."""
        if not self.session or not self.session.errors:
            return "No errors detected! Your text looks great."
        
        total = len(self.session.errors)
        applied = self.session.get_applied_corrections_count()
        
        summary = f"Analysis Results\n\n"
        summary += f"Total errors found: {total}\n"
        summary += f"Corrections applied: {applied}\n"
        summary += f"Remaining errors: {total - applied}\n\n"
        
        if applied == total:
            summary += "Excellent! All errors have been corrected."
        elif applied > 0:
            summary += f"Great progress! {applied} corrections applied."
        else:
            summary += "Review the errors and apply corrections as needed."
        
        return summary
    
    def _apply_all_corrections(self):
        """Apply all corrections and save to corrected file."""
        if not self._is_window_valid() or not self.session or not self.session.errors:
            return
        
        # Use dedicated applier module
        from llm.proofreading_apply import apply_all_corrections
        
        success, corrected_filepath = apply_all_corrections(
            self.session.errors,
            self.initial_text,
            parent_window=self.window if self._is_window_valid() else None
        )
        
        if success and self._is_window_valid():
            # Update UI to reflect applied corrections
            self._update_error_navigation()
            self._update_apply_all_button()
    
    def _browse_history(self):
        """Browse proofreading history for current document."""
        try:
            try:
                current_filepath = state.get_active_filepath()
            except:
                current_filepath = None
            
            if not current_filepath:
                messagebox.showinfo("No File", "Please save your document first to browse proofreading history.", parent=self.window)
                return
            
            # Get cached sessions
            sessions = list_cached_sessions(current_filepath)
            
            if not sessions:
                messagebox.showinfo("No History", "No proofreading history found for this document.", parent=self.window)
                return
            
            # Sort sessions by date (newest first)
            sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Create history dialog
            self._show_history_dialog(sessions)
            
        except Exception as e:
                messagebox.showerror("Error", f"Failed to browse history: {str(e)}", parent=self.window)
    
    def _show_history_dialog(self, sessions: List[dict]):
        """Show history browsing dialog."""
        history_window = tk.Toplevel(self.window)
        history_window.title("Proofreading History")
        history_window.geometry("700x500")
        history_window.transient(self.window)
        history_window.grab_set()
        
        # Main container
        main_frame = ttk.Frame(history_window, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_label = ttk.Label(main_frame, text="Proofreading History", font=("TkDefaultFont", 12, "bold"))
        header_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # Sessions list with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview for sessions
        columns = ("date", "errors", "applied", "status")
        sessions_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        sessions_tree.heading("date", text="Date & Time")
        sessions_tree.heading("errors", text="Errors Found")
        sessions_tree.heading("applied", text="Applied")
        sessions_tree.heading("status", text="Status")
        
        sessions_tree.column("date", width=200)
        sessions_tree.column("errors", width=100)
        sessions_tree.column("applied", width=100)
        sessions_tree.column("status", width=100)
        
        sessions_tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=sessions_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        sessions_tree.configure(yscrollcommand=scrollbar.set)
        
        # Populate sessions
        session_data = {}
        for session in sessions:
            date_str = session.get('created_at', 'Unknown')
            # Format date for display
            if date_str != 'Unknown':
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_display = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    date_display = date_str
            else:
                date_display = date_str
            
            errors_found = session.get('total_errors', 0)
            errors_applied = session.get('applied_errors', 0)
            status = "Complete" if errors_applied == errors_found else "Partial"
            
            item_id = sessions_tree.insert("", "end", values=(date_display, errors_found, errors_applied, status))
            session_data[item_id] = session
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, sticky="ew")
        
        def load_selected_session():
            selection = sessions_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a session to load.", parent=history_window)
                return
            
            selected_session_data = session_data[selection[0]]
            session_file = selected_session_data['file']
            
            try:
                # Load session from cache
                loaded_session = load_session_from_cache(session_file)
                if loaded_session:
                    # Replace current session
                    self.session = loaded_session
                    
                    # Update UI
                    self.progress_var.set("Loaded from history")
                    self._create_error_navigation_tab(self.session.errors)
                    self._update_error_navigation()
                    self._update_apply_all_button()
                    
                    history_window.destroy()
                else:
                    messagebox.showerror("Load Error", "Failed to load selected session.", parent=history_window)
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load session: {str(e)}", parent=history_window)
        
        def delete_selected_session():
            selection = sessions_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a session to delete.", parent=history_window)
                return
            
            selected_session_data = session_data[selection[0]]
            session_file = selected_session_data['file']
            
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this session?", parent=history_window):
                try:
                    import os
                    os.remove(session_file)
                    sessions_tree.delete(selection[0])
                except Exception as e:
                    messagebox.showerror("Delete Error", f"Failed to delete session: {str(e)}", parent=history_window)
        
        ttk.Button(buttons_frame, text="Load Selected", command=load_selected_session).pack(side="left", padx=(0, 10))
        ttk.Button(buttons_frame, text="Delete Selected", command=delete_selected_session).pack(side="left", padx=(0, 10))
        ttk.Button(buttons_frame, text="Close", command=history_window.destroy).pack(side="right")
        
        # Focus on first session if any
        if sessions_tree.get_children():
            first_item = sessions_tree.get_children()[0]
            sessions_tree.selection_set(first_item)
            sessions_tree.focus(first_item)
    
    def _on_close(self):
        """Handle dialog close."""
        if self.session and self.session.is_processing:
            if messagebox.askyesno("Analysis in Progress", 
                                 "Analysis is still running. Are you sure you want to close?"):
                self.window.destroy()
        else:
            self.window.destroy()