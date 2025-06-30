import llm_state
import llm_prompt_manager
import os
from tkinter import messagebox
import llm_dialogs
import debug_console

def load_prompts_for_current_file():
    active_filepath = llm_state._active_filepath_getter_func() if llm_state._active_filepath_getter_func else None
    debug_console.log(f"Loading prompts for: {active_filepath or 'new file'}.", level='INFO')
    loaded_prompts = llm_prompt_manager.load_prompts_from_file(active_filepath, llm_state._global_default_prompts)
    llm_state._completion_prompt_template = loaded_prompts.get("completion", "")
    llm_state._generation_prompt_template = loaded_prompts.get("generation", "")

def get_current_prompts():
    return {
        "completion": llm_state._completion_prompt_template,
        "generation": llm_state._generation_prompt_template
    }

def update_prompts(completion_template, generation_template):
    debug_console.log("Updating prompt templates.", level='CONFIG')
    llm_state._completion_prompt_template = completion_template
    llm_state._generation_prompt_template = generation_template
    active_filepath = llm_state._active_filepath_getter_func() if llm_state._active_filepath_getter_func else None
    if active_filepath:
        prompts_to_save = {
            "completion": llm_state._completion_prompt_template,
            "generation": llm_state._generation_prompt_template
        }
        llm_prompt_manager.save_prompts_to_file(prompts_to_save, active_filepath)

def open_edit_prompts_dialog():
    debug_console.log("Edit Prompts dialog opened.", level='ACTION')
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