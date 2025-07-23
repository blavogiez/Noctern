
"""
This module manages the loading, saving, and retrieval of user-defined code snippets.
It handles the persistence of snippets to a JSON file and provides an in-memory cache
for quick access during application runtime.
"""

import json
import os
from utils import debug_console

# --- Configuration and Global State ---
# The name of the file where snippets are stored.
SNIPPETS_FILE = "data/snippets.json"
# A global dictionary to hold the in-memory representation of all snippets.
_snippets = {}

def initialize_snippets():
    """
    Loads snippet definitions from the `snippets.json` file into memory.

    If the `snippets.json` file does not exist, a comprehensive set of default
    LaTeX-related snippets is created and saved to the file. This function
    should be called once during application startup to ensure snippets are available.
    """
    global _snippets
    if not os.path.exists(SNIPPETS_FILE):
        debug_console.log(f"Snippet file '{SNIPPETS_FILE}' not found. Creating a complete default set of snippets.", level='INFO')
        
        # Define a dictionary of default snippets with common LaTeX environments and symbols.
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
        _snippets = default_snippets # Set the in-memory snippets to the defaults.
        save_snippets(_snippets) # Save these default snippets to the file.
    else:
        try:
            # If the file exists, load snippets from it.
            with open(SNIPPETS_FILE, 'r', encoding='utf-8') as file_handle:
                _snippets = json.load(file_handle)
            debug_console.log(f"Successfully loaded {len(_snippets)} snippets from '{SNIPPETS_FILE}'.", level='SUCCESS')
        except (json.JSONDecodeError, IOError) as e:
            # Handle errors during file reading or JSON parsing.
            debug_console.log(f"Error reading or parsing snippet file '{SNIPPETS_FILE}': {e}. No snippets will be available.", level='ERROR')
            _snippets = {} # Reset snippets to an empty dictionary on error.

def get_snippets():
    """
    Returns the current in-memory dictionary of snippets.

    This function provides a public interface to access the loaded snippets
    without directly exposing the global `_snippets` variable.

    Returns:
        dict: A dictionary where keys are snippet keywords and values are their content.
    """
    return _snippets

def save_snippets(new_snippets_dict):
    """
    Saves the provided dictionary of snippets to the `snippets.json` file.

    After successfully saving to disk, the in-memory `_snippets` dictionary is
    updated with the new data to ensure consistency.

    Args:
        new_snippets_dict (dict): The dictionary of snippets to be saved.

    Returns:
        bool: True if the snippets were saved successfully, False otherwise.
    """
    global _snippets
    try:
        # Write the new snippets dictionary to the JSON file.
        # `indent=4` for pretty-printing, `sort_keys=True` for consistent order.
        with open(SNIPPETS_FILE, 'w', encoding='utf-8') as file_handle:
            json.dump(new_snippets_dict, file_handle, indent=4, sort_keys=True)
        _snippets = new_snippets_dict # Update the in-memory cache.
        debug_console.log("Snippets file saved and in-memory snippets reloaded successfully.", level='SUCCESS')
        return True
    except IOError as e:
        debug_console.log(f"Failed to save snippets to '{SNIPPETS_FILE}': {e}", level='ERROR')
        return False
