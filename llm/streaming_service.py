"""
This module provides a generic, centralized service for handling streaming
requests to the Large Language Model (LLM).

It encapsulates the boilerplate logic for threading, progress bar management,
API call iteration, and error handling, allowing feature-specific modules
to be cleaner and more focused on their core logic.
"""
import threading
from llm import state as llm_state
from llm import api_client as llm_api_client
from llm import utils as llm_utils
from utils import debug_console

def start_streaming_request(editor, prompt, model_name, on_chunk, on_success, on_error):
    """
    Starts a generic LLM streaming request in a background thread.

    Args:
        editor: The editor widget, used for scheduling UI updates with `after()`.
        prompt (str): The fully formatted prompt to send to the LLM.
        model_name (str): The name of the LLM model to use.
        on_chunk (callable): Callback function executed for each received text chunk.
                             Receives the chunk text as an argument.
        on_success (callable): Callback function executed when the stream completes successfully.
                               Receives the final, accumulated text as an argument.
        on_error (callable): Callback function executed if an error occurs.
                             Receives the error message as an argument.
    """
    progress_bar = llm_state._llm_progress_bar_widget
    
    def stream_thread_target():
        """Target function for the background thread."""
        accumulated_text = ""
        try:
            for response in llm_api_client.request_llm_generation(prompt, model_name=model_name):
                if llm_state._is_generation_cancelled:
                    break
                
                if response.get("success"):
                    chunk = response.get("chunk")
                    if chunk:
                        accumulated_text += chunk
                        editor.after(0, on_chunk, chunk)
                    
                    if response.get("done") and not llm_state._is_generation_cancelled:
                        final_text = accumulated_text
                        # Handle model-specific stripping, e.g., for deepseek
                        if "deepseek" in model_name:
                            final_text = llm_utils.strip_think_tags(final_text)
                        editor.after(0, on_success, final_text)
                        return
                else:
                    error_msg = response.get("error", "Unknown error during streaming.")
                    if not llm_state._is_generation_cancelled:
                        editor.after(0, on_error, error_msg)
                    return
        except Exception as e:
            error_msg = f"An unexpected error occurred in the streaming thread: {e}"
            debug_console.log(error_msg, level='ERROR')
            if not llm_state._is_generation_cancelled:
                editor.after(0, on_error, error_msg)
        finally:
            if progress_bar:
                editor.after(0, progress_bar.stop)
                editor.after(0, progress_bar.pack_forget)

    if progress_bar:
        progress_bar.pack(pady=2)
        progress_bar.start(10)
    
    threading.Thread(target=stream_thread_target, daemon=True).start()
