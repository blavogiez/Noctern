"""
This module is responsible for creating and configuring the main pane layout
of the application, including the paned window, the document outline treeview,
and the tabbed notebook for editor instances.
"""

from tkinter import ttk
import tkinter as tk
from editor import logic as editor_logic

def create_main_paned_window(root):
    """
    Creates and configures the main horizontal paned window for the application.

    This paned window allows the user to resize the sections for the document
    outline and the main editor area.

    Args:
        root (tk.Tk): The root Tkinter window of the application.

    Returns:
        tk.PanedWindow: The configured main paned window widget.
    """
    # Create a horizontal paned window with a flat sash relief and a specified sash width.
    main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
    main_pane.pack(fill="both", expand=True) # Make the paned window fill and expand within its parent.
    return main_pane

def create_outline_tree(main_pane, get_current_tab_func):
    """
    Creates and configures the document outline Treeview widget.

    This Treeview displays the hierarchical structure of the LaTeX document
    (sections, subsections, etc.) and allows users to navigate to specific
    sections within the editor.

    Args:
        main_pane (tk.PanedWindow): The main paned window to which the outline tree will be added.
        get_current_tab_func (callable): A callback function to retrieve the currently active editor tab.
                                         Expected signature: `get_current_tab_func()` returning an EditorTab instance.

    Returns:
        ttk.Treeview: The configured outline Treeview widget.
    """
    outline_frame = ttk.Frame(main_pane) # Create a frame to contain the Treeview.
    outline_tree = ttk.Treeview(outline_frame, show="tree") # Create the Treeview, showing only the tree column.
    outline_tree.pack(fill="both", expand=True) # Make the Treeview fill and expand within its frame.
    
    # Bind the TreeviewSelect event to a lambda function that calls editor_logic.go_to_section.
    # This allows navigation within the editor when a section in the outline is selected.
    outline_tree.bind(
        "<<TreeviewSelect>>",
        lambda event: editor_logic.go_to_section(
            # Safely access the editor widget from the current tab, if available.
            get_current_tab_func().editor if get_current_tab_func() and get_current_tab_func().editor else None,
            event
        )
    )
    # Add the outline frame to the main paned window with an initial width and minimum size.
    main_pane.add(outline_frame, width=250, minsize=150)
    return outline_tree

def create_notebook(main_pane):
    """
    Creates and configures the tabbed notebook widget for editor instances.

    This notebook will host individual `EditorTab` instances, each representing
    an open document.

    Args:
        main_pane (tk.PanedWindow): The main paned window to which the notebook will be added.

    Returns:
        ttk.Notebook: The configured notebook widget.
    """
    notebook_frame = ttk.Frame(main_pane) # Create a frame to contain the notebook.
    notebook = ttk.Notebook(notebook_frame) # Create the ttk.Notebook widget.
    notebook.pack(fill="both", expand=True) # Make the notebook fill and expand within its frame.
    
    # Add the notebook frame to the main paned window.
    # It is set to stretch and has a minimum size to ensure visibility.
    main_pane.add(notebook_frame, stretch="always", minsize=400)
    return notebook
