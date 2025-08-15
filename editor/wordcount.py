"""
This module provides functionality for calculating and displaying the word count of the editor's content.
It aims to provide a more accurate word count by filtering out LaTeX commands and comments.
"""

import tkinter as tk
import re

# Global variable to store the last calculated word count.
# Initialized to -1 to ensure the word count is updated on the first call.
_last_word_count = -1

def update_word_count(editor, status_label):
    """
    Calculates the word count of the text in the provided editor widget and updates a status label.

    The function attempts to provide a more accurate word count by first removing
    common LaTeX commands and comments from the text before counting words.
    The status label is only updated if the word count has changed since the last calculation.

    Args:
        editor (tk.Text): The Tkinter Text widget containing the document content.
        status_label (tk.Label): The Tkinter Label widget used to display the word count.

    Returns:
        int: The current word count of the editor's content.
    """
    global _last_word_count
    # Ensure both the editor and status label widgets are valid and exist.
    if not editor or not status_label or not status_label.winfo_exists():
        return 0 # Return 0 if widgets are not available.

    # Retrieve the entire content from the editor.
    content = editor.get("1.0", tk.END)
    
    # --- Pre-processing content for accurate word count ---
    # 1. Remove LaTeX comments (lines starting with % or % followed by anything until newline).
    content = re.sub(r"%.*?\n", "", content) 
    # 2. Remove LaTeX commands (e.g., \section{}, \includegraphics[]{}).
    # This regex matches \ followed by one or more letters/symbols, optionally followed by
    # Match square brackets for optional arguments and curly braces for mandatory arguments
    content = re.sub(r"\\[a-zA-Z@]+(?:\\[^\\]*\\)?(?:\{[^}]*\})?", "", content)
    # 3. Replace remaining LaTeX structural characters (brackets, braces, asterisks) with spaces.
    # This helps in correctly splitting words that might be adjacent to these characters.
    content = re.sub(r"\\[\\[\\]{}*]", " ", content)
    
    # Split the cleaned content by whitespace to get a list of words.
    words = content.split()
    word_count = len(words) # Calculate the number of words.

    # Update the status label only if the word count has changed.
    if word_count != _last_word_count:
        status_label.config(text=f"{word_count} words")
        _last_word_count = word_count # Store the new word count.
    
    return word_count

def get_last_word_count_text():
    """
    Returns the formatted string of the last known word count.

    This function is useful for displaying the word count in other parts of the UI
    without recalculating it, especially when the editor content hasn't changed.

    Returns:
        str: A string representing the last calculated word count (e.g., "123 words").
             Returns "..." if no word count has been calculated yet.
    """
    if _last_word_count == -1:
        return "..." # Indicate that the word count has not been initialized yet.
    return f"{_last_word_count} words" # Return the formatted word count. 
