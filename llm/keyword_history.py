import json
import os
from utils import debug_console
from llm.prompt_manager import get_document_cache_dir

def _get_keyword_filepath(file_path: str) -> str | None:
    """
    Generates the absolute file path for the keyword JSON file.
    The keyword file is stored in the document's cache directory as 'keywords.json'.
    Args:
        file_path: The absolute path to the document file.
    Returns:
        The absolute path to the keyword JSON file, or None if the
        `file_path` is invalid or not provided.
    """
    if not file_path:
        debug_console.log("Cannot generate keyword filepath: No document path provided.", level='DEBUG')
        return None
    
    cache_dir = get_document_cache_dir(file_path)
    if not cache_dir:
        return None
    
    # Ensure the cache directory exists
    os.makedirs(cache_dir, exist_ok=True)
    
    keyword_file_path = os.path.join(cache_dir, "keywords.json")
    debug_console.log(f"Generated keyword filepath: {keyword_file_path}", level='DEBUG')
    return keyword_file_path

def get_keywords_for_file(file_path: str) -> list[str]:
    """
    Retrieves the list of keywords for a specific file by reading its corresponding
    'keywords.json' file from the document's cache directory.
    Args:
        file_path: The absolute path to the file.
    Returns:
        A list of keywords, or an empty list if the keyword file doesn't exist or is invalid.
    """
    if not file_path:
        return []
    
    keyword_filepath = _get_keyword_filepath(file_path)
    if not keyword_filepath or not os.path.exists(keyword_filepath):
        return []

    try:
        with open(keyword_filepath, 'r', encoding='utf-8') as f:
            keywords = json.load(f)
            if isinstance(keywords, list):
                debug_console.log(f"Loaded {len(keywords)} keywords for '{os.path.basename(file_path)}' from {os.path.basename(keyword_filepath)}", level='INFO')
                return keywords
            else:
                debug_console.log(f"Invalid keyword file format in '{keyword_filepath}': expected a JSON list.", level='WARNING')
                return []
    except (json.JSONDecodeError, IOError) as e:
        debug_console.log(f"Error reading keyword file '{keyword_filepath}': {e}", level='ERROR')
        return []

def set_keywords_for_file(file_path: str, keywords: list[str]):
    """
    Sets the list of keywords for a specific file and saves it to a 
    'keywords.json' file in the document's cache directory.
    Args:
        file_path: The absolute path to the file.
        keywords: The new list of keywords for the file.
    """
    if not file_path:
        debug_console.log("Cannot set keywords for an empty file path.", level='WARNING')
        return

    keyword_filepath = _get_keyword_filepath(file_path)
    if not keyword_filepath:
        debug_console.log("Could not determine keyword file path. Aborting save.", level='ERROR')
        return

    debug_console.log(f"Setting keywords for '{os.path.basename(file_path)}': {keywords}", level='CONFIG')
    try:
        with open(keyword_filepath, 'w', encoding='utf-8') as f:
            json.dump(keywords, f, indent=4)
        debug_console.log(f"Saved keywords to {os.path.basename(keyword_filepath)}", level='INFO')
    except IOError as e:
        debug_console.log(f"Error saving keyword file '{keyword_filepath}': {e}", level='ERROR')
