"""
This module provides a generic, centralized service for handling streaming
requests to the Large Language Model (LLM).

It encapsulates the boilerplate logic for threading and API call iteration,
allowing feature-specific modules to be cleaner. The global state management
(`_is_generating` flag) is handled by the calling context (e.g., the interactive session).
"""
import threading
from llm import state as llm_state
from llm import api_client as llm_api_client
from llm import utils as llm_utils
from utils import debug_console

def start_streaming_request(editor, prompt, model_name, on_chunk, on_success, on_error, task_type="general"):
    """
    Starts a high-performance, non-blocking LLM streaming request with optimized profiles.
    
    Args:
        task_type: "completion", "generation", "rephrase", "debug", or "general"
    """
    progress_bar = llm_state._llm_progress_bar_widget
    
    def stream_thread_target():
        """
        Target function for the high-performance background thread.
        Uses optimized generation profiles for better performance.
        """
        try:
            # Use optimized API client with task-specific performance profiles
            for response in llm_api_client.request_llm_generation_optimized(prompt, model_name=model_name, task_type=task_type):
                # Perform additional cancellation check for safety
                if llm_state._is_generation_cancelled:
                    break
                
                if response.get("success"):
                    chunk = response.get("chunk")
                    if chunk:
                        editor.after(0, on_chunk, chunk)
                    
                    if response.get("done"):
                        final_text = response.get("data", "")
                        if "deepseek" in model_name:
                            final_text = llm_utils.strip_think_tags(final_text)
                        
                        # Check for cancellation one last time before calling success
                        if not llm_state._is_generation_cancelled:
                            editor.after(0, on_success, final_text)
                        return
                else:
                    # Check for cancellation before showing an error
                    if not llm_state._is_generation_cancelled:
                        editor.after(0, on_error, response.get("error", "Unknown error"))
                    return
        except Exception as e:
            error_msg = f"An unexpected error occurred in the streaming thread: {e}"
            debug_console.log(error_msg, level='ERROR')
            if not llm_state._is_generation_cancelled:
                editor.after(0, on_error, error_msg)
        # NO finally block here to manage global state.
        # Calling context manages global state

    if progress_bar:
        progress_bar.pack(pady=2)
        progress_bar.start(10)
    
    # Start high-performance thread
    debug_console.log(f"Starting high-performance LLM streaming thread (profile: {task_type})", level='INFO')
    threading.Thread(target=stream_thread_target, daemon=True).start()
