"""
This module is responsible for the initial setup and configuration of the Large Language Model (LLM) service.
It loads default prompt templates, initializes global state variables, and prepares the LLM service
for interaction with the rest of the application.
"""

import json
from llm import state as llm_state
from llm import history as llm_history
from llm import prompts as llm_prompts
from utils import debug_console

def _load_global_default_prompts():
    """
    Loads the default LLM prompt templates from the `data/prompts` directory.
    """
    import os
    import tkinter.messagebox
    
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompts_dir_path = os.path.join(script_dir, llm_state.DEFAULT_PROMPTS_DIR)

    if not os.path.exists(prompts_dir_path) or not os.path.isdir(prompts_dir_path):
        error_msg = f"Critical error: Prompts directory not found at '{prompts_dir_path}'. Please restore the directory."
        debug_console.log(error_msg, level='CRITICAL')
        tkinter.messagebox.showerror("Critical Error", error_msg)
        llm_state._global_default_prompts = {}
        return

    loaded_prompts = {}
    try:
        for filename in os.listdir(prompts_dir_path):
            if filename.endswith(".txt"):
                prompt_name = os.path.splitext(filename)[0]
                file_path = os.path.join(prompts_dir_path, filename)
                with open(file_path, 'r', encoding='utf-8') as file_handle:
                    loaded_prompts[prompt_name] = file_handle.read()
        
        llm_state._global_default_prompts = loaded_prompts
        debug_console.log(f"Global default LLM prompts loaded successfully from '{prompts_dir_path}'.", level='INFO')

    except Exception as e:
        error_msg = f"Critical error: Failed to load one or more prompts from '{prompts_dir_path}': {e}."
        debug_console.log(error_msg, level='CRITICAL')
        tkinter.messagebox.showerror("Critical Error", error_msg)
        llm_state._global_default_prompts = {}


def initialize_llm_service(root_window_ref, progress_bar_widget_ref,
                           theme_setting_getter_func, active_editor_getter_func, 
                           active_filepath_getter_func, app_config):
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
        app_config (dict): The application's configuration dictionary.
    """
    # Store references to essential UI components and getter functions in the global state.
    llm_state._root_window = root_window_ref
    llm_state._llm_progress_bar_widget = progress_bar_widget_ref
    llm_state._theme_setting_getter_func = theme_setting_getter_func
    llm_state._active_editor_getter_func = active_editor_getter_func
    llm_state._active_filepath_getter_func = active_filepath_getter_func
    debug_console.log("LLM service core references successfully initialized.", level='INFO')

    # Load model configuration from settings
    llm_state.model_completion = app_config.get("model_completion", "default")
    llm_state.model_generation = app_config.get("model_generation", "default")
    llm_state.model_rephrase = app_config.get("model_rephrase", "default")
    llm_state.model_debug = app_config.get("model_debug", "default")
    llm_state.model_style = app_config.get("model_style", "default")
    llm_state.model_proofreading = app_config.get("model_proofreading", "default")
    debug_console.log(f"LLM models loaded: completion='{llm_state.model_completion}', generation='{llm_state.model_generation}', proofreading='{llm_state.model_proofreading}', etc.", level='INFO')

    # Load global default prompts from the configuration file.
    _load_global_default_prompts()
    # Defer loading file-specific history and prompts until needed
    debug_console.log("LLM service core initialized and ready.", level='SUCCESS')