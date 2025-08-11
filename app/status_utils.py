"""
This module provides utility functions for updating the status bar with
file information and word count.
"""

from app import state
from editor import wordcount as editor_wordcount

def update_status_bar_text():
    """
    Updates the status bar text with the current file path and word count.
    """
    # Check if status bar exists
    if not state.status_label:
        return
        
    current_tab = state.get_current_tab()
    if current_tab:
        # Update word count
        word_count = editor_wordcount.update_word_count(current_tab.editor, state.status_label)
        # Show file path if available
        if current_tab.file_path:
            state.status_label.config(text=f"{current_tab.file_path} | {word_count} words")
        else:
            state.status_label.config(text=f"Untitled | {word_count} words")
    else:
        state.status_label.config(text="...")