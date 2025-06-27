import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import platform
import sv_ttk # Import sv_ttk

# Global variables for main widgets and state (managed within this module)
root = None
notebook = None
tabs = {} # Dictionary to hold EditorTab instances, managed by gui_file_tab_manager
outline_tree = None
llm_progress_bar = None
status_bar = None
welcome_screen = None
main_pane = None

def setup_gui():
    """Sets up the main application window and its core widgets.
    Returns a dictionary of these initialized components for other modules to use.
    """
    global root, notebook, outline_tree, llm_progress_bar, status_bar, main_pane, welcome_screen, tabs

    root = tk.Tk()
    root.title("AutomaTeX v1.0")
    root.geometry("1200x800") # Adjusted default size
    
    # --- Top Buttons Frame ---
    top_frame = ttk.Frame(root, padding=10)
    top_frame.pack(fill="x", pady=(0, 5))

    # --- Main Paned Window (Outline Tree + Editor) ---
    # PanedWindow allows resizing the panes by dragging the sash
    main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
    main_pane.pack(fill="both", expand=True)

    # --- Left Outline Tree Frame ---
    outline_frame = ttk.Frame(main_pane)
    # Treeview to display document outline
    outline_tree = ttk.Treeview(outline_frame, show="tree")
    outline_tree.pack(fill="both", expand=True)
    # Binding for outline tree selection will be set in main.py after gui_file_tab_manager is ready.
    main_pane.add(outline_frame, width=250, minsize=150)

    # --- Editor Notebook Frame ---
    notebook_frame = ttk.Frame(main_pane)

    # Welcome Screen, placed inside the notebook_frame
    welcome_screen = ttk.Frame(notebook_frame, padding=40)
    
    welcome_title = ttk.Label(welcome_screen, text="Welcome to AutomaTeX", font=("Segoe UI", 24, "bold"))
    welcome_title.pack(pady=(20, 10))
    
    welcome_subtitle = ttk.Label(welcome_screen, text="Your AI-powered LaTeX Editor", font=("Segoe UI", 14))
    welcome_subtitle.pack(pady=(0, 40))

    # Frame to hold buttons on the welcome screen (buttons added by gui_file_tab_manager)
    button_frame = ttk.Frame(welcome_screen)
    button_frame.pack(pady=20)

    notebook = ttk.Notebook(notebook_frame)
    # Binding for notebook tab changes will be set in gui_file_tab_manager.
    main_pane.add(notebook_frame, stretch="always", minsize=400)

    # --- LLM Progress Bar ---
    llm_progress_bar = ttk.Progressbar(root, mode="indeterminate", length=200)
    # Packing is handled by llm_service functions when it's shown/hidden.

    # --- Status Bar ---
    status_bar = ttk.Label(root, text="⏳ Initializing...", anchor="w", relief=tk.FLAT, padding=(5, 3))
    status_bar.pack(side="bottom", fill="x")

    # Return all created widgets and global state holders for other modules to use
    return {
        "root": root,
        "top_frame": top_frame,
        "main_pane": main_pane,
        "outline_tree": outline_tree,
        "notebook": notebook,
        "welcome_screen": welcome_screen,
        "welcome_button_frame": button_frame, # Pass this frame to add buttons to it
        "llm_progress_bar": llm_progress_bar,
        "status_bar": status_bar,
        "tabs_dict": tabs # The global dictionary to be managed by gui_file_tab_manager
    }

def on_close_request(save_file_func, root_ref, tabs_dict_ref, show_status_message_func):
    """Handles closing the main window, checking for unsaved changes."""
    if not root_ref: # Guard against calling if root is already destroyed
        return

    dirty_tabs = [tab for tab in tabs_dict_ref.values() if tab.is_dirty()]

    if dirty_tabs:
        file_list = "\n - ".join([os.path.basename(tab.file_path) if tab.file_path else "Untitled" for tab in dirty_tabs])
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            f"You have unsaved changes in the following files:\n - {file_list}\n\nDo you want to save them before closing?",
            parent=root_ref
        )
        if response is True:  # Yes, save and close
            all_saved = True
            for tab in dirty_tabs:
                # Pass the specific tab to the save function
                if not save_file_func(show_status_message_func, tab_to_save=tab):
                    all_saved = False
                    break # User cancelled a "Save As" dialog
            if all_saved:
                root_ref.destroy() # Close if all saves were successful
        elif response is False: # No, just close
            root_ref.destroy()
        # else: Cancel, do nothing and the window stays open.
    else:
        # No unsaved changes, just close.
        root_ref.destroy()