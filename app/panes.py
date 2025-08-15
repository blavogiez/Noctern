"""
This module is responsible for creating the main layout panes of the AutomaTeX
application, including the main paned window that separates the editor and the
outline, the outline tree view, the editor notebook, and the console pane.
"""

import ttkbootstrap as ttk
from tkinter.font import Font
from app.custom_notebook import ClosableNotebook
from editor.outline import Outline


def create_main_paned_window(parent):
    """
    Creates the main horizontal paned window that divides the UI into a left
    (outline) and right (editor) section.

    Args:
        parent (tk.Widget): The parent widget to contain the paned window.

    Returns:
        ttk.PanedWindow: The configured horizontal paned window.
    """
    main_pane = ttk.PanedWindow(parent, orient=ttk.HORIZONTAL)
    main_pane.pack(fill="both", expand=True)
    return main_pane

def create_left_pane(parent):
    """
    Creates the left pane, containing the outline tree and the error panel.
    """
    left_pane = ttk.PanedWindow(parent, orient=ttk.VERTICAL)
    parent.add(left_pane, weight=1)
    return left_pane

def create_outline(parent, get_current_tab_callback, config_settings=None):
    """
    Creates the outline manager and its widget.

    Args:
        parent (tk.Widget): The parent widget for the treeview.
        get_current_tab_callback (callable): A function to get the current editor tab.
        config_settings (dict): Configuration settings for font customization.

    Returns:
        Outline: The configured Outline object.
    """
    outline = Outline(parent, get_current_tab_callback, config_settings)
    parent.add(outline.get_widget(), weight=1) # Add the widget to the pane
    return outline

def create_debug_panel(parent, on_goto_line=None):
    """
    Creates the debug panel with clean SOLID architecture.
    
    Args:
        parent: The parent widget for the debug panel
        on_goto_line: Callback for navigation to a specific line
        
    Returns:
        tuple: (debug_coordinator, debug_panel_widget)
    """
    try:
        from utils import debug_console
        debug_console.log("Creating debug panel", level='INFO')
        
        from debug_system.coordinator import create_debug_system
        
        # Create the debug system
        coordinator, debug_panel = create_debug_system(
            parent_window=parent,
            on_goto_line=on_goto_line
        )
        
        # Add the panel to the parent
        parent.add(debug_panel, weight=1)
        
        debug_console.log("Debug panel created successfully", level='SUCCESS')
        return coordinator, debug_panel
        
    except Exception as e:
        # Fallback to TeXstudio system if main system fails
        from utils import debug_console
        debug_console.log(f"Failed to create debug panel, falling back: {e}", level='WARNING')
        
        try:
            from debug_system.texstudio_debug_coordinator import TeXstudioDebugCoordinatorFactory
            
            coordinator, debug_panel = TeXstudioDebugCoordinatorFactory.create_default_coordinator(
                parent_window=parent,
                on_goto_line=on_goto_line
            )
            parent.add(debug_panel, weight=1)
            return coordinator, debug_panel
            
        except Exception as e2:
            debug_console.log(f"Fallback also failed: {e2}", level='ERROR')
            return create_error_panel_fallback(parent, on_goto_line)

def create_error_panel_fallback(parent, on_goto_line=None):
    """
    Fallback vers l'ancien error panel si le nouveau système échoue.
    """
    try:
        from pre_compiler.error_panel import ErrorPanel
        error_panel = ErrorPanel(parent, on_goto_line)
        parent.add(error_panel, weight=1)
        return None, error_panel
    except ImportError:
        # Dernier recours : placeholder simple
        placeholder_frame = ttk.Frame(parent)
        placeholder_label = ttk.Label(
            placeholder_frame, 
            text="Debug system unavailable", 
            foreground="#666", 
            font=('Arial', 9)
        )
        placeholder_label.pack(pady=20)
        parent.add(placeholder_frame, weight=1)
        return None, placeholder_frame

# Maintenir la compatibilité
def create_error_panel(parent, on_goto_line=None):
    """Alias pour compatibilité."""
    coordinator, panel = create_debug_panel(parent, on_goto_line)
    return panel

def create_notebook(parent):
    """
    Creates the main notebook widget for managing editor tabs.

    Args:
        parent (tk.Widget): The parent widget for the notebook.

    Returns:
        ClosableNotebook: The configured closable notebook widget.
    """
    notebook = ClosableNotebook(parent)
    parent.add(notebook, weight=4) # Add to paned window with a weight
    return notebook

def create_console_pane(parent):
    """
    Creates the console output pane at the bottom of the window.

    Args:
        parent (tk.Widget): The parent widget for the console pane.

    Returns:
        tuple: A tuple containing the console frame (ttk.Frame) and the
               console output Text widget (ttk.Text).
    """
    console_frame = ttk.Frame(parent, height=150, padding=5)
    
    console_output = ttk.Text(console_frame, wrap="word", state="disabled", height=10)
    console_output.pack(fill="both", expand=True)
    
    # Use a specific font for the console
    console_font = Font(family="Consolas", size=10)
    console_output.configure(font=console_font)

    return console_frame, console_output


def create_pdf_preview_pane(parent):
    """
    Creates the PDF preview pane for displaying compiled PDF documents.

    Args:
        parent (tk.Widget): The parent widget for the PDF preview pane.

    Returns:
        ttk.Frame: The frame containing the PDF preview components.
    """
    preview_frame = ttk.Frame(parent)
    
    # Header label
    header = ttk.Label(
        preview_frame, 
        text="PDF Preview", 
        font=("Arial", 12, "bold"),
        anchor="center"
    )
    header.pack(fill="x", padx=5, pady=5)
    
    # Separator
    separator = ttk.Separator(preview_frame, orient="horizontal")
    separator.pack(fill="x", padx=5)
    
    # This frame will be populated by the PDF preview module
    content_frame = ttk.Frame(preview_frame)
    content_frame.pack(fill="both", expand=True, padx=2, pady=2)
    
    # Note: We don't add to parent pane here as visibility is managed by ui_visibility module
    # Add frame to parent when needed
    
    return content_frame