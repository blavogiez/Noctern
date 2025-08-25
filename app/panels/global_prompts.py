"""
Global prompts editor panel for editing default LLM prompt templates.

This panel provides a tabbed interface for editing global prompt templates
in the left sidebar instead of a separate dialog window.
"""

import tkinter as tk
import ttkbootstrap as ttk
import os
from tkinter import messagebox
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import logs_console


class GlobalPromptsPanel(BasePanel):
    """Panel for editing global default prompts."""
    
    # Define global prompts directory path
    PROMPTS_DIR = "data/prompts"
    
    def __init__(self, parent_container, theme_getter, on_close_callback=None):
        """
        Initialize the global prompts panel.
        
        Args:
            parent_container: Parent container widget
            theme_getter: Function to get theme colors
            on_close_callback: Optional callback when panel closes
        """
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        self.prompts_content = {}
        self.text_widgets = {}
        self.placeholders = {
            "completion": "Placeholders: {previous_context}, {current_phrase_start}",
            "generation": "Placeholders: {user_prompt}, {context}, {keywords}",
            "generation_latex": "Placeholders: {user_prompt}, {context}, {keywords}",
            "styling": "Placeholders: {text}, {intensity}",
            "rephrase": "Placeholders: {text}, {instruction}",
            "debug_latex_diff": "Placeholders: {added_lines}"
        }
        
        self.notebook = None
        
    def get_panel_title(self) -> str:
        """Return the panel title."""
        return "Global Prompts Editor"
        
    def get_layout_style(self) -> PanelStyle:
        """Use tabbed layout for global prompts editor."""
        return PanelStyle.TABBED
    
    def create_content(self):
        """Create the global prompts editor content."""
        # Load prompts first
        self.prompts_content = self._load_prompts()
        
        if not self.prompts_content:
            # Show error message if no prompts could be loaded
            error_label = StandardComponents.create_info_label(
                self.main_container,
                f"Error: Could not load prompts from {self.PROMPTS_DIR}",
                "body"
            )
            error_label.pack(pady=StandardComponents.SECTION_SPACING)
            return
        
        # Use standardized tabbed layout
        self.notebook = self.main_container
        
        # Create tabs for each prompt
        for key, value in self.prompts_content.items():
            tab = ttk.Frame(self.notebook, padding=StandardComponents.PADDING)
            self.notebook.add(tab, text=key.replace("_", " ").title())
            
            # Placeholder information
            placeholder_text = self.placeholders.get(key, "No specific placeholders for this prompt.")
            placeholder_label = StandardComponents.create_info_label(
                tab, 
                placeholder_text, 
                "small"
            )
            placeholder_label.pack(fill="x", pady=(0, StandardComponents.PADDING//2), anchor="w")
            
            # Text widget for editing using StandardComponents
            text_widget = StandardComponents.create_text_input(
                tab, 
                f"Enter {key.replace('_', ' ')} prompt template here...",
                height=15
            )
            text_widget.pack(fill="both", expand=True, pady=(0, StandardComponents.PADDING))
            
            # Insert content (override placeholder)
            if value:
                text_widget.delete("1.0", "end")
                text_widget.insert("1.0", value)
            self.text_widgets[key] = text_widget
        
        # Action buttons using StandardComponents
        action_buttons = [
            ("Cancel", self._handle_close, "secondary"),
            ("Save and Apply", self._save_prompts, "success")
        ]
        button_row = StandardComponents.create_button_row(self.main_container.master, action_buttons)
        button_row.pack(fill="x", pady=(StandardComponents.SECTION_SPACING, 0))
        
    def focus_main_widget(self):
        """Focus the first text widget."""
        if self.text_widgets:
            first_widget = next(iter(self.text_widgets.values()))
            first_widget.focus_set()
            
    def _load_prompts(self):
        """Load prompts from the .txt files in the prompts directory."""
        loaded_prompts = {}
        if not os.path.isdir(self.PROMPTS_DIR):
            logs_console.log(f"Prompts directory not found: {self.PROMPTS_DIR}", level='ERROR')
            return {}
        
        for filename in sorted(os.listdir(self.PROMPTS_DIR)):
            if filename.endswith(".txt"):
                prompt_name = os.path.splitext(filename)[0]
                file_path = os.path.join(self.PROMPTS_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        loaded_prompts[prompt_name] = f.read()
                except Exception as e:
                    logs_console.log(f"Could not read prompt file {filename}: {e}", level='ERROR')
        
        logs_console.log(f"Loaded {len(loaded_prompts)} global prompts", level='INFO')
        return loaded_prompts
        
    def _save_prompts(self):
        """Save the prompts to their respective .txt files and reload them."""
        saved_count = 0
        
        for key, widget in self.text_widgets.items():
            content = widget.get("1.0", "end-1c")
            file_path = os.path.join(self.PROMPTS_DIR, f"{key}.txt")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved_count += 1
            except Exception as e:
                error_msg = f"Failed to save prompt: {key}\n{e}"
                logs_console.log(error_msg, level='ERROR')
                messagebox.showerror("Error", error_msg, parent=self.content_frame)
                return  # Stop saving if one file fails
        
        # Reload the global prompts in the application state
        try:
            # Import here to avoid circular imports
            from llm import init as llm_init
            llm_init._load_global_default_prompts()
            success_msg = f"Global prompts have been saved and applied. ({saved_count} prompts saved)"
            messagebox.showinfo("Success", success_msg, parent=self.content_frame)
            logs_console.log("Global prompts saved and reloaded.", level='SUCCESS')
            self._close_panel()
        except Exception as e:
            error_msg = f"Failed to reload prompts: {e}"
            logs_console.log(error_msg, level='ERROR')
            messagebox.showerror("Error", error_msg, parent=self.content_frame)