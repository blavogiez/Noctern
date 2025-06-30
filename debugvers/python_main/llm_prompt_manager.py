import json
import os
import debug_console

def get_prompts_filepath(tex_document_filepath):
    """Generates the filepath for the custom prompts JSON file."""
    if not tex_document_filepath:
        return None
    base, _ = os.path.splitext(tex_document_filepath)
    return f"{base}_prompts.json"

def save_prompts_to_file(prompts_dict, tex_document_filepath):
    """Saves the provided prompts dictionary to a JSON file."""
    prompts_filepath = get_prompts_filepath(tex_document_filepath)
    if not prompts_filepath:
        debug_console.log("Not saving prompts as no .tex file path is available.", level='DEBUG')
        return
    try:
        with open(prompts_filepath, 'w', encoding='utf-8') as f:
            json.dump(prompts_dict, f, ensure_ascii=False, indent=4)
        debug_console.log(f"Successfully saved custom prompts to {os.path.basename(prompts_filepath)}.", level='SUCCESS')
    except Exception as e:
        debug_console.log(f"Error saving custom prompts to {prompts_filepath}: {e}", level='ERROR')

def load_prompts_from_file(tex_document_filepath, default_prompts):
    """Loads custom prompts from a JSON file. If the file doesn't exist, it creates one with the default prompts."""
    prompts_filepath = get_prompts_filepath(tex_document_filepath)

    if not prompts_filepath:
        debug_console.log("No active file, returning global default prompts.", level='INFO')
        return default_prompts

    if os.path.exists(prompts_filepath):
        try:
            with open(prompts_filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                debug_console.log(f"Successfully loaded custom prompts from {os.path.basename(prompts_filepath)}.", level='INFO')
                return {
                    "completion": loaded_data.get("completion", default_prompts["completion"]),
                    "generation": loaded_data.get("generation", default_prompts["generation"])
                }
        except Exception as e:
            debug_console.log(f"Error loading custom prompts from {prompts_filepath}, using defaults. Error: {e}", level='ERROR')
            return default_prompts
    else:
        debug_console.log(f"Prompts file not found for {os.path.basename(tex_document_filepath)}. Creating with defaults.", level='INFO')
        save_prompts_to_file(default_prompts, tex_document_filepath)
        return default_prompts