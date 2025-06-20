# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\llm_prompt_history.py
"""
Manages the prompt history for the LLM interactions.

This module provides functions to load, save, add entries to, and update
responses within the prompt history. The history is typically associated
with a specific .tex file.
"""
import json
import os

# Maximum number of prompt-response pairs to store in the history.
MAX_PROMPT_HISTORY_SIZE = 20

def _get_prompt_history_filepath(tex_document_filepath):
    """
    Generates the filepath for the prompt history JSON file based on the .tex file's path.

    Args:
        tex_document_filepath (str or None): The path to the .tex document.
                                             If None, no specific history file path is generated.

    Returns:
        str or None: The path to the history file, or None if tex_document_filepath is None.
    """
    if not tex_document_filepath:
        return None  # No specific file, so no specific history file
    base, _ = os.path.splitext(tex_document_filepath)
    return f"{base}_prompt_history.json"

def save_prompt_history_to_file(prompt_history_list, tex_document_filepath):
    """
    Saves the provided prompt history list to a JSON file.

    The file is associated with the given .tex document filepath.

    Args:
        prompt_history_list (list): The list of prompt-response tuples to save.
        tex_document_filepath (str or None): The path to the .tex document.
    """
    history_filepath = _get_prompt_history_filepath(tex_document_filepath)

    if not history_filepath:
        print("Debug: Not saving history as no .tex file path is available.")
        return  # Not saving if no .tex file is active or path cannot be determined

    try:
        with open(history_filepath, 'w', encoding='utf-8') as f:
            json.dump(prompt_history_list, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving prompt history to {history_filepath}: {e}")

def load_prompt_history_from_file(tex_document_filepath):
    """
    Loads prompt history from a JSON file associated with the given .tex file path.

    Args:
        tex_document_filepath (str or None): The path to the .tex document.

    Returns:
        list: The loaded prompt history (list of tuples), or an empty list if not found or on error.
    """
    history_filepath = _get_prompt_history_filepath(tex_document_filepath)
    loaded_history = []
    if history_filepath and os.path.exists(history_filepath):
        try:
            with open(history_filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                # Ensure loaded data is a list of 2-element lists/tuples
                loaded_history = [(item[0], item[1]) for item in loaded_data if isinstance(item, (list, tuple)) and len(item) == 2]
        except Exception as e:
            print(f"Error loading prompt history from {history_filepath}: {e}")
            loaded_history = []  # Reset to empty on error
    return loaded_history

def update_response_in_history(prompt_history_list, user_prompt_key, new_response_text):
    """
    Updates the response for a given user_prompt_key in the provided prompt_history_list.
    Modifies the list in-place.
    """
    for i, (p_user, _) in enumerate(prompt_history_list):
        if p_user == user_prompt_key: # Match the specific prompt that was being processed
            prompt_history_list[i] = (p_user, new_response_text)
            break