"""
This module provides functionality for rephrasing selected text using a Large Language Model (LLM).
It orchestrates the UI dialog, prompt construction, and the interactive session for rephrasing.
"""

import tkinter as tk
from tkinter import messagebox
import threading
from llm import state as llm_state
from llm import api_client as llm_api_client
from llm import interactive as llm_interactive
from llm.dialogs.rephrase import show_rephrase_dialog
from utils import debug_console

def open_rephrase_dialog():
    """
    Entry point for the rephrase feature.
    Gets the selected text from the active editor and opens the rephrase dialog.
    """
    debug_console.log("Rephrase dialog initiated.", level='ACTION')
    
    editor_widget = llm_state._active_editor_getter_func()
    if not editor_widget:
        messagebox.showerror("LLM Error", "No active editor found.")
        return

    try:
        start_index = editor_widget.index(tk.SEL_FIRST)
        end_index = editor_widget.index(tk.SEL_LAST)
        selected_text = editor_widget.get(start_index, end_index)
    except tk.TclError:
        selected_text = ""

    if not selected_text.strip():
        messagebox.showwarning("Rephrase", "The selected text is empty.")
        return

    def on_confirm(instruction):
        """Callback for when the user confirms the rephrase instruction."""
        # Define the callback that will restore the original text if the user discards the LLM generation
        def on_discard_generation():
            debug_console.log("Rephrase session discarded. Restoring original text.", level='INFO')
            if editor_widget.winfo_exists():
                editor_widget.insert(start_index, selected_text)
        
        request_rephrase_for_text(editor_widget, selected_text, start_index, end_index, instruction, on_discard_generation)

    show_rephrase_dialog(
        root_window=llm_state._root_window,
        theme_setting_getter_func=llm_state._theme_setting_getter_func,
        original_text=selected_text,
        on_rephrase_callback=on_confirm,
        on_cancel_callback=lambda: debug_console.log("Rephrase cancelled by user from dialog.", level='INFO')
    )

def request_rephrase_for_text(editor, original_text, start_index, end_index, instruction, on_discard_callback=None):
    """
    Handles the core logic of the rephrasing request.
    """
    if llm_state._is_generating:
        messagebox.showinfo("LLM Busy", "LLM is currently generating. Please wait.")
        return

    debug_console.log(f"Requesting rephrase with instruction: '{instruction}'", level='INFO')

    # Delete the original text to make way for the interactive session
    editor.delete(start_index, end_index)
    editor.mark_set(tk.INSERT, start_index)

    prompt_template = llm_state._global_default_prompts.get("rephrase")
    if not prompt_template:
        messagebox.showerror("LLM Error", "The 'rephrase' prompt template is missing.")
        debug_console.log("Rephrase failed: 'rephrase' template not found.", level='ERROR')
        editor.insert(start_index, original_text) # Restore original text
        return
    
    try:
        rephrase_prompt = prompt_template.format(text=original_text, instruction=instruction)
    except KeyError as e:
        messagebox.showerror("Prompt Error", f"The rephrase prompt is missing a placeholder: {e}")
        editor.insert(start_index, original_text) # Restore original text
        return

    # Start the interactive session, passing the specific callback for this rephrase operation
    session_callbacks = llm_interactive.start_new_interactive_session(
        editor, 
        is_rephrase=True,
        on_discard_callback=on_discard_callback
    )

    def rephrase_thread_target():
        """The target function for the LLM generation thread."""
        accumulated_text = ""
        try:
            for chunk in llm_api_client.request_llm_generation(rephrase_prompt):
                if llm_state._is_generation_cancelled:
                    break
                if chunk.get("success"):
                    if "chunk" in chunk:
                        chunk_text = chunk["chunk"]
                        accumulated_text += chunk_text
                        editor.after(0, session_callbacks['on_chunk'], chunk_text)
                    if chunk.get("done"):
                        editor.after(0, session_callbacks['on_success'], accumulated_text)
                        return
                else:
                    editor.after(0, session_callbacks['on_error'], chunk.get("error", "Unknown error."))
                    return
        except Exception as e:
            error_msg = f"An unexpected error occurred in the rephrase thread: {e}"
            debug_console.log(error_msg, level='ERROR')
            if editor.winfo_exists():
                editor.after(0, session_callbacks['on_error'], error_msg)

    threading.Thread(target=rephrase_thread_target, daemon=True).start()