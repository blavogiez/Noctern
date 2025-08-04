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

# --- Model Configuration ---
model_completion = "default"
model_generation = "default"
model_rephrase = "default"
model_debug = "default"
model_style = "default"
last_style_intensity = 5 # Default intensity on a 1-10 scale


# --- Prompt Templates and History ---
# Holds the global default prompts loaded from the JSON file.
_global_default_prompts = {}
# File path for the default prompts configuration.
DEFAULT_PROMPTS_FILE = "data/default_prompts.json"

# Per-document state (managed by llm.history and llm.prompts modules)
# These are loaded/saved based on the active file.
_prompt_history_list = [] # List of (user_prompt, llm_response) tuples.
_completion_prompt_template = ""      # Custom completion prompt for the current file.
_generation_prompt_template = ""      # Custom generation prompt for the current file.
_styling_prompt_template = ""         # Custom styling prompt for the current file.
_llm_keywords_list = []               # List of keywords for the current file.

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

# --- Getters ---
def get_root_window(): return _root_window
def get_llm_progress_bar(): return _llm_progress_bar_widget
def get_theme_settings(): return _theme_setting_getter_func()
def get_active_editor(): return _active_editor_getter_func()
def get_active_filepath(): return _active_filepath_getter_func()

def is_generating(): return _is_generating
def is_generation_cancelled(): return _is_generation_cancelled

def get_global_default_prompts(): return _global_default_prompts
def get_prompt_history(): return _prompt_history_list
def get_completion_prompt(): return _completion_prompt_template
def get_generation_prompt(): return _generation_prompt_template
def get_styling_prompt(): return _styling_prompt_template
def get_llm_keywords(): return _llm_keywords_list

def get_last_llm_action_type(): return _last_llm_action_type
def get_last_completion_phrase_start(): return _last_completion_phrase_start
def get_last_generation_context(): return _last_generation_context

# --- Setters ---
def set_is_generating(value):
    global _is_generating
    _is_generating = value

def set_is_generation_cancelled(value):
    global _is_generation_cancelled
    _is_generation_cancelled = value

def set_global_default_prompts(prompts):
    global _global_default_prompts
    _global_default_prompts = prompts

def set_prompt_history(history):
    global _prompt_history_list
    _prompt_history_list = history

def set_completion_prompt(prompt):
    global _completion_prompt_template
    _completion_prompt_template = prompt

def set_generation_prompt(prompt):
    global _generation_prompt_template
    _generation_prompt_template = prompt

def set_styling_prompt(prompt):
    global _styling_prompt_template
    _styling_prompt_template = prompt

def set_llm_keywords(keywords):
    global _llm_keywords_list
    _llm_keywords_list = keywords

def set_last_llm_action_type(action_type):
    global _last_llm_action_type
    _last_llm_action_type = action_type

def set_last_completion_phrase_start(phrase_start):
    global _last_completion_phrase_start
    _last_completion_phrase_start = phrase_start

def set_last_generation_context(context):
    global _last_generation_context
    _last_generation_context = context