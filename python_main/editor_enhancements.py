# editor_enhancements.py

import tkinter as tk
import re
import json
import os
import debug_console
import interface
from snippet_editor_dialog import SnippetEditorDialog

# --- Snippet Manager ---

_snippets = {}
SNIPPETS_FILE = "snippets.json"

def initialize_snippets():
    """
    Loads snippet definitions from the snippets.json file.
    If the file doesn't exist, it creates a complete default one.
    """
    global _snippets
    if not os.path.exists(SNIPPETS_FILE):
        debug_console.log(f"'{SNIPPETS_FILE}' not found. Creating a complete default one.", level='INFO')
        
        # DEFINITIVE FIX: The default_snippets dictionary now contains all 8 snippets
        # as requested, ensuring a rich and complete default set is created on first launch.
        default_snippets = {
            "table2x2": """\\begin{table}[h!]
    \\centering
    \\begin{tabular}{|c|c|}
        \\hline
        col1 & col2 \\\\
        \\hline
        cell1 & cell2 \\\\
        \\hline
    \\end{tabular}
    \\caption{Caption}
    \\label{tab:my_label}
\\end{table}""",
            "table3x3": """\\begin{table}[h!]
    \\centering
    \\begin{tabular}{|c|c|c|}
        \\hline
        col1 & col2 & col3 \\\\
        \\hline
        r1c1 & r1c2 & r1c3 \\\\
        r2c1 & r2c2 & r2c3 \\\\
        \\hline
    \\end{tabular}
    \\caption{Caption}
    \\label{tab:my_label}
\\end{table}""",
            "enum": """\\begin{enumerate}
    \\item 
    \\item 
\\end{enumerate}""",
            "item": """\\begin{itemize}
    \\item 
    \\item 
\\end{itemize}""",
            "fig": """\\begin{figure}[h!]
    \\centering
    \\includegraphics[width=0.8\\textwidth]{figures/}
    \\caption{Caption here}
    \\label{fig:my_label}
\\end{figure}""",
            "alpha": "$\\alpha$",
            "beta": "$\\beta$",
            "gamma": "$\\gamma$"
        }
        _snippets = default_snippets
        # Save the complete defaults immediately
        save_and_reload_snippets(_snippets)
    else:
        try:
            with open(SNIPPETS_FILE, 'r', encoding='utf-8') as f:
                _snippets = json.load(f)
            debug_console.log(f"Successfully loaded {len(_snippets)} snippets from '{SNIPPETS_FILE}'.", level='SUCCESS')
        except (json.JSONDecodeError, IOError) as e:
            debug_console.log(f"Error reading '{SNIPPETS_FILE}': {e}. No snippets will be available.", level='ERROR')
            _snippets = {}

def get_snippets():
    """Public getter for the current snippets dictionary."""
    return _snippets

def save_and_reload_snippets(new_snippets_dict):
    """
    Saves the provided dictionary to the snippets.json file and reloads
    the in-memory snippet dictionary for immediate use.
    """
    global _snippets
    try:
        with open(SNIPPETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_snippets_dict, f, indent=4, sort_keys=True)
        _snippets = new_snippets_dict
        debug_console.log("Snippets file saved and in-memory snippets reloaded.", level='SUCCESS')
        return True
    except IOError as e:
        debug_console.log(f"Failed to save snippets to '{SNIPPETS_FILE}': {e}", level='ERROR')
        return False

def open_snippet_editor():
    """
    Opens the snippet editor dialog window.
    """
    debug_console.log("Snippet editor opened.", level='ACTION')
    SnippetEditorDialog(
        parent=interface.root,
        theme_settings=interface._theme_settings,
        current_snippets=get_snippets(),
        save_callback=save_and_reload_snippets
    )

def handle_snippet_expansion(event):
    """
    Checks if the word before the cursor is a snippet keyword and replaces it.
    """
    if not isinstance(event.widget, tk.Text):
        return

    editor = event.widget
    cursor_pos = editor.index(tk.INSERT)
    line_start_index = editor.index(f"{cursor_pos} linestart")
    text_before_cursor = editor.get(line_start_index, cursor_pos)

    matches = re.findall(r'(\w+)', text_before_cursor)
    if not matches:
        return

    keyword = matches[-1]
    if keyword in _snippets:
        keyword_pos_in_line = text_before_cursor.rfind(keyword)
        keyword_start_index = f"{line_start_index} + {keyword_pos_in_line} chars"
        keyword_end_index = f"{keyword_start_index} + {len(keyword)} chars"

        editor.delete(keyword_start_index, keyword_end_index)
        editor.insert(keyword_start_index, _snippets[keyword])

        return "break"
    return

# --- Word Count ---

_last_word_count = -1

def update_word_count(editor, status_label):
    """Calculates and updates the word count in the status bar."""
    global _last_word_count
    if not editor or not status_label or not status_label.winfo_exists():
        return

    content = editor.get("1.0", tk.END)
    content = re.sub(r"%.*?\n", "", content)
    content = re.sub(r"\\[a-zA-Z@]+(?:\[[^\]]*\])?(?:\{[^}]*\})?", "", content)
    content = re.sub(r"[\\[\]{}*]", " ", content)
    words = content.split()
    word_count = len(words)

    if word_count != _last_word_count:
        status_label.config(text=f"{word_count} words")
        _last_word_count = word_count
    
    return word_count

def get_last_word_count_text():
    """Returns the formatted text of the last known word count."""
    if _last_word_count == -1:
        return "..."
    return f"{_last_word_count} words"