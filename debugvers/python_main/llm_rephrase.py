import llm_state
import llm_utils
import llm_api_client
import tkinter as tk
from tkinter import messagebox
import interface
import llm_interactive
import debug_console

def open_rephrase_dialog():
    """Entry point for rephrasing user-selected text."""
    debug_console.log("Rephrase dialog initiated from selection.", level='ACTION')
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not initialized (no editor getter).")
        return
    editor = llm_state._active_editor_getter_func()
    if not editor:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized (no editor).")
        return

    try:
        start_index = editor.index(tk.SEL_FIRST)
        end_index = editor.index(tk.SEL_LAST)
        selected_text = editor.get(start_index, end_index)
        debug_console.log(f"User selected text to rephrase: '{selected_text[:80]}...'", level='DEBUG')
    except tk.TclError:
        debug_console.log("Rephrase dialog: No text selected.", level='INFO')
        messagebox.showwarning("Rephrase", "Please select text to rephrase.")
        return

    request_rephrase_for_text(editor, selected_text, start_index, end_index, on_validate_callback=None)


def request_rephrase_for_text(editor, text_to_rephrase, start_index, end_index, on_validate_callback=None):
    """
    Prompts the user for an instruction and starts an interactive rephrase session.
    """
    if llm_state._is_generating:
        interface.show_temporary_status_message("LLM is already generating. Please wait.")
        debug_console.log("Rephrase aborted: another generation is in progress.", level='WARNING')
        return

    prompt_validated = False

    def _show_prompt_dialog():
        nonlocal prompt_validated

        def on_validate(entry_widget, window):
            nonlocal prompt_validated
            user_instruction = entry_widget.get().strip()
            if not user_instruction:
                messagebox.showwarning("Instruction manquante", "Veuillez saisir une instruction.", parent=window)
                return
            
            prompt_validated = True
            window.destroy()
            _handle_rephrase_request(user_instruction)

        prompt_window = tk.Toplevel(llm_state._root_window)
        prompt_window.title("Reformuler le texte")
        prompt_window.transient(llm_state._root_window)
        prompt_window.grab_set()
        prompt_window.geometry("500x200")
        prompt_window.configure(bg=llm_state._theme_setting_getter_func("root_bg", "#f0f0f0"))

        tk.Label(prompt_window, text=f"Instruction pour reformuler :\n\"{text_to_rephrase[:80]}...\"", bg=prompt_window["bg"]).pack(pady=(10, 5))
        entry = tk.Entry(prompt_window, width=60)
        entry.pack(padx=10, pady=10, ipady=4)
        entry.focus_set()

        validate_btn = tk.Button(prompt_window, text="Reformuler", command=lambda: on_validate(entry, prompt_window))
        validate_btn.pack(pady=10)
        prompt_window.bind("<Return>", lambda e: on_validate(entry, prompt_window))
        
        prompt_window.wait_window()

    def _handle_rephrase_request(user_instruction):
        """Builds the prompt and starts the generation in a thread."""
        debug_console.log(f"Rephrase request validated with instruction: '{user_instruction}'", level='ACTION')
        
        if on_validate_callback:
            on_validate_callback()
        else:
            editor.delete(start_index, end_index)

        llm_state._last_llm_action_type = "rephrase"
        llm_state._last_generation_user_prompt = user_instruction
        llm_state._last_completion_phrase_start = text_to_rephrase

        prompt = (
            f"Reformule le texte suivant selon l'instruction utilisateur, sans changer le sens, "
            f"et en respectant la langue et le ton d'origine. "
            f"Texte à reformuler :\n\"\"\"{text_to_rephrase}\"\"\"\n"
            f"Instruction utilisateur : {user_instruction}\n"
            f"Réponds uniquement avec le texte reformulé, sans explication ni balises."
        )
        debug_console.log(f"LLM Rephrase Request - Prompt (start): '{prompt[:200]}...'", level='INFO')

        editor.mark_set(tk.INSERT, start_index)
        callbacks = llm_interactive.start_new_interactive_session(editor)

        def run_rephrase_thread():
            try:
                for api_response_chunk in llm_api_client.request_llm_generation(prompt):
                    if api_response_chunk.get("success"):
                        if "chunk" in api_response_chunk:
                            editor.after(0, lambda chunk=api_response_chunk["chunk"]: callbacks['on_chunk'](chunk))
                        if api_response_chunk.get("done"):
                            editor.after(0, callbacks['on_success'])
                            return
                    else:
                        error_msg = api_response_chunk.get("error", "Unknown error")
                        editor.after(0, lambda: callbacks['on_error'](error_msg))
                        return
            except Exception as e:
                error_msg = f"Failed to get streaming rephrase response: {e}"
                debug_console.log(error_msg, level='ERROR')
                editor.after(0, lambda: callbacks['on_error'](error_msg))

        import threading
        threading.Thread(target=run_rephrase_thread, daemon=True).start()

    _show_prompt_dialog()
    
    if not prompt_validated:
        debug_console.log("Rephrase operation was cancelled by the user.", level='INFO')