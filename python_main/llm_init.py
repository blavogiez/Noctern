# llm_init.py

import json
import llm_state
import llm_history
import llm_prompts
import debug_console

def _load_global_default_prompts():
    """Loads the default prompts from the JSON file into the global state."""
    try:
        with open(llm_state.DEFAULT_PROMPTS_FILE, 'r', encoding='utf-8') as f:
            llm_state._global_default_prompts = json.load(f)
            debug_console.log("Global default prompts loaded successfully.", level='INFO')
    except Exception as e:
        debug_console.log(f"Failed to load global default prompts: {e}. Using fallback.", level='ERROR')
        llm_state._global_default_prompts = {
            "completion": "Complete this: {current_phrase_start}",
            "generation": "Generate text for this prompt: {user_prompt}",
            "generation_latex": "You are a LaTeX expert. Generate only the raw LaTeX code for the following request. Do not add any explanation or markdown. Request: {user_prompt}",
            "model_for_latex_generation": "codellama"
        }

def initialize_llm_service(root_window_ref, progress_bar_widget_ref,
                           theme_setting_getter_func, active_editor_getter, active_filepath_getter):
    """
    Initializes the LLM service by setting up all necessary state and loading initial data.
    """
    llm_state._root_window = root_window_ref
    llm_state._llm_progress_bar_widget = progress_bar_widget_ref
    llm_state._theme_setting_getter_func = theme_setting_getter_func
    llm_state._active_editor_getter_func = active_editor_getter
    llm_state._active_filepath_getter_func = active_filepath_getter
    debug_console.log("LLM service core references initialized.", level='INFO')

    _load_global_default_prompts()
    llm_history.load_prompt_history_for_current_file()
    llm_prompts.load_prompts_for_current_file()
    debug_console.log("LLM service fully initialized.", level='SUCCESS')