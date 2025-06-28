import llm_state
import llm_prompt_manager
import os
from tkinter import messagebox
import llm_dialogs

def load_prompts_for_current_file():
    active_filepath = None
    if llm_state._active_filepath_getter_func:
        active_filepath = llm_state._active_filepath_getter_func()
    loaded_prompts = llm_prompt_manager.load_prompts_from_file(active_filepath, llm_state._global_default_prompts)
    if active_filepath:
        print(f"INFO: Loaded prompts for '{os.path.basename(active_filepath)}'.")
    else:
        print("INFO: Loaded prompts for current session (no file open).")
    llm_state._completion_prompt_template = loaded_prompts["completion"]
    llm_state._generation_prompt_template = loaded_prompts["generation"]

def get_current_prompts():
    return {
        "completion": llm_state._completion_prompt_template,
        "generation": llm_state._generation_prompt_template
    }

def update_prompts(completion_template, generation_template):
    llm_state._completion_prompt_template = completion_template
    llm_state._generation_prompt_template = generation_template
    active_filepath = None
    if llm_state._active_filepath_getter_func:
        active_filepath = llm_state._active_filepath_getter_func()
    if active_filepath:
        prompts_to_save = {
            "completion": llm_state._completion_prompt_template,
            "generation": llm_state._generation_prompt_template
        }
        llm_prompt_manager.save_prompts_to_file(prompts_to_save, active_filepath)

def open_edit_prompts_dialog():
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
