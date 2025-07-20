"""
This module manages the loading and saving of custom LLM prompt templates associated with specific LaTeX documents.
It allows users to define per-document prompt configurations, falling back to global defaults if no custom prompts are found.
"""

import json
import os
from utils import debug_console

def get_prompts_filepath(tex_document_filepath):
    """
    Generates the absolute file path for the custom LLM prompts JSON file.

    The prompts file is named after the LaTeX document, with a '_prompts.json' suffix,
    and is located in the same directory as the .tex file.

    Args:
        tex_document_filepath (str): The absolute path to the LaTeX document file.

    Returns:
        str or None: The absolute path to the custom prompts JSON file, or None if the
                     `tex_document_filepath` is invalid or not provided.
    """
    if not tex_document_filepath:
        debug_console.log("Cannot generate prompts filepath: No .tex document path provided.", level='DEBUG')
        return None
    
    # Split the base name and extension, then append the prompts suffix.
    base_name_without_ext, _ = os.path.splitext(tex_document_filepath)
    prompts_file_path = f"{base_name_without_ext}_prompts.json"
    debug_console.log(f"Generated custom prompts filepath: {prompts_file_path}", level='DEBUG')
    return prompts_file_path

def save_prompts_to_file(prompts_dict, tex_document_filepath):
    """
    Saves the provided dictionary of custom LLM prompt templates to a JSON file.

    The prompts are saved to a file determined by `get_prompts_filepath`.
    If the `tex_document_filepath` is not available, the prompts are not saved.

    Args:
        prompts_dict (dict): A dictionary containing prompt templates (e.g., {"completion": "...", "generation": "..."}).
        tex_document_filepath (str): The absolute path to the associated LaTeX document file.
    """
    prompts_filepath = get_prompts_filepath(tex_document_filepath)
    if not prompts_filepath:
        debug_console.log("Skipping custom prompts save: No valid .tex file path to associate prompts with.", level='INFO')
        return
    try:
        # Write the prompts dictionary to the JSON file with pretty-printing.
        with open(prompts_filepath, 'w', encoding='utf-8') as file_handle:
            json.dump(prompts_dict, file_handle, ensure_ascii=False, indent=4)
        debug_console.log(f"Custom prompts successfully saved to {os.path.basename(prompts_filepath)}.", level='SUCCESS')
    except Exception as e:
        debug_console.log(f"Error saving custom prompts to '{prompts_filepath}': {e}", level='ERROR')

def load_prompts_from_file(tex_document_filepath, default_prompts):
    """
    Loads custom LLM prompt templates from a JSON file associated with the given LaTeX document.

    If a custom prompts file exists, its contents are loaded. If the file does not exist,
    a new one is created with the provided `default_prompts`, and these defaults are returned.
    If an error occurs during loading, the `default_prompts` are returned as a fallback.

    Args:
        tex_document_filepath (str): The absolute path to the associated LaTeX document file.
        default_prompts (dict): A dictionary of global default prompt templates to use as a fallback.

    Returns:
        dict: A dictionary containing the loaded custom prompt templates, or the default prompts
              if no custom prompts are found or an error occurs.
    """
    prompts_filepath = get_prompts_filepath(tex_document_filepath)

    if not prompts_filepath:
        debug_console.log("No active file path provided. Returning global default prompts.", level='INFO')
        return default_prompts

    if os.path.exists(prompts_filepath):
        try:
            with open(prompts_filepath, 'r', encoding='utf-8') as file_handle:
                loaded_data = json.load(file_handle)
                debug_console.log(f"Successfully loaded custom prompts from {os.path.basename(prompts_filepath)}.", level='INFO')
                # Return loaded prompts, falling back to defaults for any missing keys.
                return {
                    "completion": loaded_data.get("completion", default_prompts.get("completion", "")),
                    "generation": loaded_data.get("generation", default_prompts.get("generation", ""))
                }
        except json.JSONDecodeError as e:
            debug_console.log(f"Error decoding JSON from custom prompts file '{prompts_filepath}': {e}. Using default prompts.", level='ERROR')
            return default_prompts
        except Exception as e:
            debug_console.log(f"An unexpected error occurred loading custom prompts from '{prompts_filepath}': {e}. Using default prompts.", level='ERROR')
            return default_prompts
    else:
        debug_console.log(f"Custom prompts file not found for '{os.path.basename(tex_document_filepath)}'. Creating new file with default prompts.", level='INFO')
        # If the file doesn't exist, save the default prompts to a new file.
        save_prompts_to_file(default_prompts, tex_document_filepath)
        return default_prompts
