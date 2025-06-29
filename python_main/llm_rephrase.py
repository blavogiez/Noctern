import llm_state
import llm_dialogs
import llm_utils
import llm_api_client
import tkinter as tk
from tkinter import messagebox
import interface
import datetime

def open_rephrase_dialog():
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not initialized (no editor getter).")
        return
    editor = llm_state._active_editor_getter_func()
    if not editor or not llm_state._root_window or not llm_state._llm_progress_bar_widget or not llm_state._theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized.")
        return

    try:
        selected_text = editor.get(tk.SEL_FIRST, tk.SEL_LAST)
    except tk.TclError:
        messagebox.showwarning("Rephrase", "Please select text to rephrase.")
        return

    def _handle_rephrase_request_from_dialog(user_instruction):
        if llm_state._is_generating:
            interface.show_temporary_status_message("LLM is already generating. Please wait.")
            return

        llm_state._last_llm_action_type = "rephrase"
        prompt = (
            f"Reformule le texte suivant selon l'instruction utilisateur, sans changer le sens, "
            f"et en respectant la langue et le ton d'origine. "
            f"Texte à reformuler :\n\"\"\"{selected_text}\"\"\"\n"
            f"Instruction utilisateur : {user_instruction}\n"
            f"Réponds uniquement avec le texte reformulé, sans explication ni balises."
        )
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Rephrase Request - Prompt: '{prompt[:200]}...'")

        def on_llm_response(rephrased_text):
            editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
            editor.insert(tk.INSERT, rephrased_text)
            editor.focus_set()
            interface.show_temporary_status_message("✅ Texte reformulé.")

        def run_rephrase_thread():
            try:
                full_response = ""
                for api_response_chunk in llm_api_client.request_llm_generation(prompt):
                    if api_response_chunk["success"]:
                        if "chunk" in api_response_chunk:
                            chunk = api_response_chunk["chunk"]
                            full_response += chunk
                        if api_response_chunk.get("done"):
                            editor.after(0, lambda: on_llm_response(full_response))
                            return
                    else:
                        error_msg = api_response_chunk["error"]
                        editor.after(0, lambda: messagebox.showerror("LLM Error", error_msg))
                        return
            except Exception as e:
                editor.after(0, lambda: messagebox.showerror("LLM Error", str(e)))
            finally:
                if llm_state._llm_progress_bar_widget:
                    editor.after(0, llm_state._llm_progress_bar_widget.stop)
                    editor.after(0, llm_state._llm_progress_bar_widget.pack_forget)

        llm_state._llm_progress_bar_widget.pack(pady=2)
        llm_state._llm_progress_bar_widget.start(10)
        import threading
        threading.Thread(target=run_rephrase_thread, daemon=True).start()

    # Fenêtre de prompt utilisateur
    def _show_prompt_dialog():
        prompt_window = tk.Toplevel(llm_state._root_window)
        prompt_window.title("Reformuler la sélection")
        prompt_window.transient(llm_state._root_window)
        prompt_window.grab_set()
        prompt_window.geometry("500x200")
        prompt_window.configure(bg=llm_state._theme_setting_getter_func("root_bg", "#f0f0f0"))

        tk.Label(prompt_window, text="Instruction de reformulation :", bg=prompt_window["bg"]).pack(pady=(10, 5))
        entry = tk.Entry(prompt_window, width=60)
        entry.pack(padx=10, pady=10)
        entry.focus_set()

        def on_validate():
            user_instruction = entry.get().strip()
            if not user_instruction:
                messagebox.showwarning("Instruction manquante", "Veuillez saisir une instruction pour la reformulation.", parent=prompt_window)
                return
            prompt_window.destroy()
            _handle_rephrase_request_from_dialog(user_instruction)

        tk.Button(prompt_window, text="Reformuler", command=on_validate).pack(pady=10)
        prompt_window.bind("<Return>", lambda e: on_validate())
        prompt_window.wait_window()

    _show_prompt_dialog()
