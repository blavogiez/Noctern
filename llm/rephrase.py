"""
This module provides functionality for rephrasing selected text using a Large Language Model (LLM).
It orchestrates the UI dialog, prompt construction, and then uses the generic
streaming service to perform the rephrasing.
"""
import tkinter as tk
from tkinter import messagebox

from llm import state as llm_state
from llm import interactive as llm_interactive
from llm.dialogs.rephrase import show_rephrase_dialog
from llm.streaming_service import start_streaming_request
from utils import debug_console

def open_rephrase_dialog(initial_text=None):
    """
    Entry point for the rephrase feature.
    
    If `initial_text` is provided, it's used for rephrasing. Otherwise,
    it gets the selected text from the active editor.
    """
    debug_console.log("Rephrase dialog initiated.", level='ACTION')
    
    if not llm_state._active_editor_getter_func:
        messagebox.showerror("LLM Error", "LLM service not fully initialized.")
        return
    editor = llm_state._active_editor_getter_func()
    if not editor:
        messagebox.showerror("LLM Error", "No active editor found.")
        return

    start_index = None
    end_index = None
    
    if initial_text:
        selected_text = initial_text
    else:
        try:
            start_index = editor.index(tk.SEL_FIRST)
            end_index = editor.index(tk.SEL_LAST)
            selected_text = editor.get(start_index, end_index)
        except tk.TclError:
            selected_text = ""

    if not selected_text.strip():
        messagebox.showwarning("Rephrase", "There is no text to rephrase.")
        return

    def on_confirm(instruction):
        """Callback for when the user confirms the rephrase instruction."""
        def on_discard_generation():
            debug_console.log("Rephrase session discarded. Restoring original text.", level='INFO')
            if editor.winfo_exists():
                editor.insert(start_index, selected_text)
        
        _request_rephrase_for_text(editor, selected_text, start_index, end_index, instruction, on_discard_generation)

    show_rephrase_dialog(
        root_window=llm_state._root_window,
        theme_setting_getter_func=llm_state._theme_setting_getter_func,
        original_text=selected_text,
        on_rephrase_callback=on_confirm,
        on_cancel_callback=lambda: debug_console.log("Rephrase cancelled by user from dialog.", level='INFO')
    )

def _request_rephrase_for_text(editor, original_text, start_index, end_index, instruction, on_discard_callback=None):
    """
    Handles the core logic of the rephrasing request by calling the streaming service.
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

    # Start the interactive session to get the callbacks
    session_callbacks = llm_interactive.start_new_interactive_session(
        editor, 
        is_rephrase=True,
        on_discard_callback=on_discard_callback
    )

    # Call the generic streaming service
    start_streaming_request(
        editor=editor,
        prompt=rephrase_prompt,
        model_name=llm_state.model_rephrase,
        on_chunk=session_callbacks['on_chunk'],
        on_success=session_callbacks['on_success'],
        on_error=session_callbacks['on_error']
    )
