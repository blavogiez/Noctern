"""
This module is reserved for future functionalities related to debugging LaTeX code
with the assistance of a Large Language Model (LLM).
"""
from llm.dialogs.debug import show_debug_dialog
from llm import state as llm_state
from tkinter import messagebox

def analyze_compilation_diff(diff_content: str, log_content: str):
    """
    Opens the debug dialog to show the diff and log, offering on-demand AI analysis.
    """
    if not all([llm_state._root_window, llm_state._theme_setting_getter_func, llm_state._active_editor_getter_func]):
        messagebox.showwarning("LLM Service Not Ready", "The LLM service is not fully initialized. Cannot perform analysis.")
        return

    # The dialog itself now handles the AI analysis part.
    show_debug_dialog(
        llm_state._root_window,
        llm_state._theme_setting_getter_func,
        diff_content,
        log_content,
        llm_state._active_editor_getter_func
    )