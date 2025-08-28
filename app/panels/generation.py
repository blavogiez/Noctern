"""
Integrated generation panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import logs_console
from typing import List, Tuple, Callable, Optional


class GenerationPanel(BasePanel):
    """
    Integrated text generation panel that replaces the dialog window.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter,
                 prompt_history: List[Tuple[str, str]], 
                 on_generate_callback: Callable,
                 on_history_add_callback: Callable,
                 initial_prompt: str = None,
                 on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        self.prompt_history = prompt_history or []
        self.on_generate_callback = on_generate_callback
        self.on_history_add_callback = on_history_add_callback
        self.initial_prompt = initial_prompt
        
        # UI components
        self.prompt_text_widget: Optional[tk.Text] = None
        self.response_text_widget: Optional[tk.Text] = None
        self.history_listbox: Optional[tk.Listbox] = None
        self.lines_before_entry: Optional[tk.Entry] = None
        self.lines_after_entry: Optional[tk.Entry] = None
        self.latex_mode_var: Optional[tk.BooleanVar] = None
        self.math_mode_var: Optional[tk.BooleanVar] = None
        self.generate_button: Optional[tk.Button] = None
        
    def get_panel_title(self) -> str:
        return "Text Generation"
    
    def get_layout_style(self) -> PanelStyle:
        """Use split layout for history and input sections."""
        return PanelStyle.SPLIT
        
    def create_content(self):
        """Create the generation panel content using standardized components."""
        # main_container is a PanedWindow for split layout
        paned_window = self.main_container
        
        # History section (top)
        self._create_history_section(paned_window)
        
        # Input and controls section (bottom)
        self._create_input_section(paned_window)
        
    def _create_history_section(self, parent):
        """Create the history section."""
        history_frame = ttk.Frame(parent)
        parent.add(history_frame, weight=1)
        
        # History section using standardized components
        history_section = StandardComponents.create_section(history_frame, "Prompt History")
        history_section.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Description
        desc_label = StandardComponents.create_info_label(
            history_section,
            "Select a previous prompt to reuse or view results:",
            "small"
        )
        desc_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        # History listbox with standardized styling
        listbox_frame = ttk.Frame(history_section)
        listbox_frame.pack(fill="both", expand=True)
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)
        
        self.history_listbox = tk.Listbox(
            listbox_frame,
            height=6,
            exportselection=False,
            font=StandardComponents.BODY_FONT,
            bg=self.get_theme_color("treeview_bg", "#ffffff"),
            fg=self.get_theme_color("editor_fg", "#000000"),
            selectbackground=self.get_theme_color("sel_bg", "#0078d4"),
            selectforeground=self.get_theme_color("sel_fg", "#ffffff"),
            relief="solid",
            borderwidth=1
        )
        self.history_listbox.grid(row=0, column=0, sticky="nsew")
        
        # History scrollbar
        history_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.history_listbox.yview)
        history_scrollbar.grid(row=0, column=1, sticky="ns")
        self.history_listbox.config(yscrollcommand=history_scrollbar.set)
        
        # Populate history
        self._populate_history()
        
        # Bind selection event
        self.history_listbox.bind("<<ListboxSelect>>", self._on_history_selected)
        
    def _create_input_section(self, parent):
        """Create the input and controls section."""
        input_frame = ttk.Frame(parent)
        parent.add(input_frame, weight=2)
        
        # Main scrollable content
        main_frame = ttk.Frame(input_frame, padding=StandardComponents.PADDING)
        main_frame.pack(fill="both", expand=True)
        
        # Prompt input section
        prompt_section = StandardComponents.create_section(main_frame, "Your Prompt")
        prompt_section.pack(fill="both", expand=True, pady=(0, StandardComponents.SECTION_SPACING))
        
        # Prompt text area
        self.prompt_text_widget = StandardComponents.create_text_input(
            prompt_section,
            "Enter your prompt here...",
            height=8
        )
        self.prompt_text_widget.pack(fill="both", expand=True, pady=(0, StandardComponents.PADDING))
        
        # Set as main widget for focus
        self.main_widget = self.prompt_text_widget
        
        # Pre-fill with initial prompt if provided
        if self.initial_prompt:
            self.prompt_text_widget.delete("1.0", "end")
            self.prompt_text_widget.insert("1.0", self.initial_prompt)
        
        # Context options section
        context_section = StandardComponents.create_section(main_frame, "Context Options")
        context_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Context controls in a grid
        context_controls = ttk.Frame(context_section)
        context_controls.pack(fill="x")
        context_controls.grid_columnconfigure(1, weight=1)
        context_controls.grid_columnconfigure(3, weight=1)
        
        lines_before_label = StandardComponents.create_info_label(
            context_controls, "Lines before cursor:", "body"
        )
        lines_before_label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.lines_before_entry = StandardComponents.create_entry_input(
            context_controls, "5"
        )
        self.lines_before_entry.delete(0, "end")
        self.lines_before_entry.insert(0, "5")
        self.lines_before_entry.grid(row=0, column=1, sticky="ew", padx=(0, 15))
        
        lines_after_label = StandardComponents.create_info_label(
            context_controls, "Lines after cursor:", "body"
        )
        lines_after_label.grid(row=0, column=2, sticky="w", padx=(0, 5))
        
        self.lines_after_entry = StandardComponents.create_entry_input(
            context_controls, "0"
        )
        self.lines_after_entry.delete(0, "end")
        self.lines_after_entry.insert(0, "0")
        self.lines_after_entry.grid(row=0, column=3, sticky="ew")
        
        # Options section
        options_section = StandardComponents.create_section(main_frame, "Generation Options")
        options_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        self.latex_mode_var = tk.BooleanVar()
        latex_checkbox = ttk.Checkbutton(
            options_section,
            text="LaTeX oriented generation",
            variable=self.latex_mode_var,
            command=self._on_latex_mode_changed
        )
        latex_checkbox.pack(anchor="w")
        
        self.math_mode_var = tk.BooleanVar()
        math_checkbox = ttk.Checkbutton(
            options_section,
            text="Math mode (mathematical LaTeX)",
            variable=self.math_mode_var,
            command=self._on_math_mode_changed
        )
        math_checkbox.pack(anchor="w", pady=(StandardComponents.PADDING//2, 0))
        
        # Generate button
        generate_buttons = [(
            "Generate (Ctrl+Enter)", 
            self._handle_generate, 
            "primary"
        )]
        generate_row = StandardComponents.create_button_row(main_frame, generate_buttons)
        generate_row.pack(fill="x", pady=(StandardComponents.SECTION_SPACING, 0))
        self.generate_button = generate_row.winfo_children()[0]  # Get button reference
        
        # Response display (initially hidden)
        self.response_section = StandardComponents.create_section(main_frame, "Response")
        # Don't pack initially - will be shown when response arrives
        
        self.response_text_widget = StandardComponents.create_text_input(
            self.response_section,
            "Response will appear here...",
            height=8
        )
        self.response_text_widget.pack(fill="both", expand=True)
        self.response_text_widget.config(state="disabled")
        
        # Bind keyboard shortcut
        self.prompt_text_widget.bind("<Control-Return>", lambda e: self._handle_generate())
        
    def _populate_history(self):
        """Populate the history listbox."""
        if not self.prompt_history:
            self.history_listbox.insert(tk.END, "No history yet.")
            self.history_listbox.config(state=tk.DISABLED)
        else:
            for user_prompt, _ in self.prompt_history:
                display_text = f"Q: {user_prompt[:60]}{'...' if len(user_prompt) > 60 else ''}"
                self.history_listbox.insert(tk.END, display_text)
    
    def _on_history_selected(self, event):
        """Handle history item selection."""
        selection_indices = event.widget.curselection()
        if not selection_indices or not self.prompt_history:
            return
            
        selected_index = selection_indices[0]
        
        # Ensure valid index
        if not (0 <= selected_index < len(self.prompt_history)):
            return
            
        selected_prompt, selected_response = self.prompt_history[selected_index]
        
        # Populate prompt text area
        self.prompt_text_widget.delete("1.0", tk.END)
        self.prompt_text_widget.insert("1.0", selected_prompt)
        
        # Show and populate response area
        self._show_response_area()
        self.response_text_widget.config(state="normal")
        self.response_text_widget.delete("1.0", "end")
        self.response_text_widget.insert("1.0", selected_response)
        self.response_text_widget.config(state="disabled")
    
    def _show_response_area(self):
        """Show the response area."""
        self.response_section.pack(fill="both", expand=True, pady=(StandardComponents.SECTION_SPACING, 0))
    
    def _handle_generate(self):
        """Handle generate button click."""
        prompt_text = self.prompt_text_widget.get("1.0", tk.END).strip()
        
        if not prompt_text:
            messagebox.showwarning("Warning", "The prompt text area is empty. Please enter a prompt.", parent=self.panel_frame)
            return
            
        try:
            lines_before = int(self.lines_before_entry.get())
            lines_after = int(self.lines_after_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "Line counts must be valid integers.", parent=self.panel_frame)
            return
        
        latex_mode = self.latex_mode_var.get()
        math_mode = self.math_mode_var.get()
        
        logs_console.log(f"Generate request: '{prompt_text[:50]}...', LaTeX: {latex_mode}, Math: {math_mode}", level='ACTION')
        
        # Add to history
        if self.on_history_add_callback:
            self.on_history_add_callback(prompt_text)
        
        # Call generation callback
        if self.on_generate_callback:
            self.on_generate_callback(prompt_text, lines_before, lines_after, latex_mode, math_mode)
        
        # Close panel after generating
        self._handle_close()
    
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.prompt_text_widget:
            self.prompt_text_widget.focus_set()
    
    def _on_latex_mode_changed(self):
        """Handle LaTeX mode checkbox change - ensure mutual exclusion."""
        if self.latex_mode_var.get() and self.math_mode_var.get():
            self.math_mode_var.set(False)
    
    def _on_math_mode_changed(self):
        """Handle Math mode checkbox change - ensure mutual exclusion."""
        if self.math_mode_var.get() and self.latex_mode_var.get():
            self.latex_mode_var.set(False)