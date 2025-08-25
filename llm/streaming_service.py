"""
Handle LLM streaming requests in background threads.
Provide non-blocking text generation with progress feedback.
"""
import threading
from llm import state as llm_state
from llm import api_client
from llm import utils as llm_utils
from utils import logs_console

def start_streaming_request(editor, prompt, model_name, on_chunk, on_success, on_error, task_type="general", json_schema=None):
    """
    Start LLM streaming request in background thread.
    
    Args:
        editor: Text editor widget for UI updates
        prompt: Text prompt to send to LLM
        model_name: Model identifier for generation
        on_chunk: Callback for each text chunk received
        on_success: Callback when generation completes
        on_error: Callback when generation fails
        task_type: Type of task for optimization settings
        json_schema: Optional JSON schema for structured output
    """
    progress_bar = llm_state._llm_progress_bar_widget
    
    def stream_worker():
        """Background worker for LLM streaming."""
        try:
            # Choose appropriate generation function
            if json_schema:
                logs_console.log("Using structured output generation", level='INFO')
                generator = api_client.generate_with_structured_output(
                    prompt, json_schema, model_name=model_name, 
                    stream=True, task_type=task_type
                )
            else:
                generator = api_client.generate_with_task_profile(
                    prompt, model_name=model_name, stream=True, task_type=task_type
                )
            
            for response in generator:
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
                        
                        # Check cancellation before calling success callback
                        if not llm_state._is_generation_cancelled:
                            editor.after(0, on_success, final_text)
                        return
                else:
                    # Handle error if not cancelled
                    if not llm_state._is_generation_cancelled:
                        editor.after(0, on_error, response.get("error", "Unknown error"))
                    return
        except Exception as e:
            error_msg = f"Streaming error: {e}"
            logs_console.log(error_msg, level='ERROR')
            if not llm_state._is_generation_cancelled:
                editor.after(0, on_error, error_msg)

    # Show progress indicator
    if progress_bar:
        progress_bar.pack(pady=2)
        progress_bar.start(10)
    
    # Start background thread
    logs_console.log(f"Starting LLM streaming (task: {task_type}, structured: {json_schema is not None})", level='INFO')
    threading.Thread(target=stream_worker, daemon=True).start()