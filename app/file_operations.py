"""
Provide functions for common file operations within application.
Include opening, saving, and saving files under new name. Interact with Tkinter filedialog for user interaction and debug_console for logging.
"""

from tkinter import filedialog
import os
from utils import debug_console

def open_file(create_new_tab_callback, show_temporary_status_message_callback):
    """
    Open file dialog to allow user to select file, then open it in new editor tab.
    """
    debug_console.log("Initiating file open dialog.", level='ACTION')
    # Open file dialog to let user choose file
    file_path = filedialog.askopenfilename(
        title="Open File",
        filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if file_path:
        debug_console.log(f"File selected for opening: {file_path}", level='INFO')
        # Create new tab and load selected file
        create_new_tab_callback(file_path=file_path)
        # Display success message in status bar
        show_temporary_status_message_callback(f"✅ Opened: {os.path.basename(file_path)}")
    else:
        debug_console.log("File open dialog cancelled by user.", level='INFO')

def save_file(get_current_tab_callback, show_temporary_status_message_callback, save_file_as_callback):
    """
    Save content of current active editor tab.

    If the current tab has an associated file path, it saves directly to that path.
    If it's a new, unsaved file, it redirects to the `save_file_as` function.

    Args:
        get_current_tab_callback (callable): A callback function to retrieve the current active tab.
                                             Expected signature: `get_current_tab()` returning an EditorTab instance.
        show_temporary_status_message_callback (callable): A callback function to display
                                                            a temporary message in the status bar.
                                                            Expected signature: `show_temporary_status_message(message)`.
        save_file_as_callback (callable): A callback function to handle saving the file under a new name.
                                          Expected signature: `save_file_as()`.

    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    current_tab = get_current_tab_callback()
    if not current_tab:
        debug_console.log("Save operation failed: No active editor tab found.", level='WARNING')
        return False
    
    tab_display_name = current_tab.file_path or "Untitled" # For logging purposes.
    debug_console.log(f"Initiating save operation for tab: {tab_display_name}", level='ACTION')

    if current_tab.file_path: # Check if the tab is already associated with a file.
        if current_tab.save_file(): # Attempt to save the file.
            debug_console.log(f"File saved successfully: {current_tab.file_path}", level='SUCCESS')
            show_temporary_status_message_callback(f"✅ Saved: {os.path.basename(current_tab.file_path)}")
            
            
            return True
        else:
            debug_console.log(f"File save failed for: {current_tab.file_path}", level='ERROR')
            return False
    else:
        # If no file path is associated, prompt the user to save as a new file.
        debug_console.log("No existing file path for current tab. Redirecting to 'Save As' dialog.", level='INFO')
        return save_file_as_callback()

def save_file_as(get_current_tab_callback, show_temporary_status_message_callback, on_tab_changed_callback):
    """
    Prompts the user to select a new file path and saves the current editor content to it.

    This function is used for saving new, unsaved files or for saving an existing file
    under a different name.

    Args:
        get_current_tab_callback (callable): A callback function to retrieve the current active tab.
                                             Expected signature: `get_current_tab()` returning an EditorTab instance.
        show_temporary_status_message_callback (callable): A callback function to display
                                                            a temporary message in the status bar.
                                                            Expected signature: `show_temporary_status_message(message)`.
        on_tab_changed_callback (callable): A callback function to be called after the tab's
                                            file path has been updated (e.g., to refresh UI).
                                            Expected signature: `on_tab_changed()`.

    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    current_tab = get_current_tab_callback()
    if not current_tab:
        debug_console.log("Save As operation failed: No active editor tab found.", level='WARNING')
        return False
        
    debug_console.log("Initiating Save As dialog.", level='ACTION')
    # Open a save file dialog to get a new file path from the user.
    new_file_path = filedialog.asksaveasfilename(
        defaultextension=".tex",
        filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")],
        title="Save File As"
    )
    if new_file_path:
        debug_console.log(f"New file path selected for Save As: {new_file_path}", level='INFO')
        # Attempt to save the file to the new path.
        if current_tab.save_file(new_path=new_file_path):
            debug_console.log(f"File saved successfully to new path: {new_file_path}", level='SUCCESS')
            show_temporary_status_message_callback(f"✅ Saved as: {os.path.basename(new_file_path)}")
            on_tab_changed_callback() # Notify that the tab's file path has changed.
            
            
            return True
        else:
            debug_console.log(f"Save As operation failed for: {new_file_path}", level='ERROR')
            return False
    else:
        debug_console.log("Save As dialog cancelled by user.", level='INFO')
        return False
