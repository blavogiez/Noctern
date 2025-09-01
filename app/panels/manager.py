"""
Panel manager for the left sidebar container.

Manages the display of different panels in the left sidebar area using
pure superposition. Multiple panels can be active but only the most recent
one is visible, overlaying the others.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Callable, List
from .base_panel import BasePanel


class PanelManager:
    """
    Manages panels in the left sidebar container using pure superposition.
    
    Multiple panels can be active simultaneously, but only the most recently
    opened panel is visible. Panels are superimposed on the same space,
    with the newest one on top.
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
        
        # Panel management - pure superposition
        self.active_panels: Dict[int, BasePanel] = {}  # panel_id -> panel
        self.panel_stack: List[int] = []  # Stack of panel IDs (newest last)
        
        # UI components
        self.panel_container: Optional[tk.Widget] = None
        
        # Store original widgets state
        self._original_widgets_visible = True
        
    def show_panel(self, panel: BasePanel) -> None:
        """
        Show a panel using pure superposition. Only the newest panel is visible.
        
        Args:
            panel: The panel to display
        """
        panel_id = id(panel)
        
        # If this panel is already active, bring it to front
        if panel_id in self.active_panels:
            self._bring_to_front(panel_id)
            return
            
        # Hide original widgets on first panel
        if not self.active_panels and self._original_widgets_visible:
            self._hide_original_widgets()
        
        # Create panel container if needed
        if not self.panel_container:
            self._create_panel_container()
            
        # Hide current top panel if any
        if self.panel_stack:
            current_top = self.active_panels[self.panel_stack[-1]]
            current_top.hide()
            
        # Set up the new panel
        panel.parent_container = self.panel_container
        panel.on_close_callback = lambda panel: self._on_panel_closed(panel_id)
        
        # Create and show the panel
        panel_widget = panel.create_panel()
        panel.show()
        
        # Add to active panels and stack
        self.active_panels[panel_id] = panel
        self.panel_stack.append(panel_id)
        
        # Focus the new panel
        try:
            panel.focus_main_widget()
        except:
            # Fallback with minimal delay if immediate focus fails
            self.left_pane.after(10, panel.focus_main_widget)
            
    def _bring_to_front(self, panel_id: int):
        """Bring an existing panel to the front of the stack."""
        if panel_id not in self.active_panels:
            return
            
        # Hide current top panel
        if self.panel_stack and self.panel_stack[-1] != panel_id:
            current_top = self.active_panels[self.panel_stack[-1]]
            current_top.hide()
            
        # Move panel to front of stack
        if panel_id in self.panel_stack:
            self.panel_stack.remove(panel_id)
        self.panel_stack.append(panel_id)
        
        # Show the panel
        panel = self.active_panels[panel_id]
        panel.show()
        
        # Focus the panel
        try:
            panel.focus_main_widget()
        except:
            self.left_pane.after(10, panel.focus_main_widget)
            
    def _create_panel_container(self):
        """Create the container for superimposed panels."""
        # Single container that fills the left pane - panels will superimpose here
        self.panel_container = ttk.Frame(self.left_pane)
        self.left_pane.add(self.panel_container, weight=1)
        
        
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
        
    def _on_panel_closed(self, panel_id: int):
        """Handle panel close event."""
        if panel_id not in self.active_panels:
            return
            
        # Remove panel from active list and stack
        panel = self.active_panels[panel_id]
        panel.destroy()
        del self.active_panels[panel_id]
        
        if panel_id in self.panel_stack:
            self.panel_stack.remove(panel_id)
        
        # If there are remaining panels, show the new top panel
        if self.panel_stack:
            new_top_id = self.panel_stack[-1]
            new_top_panel = self.active_panels[new_top_id]
            new_top_panel.show()
            try:
                new_top_panel.focus_main_widget()
            except:
                pass
        else:
            # No panels left - restore original widgets
            self._show_original_widgets()
            
    def is_panel_active(self) -> bool:
        """Check if any panel is currently active."""
        return len(self.active_panels) > 0
        
    def get_active_panels(self) -> Dict[int, BasePanel]:
        """Get all currently active panels."""
        return self.active_panels.copy()
        
    def get_current_panel(self) -> Optional[BasePanel]:
        """Get the currently visible panel (top of stack)."""
        if self.panel_stack:
            return self.active_panels[self.panel_stack[-1]]
        return None
        
    def close_current_panel(self):
        """Close the currently visible panel."""
        if self.panel_stack:
            top_panel_id = self.panel_stack[-1]
            self._on_panel_closed(top_panel_id)
    
    def close_all_panels(self):
        """Close all active panels."""
        panel_ids = list(self.active_panels.keys())
        for panel_id in panel_ids:
            self._on_panel_closed(panel_id)