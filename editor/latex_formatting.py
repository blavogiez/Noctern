"""LaTeX text formatting functions for editor shortcuts."""
import tkinter as tk
import re


def apply_textit(event):
    """Apply \textit{} formatting to selected text or insert empty command."""
    editor = event.widget
    
    try:
        # Check if text is selected
        start, end = editor.tag_ranges("sel")
        selected_text = editor.get(start, end)
        
        # Check if selection is already wrapped in \textit{}
        if selected_text.startswith('\\textit{') and selected_text.endswith('}'):
            # Remove \textit{} wrapper
            unwrapped = selected_text[8:-1]  # Remove '\textit{' and '}'
            editor.delete(start, end)
            editor.insert(start, unwrapped)
            # Select the unwrapped text
            new_end = f"{start}+{len(unwrapped)}c"
            editor.tag_add("sel", start, new_end)
        else:
            # Wrap selection in \textit{}
            wrapped = f"\\textit{{{selected_text}}}"
            editor.delete(start, end)
            editor.insert(start, wrapped)
            # Select the content inside the braces
            content_start = f"{start}+8c"  # After '\textit{'
            content_end = f"{start}+{len(wrapped)-1}c"  # Before final '}'
            editor.tag_add("sel", content_start, content_end)
            
    except ValueError:
        # No selection - insert empty \textit{} with cursor inside
        cursor_pos = editor.index(tk.INSERT)
        editor.insert(cursor_pos, "\\textit{}")
        # Position cursor inside braces
        editor.mark_set(tk.INSERT, f"{cursor_pos}+8c")
    
    return "break"


def apply_textbf(event):
    """Apply \textbf{} formatting to selected text or insert empty command."""
    editor = event.widget
    
    try:
        # Check if text is selected
        start, end = editor.tag_ranges("sel")
        selected_text = editor.get(start, end)
        
        # Check if selection is already wrapped in \textbf{}
        if selected_text.startswith('\\textbf{') and selected_text.endswith('}'):
            # Remove \textbf{} wrapper
            unwrapped = selected_text[8:-1]  # Remove '\textbf{' and '}'
            editor.delete(start, end)
            editor.insert(start, unwrapped)
            # Select the unwrapped text
            new_end = f"{start}+{len(unwrapped)}c"
            editor.tag_add("sel", start, new_end)
        else:
            # Wrap selection in \textbf{}
            wrapped = f"\\textbf{{{selected_text}}}"
            editor.delete(start, end)
            editor.insert(start, wrapped)
            # Select the content inside the braces
            content_start = f"{start}+8c"  # After '\textbf{'
            content_end = f"{start}+{len(wrapped)-1}c"  # Before final '}'
            editor.tag_add("sel", content_start, content_end)
            
    except ValueError:
        # No selection - insert empty \textbf{} with cursor inside
        cursor_pos = editor.index(tk.INSERT)
        editor.insert(cursor_pos, "\\textbf{}")
        # Position cursor inside braces
        editor.mark_set(tk.INSERT, f"{cursor_pos}+8c")
    
    return "break"