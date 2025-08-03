"""
This module provides the core functionality for the "Smart Style" feature.
It orchestrates the user interaction (dialog) and the subsequent call to the
LLM API for text styling.
"""
import threading
import tkinter as tk
from tkinter import messagebox

from llm import state as llm_state
from llm import utils as llm_utils
from llm import api_client as llm_api_client
from llm.interactive import start_new_interactive_session
from llm.dialogs.autostyle import StyleIntensityDialog
from utils import debug_console

def autostyle_selection():
    """
    Main entry point for the autostyle feature.
    
    It retrieves the active editor, prompts the user for styling intensity
    via a dialog, and then initiates the LLM styling request.
    """
    # 1. Get active editor securely
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

    # 4. Initiate the styling request
    _request_llm_for_styling(editor, selected_text, selection_indices, intensity)

def _request_llm_for_styling(editor, selected_text, selection_indices, intensity):
    """
    Private function to handle the LLM request logic.
    
    - Checks if another generation is in progress.
    - Formats the prompt.
    - Starts the interactive session.
    - Runs the API call in a background thread.
    """
    if llm_state._is_generating:
        messagebox.showinfo("LLM Busy", "LLM is currently generating. Please wait.")
        return

    prompt_template = llm_state._styling_prompt_template or llm_state._global_default_prompts.get("styling", "")
    if not prompt_template:
        messagebox.showerror("LLM Error", "Styling prompt template is not configured.")
        return
        
    full_prompt = prompt_template.format(text=selected_text, intensity=f"{intensity}/10")
    
    debug_console.log(f"LLM Styling Request - Intensity: {intensity}/10", level='INFO')

    interactive_session_callbacks = start_new_interactive_session(
        editor,
        is_styling=True,
        selection_indices=selection_indices
    )

    def styling_thread_target():
        """Target for the background thread to avoid blocking the UI."""
        accumulated_text = ""
        try:
            for response in llm_api_client.request_llm_generation(full_prompt, model_name=llm_state.model_style):
                if llm_state._is_generation_cancelled:
                    break
                if response.get("success"):
                    chunk = response.get("chunk")
                    if chunk:
                        accumulated_text += chunk
                        editor.after(0, interactive_session_callbacks['on_chunk'], chunk)
                    
                    if response.get("done") and not llm_state._is_generation_cancelled:
                        final_text = accumulated_text
                        if "deepseek" in llm_state.model_style:
                            final_text = llm_utils.strip_think_tags(final_text)
                        editor.after(0, interactive_session_callbacks['on_success'], final_text)
                        return
                else:
                    error_msg = response.get("error", "Unknown error")
                    if not llm_state._is_generation_cancelled:
                        editor.after(0, interactive_session_callbacks['on_error'], error_msg)
                    return
        except Exception as e:
            error_msg = f"An unexpected error occurred in the styling thread: {e}"
            debug_console.log(error_msg, level='ERROR')
            if not llm_state._is_generation_cancelled:
                editor.after(0, interactive_session_callbacks['on_error'], error_msg)
        finally:
            progress_bar = llm_state._llm_progress_bar_widget
            if progress_bar:
                editor.after(0, progress_bar.stop)
                editor.after(0, progress_bar.pack_forget)

    progress_bar = llm_state._llm_progress_bar_widget
    if progress_bar:
        progress_bar.pack(pady=2)
        progress_bar.start(10)
    
    threading.Thread(target=styling_thread_target, daemon=True).start()