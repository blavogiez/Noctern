"""
This module provides core functionalities for managing editor tabs within the application's notebook,
including closing existing tabs and creating new ones. It handles saving unsaved changes
and managing a stack of recently closed tabs for restoration.
"""

from tkinter import messagebox
import os
from utils import debug_console
from utils.unsaved_changes_dialog import show_unsaved_changes_dialog

def close_current_tab(get_current_tab_callback, root_window, notebook_widget, save_file_callback, create_new_tab_callback, open_tabs_dict, closed_tabs_stack):
    """
    Closes the currently active editor tab.

    If the tab has unsaved changes, it prompts the user to save, discard, or cancel.
    Successfully closed tabs (with their file paths) are added to a stack for potential restoration.

    Args:
        get_current_tab_callback (callable): Function to get the current active tab.
        root_window (tk.Tk): The main application root window.
        notebook_widget (ttk.Notebook): The notebook widget managing the tabs.
        save_file_callback (callable): Function to save the current file.
        create_new_tab_callback (callable): Function to create a new tab.
        open_tabs_dict (dict): Dictionary mapping tab IDs to EditorTab instances.
        closed_tabs_stack (list): List acting as a stack for recently closed tab file paths.
    """
    current_tab = get_current_tab_callback()
    if not current_tab:
        debug_console.log("No active tab to close.", level='INFO')
        return
        
    tab_display_name = os.path.basename(current_tab.file_path) if current_tab.file_path else "Untitled"
    debug_console.log(f"Close tab requested for: '{tab_display_name}'", level='ACTION')

    # Check if the current tab has unsaved changes.
    if current_tab.is_dirty():
        debug_console.log(f"Tab '{tab_display_name}' has unsaved changes. Prompting user.", level='INFO')
        response = show_unsaved_changes_dialog(
            f"The file '{tab_display_name}' has unsaved changes.\n\nWhat would you like to do?",
            root_window
        )
        if response == "save":
            debug_console.log("User chose to SAVE before closing tab.", level='ACTION')
            if not save_file_callback(): # Attempt to save the file.
                debug_console.log("Save operation was cancelled or failed. Aborting tab close.", level='INFO')
                return # Abort closing the tab if saving fails or is cancelled.
        elif response == "cancel" or response is None: # User clicked 'Cancel'.
            debug_console.log("User CANCELLED the tab close operation.", level='ACTION')
            return
        else: # response == "dont_save" (User chose not to save).
            debug_console.log("User chose NOT to save before closing tab.", level='ACTION')

    # Add the file path to the closed tabs stack for potential restoration.
    if closed_tabs_stack is not None:
        closed_tabs_stack.append(current_tab.file_path)
        # Keep the stack size reasonable to prevent excessive memory usage.
        if len(closed_tabs_stack) > 10: 
            closed_tabs_stack.pop(0) # Remove the oldest entry if stack exceeds limit.
        debug_console.log(f"Added '{current_tab.file_path}' to closed tab stack for restoration.", level='DEBUG')

    # Get the ID of the tab to be closed and remove it from the notebook.
    tab_id_to_close = notebook_widget.select()
    notebook_widget.forget(tab_id_to_close)
    # Remove the tab instance from the global dictionary of open tabs.
    del open_tabs_dict[tab_id_to_close]
    debug_console.log(f"Tab '{tab_display_name}' successfully closed and removed from notebook.", level='INFO')
    
    # If no tabs remain open, we don't create a new 'Untitled' tab automatically
    # Application continues functioning without open tabs
    if not open_tabs_dict:
        debug_console.log("No tabs remaining. Application will continue without open tabs.", level='INFO')

def create_new_tab(file_path, notebook_widget, open_tabs_dict, apply_theme_callback, on_tab_changed_callback, EditorTab_class, schedule_heavy_updates_callback):
    """
    Creates and adds a new editor tab to the notebook.

    If the specified file is already open in another tab, it switches to that tab.
    Otherwise, a new `EditorTab` instance is created, loaded with content (either
    from the specified file or a template), and added to the notebook.

    Args:
        file_path (str): The absolute path to the file to open in the new tab. Can be None for a new untitled file.
        notebook_widget (ttk.Notebook): The notebook widget to add the new tab to.
        open_tabs_dict (dict): Dictionary mapping tab IDs to EditorTab instances.
        apply_theme_callback (callable): Function to apply the current theme to new widgets.
        on_tab_changed_callback (callable): Function to call when the tab selection changes.
        EditorTab_class (class): The EditorTab class to instantiate for new tabs.
        schedule_heavy_updates_callback (callable): Function to schedule heavy updates for the editor.
    """
    # Check if the file is already open in an existing tab.
    if file_path:
        # Iterate over the actual tabs in the notebook to find a match.
        for tab_id in notebook_widget.tabs():
            tab_widget = open_tabs_dict.get(tab_id)
            # Check if the widget exists and its file_path matches.
            if tab_widget and tab_widget.file_path == file_path:
                debug_console.log(f"File '{file_path}' is already open. Switching to existing tab.", level='INFO')
                notebook_widget.select(tab_id)  # Select the existing tab by its ID.
                return
    
    tab_display_name = os.path.basename(file_path) if file_path else "Untitled"
    debug_console.log(f"Creating new editor tab for: '{tab_display_name}'", level='INFO')
    
    # Create a new EditorTab instance.
    new_tab = EditorTab_class(notebook_widget, file_path=file_path, schedule_heavy_updates_callback=schedule_heavy_updates_callback)
    
    # Add the new tab to the notebook. It's crucial to add it before loading content
    # Enable proper notebook interaction for tab title updates
    notebook_widget.add(new_tab, text=tab_display_name)
    
    # Load content into the new tab (from file or template).
    new_tab.load_file() 
    
    # Select the newly created tab to make it active.
    notebook_widget.select(new_tab)
    # Store the new tab instance in the global dictionary, using its string representation as key.
    open_tabs_dict[str(new_tab)] = new_tab
    
    # Apply the current theme to the new tab's widgets to ensure visual consistency.
    apply_theme_callback() 
    # Note: on_tab_changed_callback will be automatically triggered by the NotebookTabChanged event
    # Automatic trigger from notebook_widget.select() above
    debug_console.log(f"Tab for '{tab_display_name}' created and loaded successfully.", level='SUCCESS')
