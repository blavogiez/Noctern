import llm_state
import llm_dialogs
import llm_utils
import llm_api_client
import tkinter as tk
from tkinter import messagebox
import interface
import datetime
from llm_history import _add_entry_to_history_and_save, _update_history_response_and_save
from llm_interactive import clear_generated_text_state, show_llm_buttons


def open_generate_text_dialog(initial_prompt_text=None):
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not initialized (no editor getter).")
        return

    editor = llm_state._active_editor_getter_func()
    if not editor or not llm_state._root_window or not llm_state._llm_progress_bar_widget or not llm_state._theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized.")
        return

    if not (llm_state._generation_prompt_template or (llm_state._global_default_prompts and llm_state._global_default_prompts.get("generation"))):
        messagebox.showerror("LLM Service Error", "LLM prompt templates are not initialized. Please reload your file or restart the application.")
        return

    def _handle_generation_request_from_dialog(user_prompt, lines_before, lines_after):
        if llm_state._is_generating:
            interface.show_temporary_status_message("LLM is already generating. Please wait or interact with current generation.")
            return

        clear_generated_text_state()
        llm_state._is_generating = True
        llm_state._last_llm_action_type = "generation"
        llm_state._last_generation_user_prompt = user_prompt
        llm_state._last_generation_lines_before = lines_before
        llm_state._last_generation_lines_after = lines_after

        def run_generation_thread_target(local_user_prompt, local_lines_before, local_lines_after):
            active_editor = llm_state._active_editor_getter_func()
            if not active_editor:
                clear_generated_text_state()
                return

            try:
                start_index = active_editor.index(tk.INSERT)
                llm_state._generated_text_range = (start_index, start_index)
                # Show buttons above the generated text
                active_editor.after(0, lambda: show_llm_buttons(active_editor, start_index))

                context = llm_utils.extract_editor_context(active_editor, local_lines_before, local_lines_after)
                prompt_template = llm_state._generation_prompt_template or llm_state._global_default_prompts.get("generation", "")
                full_llm_prompt = prompt_template.format(
                    user_prompt=local_user_prompt,
                    keywords=', '.join(llm_state._llm_keywords_list),
                    context=context
                )

                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Generation Request - Prompt: '{full_llm_prompt[:200]}...'")

                final_api_response_status = {"success": False, "error": "No response received."}
                full_generated_text = ""
                for api_response_chunk in llm_api_client.request_llm_generation(full_llm_prompt):
                    if api_response_chunk["success"]:
                        if "chunk" in api_response_chunk:
                            chunk = api_response_chunk["chunk"]
                            full_generated_text += chunk
                            def insert_and_update_buttons(c=chunk):
                                active_editor.insert(tk.INSERT, c, "llm_generated_text")
                                _update_generated_text_end_index(active_editor)
                            active_editor.after(0, insert_and_update_buttons)
                        if api_response_chunk.get("done"):
                            final_api_response_status = api_response_chunk
                            break
                    else:
                        final_api_response_status = api_response_chunk
                        error_msg = api_response_chunk["error"]
                        active_editor.after(0, lambda: messagebox.showerror("LLM Generation Error", error_msg))
                        active_editor.after(0, lambda: _update_history_response_and_save(local_user_prompt, f"❌ Error: {error_msg[:100]}..."))
                        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ERROR: LLM Generation Response - Failed: {error_msg}")
                        clear_generated_text_state()
                        return

                if final_api_response_status["success"]:
                    if full_generated_text:
                        active_editor.after(0, lambda: _update_history_response_and_save(local_user_prompt, full_generated_text))
                        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Generation Response - Success. Generated: '{full_generated_text[:200]}...'")
                    else:
                        active_editor.after(0, lambda: _update_history_response_and_save(local_user_prompt, "No text generated."))
                        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Generation Response - No text generated.")
                else:
                    pass

            except Exception as e:
                error_str = str(e)
                active_editor.after(0, lambda: messagebox.showerror("LLM Generation Error", f"An unexpected error occurred: {error_str}"))
                active_editor.after(0, lambda: _update_history_response_and_save(local_user_prompt, f"❌ Exception: {error_str[:100]}..."))
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} CRITICAL ERROR: LLM Generation Exception: {error_str}")
                clear_generated_text_state()
            finally:
                llm_state._is_generating = False
                if llm_state._llm_progress_bar_widget and active_editor:
                    active_editor.after(0, lambda: llm_state._llm_progress_bar_widget.pack_forget())
                    active_editor.after(0, lambda: llm_state._llm_progress_bar_widget.stop())

        def _update_generated_text_end_index(editor):
            if llm_state._generated_text_range:
                start = llm_state._generated_text_range[0]
                end = editor.index(tk.INSERT)
                llm_state._generated_text_range = (start, end)

        llm_state._llm_progress_bar_widget.pack(pady=2)
        llm_state._llm_progress_bar_widget.start(10)
        import threading
        threading.Thread(target=run_generation_thread_target, args=(user_prompt, lines_before, lines_after), daemon=True).start()

    def _handle_history_entry_addition_from_dialog(user_prompt):
        _add_entry_to_history_and_save(user_prompt, "⏳ Generating...")

    llm_dialogs.show_generate_text_dialog(
        root_window=llm_state._root_window,
        theme_setting_getter_func=llm_state._theme_setting_getter_func,
        current_prompt_history_list=llm_state._prompt_history_list,
        on_generate_request_callback=_handle_generation_request_from_dialog,
        on_history_entry_add_callback=_handle_history_entry_addition_from_dialog,
        initial_prompt_text=initial_prompt_text
    )