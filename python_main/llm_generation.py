import llm_state
import llm_dialogs
import llm_utils
import llm_api_client
import tkinter as tk
from tkinter import messagebox
import interface
import datetime
from llm_history import _add_entry_to_history_and_save, _update_history_response_and_save
from llm_interactive import start_new_interactive_session # The new service

def open_generate_text_dialog(initial_prompt_text=None):
    # ... (Initial checks are unchanged) ...
    if not callable(llm_state._active_editor_getter_func): messagebox.showerror("LLM Service Error", "LLM Service not initialized (no editor getter)."); return
    editor = llm_state._active_editor_getter_func()
    if not editor or not llm_state._root_window or not llm_state._llm_progress_bar_widget or not llm_state._theme_setting_getter_func: messagebox.showerror("LLM Service Error", "LLM Service not fully initialized."); return
    if not (llm_state._generation_prompt_template or (llm_state._global_default_prompts and llm_state._global_default_prompts.get("generation"))): messagebox.showerror("LLM Service Error", "LLM prompt templates are not initialized. Please reload your file or restart the application."); return

    def _handle_generation_request_from_dialog(user_prompt, lines_before, lines_after):
        if llm_state._is_generating:
            interface.show_temporary_status_message("LLM is already generating. Please wait.")
            return

        # --- LOGIC IS NOW CLEAN: Build prompt, then hand off to the session manager ---
        llm_state._last_llm_action_type = "generation"
        llm_state._last_generation_user_prompt = user_prompt
        
        context = llm_utils.extract_editor_context(editor, lines_before, lines_after)
        prompt_template = llm_state._generation_prompt_template or llm_state._global_default_prompts.get("generation", "")
        full_llm_prompt = prompt_template.format(user_prompt=user_prompt, keywords=', '.join(llm_state._llm_keywords_list), context=context)
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Generation Request - Prompt: '{full_llm_prompt[:200]}...'")
        
        # Get the safe callback functions from our new service
        callbacks = start_new_interactive_session(editor)

        def run_generation_thread_target():
            # This thread no longer knows about the UI. It just calls callbacks.
            try:
                full_generated_text = ""
                for api_response_chunk in llm_api_client.request_llm_generation(full_llm_prompt):
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
                editor.after(0, lambda e=str(e): callbacks['on_error'](f"An unexpected error occurred: {e}"))
                editor.after(0, lambda: _update_history_response_and_save(user_prompt, f"❌ Exception: {str(e)[:100]}..."))
            finally:
                if llm_state._llm_progress_bar_widget:
                    editor.after(0, llm_state._llm_progress_bar_widget.stop)
                    editor.after(0, llm_state._llm_progress_bar_widget.pack_forget)

        llm_state._llm_progress_bar_widget.pack(pady=2)
        llm_state._llm_progress_bar_widget.start(10)
        import threading
        threading.Thread(target=run_generation_thread_target, daemon=True).start()

    # ... (Dialog creation logic is unchanged) ...
    def _handle_history_entry_addition_from_dialog(user_prompt): _add_entry_to_history_and_save(user_prompt, "⏳ Generating...")
    llm_dialogs.show_generate_text_dialog(root_window=llm_state._root_window, theme_setting_getter_func=llm_state._theme_setting_getter_func, current_prompt_history_list=llm_state._prompt_history_list, on_generate_request_callback=_handle_generation_request_from_dialog, on_history_entry_add_callback=_handle_history_entry_addition_from_dialog, initial_prompt_text=initial_prompt_text)