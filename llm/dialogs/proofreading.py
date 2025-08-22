"""
Professional proofreading user interface with modern UX.
Beautiful, intuitive dialog for AI-powered document correction.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List

from utils import debug_console
from llm.proofreading_service import get_proofreading_service, ProofreadingSession, ProofreadingError


class ProofreadingDialog:
    """
    Professional document proofreading interface.
    
    Features:
    - Maximized window for optimal user experience  
    - Real-time AI analysis with streaming feedback
    - Intuitive error navigation and correction
    - Beautiful modern UI with animations
    - Clear progress indicators and status updates
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
        self.status_var = tk.StringVar(value="Ready to start proofreading")
        self.progress_var = tk.StringVar(value="")
        self.current_error_var = tk.StringVar(value="")
        self.error_counter_var = tk.StringVar(value="")
        
        # Theme colors
        self._load_theme_colors()
    
    def _load_theme_colors(self):
        """Load minimal color palette."""
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
            'syntax_color': "#990000"
        }
    
    def show(self):
        """Display the proofreading dialog."""
        self._create_window()
        self._setup_layout()
        self._bind_events()
        
        # Show window and center focus
        self.window.deiconify()
        self.window.focus_force()
        self.window.wait_window()
    
    def _create_window(self):
        """Create and configure the main window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Professional Document Proofreading")
        self.window.configure(bg=self.colors['bg'])
        
        # Maximize window for optimal experience
        self.window.state('zoomed')
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Prevent window from being destroyed accidentally
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        debug_console.log("Professional proofreading interface created", level='INFO')
    
    def _setup_layout(self):
        """Create the beautiful, professional UI layout."""
        # Main container with padding
        main_container = ttk.Frame(self.window, padding="30")
        main_container.pack(fill="both", expand=True)
        main_container.grid_rowconfigure(2, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Header section with title and status
        self._create_header(main_container)
        
        # Progress section with visual indicators
        self._create_progress_section(main_container)
        
        # Main content area with tabs
        self._create_content_area(main_container)
        
        # Footer with action buttons
        self._create_footer(main_container)
    
    def _create_header(self, parent):
        """Create professional header with branding."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title with icon
        title_frame = ttk.Frame(header_frame)
        title_frame.grid(row=0, column=0, sticky="w")
        
        title_label = ttk.Label(
            title_frame, 
            text="Document Proofreading",
            font=("Segoe UI", 16),
            foreground=self.colors['primary']
        )
        title_label.pack(side="left")
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Grammar and style checker",
            foreground=self.colors['muted']
        )
        subtitle_label.pack(side="left", padx=(10, 0))
        
        # Status display
        status_frame = ttk.Frame(header_frame)
        status_frame.grid(row=0, column=1, sticky="e")
        
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            foreground=self.colors['primary']
        )
        self.status_label.pack(anchor="e")
    
    def _create_progress_section(self, parent):
        """Create progress indicators and controls."""
        progress_frame = ttk.LabelFrame(parent, text=" Analysis Progress ", padding="15")
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
        
        # Custom instructions
        ttk.Label(progress_frame, text="Instructions:").grid(row=2, column=0, sticky="w", pady=(10, 5))
        
        self.instructions_entry = ttk.Entry(
            progress_frame, 
            width=40
        )
        self.instructions_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        # Start/Restart button
        self.analyze_button = ttk.Button(
            progress_frame,
            text="Start Analysis",
            style="Accent.TButton",
            command=self._start_proofreading
        )
        self.analyze_button.grid(row=3, column=2, sticky="e", padx=(10, 0))
    
    def _create_content_area(self, parent):
        """Create main content area with tabs."""
        # Notebook for organized content
        self.notebook = ttk.Notebook(parent, padding="5")
        self.notebook.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        
        # Text Analysis Tab
        self._create_text_analysis_tab()
        
        # Error Navigation Tab (initially hidden)
        self.errors_tab_frame = None
        
        # Results Summary Tab (initially hidden)  
        self.summary_tab_frame = None
    
    def _create_text_analysis_tab(self):
        """Create text analysis tab with streaming output."""
        analysis_frame = ttk.Frame(self.notebook, padding="15")
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
        """Create error navigation tab with beautiful error display."""
        if self.errors_tab_frame:
            self.notebook.forget(self.errors_tab_frame)
        
        self.errors_tab_frame = ttk.Frame(self.notebook, padding="15")
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
            command=self._go_previous,
            style="Outline.TButton"
        )
        self.prev_button.grid(row=0, column=0, padx=(0, 10))
        
        self.next_button = ttk.Button(
            nav_header,
            text="Next",
            command=self._go_next,
            style="Outline.TButton"
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
        """Create beautiful error display section."""
        # Error details frame
        details_frame = ttk.LabelFrame(parent, text=" Error Details ", padding="20")
        details_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        details_frame.grid_columnconfigure(1, weight=1)
        
        # Error type with colored badge
        ttk.Label(details_frame, text="Type:").grid(row=0, column=0, sticky="nw", padx=(0, 10))
        self.error_type_label = ttk.Label(details_frame, text="")
        self.error_type_label.grid(row=0, column=1, sticky="w")
        
        # Original text (highlighted)
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
        
        self.apply_button = ttk.Button(
            action_frame,
            text="Apply Correction",
            command=self._apply_current_correction,
            style="Accent.TButton"
        )
        self.apply_button.pack(side="left", padx=(0, 10))
        
        self.skip_button = ttk.Button(
            action_frame,
            text="Skip This Error",
            command=self._go_next,
            style="Outline.TButton"
        )
        self.skip_button.pack(side="left", padx=(0, 10))
        
        # Progress info
        applied_label = ttk.Label(
            action_frame,
            text="",
            foreground=self.colors['success']
        )
        applied_label.pack(side="right")
        self.applied_label = applied_label
    
    def _create_summary_tab(self):
        """Create results summary tab."""
        if self.summary_tab_frame:
            self.notebook.forget(self.summary_tab_frame)
        
        self.summary_tab_frame = ttk.Frame(self.notebook, padding="20")
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
        """Create footer with action buttons."""
        footer_frame = ttk.Frame(parent)
        footer_frame.grid(row=3, column=0, sticky="ew")
        
        ttk.Button(
            footer_frame,
            text="Close",
            command=self._on_close,
            style="Outline.TButton"
        ).pack(side="right")
        
        ttk.Button(
            footer_frame,
            text="Restart Analysis", 
            command=self._restart_analysis,
            style="Outline.TButton"
        ).pack(side="right", padx=(0, 10))
    
    def _bind_events(self):
        """Bind keyboard shortcuts and events."""
        self.window.bind("<Escape>", lambda e: self._on_close())
        self.window.bind("<F5>", lambda e: self._restart_analysis())
        self.window.bind("<Left>", lambda e: self._go_previous())
        self.window.bind("<Right>", lambda e: self._go_next())
        self.window.bind("<Return>", lambda e: self._apply_current_correction())
    
    # Event Handlers
    def _start_proofreading(self):
        """Start AI-powered proofreading analysis."""
        if self.session and self.session.is_processing:
            return
        
        custom_instructions = self.instructions_entry.get().strip()
        
        # Create new session
        self.session = self.proofreading_service.start_proofreading_session(
            self.initial_text, 
            custom_instructions
        )
        
        # Setup callbacks
        self.session.on_status_change = self._on_status_change
        self.session.on_progress_change = self._on_progress_change  
        self.session.on_chunk_received = self._on_chunk_received
        self.session.on_errors_found = self._on_errors_found
        self.session.on_error = self._on_analysis_error
        
        # Update UI
        self.analyze_button.config(state="disabled", text="Analyzing...")
        self.status_indicator.config(text="Analyzing...", foreground=self.colors['primary'])
        
        # Start analysis
        self.proofreading_service.analyze_text(self.session, self.editor)
        
        debug_console.log("Proofreading analysis started", level='INFO')
    
    def _restart_analysis(self):
        """Restart the proofreading analysis."""
        # Reset UI
        if hasattr(self, 'errors_tab_frame') and self.errors_tab_frame:
            self.notebook.forget(self.errors_tab_frame)
            self.errors_tab_frame = None
            
        if hasattr(self, 'summary_tab_frame') and self.summary_tab_frame:
            self.notebook.forget(self.summary_tab_frame)
            self.summary_tab_frame = None
        
        self.analysis_text_widget.config(state="normal")
        self.analysis_text_widget.delete("1.0", "end")
        self.analysis_text_widget.config(state="disabled")
        
        self.analyze_button.config(state="normal", text="Start Analysis")
        self.status_indicator.config(text="Ready", foreground=self.colors['muted'])
        
        # Start new analysis
        self._start_proofreading()
    
    def _go_previous(self):
        """Navigate to previous error."""
        if self.session and self.session.go_to_previous_error():
            self._update_error_navigation()
    
    def _go_next(self):
        """Navigate to next error."""
        if self.session and self.session.go_to_next_error():
            self._update_error_navigation()
    
    def _apply_current_correction(self):
        """Apply current error's correction."""
        if not self.session:
            return
            
        if self.session.apply_current_correction(self.editor):
            self.applied_label.config(text=f"Correction applied!", foreground=self.colors['success'])
            self.apply_button.config(state="disabled", text="Applied")
            
            # Auto-advance to next error
            self.window.after(1000, self._go_next)
        else:
            messagebox.showwarning("Application Failed", 
                "Could not apply the correction. The original text may have been modified.")
    
    def _update_error_navigation(self):
        """Update error navigation UI."""
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
        
        # Update error details with color coding
        error_color = self.colors.get(f'{current_error.type.value}_color', self.colors['primary'])
        self.error_type_label.config(text=current_error.type.value.title(), foreground=error_color)
        
        # Update text widgets
        self.original_error_text.config(state="normal")
        self.original_error_text.delete("1.0", "end")
        self.original_error_text.insert("1.0", current_error.original)
        self.original_error_text.config(state="disabled")
        
        self.suggested_text.config(state="normal")
        self.suggested_text.delete("1.0", "end")
        self.suggested_text.insert("1.0", current_error.suggestion)
        self.suggested_text.config(state="disabled")
        
        self.explanation_label.config(text=current_error.explanation)
        
        self.context_text.config(state="normal")
        self.context_text.delete("1.0", "end")
        self.context_text.insert("1.0", current_error.context)
        self.context_text.config(state="disabled")
        
        # Update apply button
        if current_error.is_applied:
            self.apply_button.config(state="disabled", text="Applied")
            self.applied_label.config(text="Already applied", foreground=self.colors['success'])
        else:
            self.apply_button.config(state="normal", text="Apply Correction")
            self.applied_label.config(text="")
        
        # Update applied corrections count
        applied_count = self.session.get_applied_corrections_count()
        if applied_count > 0:
            self.applied_label.config(text=f"{applied_count}/{total} corrections applied", foreground=self.colors['success'])
    
    # Callback handlers
    def _on_status_change(self, status: str):
        """Handle status updates."""
        self.status_var.set(status)
        
        if "found" in status.lower():
            # Analysis complete
            self.analyze_button.config(state="normal", text="Restart Analysis")
            self.status_indicator.config(text="Analysis complete", foreground=self.colors['success'])
    
    def _on_progress_change(self, progress: str):
        """Handle progress updates.""" 
        self.progress_var.set(progress)
    
    def _on_chunk_received(self, chunk: str):
        """Handle streaming text chunks."""
        self.analysis_text_widget.config(state="normal")
        self.analysis_text_widget.delete("1.0", "end")
        self.analysis_text_widget.insert("1.0", chunk)
        self.analysis_text_widget.see("end")
        self.analysis_text_widget.config(state="disabled")
    
    def _on_errors_found(self, errors: List[ProofreadingError]):
        """Handle when errors are found."""
        if errors:
            self._create_error_navigation_tab(errors)
        
        self._create_summary_tab()
        
        debug_console.log(f"Proofreading UI updated with {len(errors)} errors", level='INFO')
    
    def _on_analysis_error(self, error_msg: str):
        """Handle analysis errors."""
        self.analyze_button.config(state="normal", text="Retry Analysis")
        self.status_indicator.config(text="Analysis failed", foreground=self.colors['danger'])
        
        messagebox.showerror("Analysis Error", error_msg)
    
    # Utility methods
    def _get_error_stats_text(self, errors: List[ProofreadingError]) -> str:
        """Generate error statistics text."""
        if not errors:
            return "No errors found"
        
        stats = {}
        for error in errors:
            error_type = error.type.value
            stats[error_type] = stats.get(error_type, 0) + 1
        
        stats_parts = [f"{count} {error_type}" for error_type, count in stats.items()]
        return " • ".join(stats_parts)
    
    def _generate_summary_text(self) -> str:
        """Generate summary text for results."""
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
    
    def _on_close(self):
        """Handle dialog close."""
        if self.session and self.session.is_processing:
            if messagebox.askyesno("Analysis in Progress", 
                                 "Analysis is still running. Are you sure you want to close?"):
                self.window.destroy()
        else:
            self.window.destroy()