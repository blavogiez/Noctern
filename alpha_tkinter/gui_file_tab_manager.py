import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

# Import EditorTab class
from editor_tab import EditorTab

# References to main GUI components and callbacks
_notebook = None
_tabs = None # Dictionary to hold EditorTab instances
_welcome_screen = None
_root = None
_on_tab_changed_callback = None # Callback for when a tab changes (e.g., to load LLM history)
_schedule_heavy_updates_callback = None # Callback to schedule heavy updates
_apply_theme_callback = None # Callback to apply the current theme

def initialize(notebook_ref, tabs_dict_ref, welcome_screen_ref, root_ref, on_tab_changed_cb, schedule_heavy_updates_cb, welcome_button_frame_ref, apply_theme_cb):
    """Initializes the file and tab manager with necessary GUI component references."""
    global _notebook, _tabs, _welcome_screen, _root, _on_tab_changed_callback, _schedule_heavy_updates_callback, _apply_theme_callback
    _notebook = notebook_ref
    _tabs = tabs_dict_ref
    _welcome_screen = welcome_screen_ref
    _root = root_ref
    _on_tab_changed_callback = on_tab_changed_cb
    _schedule_heavy_updates_callback = schedule_heavy_updates_cb
    _apply_theme_callback = apply_theme_cb

    _notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    # Add buttons to the welcome screen
    ttk.Button(welcome_button_frame_ref, text="📄 New File (Ctrl+N)", command=lambda: create_new_tab(file_path=None)).pack(side="left", padx=10, ipady=5)
    ttk.Button(welcome_button_frame_ref, text="📂 Open File (Ctrl+O)", command=lambda: open_file(None)).pack(side="left", padx=10, ipady=5) # Pass None for status func, will be provided by main.py

def get_current_tab():
    """Returns the currently active EditorTab object, or None."""
    if not _notebook or not _tabs:
        return None
    try:
        selected_tab_id = _notebook.select()
        return _tabs.get(selected_tab_id)
    except tk.TclError: # Happens if no tabs are present
        return None

def toggle_welcome_screen():
    """Shows or hides the welcome screen based on whether tabs are open."""
    if not _welcome_screen or not _notebook:
        return

    if not _tabs: # No tabs are open
        _notebook.pack_forget()
        _welcome_screen.pack(fill="both", expand=True)
    else: # Tabs are open
        _welcome_screen.pack_forget()
        _notebook.pack(fill="both", expand=True)

def create_new_tab(file_path=None):
    """Creates a new EditorTab, adds it to the notebook, and selects it."""
    # Check if file is already open
    if file_path:
        for tab in _tabs.values():
            if tab.file_path == file_path:
                _notebook.select(tab)
                return

    is_first_tab = not _tabs

    new_tab = EditorTab(_notebook, file_path=file_path, schedule_heavy_updates_callback=_schedule_heavy_updates_callback)
    
    _notebook.add(new_tab, text=os.path.basename(file_path) if file_path else "Untitled")
    _notebook.select(new_tab)
    
    _tabs[str(new_tab)] = new_tab
    
    if is_first_tab:
        toggle_welcome_screen()

    # Apply the current theme to ensure the new tab's widgets are styled correctly.
    if _apply_theme_callback:
        _apply_theme_callback()

    # Trigger updates for the new tab (e.g., LLM history, syntax highlighting)
    on_tab_changed()

    # Now that the tab is added to the notebook, load its content
    new_tab.load_file()

def open_file(show_temporary_status_message_func):
    """Opens a file and loads its content into the editor."""
    filepath = filedialog.askopenfilename(
        title="Open File",
        filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if filepath:
        create_new_tab(file_path=filepath)
        if show_temporary_status_message_func:
            show_temporary_status_message_func(f"✅ Opened: {os.path.basename(filepath)}")

def save_file(show_temporary_status_message_func):
    """Saves the current editor content to the current file or a new file."""
    current_tab = get_current_tab()
    if not current_tab:
        return False

    if current_tab.file_path:
        if current_tab.save_file():
            if show_temporary_status_message_func:
                show_temporary_status_message_func(f"✅ Saved: {os.path.basename(current_tab.file_path)}")
            return True
        return False
    else:
        return save_file_as(show_temporary_status_message_func)

def save_file_as(show_temporary_status_message_func):
    """Saves the current tab to a new file path."""
    current_tab = get_current_tab()
    if not current_tab:
        return False

    new_filepath = filedialog.asksaveasfilename(
        defaultextension=".tex",
        filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")],
        title="Save File As"
    )
    if new_filepath:
        if current_tab.save_file(new_path=new_filepath):
            if show_temporary_status_message_func:
                show_temporary_status_message_func(f"✅ Saved as: {os.path.basename(new_filepath)}")
            # Update services that depend on file path (e.g., LLM prompts/history)
            on_tab_changed()
            return True
    return False

def close_current_tab():
    """Closes the currently active tab."""
    current_tab = get_current_tab()
    if not current_tab:
        return

    if current_tab.is_dirty():
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            f"The file '{os.path.basename(current_tab.file_path) if current_tab.file_path else 'Untitled'}' has unsaved changes. Do you want to save before closing it?",
            parent=_root
        )
        if response is True: # Yes
            if not save_file(lambda x: None): # Pass a dummy status message func
                return # User cancelled save, so don't close tab
        elif response is None: # Cancel
            return

    tab_id = _notebook.select()
    _notebook.forget(tab_id)
    del _tabs[tab_id]

    toggle_welcome_screen()

def on_tab_changed(event=None):
    """Handles logic when the active tab changes."""
    # This callback triggers updates in other modules (LLM service, editor view)
    if _on_tab_changed_callback:
        _on_tab_changed_callback()