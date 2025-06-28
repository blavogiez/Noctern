# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\llm_service.py
"""
Service layer for LLM (Large Language Model) functionalities.

This module coordinates interactions between the UI, LLM API client,
prompt history management, utility functions, and dialogs. It provides
the main entry points for LLM features like text completion, generation,
and keyword management.
"""
import tkinter as tk
from tkinter import messagebox
import os
import interface
import threading
import datetime

# Import factorized modules
import llm_state
import llm_init
import llm_keywords
import llm_interactive
import llm_prompt_history
import llm_utils
import llm_api_client
import llm_dialogs
import llm_prompt_manager
import llm_completion
import llm_generation

def initialize_llm_service(root_window_ref, progress_bar_widget_ref,
                           theme_setting_getter_func, active_editor_getter, active_filepath_getter):
    """
    Initializes the LLM service with necessary references from the main application.
    This should be called once when the application starts.
    """
    # Use the initialization module
    llm_init.initialize_llm_service(
        root_window_ref, progress_bar_widget_ref,
        theme_setting_getter_func, active_editor_getter, active_filepath_getter
    )
    
    # Bind global interaction keys using the interactive module
    root_window_ref.bind_all("<Tab>", llm_interactive.accept_generated_text)
    root_window_ref.bind_all("r", llm_interactive.rephrase_generated_text)
    root_window_ref.bind_all("c", llm_interactive.discard_generated_text)

def load_prompt_history_for_current_file():
    """
    Loads the prompt history associated with the currently active .tex file.
    """
    active_filepath = _get_active_tex_filepath()
    llm_state._prompt_history_list = llm_prompt_history.load_prompt_history_from_file(active_filepath)

def load_prompts_for_current_file():
    """Loads custom prompts for the current file."""
    active_filepath = _get_active_tex_filepath()
    loaded_prompts = llm_prompt_manager.load_prompts_from_file(active_filepath, llm_state._global_default_prompts)
    if active_filepath:
        print(f"INFO: Loaded prompts for '{os.path.basename(active_filepath)}'.")
    else:
        print("INFO: Loaded prompts for current session (no file open).")
    llm_state._completion_prompt_template = loaded_prompts["completion"]
    llm_state._generation_prompt_template = loaded_prompts["generation"]

def _get_active_tex_filepath():
    """Helper to safely get the current .tex file path using the provided getter."""
    if llm_state._active_filepath_getter_func:
        return llm_state._active_filepath_getter_func()
    return None

def request_llm_to_complete_text():
    """Requests sentence completion from the LLM based on preceding text."""
    # Delegate to the completion module
    llm_completion.request_llm_to_complete_text()

def open_generate_text_dialog(initial_prompt_text=None):
    """
    Opens a dialog for the user to input a custom prompt for LLM text generation.
    """
    # Delegate to the generation module
    llm_generation.open_generate_text_dialog(initial_prompt_text)

def open_set_keywords_dialog():
    """Opens a dialog for the user to set or update LLM keywords."""
    # Delegate to the keywords module
    llm_keywords.open_set_keywords_dialog()

def get_current_prompts():
    """Returns the current prompt templates."""
    return {
        "completion": llm_state._completion_prompt_template,
        "generation": llm_state._generation_prompt_template
    }

def update_prompts(completion_template, generation_template):
    """Updates the prompt templates and saves them to a custom file."""
    llm_state._completion_prompt_template = completion_template
    llm_state._generation_prompt_template = generation_template

    # Save to file
    active_filepath = _get_active_tex_filepath()
    if active_filepath:
        prompts_to_save = {
            "completion": llm_state._completion_prompt_template,
            "generation": llm_state._generation_prompt_template
        }
        llm_prompt_manager.save_prompts_to_file(prompts_to_save, active_filepath)
        prompts_filename = os.path.basename(llm_prompt_manager.get_prompts_filepath(active_filepath))
        interface.show_temporary_status_message(f"✅ Prompts saved: {prompts_filename}")
        print(f"INFO: Prompts saved to '{prompts_filename}'.")
    else:
        interface.show_temporary_status_message("⚠️ Prompts updated for this session only (no file open).")
        print("INFO: Prompts updated for this session only (no file open).")

def open_edit_prompts_dialog():
    """Opens a dialog to edit the LLM prompt templates."""
    if not llm_state._root_window or not llm_state._theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "UI components not fully initialized for prompts dialog.")
        return

    llm_dialogs.show_edit_prompts_dialog(
        root_window=llm_state._root_window,
        theme_setting_getter_func=llm_state._theme_setting_getter_func,
        current_prompts=get_current_prompts(),
        default_prompts=llm_state._global_default_prompts,
        on_save_callback=update_prompts
    )