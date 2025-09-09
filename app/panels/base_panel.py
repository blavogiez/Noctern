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
    
    def get_critical_action_buttons(self) -> list:
        """
        Get critical action buttons that must ALWAYS be visible.
        
        Returns:
            List of (text, callback, style) tuples for critical actions.
            These buttons will be guaranteed visible at the bottom of the panel.
            
        Example:
            return [
                ("Save", self._save, "primary"),
                ("Cancel", self._cancel, "secondary")
            ]
        """
        return []
    
    def has_unsaved_changes(self) -> bool:
        """Check if panel has unsaved changes. Override in subclass if needed."""
        return False
    
    def create_panel(self) -> tk.Widget:
        """
        Create the complete panel with header and content.
        
        Returns:
            The main panel widget
        """
        # Main panel frame with 3-row layout: header / content / critical_actions
        self.panel_frame = ttk.Frame(self.parent_container)
        self.panel_frame.grid_rowconfigure(1, weight=1)  # Content row expands
        self.panel_frame.grid_columnconfigure(0, weight=1)
        
        # Create header with title and close button (row 0)
        self._create_header()
        
        # Create content area using standardized layout (row 1 - expandable)
        self.content_frame = ttk.Frame(self.panel_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Build sticky-scroll layout: scrollable content + sticky footer
        from .panel_factory import PanelLayoutManager
        scroll_inner, self._scroll_canvas, self._footer_frame = PanelLayoutManager.create_sticky_scroll_layout(self.content_frame)

        # Create standardized layout based on panel style inside scroll area
        layout_style = self.get_layout_style()
        self.main_container = PanelFactory.create_panel_structure(scroll_inner, layout_style, scroll_context=True)
        
        # Let subclass create its content
        self.create_content()
        
        # Create critical actions container (row 2 - always visible at bottom)
        self._create_critical_actions()
        
        # Allow subclass to link button references after creation
        self._link_critical_button_references()
        
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
        close_button = ttk.Button(
            self.header_frame,
            text="×",
            width=3,
            command=self._handle_close
        )
        close_button.grid(row=0, column=1, sticky="e", padx=(StandardComponents.PADDING//2, 0))
    
    def _create_critical_actions(self):
        """Create critical actions container that ensures buttons are always visible."""
        critical_buttons = self.get_critical_action_buttons()
        if critical_buttons:
            # Put critical actions in sticky footer (outside scroll area)
            self.critical_actions_container = StandardComponents.create_critical_actions_container(
                self._footer_frame,
                critical_buttons
            )
            
            # Store reference to button widgets if needed by subclass
            if self.critical_actions_container:
                button_row_frame = None
                for child in self.critical_actions_container.winfo_children():
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, ttk.Frame):
                            button_row_frame = grandchild
                            break
                    if button_row_frame:
                        break
                
                if button_row_frame:
                    self.critical_action_buttons = button_row_frame.winfo_children()
                else:
                    self.critical_action_buttons = []
        else:
            self.critical_actions_container = None
            self.critical_action_buttons = []
    
    def _link_critical_button_references(self):
        """
        Allow subclass to link button references after creation.
        Override in subclass if needed to store specific button references.
        """
        pass
    
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
