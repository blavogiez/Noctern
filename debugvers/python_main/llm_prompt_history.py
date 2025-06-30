import json
import os
import debug_console

# Maximum number of prompt-response pairs to store in the history.
MAX_PROMPT_HISTORY_SIZE = 20

def _get_prompt_history_filepath(tex_document_filepath):
    """
    Generates the filepath for the prompt history JSON file based on the .tex file's path.
    """
    if not tex_document_filepath:
        return None
    base, _ = os.path.splitext(tex_document_filepath)
    return f"{base}_prompt_history.json"

def save_prompt_history_to_file(prompt_history_list, tex_document_filepath):
    """
    Saves the provided prompt history list to a JSON file.
    """
    history_filepath = _get_prompt_history_filepath(tex_document_filepath)
    if not history_filepath:
        debug_console.log("Not saving history as no .tex file path is available.", level='DEBUG')
        return

    try:
        with open(history_filepath, 'w', encoding='utf-8') as f:
            json.dump(prompt_history_list, f, ensure_ascii=False, indent=4)
        debug_console.log(f"Prompt history saved to {os.path.basename(history_filepath)}.", level='DEBUG')
    except Exception as e:
        debug_console.log(f"Error saving prompt history to {history_filepath}: {e}", level='ERROR')

def load_prompt_history_from_file(tex_document_filepath):
    """
    Loads prompt history from a JSON file associated with the given .tex file path.
    """
    history_filepath = _get_prompt_history_filepath(tex_document_filepath)
    loaded_history = []
    if history_filepath and os.path.exists(history_filepath):
        try:
            with open(history_filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                loaded_history = [(item[0], item[1]) for item in loaded_data if isinstance(item, (list, tuple)) and len(item) == 2]
            debug_console.log(f"Loaded {len(loaded_history)} items from prompt history file {os.path.basename(history_filepath)}.", level='INFO')
        except Exception as e:
            debug_console.log(f"Error loading prompt history from {history_filepath}: {e}", level='ERROR')
            loaded_history = []
    return loaded_history

def update_response_in_history(prompt_history_list, user_prompt_key, new_response_text):
    """
    Updates the response for a given user_prompt_key in the provided prompt_history_list.
    Modifies the list in-place.
    """
    for i, (p_user, _) in enumerate(prompt_history_list):
        if p_user == user_prompt_key:
            prompt_history_list[i] = (p_user, new_response_text)
            break