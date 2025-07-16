"""
This module handles the persistence of LLM prompt and response history.
It provides functions to load, save, and update prompt history entries
associated with specific LaTeX document files, using JSON for storage.
"""

import json
import os
from utils import debug_console

# Maximum number of prompt-response pairs to store in the history for each document.
MAX_PROMPT_HISTORY_SIZE = 20

def _get_prompt_history_filepath(tex_document_filepath):
    """
    Generates the absolute file path for the prompt history JSON file.

    The history file is named after the LaTeX document, with a '_prompt_history.json' suffix,
    and is located in the same directory as the .tex file.

    Args:
        tex_document_filepath (str): The absolute path to the LaTeX document file.

    Returns:
        str or None: The absolute path to the history JSON file, or None if the
                     `tex_document_filepath` is invalid or not provided.
    """
    if not tex_document_filepath:
        debug_console.log("Cannot generate history filepath: No .tex document path provided.", level='DEBUG')
        return None
    
    # Split the base name and extension, then append the history suffix.
    base_name_without_ext, _ = os.path.splitext(tex_document_filepath)
    history_file_path = f"{base_name_without_ext}_prompt_history.json"
    debug_console.log(f"Generated prompt history filepath: {history_file_path}", level='DEBUG')
    return history_file_path

def save_prompt_history_to_file(prompt_history_list, tex_document_filepath):
    """
    Saves the provided list of prompt history entries to a JSON file.

    The history is saved to a file determined by `_get_prompt_history_filepath`.
    If the `tex_document_filepath` is not available, the history is not saved.

    Args:
        prompt_history_list (list): A list of (user_prompt, llm_response) tuples to save.
        tex_document_filepath (str): The absolute path to the associated LaTeX document file.
    """
    history_filepath = _get_prompt_history_filepath(tex_document_filepath)
    if not history_filepath:
        debug_console.log("Skipping history save: No valid .tex file path to associate history with.", level='INFO')
        return

    try:
        # Write the history list to the JSON file with pretty-printing.
        with open(history_filepath, 'w', encoding='utf-8') as file_handle:
            json.dump(prompt_history_list, file_handle, ensure_ascii=False, indent=4)
        debug_console.log(f"Prompt history successfully saved to {os.path.basename(history_filepath)}.", level='DEBUG')
    except Exception as e:
        debug_console.log(f"Error saving prompt history to '{history_filepath}': {e}", level='ERROR')

def load_prompt_history_from_file(tex_document_filepath):
    """
    Loads prompt history entries from a JSON file associated with the given LaTeX document.

    If the history file exists and is valid, its contents are loaded. Otherwise, an empty
    list is returned. Basic validation is performed on the loaded data structure.

    Args:
        tex_document_filepath (str): The absolute path to the associated LaTeX document file.

    Returns:
        list: A list of (user_prompt, llm_response) tuples loaded from the file.
              Returns an empty list if the file does not exist, is invalid, or an error occurs.
    """
    history_filepath = _get_prompt_history_filepath(tex_document_filepath)
    loaded_history_list = []
    
    # Check if a valid history file path exists and the file itself exists.
    if history_filepath and os.path.exists(history_filepath):
        try:
            with open(history_filepath, 'r', encoding='utf-8') as file_handle:
                loaded_data = json.load(file_handle)
                # Validate that each item in the loaded data is a list/tuple of two elements.
                loaded_history_list = [
                    (item[0], item[1]) for item in loaded_data 
                    if isinstance(item, (list, tuple)) and len(item) == 2
                ]
            debug_console.log(f"Loaded {len(loaded_history_list)} entries from prompt history file {os.path.basename(history_filepath)}.", level='INFO')
        except json.JSONDecodeError as e:
            debug_console.log(f"Error decoding JSON from prompt history file '{history_filepath}': {e}. File might be corrupted.", level='ERROR')
            loaded_history_list = [] # Reset history on JSON error.
        except Exception as e:
            debug_console.log(f"An unexpected error occurred loading prompt history from '{history_filepath}': {e}", level='ERROR')
            loaded_history_list = [] # Reset history on other errors.
    else:
        debug_console.log(f"No prompt history file found for '{tex_document_filepath or 'new file'}'. Starting with empty history.", level='DEBUG')

    return loaded_history_list

def update_response_in_history(prompt_history_list, user_prompt_key, new_response_text):
    """
    Updates the LLM response for a specific user prompt within the provided history list.

    This function modifies the `prompt_history_list` in-place. It searches for an entry
    whose user prompt matches `user_prompt_key` and updates its corresponding response.

    Args:
        prompt_history_list (list): The list of (user_prompt, llm_response) tuples to modify.
        user_prompt_key (str): The user prompt text used to identify the entry to update.
        new_response_text (str): The new LLM response text to set for the identified entry.
    """
    for index, (prompt_text, _) in enumerate(prompt_history_list):
        if prompt_text == user_prompt_key:
            prompt_history_list[index] = (prompt_text, new_response_text)
            debug_console.log(f"Updated response for prompt '{user_prompt_key[:50]}...' in history.", level='DEBUG')
            break
    else:
        debug_console.log(f"Prompt '{user_prompt_key[:50]}...' not found in history for update.", level='WARNING')
