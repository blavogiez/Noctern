"""
Panel manager for the left sidebar container.

Manages the display of different panels in the left sidebar area,
showing only one panel at a time with a close button.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Callable
from .base_panel import BasePanel


class PanelManager:
    """
    Manages panels in the left sidebar container.
    
    Shows one panel at a time, replacing the outline/debug content
    when a dialog is opened, and restoring it when closed.
    """
    
    def __init__(self, left_pane_container: tk.Widget, outline_widget: tk.Widget, 
                 debug_widget: tk.Widget, theme_getter: Callable):
        """
        Initialize the panel manager.
        
        Args:
            left_pane_container: The left pane container (vertical PanedWindow)
            outline_widget: The outline widget to show/hide
            debug_widget: The debug widget to show/hide  
            theme_getter: Function to get theme settings
        """
        self.left_pane = left_pane_container
        self.outline_widget = outline_widget
        self.debug_widget = debug_widget
        self.theme_getter = theme_getter
        
        # Panel management
        self.current_panel: Optional[BasePanel] = None
        self.panel_container: Optional[tk.Widget] = None
        
        # Store original widgets state
        self._original_widgets_visible = True
        
    def show_panel(self, panel: BasePanel) -> None:
        """
        Show a panel in the left sidebar, hiding outline/debug.
        
        Args:
            panel: The panel to display
        """
        # Hide current panel if any (but don't destroy for potential reuse)
        if self.current_panel:
            self.current_panel.hide()
            self.current_panel = None
            
        # Hide original widgets (outline + debug)
        if self._original_widgets_visible:
            self._hide_original_widgets()
        
        # Create panel container if needed
        if not self.panel_container:
            self._create_panel_container()
            
        # Set the parent container for the panel
        panel.parent_container = self.panel_container
        
        # Create and show the new panel efficiently
        panel.on_close_callback = self._on_panel_closed
        panel_widget = panel.create_panel()
        
        # Show immediately for ultra-fluid experience
        panel.show()
        self.current_panel = panel
        
        # Focus immediately without delay for maximum responsiveness
        try:
            panel.focus_main_widget()
        except:
            # Fallback with minimal delay if immediate focus fails
            self.left_pane.after(1, panel.focus_main_widget)
        
    def _create_panel_container(self):
        """Create the container for panels."""
        self.panel_container = ttk.Frame(self.left_pane)
        # Set minimum width to ensure panels are usable
        self.panel_container.configure(width=420)  # Slightly larger than STANDARD_WIDTH
        self.left_pane.add(self.panel_container, weight=1)
        
        # Configure minimum size efficiently
        try:
            self.left_pane.paneconfigure(self.panel_container, minsize=400)
        except tk.TclError:
            # Fallback: just set width if minsize is not supported
            pass
        
    def _hide_original_widgets(self):
        """Hide outline and debug widgets."""
        # Remove outline and debug from the pane
        for child in self.left_pane.panes():
            self.left_pane.remove(child)
        self._original_widgets_visible = False
        
    def _show_original_widgets(self):
        """Restore outline and debug widgets."""
        # Remove panel container
        if self.panel_container:
            try:
                self.left_pane.remove(self.panel_container)
            except tk.TclError:
                pass
            self.panel_container.destroy()
            self.panel_container = None
            
        # Restore original widgets
        self.left_pane.add(self.outline_widget, weight=1)
        self.left_pane.add(self.debug_widget, weight=1)
        self._original_widgets_visible = True
        
    def _on_panel_closed(self, panel: BasePanel):
        """Handle panel close event."""
        if panel == self.current_panel:
            self.current_panel.destroy()
            self.current_panel = None
            
            # Restore original widgets
            self._show_original_widgets()
            
    def is_panel_active(self) -> bool:
        """Check if a panel is currently active."""
        return self.current_panel is not None and self.current_panel.is_visible
        
    def get_current_panel(self) -> Optional[BasePanel]:
        """Get the currently active panel."""
        return self.current_panel
        
    def close_current_panel(self):
        """Close the current panel if any."""
        if self.current_panel:
            self._on_panel_closed(self.current_panel)