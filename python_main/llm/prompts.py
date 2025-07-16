"""
This module manages the LLM prompt templates used for completion and generation tasks.
It handles loading prompts specific to the current document, providing access to them,
updating them, and saving them back to file. It also integrates with the prompt editing dialog.
"""

from tkinter import messagebox
from llm import state as llm_state
from llm import prompt_manager as llm_prompt_manager
from llm import dialogs as llm_dialogs
from utils import debug_console

def load_prompts_for_current_file():
    """
    Loads the custom prompt templates for the currently active file.

    If a custom prompts file exists for the current document, its templates are loaded.
    Otherwise, the global default prompt templates are used as a fallback.
    The loaded templates are stored in `llm_state` for application-wide access.
    """
    # Safely get the active file path using the getter function from llm_state.
    active_filepath = llm_state._active_filepath_getter_func() if llm_state._active_filepath_getter_func else None
    debug_console.log(f"Attempting to load prompt templates for: {active_filepath or 'new/untitled file'}.", level='INFO')
    
    # Load prompts using the llm_prompt_manager, providing global defaults as fallback.
    loaded_prompts = llm_prompt_manager.load_prompts_from_file(active_filepath, llm_state._global_default_prompts)
    
    # Update the global state with the loaded completion and generation prompt templates.
    llm_state._completion_prompt_template = loaded_prompts.get("completion", "")
    llm_state._generation_prompt_template = loaded_prompts.get("generation", "")
    debug_console.log("Prompt templates loaded into LLM state.", level='DEBUG')

def get_current_prompts():
    """
    Returns a dictionary containing the currently active LLM prompt templates.

    This function provides a convenient way to access the prompt templates that are
    currently in use by the LLM service, whether they are custom or default.

    Returns:
        dict: A dictionary with keys "completion" and "generation", and their
              corresponding prompt template strings as values.
    """
    return {
        "completion": llm_state._completion_prompt_template,
        "generation": llm_state._generation_prompt_template
    }

def update_prompts(completion_template_text, generation_template_text):
    """
    Updates the LLM prompt templates for the current document and saves them to file.

    This function is typically called after a user has edited the prompt templates
    in the dialog. It updates the in-memory state and then persists the changes
    to a file associated with the active document.

    Args:
        completion_template_text (str): The new template string for completion prompts.
        generation_template_text (str): The new template string for generation prompts.
    """
    debug_console.log("Updating LLM prompt templates and saving changes.", level='CONFIG')
    
    # Update the in-memory prompt templates in the global state.
    llm_state._completion_prompt_template = completion_template_text
    llm_state._generation_prompt_template = generation_template_text
    
    # Get the active file path to determine where to save the custom prompts.
    active_filepath = llm_state._active_filepath_getter_func() if llm_state._active_filepath_getter_func else None
    
    if active_filepath:
        # Create a dictionary of the prompts to be saved.
        prompts_to_save = {
            "completion": llm_state._completion_prompt_template,
            "generation": llm_state._generation_prompt_template
        }
        # Save the prompts to the file using the llm_prompt_manager.
        llm_prompt_manager.save_prompts_to_file(prompts_to_save, active_filepath)
        debug_console.log("Prompt templates saved successfully.", level='SUCCESS')
    else:
        debug_console.log("Cannot save prompt templates: No active file path available.", level='WARNING')

def open_edit_prompts_dialog():
    """
    Opens a dialog window that allows the user to edit the LLM prompt templates.

    This dialog provides an interface for customizing the completion and generation
    prompts, with options to restore default templates. Changes made in this dialog
    are saved on a per-document basis.
    """
    debug_console.log("Opening 'Edit LLM Prompt Templates' dialog.", level='ACTION')
    
    # Pre-check for essential UI components to ensure the dialog can be displayed.
    if not llm_state._root_window or not llm_state._theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "UI components are not fully initialized for the prompts dialog. Please restart the application.")
        debug_console.log("LLM Prompts dialog failed to open: Missing root window or theme getter.", level='ERROR')
        return

    # Display the prompt editing dialog, passing necessary UI references, current prompts,
    # default prompts, and the callback function for saving changes.
    llm_dialogs.show_edit_prompts_dialog(
        root_window=llm_state._root_window,
        theme_setting_getter_func=llm_state._theme_setting_getter_func,
        current_prompts=get_current_prompts(), # Pass the currently active prompts.
        default_prompts=llm_state._global_default_prompts, # Pass the global default prompts.
        on_save_callback=update_prompts # Callback for when the user saves changes in the dialog.
    )
