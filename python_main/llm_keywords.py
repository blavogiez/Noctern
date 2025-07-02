
"""
This module provides functionality for managing global keywords used by the Large Language Model (LLM).
It allows users to set and update a list of keywords that can be incorporated into LLM prompts,
thereby influencing the LLM's generation or completion behavior.
"""

import llm_state
import llm_dialogs
from tkinter import messagebox
import debug_console

def open_set_keywords_dialog():
    """
    Opens a dialog window that allows the user to set or update global LLM keywords.

    This function retrieves the current list of keywords from `llm_state` and passes
    it to the dialog for display. Upon saving, a callback function updates the global
    keyword list and provides user feedback.
    """
    debug_console.log("Attempting to open 'Set LLM Keywords' dialog.", level='ACTION')
    
    # Pre-check for essential UI components to ensure the dialog can be displayed.
    if not llm_state._root_window or not llm_state._theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "UI components are not fully initialized for the keywords dialog. Please restart the application.")
        debug_console.log("LLM Keywords dialog failed to open: Missing root window or theme getter.", level='ERROR')
        return

    def _handle_keywords_save_from_dialog(new_keywords_list):
        """
        Callback function executed when the user saves keywords from the dialog.

        This function updates the global `_llm_keywords_list` in `llm_state`
        and provides a confirmation message to the user.

        Args:
            new_keywords_list (list): A list of strings representing the newly set keywords.
        """
        debug_console.log(f"Saving new LLM keywords: {new_keywords_list}", level='CONFIG')
        llm_state._llm_keywords_list = new_keywords_list # Update the global list of keywords.
        
        if not llm_state._llm_keywords_list:
            messagebox.showinfo("Keywords Cleared", "The LLM keywords list has been successfully cleared.", parent=llm_state._root_window)
            debug_console.log("LLM keywords list cleared.", level='INFO')
        else:
            messagebox.showinfo("Keywords Saved", f"LLM keywords successfully registered:\n- {', '.join(llm_state._llm_keywords_list)}", parent=llm_state._root_window)
            debug_console.log("LLM keywords saved successfully.", level='SUCCESS')

    # Display the keywords dialog, passing necessary UI references and callbacks.
    llm_dialogs.show_set_llm_keywords_dialog(
        root_window=llm_state._root_window,
        theme_setting_getter_func=llm_state._theme_setting_getter_func,
        current_llm_keywords_list=llm_state._llm_keywords_list, # Pass the current keywords for pre-filling.
        on_save_keywords_callback=_handle_keywords_save_from_dialog # Callback for when user saves.
    )
