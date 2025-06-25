# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\llm_generation_history.py
"""
Manages the history of generated text blocks for styling purposes.
"""
import json
import os

def _get_generation_history_filepath(tex_document_filepath):
    """Generates the filepath for the generation history JSON file."""
    if not tex_document_filepath:
        return None
    base, _ = os.path.splitext(tex_document_filepath)
    return f"{base}_generation_history.json"

def save_generation_history_to_file(history_list, tex_document_filepath):
    """Saves the provided generation history list to a JSON file."""
    history_filepath = _get_generation_history_filepath(tex_document_filepath)
    if not history_filepath:
        return

    try:
        with open(history_filepath, 'w', encoding='utf-8') as f:
            json.dump(history_list, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving generation history to {history_filepath}: {e}")

def load_generation_history_from_file(tex_document_filepath):
    """Loads generation history from a JSON file."""
    history_filepath = _get_generation_history_filepath(tex_document_filepath)
    if history_filepath and os.path.exists(history_filepath):
        try:
            with open(history_filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                if isinstance(loaded_data, list):
                    return loaded_data
        except Exception as e:
            print(f"Error loading generation history from {history_filepath}: {e}")
    return []

def add_generation_to_history(history_list, indices):
    """Adds a new generation's indices to the history list."""
    # In the future, this could merge overlapping ranges. For now, just append.
    history_list.append(indices)