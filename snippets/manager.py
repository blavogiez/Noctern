
"""Manage loading, saving and retrieval of user-defined code snippets."""

import json
import os
from utils import debug_console

# Configuration and global state
SNIPPETS_FILE = "data/snippets.json"  # File where snippets are stored
# Global dictionary for in-memory representation of all snippets
_snippets = {}

def initialize_snippets():
    """Load snippet definitions from snippets.json file into memory."""
    global _snippets
    if not os.path.exists(SNIPPETS_FILE):
        debug_console.log(f"Snippet file '{SNIPPETS_FILE}' not found. Creating a complete default set of snippets.", level='INFO')
        
        # Define dictionary of default snippets with common LaTeX environments
        default_snippets = {
            "table2x2": """\begin{table}[h!]
    \centering
    \begin{tabular}{|c|c|}
        \hline
        col1 & col2 \\
        \hline
        cell1 & cell2 \\
        \hline
    \end{tabular}
    \caption{Caption}
    \label{tab:my_label}
\end{table}""",
            "table3x3": """\begin{table}[h!]
    \centering
    \begin{tabular}{|c|c|c|}
        \hline
        col1 & col2 & col3 \\
        \hline
        r1c1 & r1c2 & r1c3 \\
        r2c1 & r2c2 & r2c3 \\
        \hline
    \end{tabular}
    \caption{Caption}
    \label{tab:my_label}
\end{table}""",
            "enum": """\begin{enumerate}
    \item 
    \item 
\end{enumerate}""",
            "item": """\begin{itemize}
    \item 
    \item 
\end{itemize}""",
            "fig": """\begin{figure}[h!]
    \centering
    \includegraphics[width=0.8\textwidth]{figures/}
    \caption{Caption here}
    \label{fig:my_label}
\end{figure}""",
            "alpha": "$\alpha$",
            "beta": "$\beta$",
            "gamma": "$\gamma$"
        }
        _snippets = default_snippets  # Set in-memory snippets to defaults
        save_snippets(_snippets)  # Save default snippets to file
    else:
        try:
            # If file exists, load snippets from it
            with open(SNIPPETS_FILE, 'r', encoding='utf-8') as file_handle:
                _snippets = json.load(file_handle)
            debug_console.log(f"Successfully loaded {len(_snippets)} snippets from '{SNIPPETS_FILE}'.", level='SUCCESS')
        except (json.JSONDecodeError, IOError) as e:
            # Handle errors during file reading or JSON parsing
            debug_console.log(f"Error reading or parsing snippet file '{SNIPPETS_FILE}': {e}. No snippets will be available.", level='ERROR')
            _snippets = {}  # Reset snippets to empty dictionary on error

def get_snippets():
    """Return current in-memory dictionary of snippets."""
    return _snippets

def save_snippets(new_snippets_dict):
    """Save provided dictionary of snippets to snippets.json file."""
    global _snippets
    try:
        # Write new snippets dictionary to JSON file with pretty formatting
        with open(SNIPPETS_FILE, 'w', encoding='utf-8') as file_handle:
            json.dump(new_snippets_dict, file_handle, indent=4, sort_keys=True)
        _snippets = new_snippets_dict  # Update in-memory cache
        debug_console.log("Snippets file saved and in-memory snippets reloaded successfully.", level='SUCCESS')
        return True
    except IOError as e:
        debug_console.log(f"Failed to save snippets to '{SNIPPETS_FILE}': {e}", level='ERROR')
        return False
