"""
Refactored Keywords Panel - Example of standardized panel implementation.

This shows how to use the new standardized panel system with consistent
layout, styling, and behavior across all panels.
"""

import tkinter as tk
from tkinter import ttk
import os
from typing import Optional
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from llm import keyword_history
from utils import logs_console


class KeywordsPanel(BasePanel):
    """
    Standardized keywords panel using the new panel factory system.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter, 
                 file_path: str, on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        self.file_path = file_path
        self.original_keywords = []
        self.current_keywords = []
        
        # UI components
        self.main_widget: Optional[tk.Text] = None
        
    def get_panel_title(self) -> str:
        return "Keywords Editor"
    
    def get_layout_style(self) -> PanelStyle:
        """Use simple layout for keywords panel."""
        return PanelStyle.SIMPLE
    
    def has_unsaved_changes(self) -> bool:
        """Check if keywords have been modified."""
        return self.current_keywords != self.original_keywords
    
    def create_content(self):
        """Create the keywords panel content using standardized components."""
        # Main container is provided by BasePanel via PanelFactory
        main_frame = self.main_container
        
        # File information section
        filename = os.path.basename(self.file_path) if self.file_path else "Untitled"
        info_section = StandardComponents.create_section(main_frame, "File Information")
        info_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        info_label = StandardComponents.create_info_label(
            info_section, 
            f"Editing keywords for: {filename}",
            "body"
        )
        info_label.pack(anchor="w")
        
        # Keywords input section
        keywords_section = StandardComponents.create_section(main_frame, "Keywords")
        keywords_section.pack(fill="both", expand=True, pady=(0, StandardComponents.SECTION_SPACING))
        
        # Instructions
        instructions = StandardComponents.create_info_label(
            keywords_section,
            "Enter keywords (one per line) to help improve document analysis:",
            "small"
        )
        instructions.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        # Keywords text input
        self.main_widget = StandardComponents.create_text_input(
            keywords_section,
            placeholder="Enter keywords here...",
            height=8
        )
        self.main_widget.pack(fill="both", expand=True, pady=(0, StandardComponents.PADDING))
        
        # Load current keywords
        self._load_keywords()
        
        # Button row
        buttons = [
            ("Cancel", self._on_cancel, "secondary"),
            ("Save Keywords", self._on_save, "success")
        ]
        button_row = StandardComponents.create_button_row(main_frame, buttons)
        button_row.pack(fill="x", pady=(StandardComponents.PADDING, 0))
    
    def focus_main_widget(self):
        """Focus the keywords text widget."""
        if self.main_widget:
            self.main_widget.focus_set()
    
    def _load_keywords(self):
        """Load existing keywords for the file."""
        try:
            keywords = keyword_history.get_keywords_for_file(self.file_path)
            self.original_keywords = keywords.copy()
            self.current_keywords = keywords.copy()
            
            if keywords:
                # Clear placeholder if present
                current_content = self.main_widget.get("1.0", "end-1c")
                if current_content == "Enter keywords here...":
                    self.main_widget.delete("1.0", "end")
                    self.main_widget.config(foreground="black")
                
                # Insert keywords
                self.main_widget.delete("1.0", "end")
                self.main_widget.insert("1.0", "\n".join(keywords))
            
            logs_console.log(f"Loaded {len(keywords)} keywords for file: {self.file_path}", level='INFO')
            
        except Exception as e:
            logs_console.log(f"Error loading keywords: {e}", level='ERROR')
    
    def _save_keywords(self):
        """Save the current keywords."""
        try:
            # Get keywords from text widget
            content = self.main_widget.get("1.0", "end-1c").strip()
            
            if content and content != "Enter keywords here...":
                keywords = [line.strip() for line in content.split("\n") if line.strip()]
            else:
                keywords = []
            
            # Save to file
            keyword_history.set_keywords_for_file(self.file_path, keywords)
            
            self.original_keywords = keywords.copy()
            self.current_keywords = keywords.copy()
            
            logs_console.log(f"Saved {len(keywords)} keywords for file: {self.file_path}", level='SUCCESS')
            return True
            
        except Exception as e:
            logs_console.log(f"Error saving keywords: {e}", level='ERROR')
            from tkinter import messagebox
            messagebox.showerror("Save Error", f"Failed to save keywords: {str(e)}")
            return False
    
    def _save_changes(self):
        """Override BasePanel save method."""
        return self._save_keywords()
    
    def _on_save(self):
        """Handle save button click."""
        if self._save_keywords():
            self.close_panel()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.close_panel()