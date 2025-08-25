"""
Integrated prompts editor panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Callable
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import logs_console


class PromptsPanel(BasePanel):
    """
    Integrated prompts editor panel that replaces the dialog window.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter,
                 current_prompts: Dict[str, str],
                 default_prompts: Dict[str, str],
                 on_save_callback: Callable,
                 on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        self.current_prompts = current_prompts
        self.default_prompts = default_prompts
        self.on_save_callback = on_save_callback
        
        # Store initial state to check for unsaved changes
        self.saved_state = {
            "completion": current_prompts.get("completion", "").strip(),
            "generation": current_prompts.get("generation", "").strip(),
            "styling": current_prompts.get("styling", "").strip()
        }
        
        # UI components
        self.notebook: Optional[ttk.Notebook] = None
        self.prompt_widgets: Dict[str, tk.Text] = {}
        self.save_button: Optional[tk.Button] = None
        
    def get_panel_title(self) -> str:
        return "Edit Prompts"
    
    def get_layout_style(self) -> PanelStyle:
        """Use tabbed layout for prompts editor."""
        return PanelStyle.TABBED
    
    def create_content(self):
        """Create the prompts editor panel content."""
        # Use standardized main container
        main_container = self.main_container
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Create tabbed interface for different prompt types
        self._create_prompt_tabs(main_container)
        
        # Create action buttons
        self._create_action_section(main_container)
        
    def _create_prompt_tabs(self, parent):
        """Create tabs for different prompt types."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        # Prompt types to edit
        prompt_types = {
            "completion": "Completion",
            "generation": "Generation", 
            "styling": "Styling"
        }
        
        placeholders = {
            "completion": "{context}\n{user_prompt}\n{keywords}",
            "generation": "{user_prompt}\n{keywords}\n{context}",
            "styling": "{user_prompt}\n{context}\n{keywords}"
        }
        
        for prompt_key, prompt_name in prompt_types.items():
            # Create tab frame
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=prompt_name)
            
            tab_frame.grid_rowconfigure(1, weight=1)
            tab_frame.grid_columnconfigure(0, weight=1)
            
            # Header with info
            header_frame = ttk.Frame(tab_frame)
            header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            header_frame.grid_columnconfigure(1, weight=1)
            
            # Prompt type label
            type_label = StandardComponents.create_info_label(
                header_frame,
                f"{prompt_name} Prompt Template",
                "title"
            )
            type_label.grid(row=0, column=0, sticky="w")
            
            # Reset to default button
            reset_button = StandardComponents.create_button_input(
                header_frame,
                text="Reset to Default",
                command=lambda k=prompt_key: self._reset_to_default(k),
                width=15
            )
            reset_button.grid(row=0, column=2, sticky="e")
            
            # Placeholder info
            placeholder_info = StandardComponents.create_info_label(
                header_frame,
                f"Available placeholders: {placeholders[prompt_key]}",
                "small"
            )
            placeholder_info.grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 0))
            
            # Text editor with scrollbar
            text_frame = ttk.Frame(tab_frame)
            text_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
            text_frame.grid_rowconfigure(0, weight=1)
            text_frame.grid_columnconfigure(0, weight=1)
            
            text_widget = StandardComponents.create_text_input(
                text_frame,
                f"Enter your {prompt_name.lower()} prompt template here...",
                height=15
            )
            text_widget.grid(row=0, column=0, sticky="nsew")
            
            # Insert current prompt content (override placeholder)
            current_prompt = self.current_prompts.get(prompt_key, "")
            if current_prompt:
                text_widget.delete("1.0", "end")
                text_widget.insert("1.0", current_prompt)
            
            # Store reference to widget
            self.prompt_widgets[prompt_key] = text_widget
            
            # Bind change events to detect modifications
            text_widget.bind("<KeyRelease>", self._on_text_changed)
            text_widget.bind("<ButtonRelease>", self._on_text_changed)
            
    def _create_action_section(self, parent):
        """Create action buttons section."""
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=1, column=0, sticky="ew")
        action_frame.grid_columnconfigure(1, weight=1)
        
        # Save button using StandardComponents
        save_buttons = [("Save Changes", self._handle_save, "primary")]
        save_row = StandardComponents.create_button_row(action_frame, save_buttons)
        save_row.grid(row=0, column=0, sticky="w")
        self.save_button = save_row.winfo_children()[0]  # Get button reference
        
        # Status label
        self.status_label = StandardComponents.create_info_label(
            action_frame,
            "Ready",
            "small"
        )
        self.status_label.grid(row=0, column=2, sticky="e")
        
        # Help text
        help_label = StandardComponents.create_info_label(
            action_frame,
            "Changes are applied immediately to the current session",
            "small"
        )
        help_label.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.notebook and self.prompt_widgets:
            # Focus the first prompt widget
            first_widget = next(iter(self.prompt_widgets.values()))
            first_widget.focus_set()
    
    def _reset_to_default(self, prompt_key: str):
        """Reset a specific prompt to its default value."""
        if prompt_key in self.default_prompts and prompt_key in self.prompt_widgets:
            default_prompt = self.default_prompts[prompt_key]
            text_widget = self.prompt_widgets[prompt_key]
            
            # Confirm reset
            result = messagebox.askyesno(
                "Reset Prompt",
                f"Reset the {prompt_key} prompt to default?\n\nThis will overwrite your current changes.",
                parent=self.panel_frame
            )
            
            if result:
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", default_prompt)
                self._on_text_changed()
                logs_console.log(f"Reset {prompt_key} prompt to default", level='ACTION')
    
    def _on_text_changed(self, event=None):
        """Handle text change events."""
        # Check if there are unsaved changes
        has_changes = self._has_unsaved_changes()
        
        if has_changes:
            self.save_button.config(state="normal")
            self.status_label.config(text="Unsaved changes")
        else:
            self.save_button.config(state="disabled")
            self.status_label.config(text="No changes")
    
    def _has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        for prompt_key, text_widget in self.prompt_widgets.items():
            current_content = text_widget.get("1.0", tk.END + "-1c").strip()
            saved_content = self.saved_state.get(prompt_key, "").strip()
            
            if current_content != saved_content:
                return True
        
        return False
    
    def _handle_save(self):
        """Handle save button click."""
        # Get current content from all widgets
        new_prompts = {}
        for prompt_key, text_widget in self.prompt_widgets.items():
            new_prompts[prompt_key] = text_widget.get("1.0", tk.END + "-1c").strip()
        
        logs_console.log("Saving prompt templates", level='ACTION')
        
        # Call the save callback
        if self.on_save_callback:
            self.on_save_callback(
                new_prompts.get("completion", ""),
                new_prompts.get("generation", ""),
                new_prompts.get("styling", "")
            )
        
        # Update saved state
        self.saved_state = new_prompts.copy()
        
        # Update UI
        self.save_button.config(state="disabled")
        self.status_label.config(text="Saved")
        
        # Reset status after delay
        self.panel_frame.after(2000, lambda: (
            self.status_label.config(text="Ready")
            if self.status_label and self.status_label.winfo_exists() else None
        ))
    
    def _handle_close(self):
        """Handle panel close with unsaved changes check."""
        if self._has_unsaved_changes():
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before closing?",
                parent=self.panel_frame
            )
            
            if result is True:  # Yes, save
                self._handle_save()
            elif result is False:  # No, don't save
                pass
            else:  # Cancel
                return
        
        # Call parent close
        super()._handle_close()