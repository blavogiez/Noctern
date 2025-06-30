# editor_wordcount.py

import tkinter as tk
import re

# This module contains the logic for the editor's word count feature.

_last_word_count = -1

def update_word_count(editor, status_label):
    """Calculates and updates the word count in the status bar if it has changed."""
    global _last_word_count
    if not editor or not status_label or not status_label.winfo_exists():
        return

    # Get content and strip out LaTeX commands and comments for a more accurate count
    content = editor.get("1.0", tk.END)
    content = re.sub(r"%.*?\n", "", content) # Remove comments
    content = re.sub(r"\\[a-zA-Z@]+(?:\[[^\]]*\])?(?:\{[^}]*\})?", "", content) # Remove commands
    content = re.sub(r"[\\[\]{}*]", " ", content) # Replace brackets with spaces
    
    words = content.split()
    word_count = len(words)

    if word_count != _last_word_count:
        status_label.config(text=f"{word_count} words")
        _last_word_count = word_count
    
    return word_count

def get_last_word_count_text():
    """Returns the formatted text of the last known word count for display purposes."""
    if _last_word_count == -1:
        return "..."
    return f"{_last_word_count} words"