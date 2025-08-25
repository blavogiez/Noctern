"""
Style intensity panel for selecting styling intensity.

This panel replaces the StyleIntensityDialog, providing a clean
interface for selecting styling intensity in the left sidebar.
"""

import ttkbootstrap as ttk
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents


class StyleIntensityPanel(BasePanel):
    """Panel for selecting styling intensity."""
    
    def __init__(self, parent_container, theme_getter, last_intensity=5, 
                 on_confirm_callback=None, on_cancel_callback=None):
        """
        Initialize the style intensity panel.
        
        Args:
            parent_container: Parent container widget
            theme_getter: Function to get theme colors
            last_intensity: Last used intensity value
            on_confirm_callback: Callback when confirmed (intensity)
            on_cancel_callback: Callback when cancelled
        """
        super().__init__(parent_container, theme_getter, self._on_close)
        
        self.last_intensity = last_intensity
        self.on_confirm_callback = on_confirm_callback
        self.on_cancel_callback = on_cancel_callback
        
        # Result storage
        self.intensity = last_intensity
        self.cancelled = True
        
        # UI elements
        self.intensity_var = None
        self.intensity_scale = None
        
    def get_panel_title(self) -> str:
        """Return the panel title."""
        return "Style Intensity"
        
    def get_layout_style(self) -> PanelStyle:
        """Use simple layout for style intensity."""
        return PanelStyle.SIMPLE
    
    def create_content(self):
        """Create the style intensity selection content using standardized components."""
        # Use standardized main container
        main_frame = self.main_container
        
        # Title using standardized component
        title_label = StandardComponents.create_info_label(
            main_frame, 
            "Style Intensity", 
            "title"
        )
        title_label.pack(pady=(0, StandardComponents.ELEMENT_SPACING))
        
        # Description using standardized component
        desc_text = ("Choose the intensity of the styling. A low value means minor changes, "
                    "while a high value allows for significant reformatting.")
        desc_label = StandardComponents.create_info_label(
            main_frame,
            desc_text,
            "body"
        )
        desc_label.pack(pady=(0, StandardComponents.SECTION_SPACING))
        
        # Intensity scale
        self.intensity_var = ttk.IntVar(value=self.last_intensity)
        
        intensity_frame = ttk.Frame(main_frame)
        intensity_frame.pack(fill="x", pady=(0, 10))
        
        # Labels for scale
        ttk.Label(intensity_frame, text="1 (Minimal)").pack(side="left")
        ttk.Label(intensity_frame, text="10 (Maximum)").pack(side="right")
        
        # Scale widget
        self.intensity_scale = ttk.Scale(
            main_frame,
            from_=1,
            to=10,
            orient="horizontal",
            variable=self.intensity_var,
            length=250
        )
        self.intensity_scale.pack(pady=(StandardComponents.ELEMENT_SPACING, StandardComponents.SECTION_SPACING))
        
        # Current value display using standardized component
        self.value_label = StandardComponents.create_info_label(
            main_frame,
            f"Current: {self.intensity_var.get()}",
            "body"
        )
        self.value_label.pack(pady=(0, StandardComponents.SECTION_SPACING))
        
        # Update value display when scale changes
        self.intensity_var.trace('w', self._update_value_label)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Apply button
        apply_button = ttk.Button(
            button_frame, 
            text="Apply Styling", 
            command=self._on_apply,
            bootstyle="success"
        )
        apply_button.pack(side="right", padx=(5, 0))
        
        # Cancel button
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self._on_cancel,
            bootstyle="secondary"
        )
        cancel_button.pack(side="right")
        
        # Bind keyboard shortcuts
        self.content_frame.bind("<Return>", lambda e: self._on_apply())
        self.content_frame.bind("<Escape>", lambda e: self._on_cancel())
        
        # Focus handling for keyboard events
        self.content_frame.focus_set()
        
    def focus_main_widget(self):
        """Focus the intensity scale."""
        if self.intensity_scale:
            self.intensity_scale.focus_set()
            
    def _update_value_label(self, *args):
        """Update the current value display."""
        current_value = int(self.intensity_var.get())
        if hasattr(self, 'value_label'):
            self.value_label.config(text=f"Current: {current_value}")
            
    def _on_apply(self):
        """Handle apply button click."""
        self.intensity = int(self.intensity_var.get())
        self.cancelled = False
        
        if self.on_confirm_callback:
            self.on_confirm_callback(self.intensity)
            
        self.close_panel()
        
    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancelled = True
        
        if self.on_cancel_callback:
            self.on_cancel_callback()
            
        self.close_panel()
        
    def _on_close(self):
        """Handle panel close event."""
        if self.cancelled and self.on_cancel_callback:
            self.on_cancel_callback()