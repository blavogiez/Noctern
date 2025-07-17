"""
This module manages the global state of the Large Language Model (LLM) service.
It centralizes variables and references that need to be accessed by different
parts of the LLM functionality, such as UI components, API clients, and prompt managers.
"""

# --- Core UI and Application References ---
_root_window = None                  # Reference to the main Tkinter root window.
_llm_progress_bar_widget = None      # Reference to the LLM progress bar widget.
_theme_setting_getter_func = None    # Function to get current theme settings (e.g., colors, fonts).
_active_editor_getter_func = None    # Function to get the currently active editor widget.
_active_filepath_getter_func = None  # Function to get the file path of the active editor.

# --- LLM Generation State ---
_is_generating = False  # Flag to indicate if an LLM generation is currently in progress.
_is_generation_cancelled = False # Flag to indicate if the user has cancelled the current generation.

# --- Prompt Templates and History ---
# Holds the global default prompts loaded from the JSON file.
_global_default_prompts = {}
# File path for the default prompts configuration.
DEFAULT_PROMPTS_FILE = "data/default_prompts.json"

# Per-document state (managed by llm.history and llm.prompts modules)
# These are loaded/saved based on the active file.
_prompt_history_for_current_file = [] # List of (user_prompt, llm_response) tuples.
_completion_prompt_template = ""      # Custom completion prompt for the current file.
_generation_prompt_template = ""      # Custom generation prompt for the current file.

# --- Last Action State (for re-generation) ---
# Stores the type of the last LLM action ('completion' or 'generation') to enable re-doing.
_last_llm_action_type = None
# Stores the context of the last completion request.
_last_completion_phrase_start = ""
# Stores the context of the last generation request.
_last_generation_context = {
    "user_prompt": "",
    "lines_before": 0,
    "lines_after": 0,
    "is_latex_mode": False
}