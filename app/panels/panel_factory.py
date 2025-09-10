"""
Panel Factory and Common UI Components for consistent panel behavior.

This module provides a unified interface for creating panels with consistent
layouts, styling, and behaviors across the entire application.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Tuple
from enum import Enum


class PanelStyle(Enum):
    """Standard panel styles."""
    SIMPLE = "simple"           # Basic form layout
    SCROLLABLE = "scrollable"   # With scrollbar
    SPLIT = "split"            # Split panes (horizontal/vertical)
    TABBED = "tabbed"          # Tabbed interface


class StandardComponents:
    """Factory for creating standardized UI components."""
    
    # Standard measurements - clean spacing
    PADDING = 12
    SECTION_SPACING = 20
    BUTTON_SPACING = 8
    ELEMENT_SPACING = 6
    STANDARD_WIDTH = 420  # Optimal for 1/4 screen width
    
    # Standard fonts - clean and consistent, no bold
    TITLE_FONT = ("Segoe UI", 10)
    BODY_FONT = ("Segoe UI", 9) 
    SMALL_FONT = ("Segoe UI", 8)
    CODE_FONT = ("Consolas", 9)
    
    @staticmethod
    def create_section(parent, title: str, collapsible: bool = False) -> ttk.Frame:
        """Create a standard section with consistent styling."""
        if title:
            section = ttk.LabelFrame(parent, text=f" {title} ", padding=StandardComponents.PADDING)
        else:
            section = ttk.Frame(parent, padding=StandardComponents.PADDING)
        return section
    
    @staticmethod
    def create_text_input(parent, placeholder: str = "", height: int = 3) -> tk.Text:
        """Create a standard text input widget."""
        text_widget = tk.Text(
            parent,
            height=height,
            font=StandardComponents.CODE_FONT,
            wrap="word",
            undo=True,
            relief="solid",
            borderwidth=1
        )
        
        if placeholder:
            text_widget.insert("1.0", placeholder)
            text_widget.config(foreground="gray")
            
            def on_focus_in(event):
                if text_widget.get("1.0", "end-1c") == placeholder:
                    text_widget.delete("1.0", "end")
                    text_widget.config(foreground="black")
            
            def on_focus_out(event):
                if not text_widget.get("1.0", "end-1c").strip():
                    text_widget.insert("1.0", placeholder)
                    text_widget.config(foreground="gray")
            
            text_widget.bind("<FocusIn>", on_focus_in)
            text_widget.bind("<FocusOut>", on_focus_out)
        
        return text_widget
    
    @staticmethod
    def create_entry_input(parent, placeholder: str = "", width: int = 25) -> ttk.Entry:
        """Create a standard entry input widget with optimal width for panels."""
        entry = ttk.Entry(parent, width=width, font=StandardComponents.BODY_FONT)
        
        if placeholder:
            entry.insert(0, placeholder)
            entry.config(foreground="gray")
            
            def on_focus_in(event):
                if entry.get() == placeholder:
                    entry.delete(0, tk.END)
                    entry.config(foreground="black")
            
            def on_focus_out(event):
                if not entry.get().strip():
                    entry.insert(0, placeholder)
                    entry.config(foreground="gray")
            
            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)
        
        return entry
    
    @staticmethod
    def create_combobox_input(parent, values: List[str], width: int = 20, state: str = "readonly") -> ttk.Combobox:
        """Create a standard combobox widget optimized for panels."""
        combo = ttk.Combobox(parent, values=values, width=width, state=state, font=StandardComponents.BODY_FONT)
        return combo
    
    @staticmethod
    def create_button_input(parent, text: str, command: Callable = None, width: int = 12) -> ttk.Button:
        """Create a standard button widget optimized for panels."""
        button = ttk.Button(parent, text=text, command=command, width=width)
        return button
    
    @staticmethod
    def create_grid_frame(parent, columns: int = 2, padding: int = 5) -> ttk.Frame:
        """Create a frame optimized for grid layouts in panels."""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=padding, pady=padding)
        
        # Configure columns to expand appropriately
        for i in range(columns):
            if i == columns - 1:  # Last column takes extra space
                frame.columnconfigure(i, weight=1)
            else:
                frame.columnconfigure(i, weight=0)
        
        return frame
    
    @staticmethod
    def create_label_input(parent, text: str, font_style: str = "BODY_FONT", width: int = None) -> ttk.Label:
        """Create a standard label optimized for panels."""
        font = getattr(StandardComponents, font_style, StandardComponents.BODY_FONT)
        label = ttk.Label(parent, text=text, font=font)
        if width:
            label.configure(wraplength=width)
        return label
    
    @staticmethod
    def create_button_row(parent, buttons: List[Tuple[str, Callable, str]]) -> ttk.Frame:
        """
        Create a standardized button row.
        
        Args:
            parent: Parent widget
            buttons: List of (text, callback, style) tuples
                    style can be: "primary", "success", "secondary", "danger"
        
        Returns:
            Frame containing the buttons
        """
        button_frame = ttk.Frame(parent)
        
        for i, (text, callback, style) in enumerate(buttons):
            # Map style to ttkbootstrap styles
            style_map = {
                "primary": "primary",
                "success": "success",
                "secondary": "secondary", 
                "danger": "danger"
            }
            
            button = ttk.Button(
                button_frame,
                text=text,
                command=callback,
                bootstyle=style_map.get(style, "secondary")
            )
            
            # Pack from right to left for consistent positioning
            button.pack(side="right", padx=(StandardComponents.BUTTON_SPACING if i > 0 else 0, 0))
        
        return button_frame
    
    @staticmethod
    def create_info_label(parent, text: str, style: str = "body") -> ttk.Label:
        """Create a standard info label."""
        font_map = {
            "title": StandardComponents.TITLE_FONT,
            "body": StandardComponents.BODY_FONT,
            "small": StandardComponents.SMALL_FONT
        }
        
        label = ttk.Label(
            parent,
            text=text,
            font=font_map.get(style, StandardComponents.BODY_FONT),
            wraplength=StandardComponents.STANDARD_WIDTH - 40
        )
        return label
    
    @staticmethod
    def create_critical_actions_container(parent, buttons: List[Tuple[str, Callable, str]]) -> ttk.Frame:
        """
        Create a critical actions container that ensures buttons are ALWAYS visible.
        
        This container is designed to be placed at the bottom of panels with guaranteed visibility.
        
        Args:
            parent: Parent widget
            buttons: List of (text, callback, style) tuples for critical actions
            
        Returns:
            Frame containing critical action buttons with guaranteed visibility
        """
        if not buttons:
            return None
            
        # Main container with visual separation
        critical_container = ttk.Frame(parent, relief="solid", borderwidth=1)
        critical_container.pack(side="bottom", fill="x", padx=2, pady=2)
        
        # Inner frame with padding for better visual appearance
        inner_frame = ttk.Frame(critical_container, padding=(StandardComponents.PADDING//2, StandardComponents.PADDING//4))
        inner_frame.pack(fill="x")
        
        # Create button row using existing standardized component
        button_row = StandardComponents.create_button_row(inner_frame, buttons)
        button_row.pack(fill="x")
        
        return critical_container


class PanelLayoutManager:
    """Manages consistent panel layouts."""
    
    @staticmethod
    def create_simple_layout(content_frame) -> ttk.Frame:
        """Create a simple vertical layout."""
        main_frame = ttk.Frame(content_frame, padding=StandardComponents.PADDING)
        main_frame.pack(fill="both", expand=True)
        return main_frame

    @staticmethod
    def create_vertical_stack_container(parent) -> ttk.Frame:
        """Create a container that mimics PanedWindow.add by stacking children vertically.

        Provides an .add(widget, weight=...) method to stay compatible with panels
        that expect a PanedWindow, while keeping content scroll-friendly.
        """
        class VerticalStackContainer(ttk.Frame):
            def add(self, widget, weight=1):
                try:
                    # If a raw widget was passed, ensure it is packed
                    widget.pack(fill="x", expand=True, padx=0, pady=(0, StandardComponents.SECTION_SPACING//2))
                except Exception:
                    pass
        container = VerticalStackContainer(parent)
        container.pack(fill="both", expand=True)
        return container
    
    @staticmethod
    def create_scrollable_layout(content_frame) -> Tuple[ttk.Frame, tk.Canvas]:
        """Create a scrollable layout."""
        # Create canvas and scrollbar
        canvas = tk.Canvas(content_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack elements
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add mousewheel support
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        return scrollable_frame, canvas

    @staticmethod
    def create_sticky_scroll_layout(parent) -> Tuple[ttk.Frame, tk.Canvas, ttk.Frame]:
        """Create a layout with a scrollable content area and a sticky footer.

        Returns a tuple of (scroll_inner_frame, canvas, footer_frame).
        The footer_frame is guaranteed to remain visible below the scroll area.
        """
        container = ttk.Frame(parent)
        container.grid(row=0, column=0, sticky="nsew")
        # Ensure container expands
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Create canvas + scrollbar (row 0)
        canvas = tk.Canvas(container, highlightthickness=0)
        vscroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Inner scroll frame
        scroll_inner = ttk.Frame(canvas)
        inner_window = canvas.create_window((0, 0), window=scroll_inner, anchor="nw")

        # Footer (row 1)
        footer_frame = ttk.Frame(container)
        footer_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Sync scrollregion and inner width
        def _on_inner_config(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scroll_inner.bind("<Configure>", _on_inner_config)

        def _on_canvas_config(event):
            try:
                canvas.itemconfigure(inner_window, width=event.width)
            except Exception:
                pass
        canvas.bind("<Configure>", _on_canvas_config)

        # Basic mouse wheel support (Windows)
        def _on_mousewheel(event):
            delta = event.delta
            if delta:
                canvas.yview_scroll(int(-1 * (delta/120)), "units")
        def _bind_wheel(_):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _unbind_wheel(_):
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)

        return scroll_inner, canvas, footer_frame
    
    @staticmethod
    def create_split_layout(content_frame, orientation=tk.VERTICAL) -> ttk.PanedWindow:
        """Create a split pane layout. Button visibility is ensured by repositioning in panels."""
        paned_window = ttk.PanedWindow(content_frame, orient=orientation)
        paned_window.pack(fill="both", expand=True)
        
        # Note: ttk.PanedWindow doesn't support minsize option like tk.PanedWindow
        # Button visibility is handled by repositioning buttons with side="bottom" in panels
        
        return paned_window
    
    @staticmethod
    def create_tabbed_layout(content_frame) -> ttk.Notebook:
        """Create a tabbed layout."""
        notebook = ttk.Notebook(content_frame)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        return notebook


class StandardPanelBehavior:
    """Standard behaviors for all panels."""
    
    @staticmethod
    def setup_common_bindings(panel, main_widget):
        """Setup common keyboard bindings for panels."""
        # Ensure the panel can receive focus
        if hasattr(panel, 'content_frame'):
            panel.content_frame.focus_set()
        
        # Setup tab navigation
        if hasattr(main_widget, 'bind'):
            main_widget.bind("<Tab>", lambda e: StandardPanelBehavior._focus_next_widget(e))
            main_widget.bind("<Shift-Tab>", lambda e: StandardPanelBehavior._focus_prev_widget(e))
    
    @staticmethod
    def _focus_next_widget(event):
        """Focus the next widget in tab order."""
        event.widget.tk_focusNext().focus()
        return "break"
    
    @staticmethod
    def _focus_prev_widget(event):
        """Focus the previous widget in tab order."""  
        event.widget.tk_focusPrev().focus()
        return "break"
    
    @staticmethod
    def create_standard_close_confirm(panel_name: str, has_unsaved_changes: bool = False) -> bool:
        """Standard confirmation dialog for panel close."""
        if has_unsaved_changes:
            from tkinter import messagebox
            result = messagebox.askyesnocancel(
                "Unsaved Changes Confirmation",
                f"The {panel_name} panel has unsaved changes.\n\nDo you want to save before closing?",
            )
            if result is True:  # Save
                return "save"
            elif result is False:  # Don't save
                return "close"
            else:  # Cancel
                return "cancel"
        return "close"


class PanelFactory:
    """Factory for creating consistent panels."""
    
    @staticmethod
    def create_panel_structure(content_frame, layout_style: PanelStyle, **kwargs):
        """
        Create a standardized panel structure.
        
        Args:
            content_frame: The panel's content frame
            layout_style: The type of layout to use
            **kwargs: Additional layout-specific parameters
            
        Returns:
            Main container and any additional components
        """
        if layout_style == PanelStyle.SIMPLE:
            return PanelLayoutManager.create_simple_layout(content_frame)
        
        elif layout_style == PanelStyle.SCROLLABLE:
            return PanelLayoutManager.create_scrollable_layout(content_frame)
        
        elif layout_style == PanelStyle.SPLIT:
            # When inside a scroll context, a PanedWindow hides content. Stack vertically instead.
            if kwargs.get('scroll_context'):
                return PanelLayoutManager.create_vertical_stack_container(content_frame)
            orientation = kwargs.get('orientation', tk.VERTICAL)
            return PanelLayoutManager.create_split_layout(content_frame, orientation)
        
        elif layout_style == PanelStyle.TABBED:
            return PanelLayoutManager.create_tabbed_layout(content_frame)
        
        else:
            # Fallback to simple
            return PanelLayoutManager.create_simple_layout(content_frame)
