# editor_snippets.py

import tkinter as tk
import re
import debug_console
import interface
import snippet_manager
from snippet_editor_dialog import SnippetEditorDialog

# This module provides the user-facing features for snippets, acting as a controller.

def open_snippet_editor():
    """
    Opens the snippet editor dialog, providing it with the necessary data
    and save callback from the snippet_manager.
    """
    debug_console.log("Snippet editor opened.", level='ACTION')
    SnippetEditorDialog(
        parent=interface.root,
        theme_settings=interface.get_theme_settings(),
        current_snippets=snippet_manager.get_snippets(),
        save_callback=snippet_manager.save_snippets
    )

def handle_snippet_expansion(event):
    """
    Checks if the word before the cursor is a snippet keyword and replaces it.
    This function is bound to a keyboard shortcut.
    """
    if not isinstance(event.widget, tk.Text):
        return

    editor = event.widget
    cursor_pos = editor.index(tk.INSERT)
    line_start_index = editor.index(f"{cursor_pos} linestart")
    text_before_cursor = editor.get(line_start_index, cursor_pos)

    # Find the last potential keyword before the cursor
    matches = re.findall(r'(\w+)', text_before_cursor)
    if not matches:
        return

    keyword = matches[-1]
    snippets = snippet_manager.get_snippets()
    
    if keyword in snippets:
        # Calculate the exact start position of the keyword to replace it
        keyword_pos_in_line = text_before_cursor.rfind(keyword)
        keyword_start_index = f"{line_start_index} + {keyword_pos_in_line} chars"
        
        # Replace the keyword with its corresponding snippet content
        editor.delete(keyword_start_index, cursor_pos)
        editor.insert(keyword_start_index, snippets[keyword])

        # Prevent the default event (e.g., inserting a space)
        return "break"
    return