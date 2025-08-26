"""
This module is reserved for future functionalities related to debugging LaTeX code
with the assistance of a Large Language Model (LLM).
UI integration through callbacks provided by app layer.
"""
from llm import state as llm_state
from tkinter import messagebox

def prepare_compilation_analysis(diff_content: str, log_content: str, panel_callback=None):
    """
    Prepare compilation analysis - pure business logic.
    
    Args:
        diff_content: Content diff to analyze
        log_content: Log content to analyze  
        panel_callback: Callback to show the UI panel
        
    Opens the debug interface to show the diff and log, offering on-demand AI analysis.
    """
    if not all([llm_state._root_window, llm_state._theme_setting_getter_func, llm_state._active_editor_getter_func]):
        messagebox.showwarning("LLM Service Not Ready", "The LLM service is not fully initialized. Cannot perform analysis.")
        return

    # Call UI callback if provided
    if panel_callback:
        panel_callback(
            diff_content,
            log_content,
            llm_state._active_editor_getter_func
        )


# Backward compatibility wrapper
def analyze_compilation_diff(diff_content: str, log_content: str):
    """Legacy function name for backward compatibility."""
    prepare_compilation_analysis(diff_content, log_content)