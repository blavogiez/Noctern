"""
Base panel interface for integrated sidebar panels.
"""

from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from .panel_factory import PanelFactory, StandardComponents, PanelStyle, StandardPanelBehavior


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
    
    @abstractmethod
    def get_layout_style(self) -> PanelStyle:
        """Get the layout style for this panel."""
        pass
    
    def has_unsaved_changes(self) -> bool:
        """Check if panel has unsaved changes. Override in subclass if needed."""
        return False
    
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
        
        # Create content area using standardized layout
        self.content_frame = ttk.Frame(self.panel_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Create standardized layout based on panel style
        layout_style = self.get_layout_style()
        self.main_container = PanelFactory.create_panel_structure(self.content_frame, layout_style)
        
        # Let subclass create its content
        self.create_content()
        
        # Setup standard behaviors
        self._setup_standard_behaviors()
        
        return self.panel_frame
    
    def _create_header(self):
        """Create the panel header with title and close button."""
        self.header_frame = ttk.Frame(self.panel_frame, padding=(StandardComponents.PADDING//2, StandardComponents.PADDING//2, StandardComponents.PADDING//2, 0))
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        # Panel title using standard font
        title_label = ttk.Label(
            self.header_frame,
            text=self.get_panel_title(),
            font=StandardComponents.TITLE_FONT
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
        """Handle close button click with unsaved changes check."""
        # Check for unsaved changes
        if self.has_unsaved_changes():
            action = StandardPanelBehavior.create_standard_close_confirm(self.get_panel_title(), True)
            if action == "save":
                self._save_changes()
            elif action == "cancel":
                return  # Don't close
            # "close" continues to close without saving
        
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
    
    def close_panel(self):
        """Close this panel (alias for _handle_close)."""
        self._handle_close()
    
    def _setup_standard_behaviors(self):
        """Setup standard panel behaviors including escape binding."""
        if self.panel_frame:
            # Bind Escape key to close panel
            self.panel_frame.bind('<Escape>', lambda e: self.close_panel())
            if self.content_frame:
                self.content_frame.bind('<Escape>', lambda e: self.close_panel())
            
            # Setup standard behaviors
            main_widget = getattr(self, 'main_widget', self.content_frame)
            StandardPanelBehavior.setup_common_bindings(self, main_widget)
            
            # Make sure frames can receive focus for key events
            self.panel_frame.focus_set()
            self.content_frame.focus_set()
    
    def _save_changes(self):
        """Save changes. Override in subclass if panel supports saving."""
        pass