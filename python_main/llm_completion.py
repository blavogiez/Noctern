import llm_state
import llm_utils
import llm_api_client
import tkinter as tk
from tkinter import messagebox
import interface
import datetime
from llm_interactive import clear_generated_text_state, show_llm_buttons


def request_llm_to_complete_text():
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not initialized (no editor getter).")
        return

    editor = llm_state._active_editor_getter_func()
    if not editor or not llm_state._root_window or not llm_state._llm_progress_bar_widget or not llm_state._theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized.")
        return

    if not (llm_state._completion_prompt_template or (llm_state._global_default_prompts and llm_state._global_default_prompts.get("completion"))):
        messagebox.showerror("LLM Service Error", "LLM prompt templates are not initialized. Please reload your file or restart the application.")
        return

    if llm_state._is_generating:
        interface.show_temporary_status_message("LLM is already generating. Please wait or interact with current generation.")
        return

    clear_generated_text_state()
    llm_state._is_generating = True
    llm_state._last_llm_action_type = "completion"

    def run_completion_thread_target():
        active_editor = llm_state._active_editor_getter_func()
        if not active_editor:
            clear_generated_text_state()
            return

        try:
            start_index = active_editor.index(tk.INSERT)
            llm_state._generated_text_range = (start_index, start_index)
            # Show buttons above the generated text
            active_editor.after(0, lambda: show_llm_buttons(active_editor, start_index))

            context = llm_utils.extract_editor_context(active_editor, lines_before_cursor=30, lines_after_cursor=0)
            last_dot_index = max(context.rfind("."), context.rfind("!"), context.rfind("?"))
            if last_dot_index == -1:
                current_phrase_start = context.strip()
                previous_context = ""
            else:
                current_phrase_start = context[last_dot_index + 1:].strip()
                previous_context = context[:last_dot_index + 1].strip()

            llm_state._last_completion_phrase_start = current_phrase_start

            prompt_template = llm_state._completion_prompt_template or llm_state._global_default_prompts.get("completion", "")
            full_llm_prompt = prompt_template.format(
                previous_context=previous_context,
                current_phrase_start=current_phrase_start,
                keywords=', '.join(llm_state._llm_keywords_list)
            )

            import datetime
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Completion Request - Prompt: '{full_llm_prompt[:200]}...'")

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
                    active_editor.after(0, lambda: messagebox.showerror("LLM Completion Error", error_msg))
                    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ERROR: LLM Completion Response - Failed: {final_api_response_status['error']}")
                    clear_generated_text_state()
                    return

            if final_api_response_status["success"]:
                completion_raw = full_generated_text.strip('"')
                cleaned_completion = llm_utils.remove_prefix_overlap_from_completion(current_phrase_start, completion_raw)

                def _replace_with_cleaned_text(start_idx, end_idx, cleaned_text):
                    editor = llm_state._active_editor_getter_func()
                    if editor and editor.winfo_exists():
                        editor.delete(start_idx, end_idx)
                        editor.insert(start_idx, cleaned_text, "llm_generated_text")
                        llm_state._generated_text_range = (start_idx, editor.index(f"{start_idx} + {len(cleaned_text)} chars"))

                if llm_state._generated_text_range:
                    active_editor.after(0, lambda: _replace_with_cleaned_text(
                        llm_state._generated_text_range[0], llm_state._generated_text_range[1], cleaned_completion
                    ))
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Completion Response - Success. Generated: '{cleaned_completion[:200]}...'")
            else:
                if not full_generated_text:
                    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ERROR: LLM Completion Response - No text generated due to error: {final_api_response_status.get('error', 'Unknown error')}")

        except Exception as e:
            active_editor.after(0, lambda: messagebox.showerror("LLM Completion Error", f"An unexpected error occurred: {str(e)}"))
            import datetime
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} CRITICAL ERROR: LLM Completion Exception: {str(e)}")
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
    threading.Thread(target=run_completion_thread_target, daemon=True).start()