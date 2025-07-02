"""
This module is responsible for the initial setup and configuration of the Large Language Model (LLM) service.
It loads default prompt templates, initializes global state variables, and prepares the LLM service
for interaction with the rest of the application.
"""

import json
import llm_state
import llm_history
import llm_prompts
import debug_console

def _load_global_default_prompts():
    """
    Loads the default LLM prompt templates from a JSON file into the global application state.

    These default prompts serve as a fallback if no custom prompts are defined for a specific document.
    If the file cannot be loaded, a set of hardcoded fallback prompts is used.
    """
    try:
        # Attempt to open and load the default prompts from the specified JSON file.
        with open(llm_state.DEFAULT_PROMPTS_FILE, 'r', encoding='utf-8') as file_handle:
            llm_state._global_default_prompts = json.load(file_handle)
            debug_console.log("Global default LLM prompts loaded successfully from file.", level='INFO')
    except Exception as e:
        # If loading fails, log the error and use hardcoded fallback prompts.
        debug_console.log(f"Failed to load global default LLM prompts from '{llm_state.DEFAULT_PROMPTS_FILE}': {e}. Using hardcoded fallback prompts.", level='ERROR')
        llm_state._global_default_prompts = {
            "completion": "Complete this: {current_phrase_start}",
            "generation": "Generate text for this prompt: {user_prompt}",
            "generation_latex": "You are a LaTeX expert. Generate only the raw LaTeX code for the following request. Do not add any explanation or markdown. Request: {user_prompt}",
            "model_for_latex_generation": "codellama" # Default model for LaTeX-oriented generation.
        }

def initialize_llm_service(root_window_ref, progress_bar_widget_ref,
                           theme_setting_getter_func, active_editor_getter_func, active_filepath_getter_func):
    """
    Initializes the core components and state of the LLM service.

    This function sets up global references to key Tkinter widgets and callback functions
    that the LLM service needs to interact with the main application UI and data.
    It also triggers the loading of default prompts and file-specific history/prompts.

    Args:
        root_window_ref (tk.Tk): Reference to the main Tkinter root window.
        progress_bar_widget_ref (ttk.Progressbar): Reference to the LLM progress bar widget.
        theme_setting_getter_func (callable): Function to retrieve current theme settings.
        active_editor_getter_func (callable): Function to get the currently active editor widget.
        active_filepath_getter_func (callable): Function to get the file path of the active editor.
    """
    # Store references to essential UI components and getter functions in the global state.
    llm_state._root_window = root_window_ref
    llm_state._llm_progress_bar_widget = progress_bar_widget_ref
    llm_state._theme_setting_getter_func = theme_setting_getter_func
    llm_state._active_editor_getter_func = active_editor_getter_func
    llm_state._active_filepath_getter_func = active_filepath_getter_func
    debug_console.log("LLM service core references successfully initialized.", level='INFO')

    # Load global default prompts from the configuration file.
    _load_global_default_prompts()
    # Load prompt history specific to the current file.
    llm_history.load_prompt_history_for_current_file()
    # Load custom prompts specific to the current file.
    llm_prompts.load_prompts_for_current_file()
    debug_console.log("LLM service fully initialized and ready.", level='SUCCESS')
