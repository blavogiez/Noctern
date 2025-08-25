"""
This module provides the user-facing functionalities for managing and expanding code snippets within the editor.
It acts as a controller, orchestrating interactions between the UI (dialogs) and the snippet data management (snippet_manager).
"""

import tkinter as tk
import re
from utils import debug_console
from snippets import manager as snippet_manager
from app.panels import show_snippets_panel
from editor.placeholder_navigation import PlaceholderManager, handle_placeholder_navigation


def open_snippet_editor(root_window, theme_settings):
    """
    Opens the integrated snippet editor panel in the left sidebar.

    This function displays the SnippetsPanel, passing it the current snippet data 
    and a callback function for saving changes.
    """
    debug_console.log("Attempting to open snippet editor panel.", level='ACTION')
    # Show the integrated snippets panel
    show_snippets_panel(
        current_snippets=snippet_manager.get_snippets(),  # The current dictionary of snippets.
        save_callback=snippet_manager.save_snippets  # Callback function to save modified snippets.
    )
    debug_console.log("Snippet editor panel opened.", level='INFO')


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
    
    # Check if keyword exists in snippets
    if keyword in all_snippets:
        debug_console.log(f"Snippet keyword '{keyword}' detected. Attempting expansion.", level='ACTION')
        # Calculate keyword start position for replacement
        keyword_position_in_line = text_before_cursor.rfind(keyword)
        keyword_start_index = f"{line_start_index} + {keyword_position_in_line} chars"
        
        # Record insertion point for placeholder detection
        insertion_point = editor.index(keyword_start_index)
        
        # Get the snippet content and convert legacy placeholders if needed
        snippet_content = all_snippets[keyword]
        converted_snippet = PlaceholderManager.convert_legacy_placeholders(snippet_content)
        
        # If conversion happened, update the snippet in memory and save
        if converted_snippet != snippet_content:
            debug_console.log(f"Converted legacy placeholders in snippet '{keyword}'", level='INFO')
            all_snippets[keyword] = converted_snippet
            snippet_manager.save_snippets(all_snippets)
            snippet_content = converted_snippet
        
        # Delete keyword from editor
        editor.delete(keyword_start_index, cursor_position)
        # Insert converted snippet content
        editor.insert(insertion_point, snippet_content)
        
        # Check for placeholders in snippet using new format
        if PlaceholderManager.PLACEHOLDER_START in snippet_content:
            # Create placeholder manager if needed
            if not hasattr(editor, 'placeholder_manager'):
                editor.placeholder_manager = PlaceholderManager(editor)
            
            # Set snippet context for better placeholder tracking
            editor.placeholder_manager.set_snippet_context(insertion_point, snippet_content)
            
            # Find placeholders in the inserted snippet
            snippet_lines = snippet_content.count('\n')
            end_position = editor.index(f"{insertion_point} + {snippet_lines + 1} lines")
            
            if editor.placeholder_manager.find_placeholders(insertion_point, end_position):
                # Navigate to the first placeholder
                editor.placeholder_manager.navigate_to_next_placeholder()

        debug_console.log(f"Snippet '{keyword}' successfully expanded.", level='INFO')
        # Return "break" to prevent Tkinter from processing the event further (e.g., inserting a space).
        return "break"
    
    debug_console.log(f"Keyword '{keyword}' is not a registered snippet. No expansion performed.", level='DEBUG')
    return