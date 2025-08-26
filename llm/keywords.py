
"""
This module provides functionality for managing global keywords used by the Large Language Model (LLM).
It allows users to set and update a list of keywords that can be incorporated into LLM prompts,
thereby influencing the LLM's generation or completion behavior.
UI integration through callbacks provided by app layer.
"""

from tkinter import messagebox
from llm import state as llm_state
from utils import logs_console

def prepare_keywords_panel(panel_callback=None):
    """
    Prepare keywords panel - pure business logic.
    
    Args:
        panel_callback: Callback to show the UI panel
        
    Opens the keywords panel for setting LLM keywords for the currently active file.
    Retrieves the active file path and passes it to the keywords panel.
    If no file is active, it displays an error message.
    """
    logs_console.log("Attempting to open 'Set LLM Keywords' panel.", level='ACTION')

    # Check for required UI components.
    if not llm_state._root_window or not llm_state._theme_setting_getter_func or not llm_state._active_filepath_getter_func:
        messagebox.showerror("LLM Service Error", "UI components are not fully initialized. Please restart.")
        logs_console.log("LLM Keywords panel failed: Missing root window, theme, or filepath getter.", level='ERROR')
        return

    # Get the path of the currently active file.
    active_file_path = llm_state._active_filepath_getter_func()
    if not active_file_path:
        messagebox.showwarning("No Active File", "Please open or focus a file before setting its keywords.", parent=llm_state._root_window)
        logs_console.log("Keyword dialog aborted: No active file path found.", level='WARNING')
        return

    # Call UI callback if provided
    if panel_callback:
        panel_callback(active_file_path)


# Backward compatibility wrapper
def open_set_keywords_panel():
    """Legacy function name for backward compatibility."""
    prepare_keywords_panel()
