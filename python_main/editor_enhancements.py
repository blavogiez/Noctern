# editor_enhancements.py

import tkinter as tk
import re
import json
import os
import debug_console

# --- Snippet Manager ---

_snippets = {}
SNIPPETS_FILE = "snippets.json"

def initialize_snippets():
    """
    Loads snippet definitions from the snippets.json file.
    If the file doesn't exist, creates a default one.
    """
    global _snippets
    if not os.path.exists(SNIPPETS_FILE):
        debug_console.log(f"'{SNIPPETS_FILE}' not found. Creating a default one.", level='INFO')
        # FIXED: Ensured all default snippets are stored as strings, not tuples.
        # Multi-line strings are defined using triple quotes for clarity and correctness.
        default_snippets = {
            "table2x2": (
                "\\begin{table}[h!]\n"
                "    \\centering\n"
                "    \\begin{tabular}{|c|c|}\n"
                "        \\hline\n"
                "        col1 & col2 \\\\\n"
                "        \\hline\n"
                "        cell1 & cell2 \\\\\n"
                "        \\hline\n"
                "    \\end{tabular}\n"
                "    \\caption{Caption}\n"
                "    \\label{tab:my_label}\n"
                "\\end{table}"
            ),
            "enum": (
                "\\begin{enumerate}\n"
                "    \\item \n"
                "    \\item \n"
                "\\end{enumerate}"
            ),
            "item": "\\item "
        }
        with open(SNIPPETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_snippets, f, indent=4)
        _snippets = default_snippets
    else:
        try:
            with open(SNIPPETS_FILE, 'r', encoding='utf-8') as f:
                _snippets = json.load(f)
            debug_console.log(f"Successfully loaded {len(_snippets)} snippets from '{SNIPPETS_FILE}'.", level='SUCCESS')
        except json.JSONDecodeError:
            debug_console.log(f"Error decoding '{SNIPPETS_FILE}'. No snippets will be available.", level='ERROR')
            _snippets = {}

def handle_tab_key(event):
    """
    Checks if the word before the cursor is a snippet keyword and replaces it.
    This is the FIXED and more robust implementation.
    """
    editor = event.widget
    cursor_pos = editor.index(tk.INSERT)

    # FIXED: Use the 'wordstart' index modifier to reliably find the beginning
    # of the word immediately preceding the cursor. This is much more robust
    # than the previous line-based regex approach.
    word_start_index = editor.index(f"{cursor_pos} wordstart")
    
    # Extract the keyword between the start of the word and the cursor.
    keyword = editor.get(word_start_index, cursor_pos)

    # Check if the extracted keyword exists in our snippets dictionary.
    if keyword in _snippets:
        debug_console.log(f"Snippet triggered for keyword: '{keyword}'", level='ACTION')
        
        # We already have the exact start index of the keyword.
        # Replace the keyword with its corresponding snippet content.
        editor.delete(word_start_index, cursor_pos)
        editor.insert(word_start_index, _snippets[keyword])
        
        # Return "break" to prevent the default Tab behavior (i.e., inserting a tab character).
        return "break"
    
    # If no snippet was found, return nothing to allow the default Tab behavior.
    return


# --- Word Count ---

_last_word_count = -1

def update_word_count(editor, status_label):
    """
    Calculates the word count of the editor's content, ignoring LaTeX commands,
    and updates the provided status label.
    """
    global _last_word_count
    if not editor or not status_label or not status_label.winfo_exists():
        return

    content = editor.get("1.0", tk.END)
    
    # 1. Remove comments (lines starting with %)
    content = re.sub(r"%.*?\n", "", content)
    # 2. Remove LaTeX commands (e.g., \section{...}, \textbf, \documentclass, etc.)
    # This also handles commands with optional arguments like \includegraphics[...]
    content = re.sub(r"\\[a-zA-Z@]+(?:\[[^\]]*\])?(?:\{[^}]*\})?", "", content)
    # 3. Remove any remaining single backslashes or other non-word characters that are not spaces.
    content = re.sub(r"[\\[\]{}*]", " ", content)

    # Count words in the cleaned text
    words = content.split()
    word_count = len(words)

    # Only update the label if the count has changed to reduce flicker and unnecessary work.
    if word_count != _last_word_count:
        status_label.config(text=f"{word_count} words")
        _last_word_count = word_count
    
    return word_count

def get_last_word_count_text():
    """Returns the formatted text of the last known word count for the status bar."""
    if _last_word_count == -1:
        return "..."
    return f"{_last_word_count} words"