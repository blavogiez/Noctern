# llm_completion.py

import llm_state
import llm_utils
import llm_api_client
import tkinter as tk
from tkinter import messagebox
import interface
import debug_console
from llm_interactive import start_new_interactive_session

def request_llm_to_complete_text():
    """Initiates a text completion request based on the text before the cursor."""
    debug_console.log("LLM Completion request initiated.", level='ACTION')
    
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not initialized (no editor getter).")
        debug_console.log("LLM Completion failed: no editor getter.", level='ERROR')
        return
        
    editor = llm_state._active_editor_getter_func()
    if not editor or not llm_state._root_window or not llm_state._llm_progress_bar_widget or not llm_state._theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized.")
        debug_console.log("LLM Completion failed: service not fully initialized.", level='ERROR')
        return
        
    if not (llm_state._completion_prompt_template or (llm_state._global_default_prompts and llm_state._global_default_prompts.get("completion"))):
        messagebox.showerror("LLM Service Error", "LLM prompt templates are not initialized. Please reload your file or restart the application.")
        debug_console.log("LLM Completion failed: prompt templates not initialized.", level='ERROR')
        return
        
    if llm_state._is_generating:
        interface.show_temporary_status_message("LLM is already generating. Please wait.")
        debug_console.log("LLM Completion aborted: another generation is in progress.", level='WARNING')
        return

    context = llm_utils.extract_editor_context(editor, lines_before_cursor=30, lines_after_cursor=0)
    last_dot_index = max(context.rfind("."), context.rfind("!"), context.rfind("?"))
    current_phrase_start = context[last_dot_index + 1:].strip() if last_dot_index != -1 else context.strip()
    previous_context = context[:last_dot_index + 1].strip() if last_dot_index != -1 else ""

    llm_state._last_llm_action_type = "completion"
    llm_state._last_completion_phrase_start = current_phrase_start

    prompt_template = llm_state._completion_prompt_template or llm_state._global_default_prompts.get("completion", "")
    full_llm_prompt = prompt_template.format(previous_context=previous_context, current_phrase_start=current_phrase_start, keywords=', '.join(llm_state._llm_keywords_list))
    debug_console.log(f"LLM Completion Request - Prompt (start): '{full_llm_prompt[:200]}...'", level='INFO')

    callbacks = start_new_interactive_session(editor, is_completion=True, completion_phrase=current_phrase_start)

    def run_completion_thread_target():
        try:
            for api_response_chunk in llm_api_client.request_llm_generation(full_llm_prompt):
                if api_response_chunk["success"]:
                    if "chunk" in api_response_chunk:
                        editor.after(0, lambda c=api_response_chunk["chunk"]: callbacks['on_chunk'](c))
                    if api_response_chunk.get("done"):
                        editor.after(0, callbacks['on_success'])
                        return
                else:
                    error_msg = api_response_chunk["error"]
                    editor.after(0, lambda e=error_msg: callbacks['on_error'](e))
                    return
        except Exception as e:
            error_msg = f"An unexpected error occurred in completion thread: {e}"
            debug_console.log(error_msg, level='ERROR')
            editor.after(0, lambda e_msg=error_msg: callbacks['on_error'](e_msg))
        finally:
            if llm_state._llm_progress_bar_widget:
                editor.after(0, llm_state._llm_progress_bar_widget.stop)
                editor.after(0, llm_state._llm_progress_bar_widget.pack_forget)
    
    llm_state._llm_progress_bar_widget.pack(pady=2)
    llm_state._llm_progress_bar_widget.start(10)
    import threading
    threading.Thread(target=run_completion_thread_target, daemon=True).start()