"""
Integrated rephrase panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import logs_console


class RephrasePanel(BasePanel):
    """
    Integrated rephrase panel that replaces the dialog window.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter,
                 original_text: str,
                 on_rephrase_callback: Callable,
                 on_cancel_callback: Optional[Callable] = None,
                 on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        self.original_text = original_text
        self.on_rephrase_callback = on_rephrase_callback
        self.on_cancel_callback = on_cancel_callback
        
        # UI components
        self.instruction_entry: Optional[tk.Entry] = None
        self.original_text_widget: Optional[tk.Text] = None
        self.rephrase_button: Optional[tk.Button] = None
        
    def get_panel_title(self) -> str:
        return "Rephrase Text"
    
    def get_layout_style(self) -> PanelStyle:
        """Use simple layout for rephrase panel."""
        return PanelStyle.SIMPLE
    
    def get_critical_action_buttons(self) -> list:
        """Return critical action buttons for this panel."""
        return [
            ("Rephrase (Enter)", self._handle_rephrase, "primary"),
            ("Cancel", self._handle_cancel, "secondary")
        ]
        
    def create_content(self):
        """Create the rephrase panel content using standardized components."""
        # main_container is provided by PanelFactory
        main_frame = self.main_container
        
        # Instruction section
        self._create_instruction_section(main_frame)
        
        # Original text display section  
        self._create_original_text_section(main_frame)
        
        # Help text
        help_label = StandardComponents.create_info_label(
            main_frame,
            "Press Enter to rephrase or use the close button (×) to cancel",
            "small"
        )
        help_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
    def _create_instruction_section(self, parent):
        """Create the instruction input section."""
        instruction_section = StandardComponents.create_section(parent, "Rephrase Instruction")
        instruction_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Instruction label
        instruction_label = StandardComponents.create_info_label(
            instruction_section,
            "Enter your rephrase instruction:",
            "body"
        )
        instruction_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        # Instruction entry
        self.instruction_entry = StandardComponents.create_entry_input(
            instruction_section,
            "e.g., 'Make it more formal' or 'Simplify the language'"
        )
        self.instruction_entry.pack(fill="x", pady=(0, StandardComponents.PADDING//2))
        
        # Set as main widget for focus
        self.main_widget = self.instruction_entry
        
        # Example text
        example_label = StandardComponents.create_info_label(
            instruction_section,
            "Examples: 'Make it more formal', 'Simplify the language', 'Add more details'",
            "small"
        )
        example_label.pack(anchor="w")
        
        # Bind Enter key
        self.instruction_entry.bind("<Return>", lambda e: self._handle_rephrase())
        
    def _create_original_text_section(self, parent):
        """Create the original text display section."""
        original_section = StandardComponents.create_section(parent, "Original Text")
        original_section.pack(fill="both", expand=True, pady=(0, StandardComponents.SECTION_SPACING))
        
        # Description
        desc_label = StandardComponents.create_info_label(
            original_section,
            "This is the text that will be rephrased:",
            "small"
        )
        desc_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        # Original text widget
        self.original_text_widget = StandardComponents.create_text_input(
            original_section,
            "Original text will appear here...",
            height=8
        )
        self.original_text_widget.pack(fill="both", expand=True)
        
        # Insert original text and make readonly
        self.original_text_widget.config(state="normal")
        self.original_text_widget.delete("1.0", "end")
        self.original_text_widget.insert("1.0", self.original_text)
        self.original_text_widget.config(state="disabled")
        
        
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.instruction_entry:
            self.instruction_entry.focus_set()
    
    def _handle_rephrase(self):
        """Handle rephrase button click."""
        instruction = self.instruction_entry.get().strip()
        
        if not instruction:
            messagebox.showwarning(
                "Rephrase Instruction Required", 
                "Please enter an instruction for rephrasing.",
                parent=self.panel_frame
            )
            return
        
        logs_console.log(f"Rephrase instruction: '{instruction}'", level='ACTION')
        
        # Call the callback
        if self.on_rephrase_callback:
            self.on_rephrase_callback(instruction)
        
        # Close the panel
        self._handle_close()
    
    def _handle_cancel(self):
        """Handle cancel action."""
        logs_console.log("Rephrase cancelled by user from panel.", level='INFO')
        
        if self.on_cancel_callback:
            self.on_cancel_callback()
        
        # Close the panel
        self._handle_close()