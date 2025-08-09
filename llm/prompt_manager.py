"""
This module manages loading and saving custom LLM prompt templates for specific documents.
It uses a cache directory (`document_name.cache/prompts/`) alongside the document to store overrides.
"""

import os
from utils import debug_console

def get_document_cache_dir(tex_filepath):
    """Returns the path to the document's cache directory."""
    if not tex_filepath:
        return None
    base_name, _ = os.path.splitext(tex_filepath)
    return f"{base_name}.cache"

def get_custom_prompts_dir(tex_filepath):
    """Returns the path to the custom prompts directory within the document's cache."""
    cache_dir = get_document_cache_dir(tex_filepath)
    return os.path.join(cache_dir, "prompts") if cache_dir else None

def save_prompts_to_file(prompts_to_save, global_defaults, tex_filepath):
    """
    Saves custom prompts that differ from the global defaults to the document's cache.
    If a prompt is reverted to its default, the custom file is deleted.
    """
    custom_prompts_dir = get_custom_prompts_dir(tex_filepath)
    if not custom_prompts_dir:
        debug_console.log("Skipping custom prompts save: No valid .tex file path.", level='INFO')
        return

    os.makedirs(custom_prompts_dir, exist_ok=True)

    for key, value in prompts_to_save.items():
        default_value = global_defaults.get(key, "")
        custom_prompt_path = os.path.join(custom_prompts_dir, f"{key}.txt")

        # If the prompt is custom (different from default), save it
        if value.strip() != default_value.strip():
            try:
                with open(custom_prompt_path, 'w', encoding='utf-8') as f:
                    f.write(value)
                debug_console.log(f"Saved custom prompt '{key}' for {os.path.basename(tex_filepath)}.", level='INFO')
            except Exception as e:
                debug_console.log(f"Error saving custom prompt '{key}': {e}", level='ERROR')
        # If the prompt is same as default and a custom file exists, remove it
        elif os.path.exists(custom_prompt_path):
            try:
                os.remove(custom_prompt_path)
                debug_console.log(f"Removed default prompt override '{key}' for {os.path.basename(tex_filepath)}.", level='INFO')
            except Exception as e:
                debug_console.log(f"Error removing custom prompt file '{key}': {e}", level='ERROR')

def load_prompts_from_file(tex_filepath, global_defaults):
    """
    Loads prompts for a document, starting with global defaults and overriding
    with any custom prompts found in the document's cache directory.
    """
    # Start with a copy of the global defaults
    loaded_prompts = global_defaults.copy()
    
    custom_prompts_dir = get_custom_prompts_dir(tex_filepath)
    if not custom_prompts_dir or not os.path.isdir(custom_prompts_dir):
        # No custom prompts directory, so just return the defaults
        return loaded_prompts

    # Override defaults with any custom prompts found
    for key in loaded_prompts:
        custom_prompt_path = os.path.join(custom_prompts_dir, f"{key}.txt")
        if os.path.exists(custom_prompt_path):
            try:
                with open(custom_prompt_path, 'r', encoding='utf-8') as f:
                    loaded_prompts[key] = f.read()
                debug_console.log(f"Loaded custom prompt override '{key}' for {os.path.basename(tex_filepath)}.", level='INFO')
            except Exception as e:
                debug_console.log(f"Error loading custom prompt '{key}': {e}", level='ERROR')
                # Keep the default value if loading fails

    return loaded_prompts