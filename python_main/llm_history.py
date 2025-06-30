# llm_history.py

import llm_state
import llm_prompt_history
import debug_console

def _get_active_tex_filepath():
    """Helper to safely get the current .tex file path using the provided getter."""
    if llm_state._active_filepath_getter_func:
        return llm_state._active_filepath_getter_func()
    return None

def load_prompt_history_for_current_file():
    """Load prompt history for the current file."""
    active_filepath = _get_active_tex_filepath()
    debug_console.log(f"Loading prompt history for: {active_filepath or 'new file'}.", level='INFO')
    llm_state._prompt_history_list = llm_prompt_history.load_prompt_history_from_file(active_filepath)

def _add_entry_to_history_and_save(user_prompt, response_placeholder="⏳ Generating..."):
    """Internal helper to add a new entry and save the history."""
    debug_console.log(f"Adding new entry to prompt history: '{user_prompt[:50]}...'", level='DEBUG')
    # Remove existing entry for this user_prompt to move it to the top or update status
    llm_state._prompt_history_list = [item for item in llm_state._prompt_history_list if item[0] != user_prompt]
    llm_state._prompt_history_list.insert(0, (user_prompt, response_placeholder))

    if len(llm_state._prompt_history_list) > llm_prompt_history.MAX_PROMPT_HISTORY_SIZE:
        llm_state._prompt_history_list = llm_state._prompt_history_list[:llm_prompt_history.MAX_PROMPT_HISTORY_SIZE]

    active_filepath = _get_active_tex_filepath()
    llm_prompt_history.save_prompt_history_to_file(llm_state._prompt_history_list, active_filepath)

def _update_history_response_and_save(user_prompt_key, new_response_text):
    """Internal helper to update a response in history and save."""
    debug_console.log(f"Updating history response for prompt: '{user_prompt_key[:50]}...'", level='DEBUG')
    llm_prompt_history.update_response_in_history(llm_state._prompt_history_list, user_prompt_key, new_response_text)
    active_filepath = _get_active_tex_filepath()
    llm_prompt_history.save_prompt_history_to_file(llm_state._prompt_history_list, active_filepath)