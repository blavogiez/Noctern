"""
Integrated keywords panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk
import os
from typing import Optional
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
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
    
    def get_layout_style(self) -> PanelStyle:
        """Use simple layout for keywords panel."""
        return PanelStyle.SIMPLE
    
    def create_content(self):
        """Create the keywords panel content using standardized components."""
        # File info section
        info_section = StandardComponents.create_section(self.main_container, "File Information")
        info_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        filename = os.path.basename(self.file_path) if self.file_path else "Untitled"
        
        self.file_label = StandardComponents.create_info_label(
            info_section,
            f"Editing keywords for: {filename}",
            "body"
        )
        self.file_label.pack(anchor="w", padx=StandardComponents.PADDING, pady=StandardComponents.PADDING)
        
        # Keywords input section
        keywords_section = StandardComponents.create_section(self.main_container, "Keywords")
        keywords_section.pack(fill="both", expand=True)
        
        # Instructions
        instructions_label = StandardComponents.create_info_label(
            keywords_section,
            "Enter keywords (one per line or comma-separated):",
            "small"
        )
        instructions_label.pack(anchor="w", padx=StandardComponents.PADDING, pady=(StandardComponents.PADDING, StandardComponents.ELEMENT_SPACING))
        
        # Text widget using standardized component
        self.keyword_text_widget = StandardComponents.create_text_input(
            keywords_section,
            "Enter keywords here...",
            height=12
        )
        self.keyword_text_widget.pack(fill="both", expand=True, padx=StandardComponents.PADDING, pady=(0, StandardComponents.PADDING))
        
        # Set as main widget for focus
        self.main_widget = self.keyword_text_widget
        
        # Load existing keywords
        self._load_current_keywords()
        
        # Save button using standardized component
        save_buttons = [("Save Keywords (Ctrl+Enter)", self._save_keywords, "primary")]
        button_row = StandardComponents.create_button_row(keywords_section, save_buttons)
        button_row.pack(padx=StandardComponents.PADDING, pady=(StandardComponents.ELEMENT_SPACING, StandardComponents.PADDING))
        
        # Bind keyboard shortcuts
        self.keyword_text_widget.bind("<Control-Return>", lambda e: self._save_keywords())
        
        # Help text using standardized component
        help_text = StandardComponents.create_info_label(
            keywords_section,
            "Tip: Keywords help improve document analysis context.",
            "small"
        )
        help_text.pack(anchor="w", padx=StandardComponents.PADDING, pady=(StandardComponents.ELEMENT_SPACING, 0))
        
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