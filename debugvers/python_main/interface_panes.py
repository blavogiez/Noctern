from tkinter import ttk
import tkinter as tk
import editor_logic

def create_main_paned_window(root):
    main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
    main_pane.pack(fill="both", expand=True)
    return main_pane

def create_outline_tree(main_pane, get_current_tab_func):
    outline_frame = ttk.Frame(main_pane)
    outline_tree = ttk.Treeview(outline_frame, show="tree")
    outline_tree.pack(fill="both", expand=True)
    outline_tree.bind(
        "<<TreeviewSelect>>",
        lambda event: editor_logic.go_to_section(
            get_current_tab_func().editor if get_current_tab_func() and get_current_tab_func().editor else None,
            event
        )
    )
    main_pane.add(outline_frame, width=250, minsize=150)
    return outline_tree

def create_notebook(main_pane):
    notebook_frame = ttk.Frame(main_pane)
    notebook = ttk.Notebook(notebook_frame)
    notebook.pack(fill="both", expand=True)
    # The binding to on_tab_changed should be done in interface.py after import
    main_pane.add(notebook_frame, stretch="always", minsize=400)
    return notebook