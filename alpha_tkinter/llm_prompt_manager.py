# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\llm_prompt_manager.py
"""
Manages loading and saving custom LLM prompt templates.

Prompts are saved on a per-document basis, allowing users to have
different prompt configurations for different projects.
"""
import json
import os

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
        print("Debug: Not saving prompts as no .tex file path is available.")
        return
    try:
        with open(prompts_filepath, 'w', encoding='utf-8') as f:
            json.dump(prompts_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving custom prompts to {prompts_filepath}: {e}")

def load_prompts_from_file(tex_document_filepath, default_prompts):
    """
    Loads custom prompts from a JSON file. If the file doesn't exist, it creates one with the default prompts.
    It also automatically upgrades outdated simple prompts in existing files to the new defaults,
    while preserving actual user customizations.
    """
    prompts_filepath = get_prompts_filepath(tex_document_filepath)

    # If no file is open, just return the in-memory defaults
    if not prompts_filepath:
        return default_prompts

    if os.path.exists(prompts_filepath):
        try:
            with open(prompts_filepath, 'r', encoding='utf-8') as f:
                file_prompts = json.load(f)

            if not isinstance(file_prompts, dict):
                raise TypeError("Prompts file is not a valid dictionary.")

            # Start with the current, correct defaults.
            final_prompts = default_prompts.copy()
            needs_resave = False

            # If the loaded file is already up-to-date, no changes needed.
            if file_prompts == final_prompts:
                return final_prompts

            # Intelligently merge the file's prompts with the defaults.
            for key, default_value in default_prompts.items():
                file_value = file_prompts.get(key)

                if file_value is None:
                    needs_resave = True # Key is missing, file needs update.
                    continue # The default value is already in final_prompts.

                # Heuristic: old fallbacks were simple, single-line strings.
                # A prompt with no newlines is likely an old default, not a custom one.
                if '\n' not in file_value:
                    needs_resave = True # Mark for healing, use the new default.
                else:
                    # The value is multi-line, so we trust it as a customization.
                    final_prompts[key] = file_value
            
            if needs_resave:
                print(f"Debug: Upgrading prompts file for {os.path.basename(prompts_filepath)} with latest defaults.")
                save_prompts_to_file(final_prompts, tex_document_filepath)

            return final_prompts
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error loading or parsing custom prompts from {prompts_filepath}, overwriting with defaults. Error: {e}")
            save_prompts_to_file(default_prompts, tex_document_filepath)
            return default_prompts
    else:
        # File doesn't exist, so create it with default values
        print(f"Debug: Prompts file not found for {tex_document_filepath}. Creating with defaults.")
        save_prompts_to_file(default_prompts, tex_document_filepath)
        return default_prompts