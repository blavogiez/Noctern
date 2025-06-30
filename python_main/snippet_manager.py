# snippet_manager.py

import json
import os
import debug_console

# This module handles the data and persistence logic for snippets.

SNIPPETS_FILE = "snippets.json"
_snippets = {}

def initialize_snippets():
    """
    Loads snippet definitions from the snippets.json file.
    If the file doesn't exist, it creates a complete default one.
    This function should be called on application startup.
    """
    global _snippets
    if not os.path.exists(SNIPPETS_FILE):
        debug_console.log(f"'{SNIPPETS_FILE}' not found. Creating a complete default one.", level='INFO')
        
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
        save_snippets(_snippets)
    else:
        try:
            with open(SNIPPETS_FILE, 'r', encoding='utf-8') as f:
                _snippets = json.load(f)
            debug_console.log(f"Successfully loaded {len(_snippets)} snippets from '{SNIPPETS_FILE}'.", level='SUCCESS')
        except (json.JSONDecodeError, IOError) as e:
            debug_console.log(f"Error reading '{SNIPPETS_FILE}': {e}. No snippets will be available.", level='ERROR')
            _snippets = {}

def get_snippets():
    """Public getter for the current in-memory snippets dictionary."""
    return _snippets

def save_snippets(new_snippets_dict):
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