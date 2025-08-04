"""
This module provides the core functionality for the "Smart Style" feature.
It orchestrates the user interaction (dialog) and then uses the generic
streaming service to apply text styling.
"""
import tkinter as tk
from tkinter import messagebox

from llm import state as llm_state
from llm.interactive import start_new_interactive_session
from llm.dialogs.autostyle import StyleIntensityDialog
from llm.streaming_service import start_streaming_request
from utils import debug_console

def autostyle_selection():
    """
    Main entry point for the autostyle feature.
    
    Retrieves the active editor, prompts for intensity, and initiates styling.
    """
    # 1. Get active editor
    if not llm_state._active_editor_getter_func:
        messagebox.showerror("LLM Error", "LLM service not fully initialized.")
        return
    editor = llm_state._active_editor_getter_func()
    if not editor:
        messagebox.showerror("LLM Error", "No active editor found.")
        return

    # 2. Get selected text
    try:
        selection_indices = editor.tag_ranges("sel")
        if not selection_indices:
            messagebox.showinfo("Smart Style", "Please select some text to style.")
            return
        selected_text = editor.get(selection_indices[0], selection_indices[1])
        if not selected_text.strip():
            messagebox.showinfo("Smart Style", "The selected text is empty.")
            return
    except tk.TclError:
        messagebox.showinfo("Smart Style", "Please select some text to style.")
        return

    # 3. Open dialog to get intensity
    dialog = StyleIntensityDialog(editor, title="Smart Styling")
    intensity = dialog.result

    if intensity is None:
        debug_console.log("Smart Styling cancelled by user.", level='INFO')
        return

    # 4. Check for ongoing generation and prepare prompt
    if llm_state.is_generating():
        messagebox.showinfo("LLM Busy", "LLM is currently generating. Please wait.")
        return

    prompt_template = llm_state.get_styling_prompt()
    if not prompt_template:
        messagebox.showerror("LLM Error", "Styling prompt template is not configured. Please check the global or document-specific prompt settings.")
        return
        
    full_prompt = prompt_template.format(text=selected_text, intensity=f"{intensity}/10")
    debug_console.log(f"LLM Styling Request - Intensity: {intensity}/10", level='INFO')

    # 5. Start interactive session and define callbacks
    session_callbacks = start_new_interactive_session(
        editor,
        is_styling=True,
        selection_indices=selection_indices
    )

    # 6. Call the generic streaming service
    start_streaming_request(
        editor=editor,
        prompt=full_prompt,
        model_name=llm_state.model_style,
        on_chunk=session_callbacks['on_chunk'],
        on_success=session_callbacks['on_success'],
        on_error=session_callbacks['on_error']
    )
