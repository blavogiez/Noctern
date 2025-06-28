import json
import llm_state
import llm_history
import llm_prompts

def _load_global_default_prompts():
    try:
        with open(llm_state.DEFAULT_PROMPTS_FILE, 'r', encoding='utf-8') as f:
            llm_state._global_default_prompts = json.load(f)
    except Exception:
        llm_state._global_default_prompts = {
            "completion": "Complete this: {current_phrase_start}",
            "generation": "Generate text for this prompt: {user_prompt}"
        }

def initialize_llm_service(root_window_ref, progress_bar_widget_ref,
                           theme_setting_getter_func, active_editor_getter, active_filepath_getter):
    llm_state._root_window = root_window_ref
    llm_state._llm_progress_bar_widget = progress_bar_widget_ref
    llm_state._theme_setting_getter_func = theme_setting_getter_func
    llm_state._active_editor_getter_func = active_editor_getter  # Renamed for clarity
    llm_state._active_filepath_getter_func = active_filepath_getter

    _load_global_default_prompts()
    llm_history.load_prompt_history_for_current_file()
    llm_prompts.load_prompts_for_current_file()
