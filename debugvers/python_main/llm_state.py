import os

_root_window = None
_llm_progress_bar_widget = None
_theme_setting_getter_func = None
_active_editor_getter_func = None
_active_filepath_getter_func = None

_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROMPTS_FILE = os.path.join(_SERVICE_DIR, "default_prompts.json")
_global_default_prompts = {}

_llm_keywords_list = []
_prompt_history_list = []
_completion_prompt_template = ""
_generation_prompt_template = ""

_generated_text_range = None
_is_generating = False
_last_llm_action_type = None
_last_completion_phrase_start = None
_last_generation_user_prompt = None
_last_generation_lines_before = None
_last_generation_lines_after = None

def is_llm_service_initialized():
    return (
        _root_window is not None and
        _llm_progress_bar_widget is not None and
        _theme_setting_getter_func is not None and
        _active_editor_getter_func is not None and
        _active_filepath_getter_func is not None and
        (_completion_prompt_template or (_global_default_prompts and _global_default_prompts.get("completion"))) and
        (_generation_prompt_template or (_global_default_prompts and _global_default_prompts.get("generation")))
    )