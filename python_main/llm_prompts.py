import llm_state
import llm_prompt_manager

def load_prompts_for_current_file():
    active_filepath = None
    if llm_state._active_filepath_getter_func:
        active_filepath = llm_state._active_filepath_getter_func()
    loaded_prompts = llm_prompt_manager.load_prompts_from_file(
        active_filepath, llm_state._global_default_prompts
    )
    llm_state._completion_prompt_template = loaded_prompts.get(
        "completion", llm_state._global_default_prompts.get("completion", "")
    )
    llm_state._generation_prompt_template = loaded_prompts.get(
        "generation", llm_state._global_default_prompts.get("generation", "")
    )

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
    import llm_prompts_dialog
    llm_prompts_dialog.open_edit_prompts_dialog()
