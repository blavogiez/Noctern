"""
This module provides the user-facing functionalities for managing and expanding code snippets within the editor.
It acts as a controller, orchestrating interactions between the UI (dialogs) and the snippet data management (snippet_manager).
"""

import tkinter as tk
import re
from utils import debug_console
from snippets import manager as snippet_manager
from snippets.editor_dialog import SnippetEditorDialog

def open_snippet_editor():
    """
    Opens the snippet editor dialog, allowing users to view, add, edit, or delete code snippets.

    This function initializes and displays the `SnippetEditorDialog`, passing it the necessary
    application context, current snippet data, and a callback function for saving changes.
    """
    debug_console.log("Attempting to open snippet editor dialog.", level='ACTION')
    # Create and show the SnippetEditorDialog, passing required data and callbacks.
    SnippetEditorDialog(
        parent=interface.root,  # The main application window as the parent.
        theme_settings=interface.get_theme_settings(),  # Current theme settings for consistent UI.
        current_snippets=snippet_manager.get_snippets(),  # The current dictionary of snippets.
        save_callback=snippet_manager.save_snippets  # Callback function to save modified snippets.
    )
    debug_console.log("Snippet editor dialog opened.", level='INFO')

def handle_snippet_expansion(event):
    """
    Handles the expansion of a snippet keyword into its full content within the editor.

    This function is typically bound to a keyboard event (e.g., Spacebar or Tab).
    It checks the word immediately preceding the cursor. If this word matches a
    defined snippet keyword, the keyword is replaced with its corresponding snippet content.

    Args:
        event (tk.Event): The Tkinter event object that triggered this function.
                          Expected to be a keyboard event from a `tk.Text` widget.

    Returns:
        str or None: Returns the string "break" to stop further event propagation
                     if a snippet was expanded, otherwise returns None.
    """
    # Ensure the event originated from a Tkinter Text widget.
    if not isinstance(event.widget, tk.Text):
        debug_console.log("Snippet expansion event not from a Text widget.", level='DEBUG')
        return

    editor = event.widget
    cursor_position = editor.index(tk.INSERT) # Get the current cursor position.
    # Determine the start of the current line to extract text before the cursor.
    line_start_index = editor.index(f"{cursor_position} linestart")
    text_before_cursor = editor.get(line_start_index, cursor_position)

    # Use a regular expression to find the last word (potential keyword) before the cursor.
    # \w+ matches one or more word characters (alphanumeric + underscore).
    matches = re.findall(r'(\w+)', text_before_cursor)
    if not matches:
        debug_console.log("No potential snippet keyword found before cursor.", level='DEBUG')
        return

    keyword = matches[-1] # The last word found is the most relevant potential keyword.
    all_snippets = snippet_manager.get_snippets() # Retrieve all defined snippets.
    
    # Check if the extracted keyword exists in the list of defined snippets.
    if keyword in all_snippets:
        debug_console.log(f"Snippet keyword '{keyword}' detected. Attempting expansion.", level='ACTION')
        # Calculate the exact starting position of the keyword within the editor.
        # This is necessary to replace only the keyword, not the entire line.
        keyword_position_in_line = text_before_cursor.rfind(keyword)
        keyword_start_index = f"{line_start_index} + {keyword_position_in_line} chars"
        
        # Delete the keyword from the editor.
        editor.delete(keyword_start_index, cursor_position)
        # Insert the full snippet content in place of the keyword.
        editor.insert(keyword_start_index, all_snippets[keyword])

        debug_console.log(f"Snippet '{keyword}' successfully expanded.", level='INFO')
        # Return "break" to prevent Tkinter from processing the event further (e.g., inserting a space).
        return "break"
    
    debug_console.log(f"Keyword '{keyword}' is not a registered snippet. No expansion performed.", level='DEBUG')
    return