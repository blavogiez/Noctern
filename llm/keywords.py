
"""
This module provides functionality for managing global keywords used by the Large Language Model (LLM).
It allows users to set and update a list of keywords that can be incorporated into LLM prompts,
thereby influencing the LLM's generation or completion behavior.
"""

from tkinter import messagebox
from llm import state as llm_state
from llm.dialogs.keywords import show_set_llm_keywords_dialog
from utils import debug_console

def open_set_keywords_dialog():
    """
    Opens a dialog for setting LLM keywords for the currently active file.

    Retrieves the active file path and passes it to the keywords dialog.
    If no file is active, it displays an error message.
    """
    debug_console.log("Attempting to open 'Set LLM Keywords' dialog.", level='ACTION')

    # Check for required UI components.
    if not llm_state._root_window or not llm_state._theme_setting_getter_func or not llm_state._active_filepath_getter_func:
        messagebox.showerror("LLM Service Error", "UI components are not fully initialized. Please restart.")
        debug_console.log("LLM Keywords dialog failed: Missing root window, theme, or filepath getter.", level='ERROR')
        return

    # Get the path of the currently active file.
    active_file_path = llm_state._active_filepath_getter_func()
    if not active_file_path:
        messagebox.showwarning("No Active File", "Please open or focus a file before setting its keywords.", parent=llm_state._root_window)
        debug_console.log("Keyword dialog aborted: No active file path found.", level='WARNING')
        return

    # Open the dialog, passing the file path.
    show_set_llm_keywords_dialog(
        root_window=llm_state._root_window,
        theme_setting_getter_func=llm_state._theme_setting_getter_func,
        file_path=active_file_path
    )
