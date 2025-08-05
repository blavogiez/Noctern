"""
This module is responsible for creating the main layout panes of the AutomaTeX
application, including the main paned window that separates the editor and the
outline, the outline tree view, the editor notebook, and the console pane.
"""

import ttkbootstrap as ttk
from tkinter.font import Font
from app.custom_notebook import ClosableNotebook

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

def create_outline_tree(parent, get_current_tab_callback):
    """
    Creates the treeview widget used to display the document's outline.

    Args:
        parent (tk.Widget): The parent widget for the treeview.
        get_current_tab_callback (callable): A function to get the current editor tab.

    Returns:
        ttk.Treeview: The configured treeview for the document outline.
    """
    outline_tree = ttk.Treeview(parent, show="tree", selectmode="browse")
    parent.add(outline_tree, weight=1) # Add to paned window with a weight

    def on_tree_select(event):
        """Callback to handle selection changes in the outline tree."""
        from editor import outline as editor_outline
        editor_outline.go_to_section(get_current_tab_callback, event)


    outline_tree.bind("<<TreeviewSelect>>", on_tree_select)
    return outline_tree

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

