# File: llm_keyword_manager.py
# automa_tex_pyqt/services/llm_keyword_manager.py
import json
import os

def _get_keywords_filepath(tex_document_filepath):
    """Generates the filepath for the custom keywords JSON file."""
    if not tex_document_filepath:
        return None
    base, _ = os.path.splitext(tex_document_filepath)
    return f"{base}_keywords.json"

def save_keywords_to_file(keywords_list, tex_document_filepath):
    """Saves the provided keywords list to a JSON file."""
    keywords_filepath = _get_keywords_filepath(tex_document_filepath)
    if not keywords_filepath:
        print("Debug: Not saving keywords as no .tex file path is available.")
        return
    try:
        with open(keywords_filepath, 'w', encoding='utf-8') as f:
            json.dump(keywords_list, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving custom keywords to {keywords_filepath}: {e}")

def load_keywords_from_file(tex_document_filepath):
    """Loads custom keywords from a JSON file. If the file doesn't exist, returns an empty list."""
    keywords_filepath = _get_keywords_filepath(tex_document_filepath)

    if not keywords_filepath or not os.path.exists(keywords_filepath):
        return []

    try:
        with open(keywords_filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            return loaded_data if isinstance(loaded_data, list) else []
    except Exception as e:
        print(f"Error loading custom keywords from {keywords_filepath}: {e}. Returning empty list.")
        return []
