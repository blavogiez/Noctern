"""
This module provides the functionality for automatic LaTeX styling of selected text
using a Large Language Model (LLM) in an interactive, streaming manner.
"""
import threading
import ttkbootstrap as ttk
from tkinter import simpledialog
from llm import state as llm_state
from llm import utils as llm_utils
from llm import api_client as llm_api_client
from llm.interactive import start_new_interactive_session
from utils import debug_console

class StyleIntensityDialog(simpledialog.Dialog):
    """A dialog to ask the user for the styling intensity."""
    def __init__(self, parent, title=None):
        self.intensity = "Medium"
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Choose the desired styling intensity:").pack(pady=5)
        self.combo = ttk.Combobox(master, values=["Low", "Medium", "High"], state="readonly")
        self.combo.set(self.intensity)
        self.combo.pack(pady=5, padx=10)
        return self.combo

    def apply(self):
        self.intensity = self.combo.get()

def get_style_intensity(parent):
    dialog = StyleIntensityDialog(parent, title="Smart Styling")
    return dialog.intensity

def request_llm_for_styling(editor, selected_text, selection_indices, intensity):
    """
    Initiates an interactive LLM request to style the selected text.
    """
    prompt_template = llm_state._styling_prompt_template or llm_state._global_default_prompts.get("styling", "")
    full_prompt = prompt_template.format(text=selected_text, intensity=intensity)
    
    debug_console.log(f"LLM Styling Request - Prompt (first 100 chars): '{full_prompt[:100]}...'", level='INFO')

    interactive_session_callbacks = start_new_interactive_session(
        editor,
        is_styling=True,
        selection_indices=selection_indices
    )

    def run_styling_thread():
        accumulated_text = ""
        try:
            for api_response_chunk in llm_api_client.request_llm_generation(full_prompt, model_name=llm_state.model_style):
                if llm_state._is_generation_cancelled:
                    break
                if api_response_chunk["success"]:
                    if "chunk" in api_response_chunk:
                        chunk_text = api_response_chunk["chunk"]
                        accumulated_text += chunk_text
                        editor.after(0, lambda c=chunk_text: interactive_session_callbacks['on_chunk'](c))
                    
                    if api_response_chunk.get("done"):
                        if not llm_state._is_generation_cancelled:
                            final_text = accumulated_text
                            if "deepseek" in llm_state.model_style:
                                final_text = llm_utils.strip_think_tags(final_text)
                            editor.after(0, interactive_session_callbacks['on_success'], final_text)
                        return
                else:
                    error_message = api_response_chunk["error"]
                    if not llm_state._is_generation_cancelled:
                        editor.after(0, lambda e=error_message: interactive_session_callbacks['on_error'](e))
                    return
        except Exception as e:
            error_message = f"An unexpected error occurred in the LLM styling thread: {e}"
            debug_console.log(error_message, level='ERROR')
            if not llm_state._is_generation_cancelled:
                editor.after(0, lambda e_msg=error_message: interactive_session_callbacks['on_error'](e_msg))
        finally:
            if llm_state._llm_progress_bar_widget:
                editor.after(0, llm_state._llm_progress_bar_widget.stop)
                editor.after(0, llm_state._llm_progress_bar_widget.pack_forget)

    if llm_state._llm_progress_bar_widget:
        llm_state._llm_progress_bar_widget.pack(pady=2)
        llm_state._llm_progress_bar_widget.start(10)
    
    threading.Thread(target=run_styling_thread, daemon=True).start()
