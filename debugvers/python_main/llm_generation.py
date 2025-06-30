import llm_state
import llm_dialogs
import llm_utils
import llm_api_client
import tkinter as tk
from tkinter import messagebox
import interface
import debug_console
from llm_history import _add_entry_to_history_and_save, _update_history_response_and_save
from llm_interactive import start_new_interactive_session

def open_generate_text_dialog(initial_prompt_text=None):
    """Opens the dialog for custom text generation."""
    debug_console.log("LLM Generation dialog opened.", level='ACTION')
    if not callable(llm_state._active_editor_getter_func): messagebox.showerror("LLM Service Error", "LLM Service not initialized (no editor getter)."); return
    editor = llm_state._active_editor_getter_func()
    if not editor or not llm_state._root_window or not llm_state._llm_progress_bar_widget or not llm_state._theme_setting_getter_func: messagebox.showerror("LLM Service Error", "LLM Service not fully initialized."); return
    if not (llm_state._generation_prompt_template or (llm_state._global_default_prompts and llm_state._global_default_prompts.get("generation"))): messagebox.showerror("LLM Service Error", "LLM prompt templates are not initialized. Please reload your file or restart the application."); return

    def _handle_generation_request_from_dialog(user_prompt, lines_before, lines_after, is_latex_mode):
        if llm_state._is_generating:
            interface.show_temporary_status_message("LLM is already generating. Please wait.")
            debug_console.log("LLM Generation aborted: another generation is in progress.", level='WARNING')
            return

        model_name = llm_api_client.DEFAULT_LLM_MODEL
        if is_latex_mode:
            prompt_template = llm_state._global_default_prompts.get("generation_latex")
            model_name = llm_state._global_default_prompts.get("model_for_latex_generation", "codellama")
            if not prompt_template:
                messagebox.showerror("Configuration Error", "The 'generation_latex' prompt is missing from default_prompts.json.")
                debug_console.log("LLM Generation failed: 'generation_latex' prompt missing.", level='ERROR')
                return
            debug_console.log(f"Using LaTeX generation mode with model '{model_name}'.", level='INFO')
        else:
            prompt_template = llm_state._generation_prompt_template or llm_state._global_default_prompts.get("generation", "")
        
        llm_state._last_llm_action_type = "generation"
        llm_state._last_generation_user_prompt = user_prompt
        
        context = llm_utils.extract_editor_context(editor, lines_before, lines_after)
        full_llm_prompt = prompt_template.format(user_prompt=user_prompt, keywords=', '.join(llm_state._llm_keywords_list), context=context)
        debug_console.log(f"LLM Generation Request - Prompt (start): '{full_llm_prompt[:200]}...'", level='INFO')
        
        callbacks = start_new_interactive_session(editor)

        def run_generation_thread_target():
            try:
                full_generated_text = ""
                for api_response_chunk in llm_api_client.request_llm_generation(full_llm_prompt, model_name=model_name):
                    if api_response_chunk["success"]:
                        if "chunk" in api_response_chunk:
                            chunk = api_response_chunk["chunk"]
                            full_generated_text += chunk
                            editor.after(0, lambda c=chunk: callbacks['on_chunk'](c))
                        if api_response_chunk.get("done"):
                            editor.after(0, callbacks['on_success'])
                            editor.after(0, lambda: _update_history_response_and_save(user_prompt, full_generated_text))
                            return
                    else:
                        error_msg = api_response_chunk["error"]
                        editor.after(0, lambda e=error_msg: callbacks['on_error'](e))
                        editor.after(0, lambda: _update_history_response_and_save(user_prompt, f"❌ Error: {error_msg[:100]}..."))
                        return
            except Exception as e:
                error_msg = f"An unexpected error occurred in generation thread: {e}"
                debug_console.log(error_msg, level='ERROR')
                editor.after(0, lambda e_msg=error_msg: callbacks['on_error'](e_msg))
                editor.after(0, lambda: _update_history_response_and_save(user_prompt, f"❌ Exception: {str(e)[:100]}..."))
            finally:
                if llm_state._llm_progress_bar_widget:
                    editor.after(0, llm_state._llm_progress_bar_widget.stop)
                    editor.after(0, llm_state._llm_progress_bar_widget.pack_forget)
        
        llm_state._llm_progress_bar_widget.pack(pady=2)
        llm_state._llm_progress_bar_widget.start(10)
        import threading
        threading.Thread(target=run_generation_thread_target, daemon=True).start()

    def _handle_history_entry_addition_from_dialog(user_prompt): _add_entry_to_history_and_save(user_prompt, "⏳ Generating...")
    llm_dialogs.show_generate_text_dialog(root_window=llm_state._root_window, theme_setting_getter_func=llm_state._theme_setting_getter_func, current_prompt_history_list=llm_state._prompt_history_list, on_generate_request_callback=_handle_generation_request_from_dialog, on_history_entry_add_callback=_handle_history_entry_addition_from_dialog, initial_prompt_text=initial_prompt_text)