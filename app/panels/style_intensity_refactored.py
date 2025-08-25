"""
Refactored Style Intensity Panel - Example of standardized scrollable panel.

Shows how to use the standardized panel system with scrollable layout
and consistent styling.
"""

import tkinter as tk
from tkinter import ttk
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import logs_console


class StyleIntensityPanel(BasePanel):
    """
    Standardized style intensity panel using scrollable layout.
    """
    
    def __init__(self, parent_container, theme_getter, last_intensity=5, 
                 on_confirm_callback=None, on_cancel_callback=None):
        super().__init__(parent_container, theme_getter, self._on_close)
        
        self.last_intensity = last_intensity
        self.on_confirm_callback = on_confirm_callback
        self.on_cancel_callback = on_cancel_callback
        
        # Result storage
        self.intensity = last_intensity
        self.cancelled = True
        
        # UI components
        self.main_widget = None
        self.intensity_var = None
        
    def get_panel_title(self) -> str:
        return "Style Intensity"
    
    def get_layout_style(self) -> PanelStyle:
        """Use scrollable layout in case content is too tall."""
        return PanelStyle.SCROLLABLE
    
    def create_content(self):
        """Create the style intensity selection content."""
        # main_container is a tuple for scrollable: (scrollable_frame, canvas)
        scrollable_frame, canvas = self.main_container
        
        # Main content in scrollable area
        main_frame = ttk.Frame(scrollable_frame, padding=StandardComponents.PADDING)
        main_frame.pack(fill="both", expand=True)
        
        # Title section
        title_section = StandardComponents.create_section(main_frame, "")
        title_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        title_label = StandardComponents.create_info_label(
            title_section,
            "Style Intensity Selection",
            "title"
        )
        title_label.pack(pady=(0, StandardComponents.PADDING//2))
        
        # Description section
        desc_section = StandardComponents.create_section(main_frame, "Description")
        desc_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        desc_text = ("Choose the intensity of the styling. A low value means minor changes, "
                    "while a high value allows for significant reformatting and restructuring.")\n"
        "\nThis affects how aggressively the system will modify your text:"
        "\n• 1-3: Minor improvements (grammar, word choice)"
        "\n• 4-6: Moderate changes (sentence structure)"
        "\n• 7-10: Significant rewriting (style transformation)"
        
        desc_label = StandardComponents.create_info_label(
            desc_section,
            desc_text,
            "body"
        )
        desc_label.pack(anchor="w")
        
        # Intensity selection section
        intensity_section = StandardComponents.create_section(main_frame, "Intensity Level")
        intensity_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Scale labels
        scale_labels_frame = ttk.Frame(intensity_section)
        scale_labels_frame.pack(fill="x", pady=(0, StandardComponents.PADDING//2))
        
        ttk.Label(scale_labels_frame, text="1 (Minimal)", font=StandardComponents.SMALL_FONT).pack(side="left")
        ttk.Label(scale_labels_frame, text="10 (Maximum)", font=StandardComponents.SMALL_FONT).pack(side="right")
        
        # Intensity scale
        self.intensity_var = tk.IntVar(value=self.last_intensity)
        
        self.main_widget = ttk.Scale(
            intensity_section,
            from_=1,
            to=10,
            orient="horizontal",
            variable=self.intensity_var,
            length=250
        )
        self.main_widget.pack(pady=(0, StandardComponents.PADDING))
        
        # Current value display
        self.value_label = StandardComponents.create_info_label(
            intensity_section,
            f"Current: {self.intensity_var.get()}",
            "body"
        )
        self.value_label.pack(pady=(0, StandardComponents.SECTION_SPACING))
        
        # Update value display when scale changes
        self.intensity_var.trace('w', self._update_value_label)
        
        # Examples section
        examples_section = StandardComponents.create_section(main_frame, "Examples by Level")
        examples_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        examples_text = ("Level 1-2: Fix typos, basic grammar"
                       "\nLevel 3-4: Improve word choice, clarity"
                       "\nLevel 5-6: Enhance sentence flow, structure"
                       "\nLevel 7-8: Rewrite for style, tone"
                       "\nLevel 9-10: Complete transformation")
        
        examples_label = StandardComponents.create_info_label(
            examples_section,
            examples_text,
            "small"
        )
        examples_label.pack(anchor="w")
        
        # Button row
        buttons = [
            ("Cancel", self._on_cancel, "secondary"),
            ("Apply Styling", self._on_apply, "success")
        ]
        button_row = StandardComponents.create_button_row(main_frame, buttons)
        button_row.pack(fill="x", pady=(StandardComponents.SECTION_SPACING, 0))
        
        # Add some padding at the bottom for scrolling
        ttk.Frame(main_frame, height=20).pack()
    
    def focus_main_widget(self):
        """Focus the intensity scale."""
        if self.main_widget:
            self.main_widget.focus_set()
    
    def _update_value_label(self, *args):
        """Update the current value display."""
        if hasattr(self, 'value_label'):
            current_value = int(self.intensity_var.get())
            self.value_label.config(text=f"Current: {current_value}")
    
    def _on_apply(self):
        """Handle apply button click."""
        self.intensity = int(self.intensity_var.get())
        self.cancelled = False
        
        logs_console.log(f"Style intensity selected: {self.intensity}/10", level='INFO')
        
        if self.on_confirm_callback:
            self.on_confirm_callback(self.intensity)
            
        self.close_panel()
        
    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancelled = True
        
        logs_console.log("Style intensity selection cancelled", level='INFO')
        
        if self.on_cancel_callback:
            self.on_cancel_callback()
            
        self.close_panel()
        
    def _on_close(self):
        """Handle panel close event."""
        if self.cancelled and self.on_cancel_callback:
            self.on_cancel_callback()