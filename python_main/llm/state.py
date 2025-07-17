"""
This module defines and manages the global state for the Large Language Model (LLM) service.
It holds references to key UI components, configuration settings, LLM-related data (like prompts and history),
and flags indicating the current status of LLM operations.
"""

import os

# --- UI Component References ---
# These variables hold references to Tkinter widgets and functions from the main application
# that the LLM service needs to interact with.
_root_window = None  # Reference to the main Tkinter root window.
_llm_progress_bar_widget = None  # Reference to the progress bar used during LLM generation.
_theme_setting_getter_func = None  # Function to retrieve current theme settings (e.g., colors).
_active_editor_getter_func = None  # Function to get the currently active Tkinter Text editor widget.
_active_filepath_getter_func = None  # Function to get the file path of the active editor.

# --- Configuration and Defaults ---
# Determines the directory of this service module.
_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
# Path to the JSON file containing default LLM prompt templates.
DEFAULT_PROMPTS_FILE = os.path.join(_SERVICE_DIR, "default_prompts.json")
# Dictionary to store global default prompt templates loaded from `DEFAULT_PROMPTS_FILE`.
_global_default_prompts = {}

# --- LLM Data and State ---

# List of (user_prompt, llm_response) tuples, representing the history of LLM interactions.
_prompt_history_list = []
# The current prompt template string used for LLM text completion.
_completion_prompt_template = ""
# The current prompt template string used for general LLM text generation.
_generation_prompt_template = ""

# --- Interactive Session State ---
# Stores the Tkinter Text widget range (start, end) of the currently generated LLM text.
_generated_text_range = None
# Boolean flag indicating whether an LLM generation process is currently active.
_is_generating = False
# Stores the type of the last LLM action performed (e.g., "completion", "generation", "rephrase").
_last_llm_action_type = None
# Stores the starting phrase used for the last LLM completion request.
_last_completion_phrase_start = None
# Stores the user's prompt for the last LLM generation request.
_last_generation_user_prompt = None
# Stores the number of lines before the cursor used for context in the last generation request.
_last_generation_lines_before = None
# Stores the number of lines after the cursor used for context in the last generation request.
_last_generation_lines_after = None

def is_llm_service_initialized():
    """
    Checks if the essential components of the LLM service have been initialized.

    This function verifies that all critical UI references and prompt templates
    are set, indicating that the LLM service is ready to operate.

    Returns:
        bool: True if the LLM service is fully initialized, False otherwise.
    """
    return (
        _root_window is not None and
        _llm_progress_bar_widget is not None and
        _theme_setting_getter_func is not None and
        _active_editor_getter_func is not None and
        _active_filepath_getter_func is not None and
        # Ensure at least one of the prompt templates (custom or default) is available.
        (_completion_prompt_template or (_global_default_prompts and _global_default_prompts.get("completion"))) and
        (_generation_prompt_template or (_global_default_prompts and _global_default_prompts.get("generation")))
    )
