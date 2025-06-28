import llm_state
import llm_dialogs
import llm_prompt_manager

def open_edit_prompts_dialog():
    # Utilise les variables d'état via llm_state
    if not llm_state._root_window or not llm_state._theme_setting_getter_func:
        from tkinter import messagebox
        messagebox.showerror("LLM Service Error", "UI components not fully initialized for prompts dialog.")
        return

    llm_dialogs.show_edit_prompts_dialog(
        root_window=llm_state._root_window,
        theme_setting_getter_func=llm_state._theme_setting_getter_func,
        current_prompts={
            "completion": llm_state._completion_prompt_template,
            "generation": llm_state._generation_prompt_template
        },
        default_prompts=llm_state._global_default_prompts,
        on_save_callback=update_prompts
    )

def update_prompts(completion_template, generation_template):
    llm_state._completion_prompt_template = completion_template
    llm_state._generation_prompt_template = generation_template
    active_filepath = None
    if llm_state._active_filepath_getter_func:
        active_filepath = llm_state._active_filepath_getter_func()
    if active_filepath:
        prompts_to_save = {
            "completion": completion_template,
            "generation": generation_template
        }
        llm_prompt_manager.save_prompts_to_file(prompts_to_save, active_filepath)
