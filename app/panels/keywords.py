"""
Integrated keywords panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk
import os
from typing import Optional
from .base_panel import BasePanel
from llm import keyword_history
from utils import debug_console


class KeywordsPanel(BasePanel):
    """
    Integrated keywords panel that replaces the dialog window.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter, 
                 file_path: str, on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        self.file_path = file_path
        
        # UI components
        self.file_label: Optional[tk.Label] = None
        self.keyword_text_widget: Optional[tk.Text] = None
        self.save_button: Optional[tk.Button] = None
        
    def get_panel_title(self) -> str:
        return "Keywords Editor"
    
    def create_content(self):
        """Create the keywords panel content."""
        # File info section
        info_frame = ttk.LabelFrame(self.content_frame, text=" File Information ", padding="10")
        info_frame.pack(fill="x", padx=5, pady=5)
        
        filename = os.path.basename(self.file_path) if self.file_path else "Untitled"
        file_info_text = f"Editing keywords for: {filename}"
        
        self.file_label = ttk.Label(
            info_frame,
            text=file_info_text,
            font=("Segoe UI", 9),
            wraplength=250
        )
        self.file_label.pack(anchor="w")
        
        # Keywords input section
        keywords_frame = ttk.LabelFrame(self.content_frame, text=" Keywords ", padding="10")
        keywords_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Instructions
        instructions_label = ttk.Label(
            keywords_frame,
            text="Enter keywords (one per line or comma-separated):",
            wraplength=250
        )
        instructions_label.pack(anchor="w", pady=(0, 10))
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(keywords_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 10))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        self.keyword_text_widget = tk.Text(
            text_frame,
            height=12,
            font=("Segoe UI", 10),
            bg=self.get_theme_color("editor_bg", "#ffffff"),
            fg=self.get_theme_color("editor_fg", "#000000"),
            selectbackground=self.get_theme_color("sel_bg", "#0078d4"),
            selectforeground=self.get_theme_color("sel_fg", "#ffffff"),
            insertbackground=self.get_theme_color("editor_insert_bg", "#000000"),
            relief="solid",
            borderwidth=1,
            wrap="word"
        )
        self.keyword_text_widget.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.keyword_text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.keyword_text_widget.config(yscrollcommand=scrollbar.set)
        
        # Load existing keywords
        self._load_current_keywords()
        
        # Save button
        button_frame = ttk.Frame(keywords_frame)
        button_frame.pack(fill="x")
        
        self.save_button = ttk.Button(
            button_frame,
            text="Save Keywords (Ctrl+Enter)",
            command=self._save_keywords
        )
        self.save_button.pack(side="left")
        
        # Bind keyboard shortcuts
        self.keyword_text_widget.bind("<Control-Return>", lambda e: self._save_keywords())
        
        # Help text
        help_text = ttk.Label(
            keywords_frame,
            text="Tip: Keywords help the AI understand your document context.",
            font=("Segoe UI", 8),
            foreground=self.get_theme_color("muted_text", "#666666")
        )
        help_text.pack(anchor="w", pady=(10, 0))
        
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.keyword_text_widget:
            self.keyword_text_widget.focus_set()
            
    def _load_current_keywords(self):
        """Load current keywords for the file."""
        if not self.file_path:
            return
            
        current_keywords = keyword_history.get_keywords_for_file(self.file_path)
        if current_keywords and self.keyword_text_widget:
            self.keyword_text_widget.delete("1.0", tk.END)
            self.keyword_text_widget.insert("1.0", "\n".join(current_keywords))
    
    def _save_keywords(self):
        """Save the entered keywords."""
        if not self.keyword_text_widget or not self.file_path:
            return
            
        input_text = self.keyword_text_widget.get("1.0", tk.END).strip()
        
        # Parse keywords (split by newlines, then by commas)
        new_keywords = []
        for line in input_text.split('\n'):
            for kw in line.split(','):
                stripped_kw = kw.strip()
                if stripped_kw:
                    new_keywords.append(stripped_kw)
        
        # Save keywords for the file
        keyword_history.set_keywords_for_file(self.file_path, new_keywords)
        
        debug_console.log(f"Saved keywords for {os.path.basename(self.file_path)}: {new_keywords}", level='SUCCESS')
        
        # Visual feedback
        original_text = self.save_button.cget("text")
        self.save_button.config(text="Saved!", state="disabled")
        
        # Restore button after delay
        self.panel_frame.after(1500, lambda: (
            self.save_button.config(text=original_text, state="normal")
            if self.save_button and self.save_button.winfo_exists() else None
        ))