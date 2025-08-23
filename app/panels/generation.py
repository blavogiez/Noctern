"""
Integrated generation panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .base_panel import BasePanel
from utils import debug_console
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
        self.generate_button: Optional[tk.Button] = None
        
    def get_panel_title(self) -> str:
        return "AI Text Generation"
    
    def create_content(self):
        """Create the generation panel content."""
        # Create main paned window for history and input
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.VERTICAL)
        main_pane.pack(fill="both", expand=True)
        
        # History section (top)
        self._create_history_section(main_pane)
        
        # Input and controls section (bottom)
        self._create_input_section(main_pane)
        
    def _create_history_section(self, parent):
        """Create the history section."""
        history_frame = ttk.LabelFrame(parent, text=" Prompt History ", padding="5")
        
        # History listbox
        listbox_frame = ttk.Frame(history_frame)
        listbox_frame.pack(fill="both", expand=True)
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)
        
        self.history_listbox = tk.Listbox(
            listbox_frame,
            height=6,
            exportselection=False,
            font=("Segoe UI", 9),
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
        
        parent.add(history_frame, weight=1, minsize=120)
        
    def _create_input_section(self, parent):
        """Create the input and controls section."""
        input_frame = ttk.Frame(parent)
        input_frame.grid_rowconfigure(1, weight=1)  # Prompt text area
        input_frame.grid_rowconfigure(5, weight=0)  # Response area (initially small)
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Prompt input
        ttk.Label(input_frame, text="Your Prompt:").grid(row=0, column=0, sticky="w", pady=(5, 5))
        
        prompt_frame = ttk.Frame(input_frame)
        prompt_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        prompt_frame.grid_rowconfigure(0, weight=1)
        prompt_frame.grid_columnconfigure(0, weight=1)
        
        self.prompt_text_widget = tk.Text(
            prompt_frame,
            height=8,
            wrap="word",
            font=("Segoe UI", 10),
            bg=self.get_theme_color("editor_bg", "#ffffff"),
            fg=self.get_theme_color("editor_fg", "#000000"),
            selectbackground=self.get_theme_color("sel_bg", "#0078d4"),
            selectforeground=self.get_theme_color("sel_fg", "#ffffff"),
            insertbackground=self.get_theme_color("editor_insert_bg", "#000000"),
            relief="solid",
            borderwidth=1
        )
        self.prompt_text_widget.grid(row=0, column=0, sticky="nsew")
        
        prompt_scrollbar = ttk.Scrollbar(prompt_frame, orient="vertical", command=self.prompt_text_widget.yview)
        prompt_scrollbar.grid(row=0, column=1, sticky="ns")
        self.prompt_text_widget.config(yscrollcommand=prompt_scrollbar.set)
        
        # Pre-fill with initial prompt if provided
        if self.initial_prompt:
            self.prompt_text_widget.insert("1.0", self.initial_prompt)
        
        # Context options
        context_frame = ttk.LabelFrame(input_frame, text=" Context Options ", padding="5")
        context_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        context_frame.grid_columnconfigure(1, weight=1)
        context_frame.grid_columnconfigure(3, weight=1)
        
        ttk.Label(context_frame, text="Lines before cursor:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.lines_before_entry = ttk.Entry(context_frame, width=8)
        self.lines_before_entry.insert(0, "5")
        self.lines_before_entry.grid(row=0, column=1, sticky="w", padx=(0, 15))
        
        ttk.Label(context_frame, text="Lines after cursor:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.lines_after_entry = ttk.Entry(context_frame, width=8)
        self.lines_after_entry.insert(0, "0")
        self.lines_after_entry.grid(row=0, column=3, sticky="w")
        
        # Options
        options_frame = ttk.Frame(input_frame)
        options_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        
        self.latex_mode_var = tk.BooleanVar()
        latex_checkbox = ttk.Checkbutton(
            options_frame,
            text="LaTeX oriented generation (uses code model)",
            variable=self.latex_mode_var
        )
        latex_checkbox.pack(anchor="w")
        
        # Generate button
        self.generate_button = ttk.Button(
            input_frame,
            text="Generate (Ctrl+Enter)",
            command=self._handle_generate
        )
        self.generate_button.grid(row=4, column=0, pady=(0, 10))
        
        # Response display (initially hidden)
        self.response_label = ttk.Label(input_frame, text="AI Response:")
        self.response_frame = ttk.Frame(input_frame)
        self.response_frame.grid_rowconfigure(0, weight=1)
        self.response_frame.grid_columnconfigure(0, weight=1)
        
        self.response_text_widget = tk.Text(
            self.response_frame,
            height=8,
            wrap="word",
            state="disabled",
            font=("Segoe UI", 10),
            bg=self.get_theme_color("llm_generated_bg", "#f0f0f0"),
            fg=self.get_theme_color("llm_generated_fg", "#000000"),
            selectbackground=self.get_theme_color("sel_bg", "#0078d4"),
            selectforeground=self.get_theme_color("sel_fg", "#ffffff"),
            relief="solid",
            borderwidth=1
        )
        
        response_scrollbar = ttk.Scrollbar(self.response_frame, orient="vertical", command=self.response_text_widget.yview)
        self.response_text_widget.config(yscrollcommand=response_scrollbar.set)
        
        # Bind keyboard shortcut
        self.prompt_text_widget.bind("<Control-Return>", lambda e: self._handle_generate())
        
        parent.add(input_frame, weight=2, minsize=300)
        
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
        """Show the AI response area."""
        self.response_label.grid(row=5, column=0, sticky="w", pady=(10, 5))
        self.response_frame.grid(row=6, column=0, sticky="nsew", pady=(0, 5))
        self.response_text_widget.grid(row=0, column=0, sticky="nsew")
        
        # Add scrollbar
        response_scrollbar = ttk.Scrollbar(self.response_frame, orient="vertical", command=self.response_text_widget.yview)
        response_scrollbar.grid(row=0, column=1, sticky="ns")
        self.response_text_widget.config(yscrollcommand=response_scrollbar.set)
        
        # Make response area expandable
        self.content_frame.winfo_children()[0].paneconfig(
            self.content_frame.winfo_children()[0].panes()[1], 
            weight=3
        )
    
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
        
        debug_console.log(f"Generate request: '{prompt_text[:50]}...', LaTeX mode: {latex_mode}", level='ACTION')
        
        # Add to history
        if self.on_history_add_callback:
            self.on_history_add_callback(prompt_text)
        
        # Call generation callback
        if self.on_generate_callback:
            self.on_generate_callback(prompt_text, lines_before, lines_after, latex_mode)
        
        # Close panel after generating
        self._handle_close()
    
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.prompt_text_widget:
            self.prompt_text_widget.focus_set()