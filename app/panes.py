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

"""
This module is responsible for creating the main layout panes of the AutomaTeX
application, including the main paned window that separates the editor and the
outline, the outline tree view, the editor notebook, and the console pane.
"""

import ttkbootstrap as ttk
from tkinter.font import Font
from app import main_window as mw
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
        selected_item = outline_tree.selection()
        if selected_item:
            line_number = outline_tree.item(selected_item, "tags")[0]
            current_tab = get_current_tab_callback()
            if current_tab and current_tab.editor:
                current_tab.editor.see(f"{line_number}.0")
                current_tab.editor.mark_set("insert", f"{line_number}.0")
                current_tab.editor.focus_set()

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

