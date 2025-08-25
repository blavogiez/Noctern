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
from utils import debug_console


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
            placeholder_label = ttk.Label(
                tab, 
                text=placeholder_text, 
                font=("Segoe UI", 9), 
                foreground="gray"
            )
            placeholder_label.pack(fill="x", pady=(0, 5), anchor="w")
            
            # Text widget for editing
            text_widget = tk.Text(
                tab, 
                wrap="word", 
                font=("Consolas", 10), 
                undo=True,
                height=15  # Set a reasonable height
            )
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            # Pack text widget and scrollbar
            text_frame = ttk.Frame(tab)
            text_frame.pack(fill="both", expand=True)
            
            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Insert content
            text_widget.insert("1.0", value)
            self.text_widgets[key] = text_widget
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Save button
        save_button = ttk.Button(
            button_frame, 
            text="Save and Apply", 
            command=self._save_prompts,
            bootstyle="success"
        )
        save_button.pack(side="right", padx=(5, 0))
        
        # Cancel button
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self._handle_close,
            bootstyle="secondary"
        )
        cancel_button.pack(side="right")
        
    def focus_main_widget(self):
        """Focus the first text widget."""
        if self.text_widgets:
            first_widget = next(iter(self.text_widgets.values()))
            first_widget.focus_set()
            
    def _load_prompts(self):
        """Load prompts from the .txt files in the prompts directory."""
        loaded_prompts = {}
        if not os.path.isdir(self.PROMPTS_DIR):
            debug_console.log(f"Prompts directory not found: {self.PROMPTS_DIR}", level='ERROR')
            return {}
        
        for filename in sorted(os.listdir(self.PROMPTS_DIR)):
            if filename.endswith(".txt"):
                prompt_name = os.path.splitext(filename)[0]
                file_path = os.path.join(self.PROMPTS_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        loaded_prompts[prompt_name] = f.read()
                except Exception as e:
                    debug_console.log(f"Could not read prompt file {filename}: {e}", level='ERROR')
        
        debug_console.log(f"Loaded {len(loaded_prompts)} global prompts", level='INFO')
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
                debug_console.log(error_msg, level='ERROR')
                messagebox.showerror("Error", error_msg, parent=self.content_frame)
                return  # Stop saving if one file fails
        
        # Reload the global prompts in the application state
        try:
            # Import here to avoid circular imports
            from llm import init as llm_init
            llm_init._load_global_default_prompts()
            success_msg = f"Global prompts have been saved and applied. ({saved_count} prompts saved)"
            messagebox.showinfo("Success", success_msg, parent=self.content_frame)
            debug_console.log("Global prompts saved and reloaded.", level='SUCCESS')
            self._close_panel()
        except Exception as e:
            error_msg = f"Failed to reload prompts: {e}"
            debug_console.log(error_msg, level='ERROR')
            messagebox.showerror("Error", error_msg, parent=self.content_frame)