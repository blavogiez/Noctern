"""
Image details panel for collecting image caption and label information.

This panel is used when pasting images from clipboard, providing a clean
interface for entering image metadata in the left sidebar.
"""

from tkinter import ttk
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents


class ImageDetailsPanel(BasePanel):
    """Panel for collecting image details including caption and label."""
    
    def __init__(self, parent_container, theme_getter, suggested_label, 
                 on_ok_callback=None, on_cancel_callback=None):
        """
        Initialize the image details panel.
        
        Args:
            parent_container: Parent container widget
            theme_getter: Function to get theme colors
            suggested_label: Suggested label text
            on_ok_callback: Callback when OK is pressed
            on_cancel_callback: Callback when cancelled
        """
        super().__init__(parent_container, theme_getter, self._on_close)
        
        self.suggested_label = suggested_label
        self.on_ok_callback = on_ok_callback
        self.on_cancel_callback = on_cancel_callback
        
        # Result storage
        self.caption = ""
        self.label = ""
        self.cancelled = True
        
        # UI elements
        self.caption_entry = None
        self.label_entry = None
        
    def get_panel_title(self) -> str:
        """Return the panel title."""
        return "Image Details"
        
    def get_layout_style(self) -> PanelStyle:
        """Use simple layout for image details."""
        return PanelStyle.SIMPLE
    
    def get_critical_action_buttons(self) -> list:
        """Return critical action buttons for this panel."""
        return [
            ("OK", self._on_ok, "success"),
            ("Cancel", self._on_cancel, "secondary")
        ]
    
    def create_content(self):
        """Create the image details form content using standardized components."""
        # Use standardized main container
        main_frame = self.main_container
        
        # Caption input section
        caption_section = StandardComponents.create_section(main_frame, "Image Caption")
        caption_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        self.caption_entry = StandardComponents.create_entry_input(caption_section, "Enter image caption...")
        self.caption_entry.pack(fill="x", padx=StandardComponents.PADDING, pady=StandardComponents.PADDING)
        
        # Label input section
        label_section = StandardComponents.create_section(main_frame, "Image Label")
        label_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        self.label_entry = StandardComponents.create_entry_input(label_section)
        self.label_entry.pack(fill="x", padx=StandardComponents.PADDING, pady=StandardComponents.PADDING)
        self.label_entry.insert(0, self.suggested_label)
        
        # Set main widget for focus
        self.main_widget = self.caption_entry
        
        # Bind keyboard shortcuts
        self.caption_entry.bind("<Return>", lambda e: self._on_ok())
        self.label_entry.bind("<Return>", lambda e: self._on_ok())
        main_frame.bind("<Escape>", lambda e: self._on_cancel())
        
        # Focus on main widget
        self.caption_entry.focus_set()
        
    def focus_main_widget(self):
        """Focus the caption entry field."""
        if self.caption_entry:
            self.caption_entry.focus_set()
            
    def _on_ok(self):
        """Handle OK button click."""
        self.caption = self.caption_entry.get().strip()
        self.label = self.label_entry.get().strip()
        
        if not self.label:
            # Show warning using standard messagebox
            from tkinter import messagebox
            messagebox.showwarning(
                "Image Label Required",
                "The image label cannot be empty.",
                parent=self.panel_frame
            )
            return
            
        self.cancelled = False
        
        if self.on_ok_callback:
            self.on_ok_callback(self.caption, self.label)
            
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