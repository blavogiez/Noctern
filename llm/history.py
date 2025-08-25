"""
This module manages the history of LLM prompts and responses, associating them with specific LaTeX files.
It provides functions to load, save, add, and update entries in the prompt history,
ensuring persistence across application sessions.
"""

from llm import state as llm_state
from llm import prompt_history as llm_prompt_history
from utils import logs_console

def _get_active_tex_filepath():
    """
    Helper function to safely retrieve the file path of the currently active LaTeX document.

    This function uses a getter provided by `llm_state` to ensure that the correct
    file path is obtained, which is crucial for loading and saving file-specific history.

    Returns:
        str or None: The absolute path to the active .tex file, or None if no file is active.
    """
    if llm_state._active_filepath_getter_func:
        return llm_state._active_filepath_getter_func()
    return None

def load_prompt_history_for_current_file():
    """
    Loads the LLM prompt history relevant to the currently active LaTeX file.

    This function is typically called when a new file is opened or a tab is switched,
    ensuring that the displayed history is contextually accurate.
    The loaded history is stored in `llm_state._prompt_history_list`.
    """
    active_filepath = _get_active_tex_filepath()
    logs_console.log(f"Attempting to load prompt history for: {active_filepath or 'new/untitled file'}.", level='INFO')
    # Load history from the file using llm_prompt_history module.
    llm_state._prompt_history_list = llm_prompt_history.load_prompt_history_from_file(active_filepath)
    logs_console.log(f"Loaded {len(llm_state._prompt_history_list)} history entries.", level='DEBUG')

def _add_entry_to_history_and_save(user_prompt_text, response_placeholder="⏳ Generating..."):
    """
    Adds a new prompt-response entry to the current history list and saves it to file.

    If an entry with the same `user_prompt_text` already exists, it is removed and
    the new entry is added at the beginning, effectively moving it to the top.
    The history list is also truncated to a maximum size.

    Args:
        user_prompt_text (str): The user's prompt text.
        response_placeholder (str, optional): A placeholder text for the response, used
                                              while the LLM is generating. Defaults to "⏳ Generating...".
    """
    logs_console.log(f"Adding new entry to prompt history: '{user_prompt_text[:50]}...'", level='DEBUG')
    
    # Remove any existing entry with the same user prompt to ensure uniqueness and freshness.
    new_history_list = []
    for item in llm_state._prompt_history_list:
        if item[0] != user_prompt_text:
            new_history_list.append(item)
    llm_state._prompt_history_list = new_history_list
    
    # Insert the new entry at the beginning of the list (most recent first).
    llm_state._prompt_history_list.insert(0, (user_prompt_text, response_placeholder))

    # Enforce maximum history size.
    if len(llm_state._prompt_history_list) > llm_prompt_history.MAX_PROMPT_HISTORY_SIZE:
        llm_state._prompt_history_list = llm_state._prompt_history_list[:llm_prompt_history.MAX_PROMPT_HISTORY_SIZE]
        logs_console.log(f"Prompt history truncated to {llm_prompt_history.MAX_PROMPT_HISTORY_SIZE} entries.", level='DEBUG')

    # Save the updated history to the file associated with the current document.
    active_filepath = _get_active_tex_filepath()
    llm_prompt_history.save_prompt_history_to_file(llm_state._prompt_history_list, active_filepath)

def _update_history_response_and_save(user_prompt_key, new_response_text):
    """
    Updates the response text for a specific prompt entry in the history and saves the history.

    This is typically used to replace a placeholder response (e.g., "Generating...")
    with the actual LLM-generated text once it's fully received.

    Args:
        user_prompt_key (str): The user's prompt text that serves as the key to find the entry.
        new_response_text (str): The complete LLM-generated response text.
    """
    logs_console.log(f"Updating history response for prompt: '{user_prompt_key[:50]}...'", level='DEBUG')
    
    # Update the response for the matching user prompt in the history list.
    llm_prompt_history.update_response_in_history(llm_state._prompt_history_list, user_prompt_key, new_response_text)
    
    # Save the modified history to the file associated with the current document.
    active_filepath = _get_active_tex_filepath()
    llm_prompt_history.save_prompt_history_to_file(llm_state._prompt_history_list, active_filepath)
