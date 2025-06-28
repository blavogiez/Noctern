import tkinter as tk
from tkinter import ttk
import interface_zoom
import interface_statusbar
import interface_fileops
import interface_tabops
import interface_theme
from interface_topbar import create_top_buttons_frame
from interface_panes import create_main_paned_window, create_outline_tree, create_notebook
from interface_status import create_status_bar, start_gpu_status_loop
from interface_shortcuts import bind_shortcuts
from editor_tab import EditorTab
import llm_service
import editor_logic
import latex_compiler
import latex_translator
import os
import datetime  # Ajout pour print datetime dans perform_heavy_updates

# Global variables for main widgets and state
# These are initialized in setup_gui and accessed by other modules
root = None
notebook = None # NEW: Replaces the single editor
tabs = {} # NEW: Dictionary to hold EditorTab instances, mapping tab_id to tab_object
outline_tree = None
llm_progress_bar = None
status_bar = None
main_pane = None
_theme_settings = {} # Store current theme colors and properties
current_theme = "light" # Initial theme state, ensure it matches main.py if it sets it first

# Zoom settings
zoom_factor = 1.1
min_font_size = 8
max_font_size = 36

# --- Configuration for Heavy Updates ---
# Threshold for considering a file "large" (in number of lines)
LARGE_FILE_LINE_THRESHOLD = 1000
HEAVY_UPDATE_DELAY_NORMAL = 200  # milliseconds
HEAVY_UPDATE_DELAY_LARGE_FILE = 2000  # milliseconds for large files
heavy_update_timer_id = None

# Status bar temporary message state
_temporary_status_active = False
_temporary_status_timer_id = None

def perform_heavy_updates():
    """Performs updates that might be computationally heavy."""
    global heavy_update_timer_id
    heavy_update_timer_id = None  # Reset timer ID
    
    current_tab = get_current_tab()
    
    # If there is no active tab, clear the outline and stop.
    if not current_tab:
        if outline_tree:
            outline_tree.delete(*outline_tree.get_children())
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Heavy updates skipped (no active tab).")
        return

    # Perform all updates for the current tab
    editor_logic.apply_syntax_highlighting(current_tab.editor)
    editor_logic.update_outline_tree(current_tab.editor)
    if current_tab.line_numbers:
        current_tab.line_numbers.redraw()
    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Performed heavy updates (syntax highlighting, outline, line numbers) for '{os.path.basename(current_tab.file_path) if current_tab.file_path else 'Untitled'}'.")
def schedule_heavy_updates(_=None):
    """Schedules heavy updates after a short delay."""
    global heavy_update_timer_id
    if root and heavy_update_timer_id is not None:
        root.after_cancel(heavy_update_timer_id)
    current_tab = get_current_tab()
    if root and current_tab: # Ensure root and a tab are available
        current_delay = HEAVY_UPDATE_DELAY_NORMAL
        try:
            # Get total lines to determine if the file is large
            last_line_index_str = current_tab.editor.index("end-1c")
            # Correctly get total_lines, handling empty editor
            total_lines = 0
            if last_line_index_str: # Ensure index is not None or empty
                total_lines = int(last_line_index_str.split(".")[0])
                if total_lines == 1 and not current_tab.editor.get("1.0", "1.end").strip(): # Check if line 1 is empty
                    total_lines = 0
            
            if total_lines > LARGE_FILE_LINE_THRESHOLD:
                current_delay = HEAVY_UPDATE_DELAY_LARGE_FILE
        except tk.TclError: # Handle cases where editor might not be ready
            pass # Use normal delay
        heavy_update_timer_id = root.after(current_delay, perform_heavy_updates)

def get_theme_setting(key, default=None):
    """Gets a value from the current theme settings."""
    return _theme_settings.get(key, default)

def get_current_tab():
    """Returns the currently active EditorTab object, or None."""
    global notebook, tabs
    if not notebook or not tabs:
        return None
    try:
        selected_tab_id = notebook.select()
        return tabs.get(selected_tab_id)
    except tk.TclError: # Happens if no tabs are present
        return None

## -- Zoom Functionality -- ##

def zoom_in(_=None):
    return interface_zoom.zoom_in(get_current_tab, perform_heavy_updates, min_font_size, max_font_size, zoom_factor)

def zoom_out(_=None):
    return interface_zoom.zoom_out(get_current_tab, perform_heavy_updates, min_font_size, max_font_size, zoom_factor)

## -- Status Bar Feedback -- ##

def show_temporary_status_message(message, duration_ms=2500):
    return interface_statusbar.show_temporary_status_message(
        message, duration_ms, status_bar, root, clear_temporary_status_message
    )

def clear_temporary_status_message():
    return interface_statusbar.clear_temporary_status_message(
        status_bar, apply_theme, current_theme
    )

def on_close_request():
    """Handles closing the main window, checking for unsaved changes."""
    global root, tabs

    if not root:
        root.destroy()
        return

    dirty_tabs = [tab for tab in tabs.values() if tab.is_dirty()]

    if dirty_tabs:
        file_list = "\n - ".join([os.path.basename(tab.file_path) if tab.file_path else "Untitled" for tab in dirty_tabs])
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            f"You have unsaved changes in the following files:\n - {file_list}\n\nDo you want to save them before closing?",
            parent=root
        )
        if response is True:  # Yes, save and close
            all_saved = True
            for tab in dirty_tabs:
                # Switch to the tab to save it
                notebook.select(tab)
                if not save_file(): # save_file will handle the current tab
                    all_saved = False
                    break # User cancelled a "Save As" dialog
            if all_saved:
                root.destroy() # Close if all saves were successful
        elif response is False:  # No, just close
            root.destroy()
        # else: Cancel, do nothing and the window stays open.
    else:
        # No unsaved changes, just close.
        root.destroy()

def close_current_tab():
    return interface_tabops.close_current_tab(get_current_tab, root, notebook, save_file, create_new_tab, tabs)

## -- File Operations -- ##

def create_new_tab(file_path=None):
    return interface_tabops.create_new_tab(
        file_path, notebook, tabs, apply_theme, current_theme, on_tab_changed, EditorTab, schedule_heavy_updates
    )

def open_file():
    return interface_fileops.open_file(create_new_tab, show_temporary_status_message)

def save_file():
    return interface_fileops.save_file(get_current_tab, show_temporary_status_message, save_file_as)

def save_file_as():
    return interface_fileops.save_file_as(get_current_tab, show_temporary_status_message, on_tab_changed)

def on_tab_changed(event=None):
    """Handles logic when the active tab changes."""
    # Load prompt history and custom prompts for the newly active file
    llm_service.load_prompt_history_for_current_file()
    llm_service.load_prompts_for_current_file()
    # Update outline, syntax highlighting, etc.
    perform_heavy_updates()

def setup_gui():
    """Sets up the main application window and widgets."""
    global root, notebook, outline_tree, llm_progress_bar, _theme_settings, status_bar, main_pane

    root = tk.Tk()
    root.title("AutomaTeX v1.0")
    root.geometry("1200x800")

    # --- Top Buttons Frame ---
    top_frame = create_top_buttons_frame(root)

    # --- Main Paned Window (Outline Tree + Editor) ---
    main_pane = create_main_paned_window(root)

    # --- Left Outline Tree Frame ---
    outline_tree = create_outline_tree(main_pane, get_current_tab)

    # --- Editor Notebook ---
    notebook = create_notebook(main_pane)

    # --- LLM Progress Bar ---
    llm_progress_bar = ttk.Progressbar(root, mode="indeterminate", length=200)

    # --- Status Bar ---
    status_bar = create_status_bar(root)

    # --- GPU Status Update Loop ---
    start_gpu_status_loop(status_bar, root)

    # --- Bind Keyboard Shortcuts ---
    bind_shortcuts(root)

    # Create the first empty tab to start with
    create_new_tab()

    # Intercept the window close ('X') button to check for unsaved changes
    root.protocol("WM_DELETE_WINDOW", on_close_request)
    return root

def apply_theme(theme_name):
    return interface_theme.apply_theme(
        theme_name, current_theme, _theme_settings, root, outline_tree, status_bar, main_pane, tabs, perform_heavy_updates
    )
