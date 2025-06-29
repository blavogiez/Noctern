import llm_state
import llm_utils
import llm_api_client
import tkinter as tk
from tkinter import messagebox
import interface
import datetime
# On importe le module interactif pour pouvoir l'utiliser
import llm_interactive

def open_rephrase_dialog():
    """Point d'entrée pour reformuler le texte sélectionné par l'utilisateur."""
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not initialized (no editor getter).")
        return
    editor = llm_state._active_editor_getter_func()
    if not editor:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized (no editor).")
        return

    try:
        start_index = editor.index(tk.SEL_FIRST)
        selected_text = editor.get(start_index, tk.SEL_LAST)
        # On supprime le texte sélectionné pour le remplacer par la session interactive
        editor.delete(start_index, tk.SEL_LAST)
        editor.mark_set(tk.INSERT, start_index)
    except tk.TclError:
        messagebox.showwarning("Rephrase", "Please select text to rephrase.")
        return

    # On appelle la nouvelle fonction logique avec le texte récupéré
    request_rephrase_for_text(editor, selected_text, start_index)


def request_rephrase_for_text(editor, text_to_rephrase, start_index):
    """
    Demande à l'utilisateur une instruction et lance une session interactive
    pour reformuler le texte fourni. C'est le nouveau cœur logique.
    """
    if llm_state._is_generating:
        interface.show_temporary_status_message("LLM is already generating. Please wait.")
        return

    def _show_prompt_dialog():
        """Affiche la fenêtre modale pour obtenir l'instruction de l'utilisateur."""
        # --- Utilisation d'une fonction interne pour éviter la pollution de l'espace de noms ---
        def on_validate(entry_widget, window):
            user_instruction = entry_widget.get().strip()
            if not user_instruction:
                messagebox.showwarning("Instruction manquante", "Veuillez saisir une instruction.", parent=window)
                return
            window.destroy()
            # On lance la requête LLM après avoir eu l'instruction
            _handle_rephrase_request(user_instruction)

        # La logique de la fenêtre reste la même
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
        
        # Centrer la fenêtre
        prompt_window.update_idletasks()
        x = llm_state._root_window.winfo_x() + (llm_state._root_window.winfo_width() // 2) - (prompt_window.winfo_width() // 2)
        y = llm_state._root_window.winfo_y() + (llm_state._root_window.winfo_height() // 2) - (prompt_window.winfo_height() // 2)
        prompt_window.geometry(f"+{x}+{y}")
        
        prompt_window.wait_window()

    def _handle_rephrase_request(user_instruction):
        """Construit le prompt et lance la génération via un thread."""
        llm_state._last_llm_action_type = "rephrase"
        # On stocke l'instruction et le texte pour d'éventuelles futures reformulations
        llm_state._last_generation_user_prompt = user_instruction
        llm_state._last_completion_phrase_start = text_to_rephrase # Réutilisation créative du state

        prompt = (
            f"Reformule le texte suivant selon l'instruction utilisateur, sans changer le sens, "
            f"et en respectant la langue et le ton d'origine. "
            f"Texte à reformuler :\n\"\"\"{text_to_rephrase}\"\"\"\n"
            f"Instruction utilisateur : {user_instruction}\n"
            f"Réponds uniquement avec le texte reformulé, sans explication ni balises."
        )
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Rephrase Request - Instruction: '{user_instruction}'")

        # --- INTÉGRATION CLÉ : On lance une session interactive ---
        # On s'assure que le curseur est au bon endroit avant de créer la session
        editor.mark_set(tk.INSERT, start_index)
        callbacks = llm_interactive.start_new_interactive_session(editor)

        def run_rephrase_thread():
            try:
                # --- CORRECTION ICI ---
                # On utilise la fonction qui existe vraiment : request_llm_generation
                # Elle gère déjà le streaming. J'ai aussi retiré l'argument "rephrase" qui était incorrect.
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
                error_msg = f"Failed to get streaming response: {e}"
                editor.after(0, lambda: callbacks['on_error'](error_msg))

        import threading
        threading.Thread(target=run_rephrase_thread, daemon=True).start()

    # Démarre le processus en affichant la boîte de dialogue
    _show_prompt_dialog()