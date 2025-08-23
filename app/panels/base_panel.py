"""
Base panel interface for integrated sidebar panels.
"""

from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


class BasePanel(ABC):
    """
    Abstract base class for integrated sidebar panels.
    
    Defines the interface that all integrated panels must implement
    to work with the PanelManager system.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter: Callable, 
                 on_close_callback: Optional[Callable] = None):
        """
        Initialize the base panel.
        
        Args:
            parent_container: The container widget for this panel
            theme_getter: Function to get theme settings
            on_close_callback: Callback when panel is closed
        """
        self.parent_container = parent_container
        self.theme_getter = theme_getter
        self.on_close_callback = on_close_callback
        
        # Main panel container
        self.panel_frame: Optional[tk.Widget] = None
        self.header_frame: Optional[tk.Widget] = None
        self.content_frame: Optional[tk.Widget] = None
        self.close_button: Optional[tk.Widget] = None
        
        # Panel state
        self.is_visible = False
        self.is_focused = False
        
    @abstractmethod
    def get_panel_title(self) -> str:
        """Get the display title for this panel."""
        pass
    
    @abstractmethod
    def create_content(self) -> None:
        """Create the main content of the panel."""
        pass
    
    @abstractmethod
    def focus_main_widget(self) -> None:
        """Focus the main interactive widget of this panel."""
        pass
    
    def create_panel(self) -> tk.Widget:
        """
        Create the complete panel with header and content.
        
        Returns:
            The main panel widget
        """
        # Main panel frame
        self.panel_frame = ttk.Frame(self.parent_container)
        self.panel_frame.grid_rowconfigure(1, weight=1)
        self.panel_frame.grid_columnconfigure(0, weight=1)
        
        # Create header with title and close button
        self._create_header()
        
        # Create content area
        self.content_frame = ttk.Frame(self.panel_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Let subclass create its content
        self.create_content()
        
        return self.panel_frame
    
    def _create_header(self):
        """Create the panel header with title and close button."""
        self.header_frame = ttk.Frame(self.panel_frame, padding=(5, 5, 5, 0))
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        # Panel title
        title_label = ttk.Label(
            self.header_frame,
            text=self.get_panel_title(),
            font=("Segoe UI", 9, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Close button
        self.close_button = ttk.Button(
            self.header_frame,
            text="×",
            width=3,
            command=self._handle_close
        )
        self.close_button.grid(row=0, column=1, sticky="e")
    
    def _handle_close(self):
        """Handle close button click."""
        self.hide()
        if self.on_close_callback:
            self.on_close_callback(self)
    
    def show(self):
        """Show this panel."""
        if self.panel_frame and self.parent_container:
            # Pack the panel frame in its parent container
            self.panel_frame.pack(fill="both", expand=True)
            self.is_visible = True
            self.focus_main_widget()
    
    def hide(self):
        """Hide this panel."""
        if self.panel_frame:
            self.panel_frame.pack_forget()
            self.is_visible = False
            self.is_focused = False
    
    def destroy(self):
        """Destroy this panel and cleanup resources."""
        if self.panel_frame:
            self.panel_frame.destroy()
            self.panel_frame = None
        self.is_visible = False
        self.is_focused = False
    
    def on_focus_gained(self):
        """Called when this panel gains focus."""
        self.is_focused = True
        self.focus_main_widget()
    
    def on_focus_lost(self):
        """Called when this panel loses focus."""
        self.is_focused = False
    
    def get_theme_color(self, color_name: str, default: str = "#ffffff") -> str:
        """Get theme color with fallback."""
        if self.theme_getter:
            return self.theme_getter(color_name, default)
        return default