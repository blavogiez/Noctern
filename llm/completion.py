"""
This module handles the logic for requesting text completion from a Large Language Model (LLM).
It extracts context from the editor, constructs a prompt, and manages the streaming
response from the LLM, integrating the generated text back into the editor.
"""

from llm import state as llm_state
from llm import utils as llm_utils
from llm import api_client as llm_api_client
from llm import keyword_history # Import the keyword history module
import tkinter as tk
from tkinter import messagebox
from utils import debug_console
from llm.interactive import start_new_interactive_session
import threading

def request_llm_to_complete_text():
    """
    Initiates a text completion request to the LLM based on the content before the cursor.

    This function prepares the necessary context and prompt, starts an interactive session
    to display the streaming LLM output, and handles potential errors or busy states.
    """
    debug_console.log("LLM Text Completion request initiated.", level='ACTION')
    
    # Validate that essential LLM service components are initialized.
    if not callable(llm_state._active_editor_getter_func) or not callable(llm_state._active_filepath_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized: Active editor or filepath getter is missing.")
        debug_console.log("LLM Completion failed: Active editor or filepath getter function is not callable.", level='ERROR')
        return
        
    editor_widget = llm_state._active_editor_getter_func()
    active_file_path = llm_state._active_filepath_getter_func()

    if not editor_widget or not llm_state._root_window or not llm_state._llm_progress_bar_widget or not llm_state._theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized: Missing core UI components.")
        debug_console.log("LLM Completion failed: One or more core UI components are missing.", level='ERROR')
        return
        
    # Check if prompt templates are available.
    if not (llm_state._completion_prompt_template or (llm_state._global_default_prompts and llm_state._global_default_prompts.get("completion"))):
        messagebox.showerror("LLM Service Error", "LLM prompt templates for completion are not initialized. Please reload your file or restart the application.")
        debug_console.log("LLM Completion failed: Prompt templates are not initialized.", level='ERROR')
        return
        
    # Prevent multiple LLM generations from running concurrently.
    if llm_state._is_generating:
        interface.show_temporary_status_message("LLM is currently generating. Please wait for the current operation to complete.")
        debug_console.log("LLM Completion aborted: Another generation process is already in progress.", level='WARNING')
        return

    # Extract relevant text context from the editor for the LLM prompt.
    # We take 30 lines before the cursor and 0 lines after for completion context.
    editor_context = llm_utils.extract_editor_context(editor_widget, lines_before_cursor=30, lines_after_cursor=0)
    
    # Identify the start of the current phrase by looking for the last sentence-ending punctuation.
    last_punctuation_index = max(editor_context.rfind("."), editor_context.rfind("!"), editor_context.rfind("?"))
    
    # Extract the current phrase (text after the last punctuation) and the preceding context.
    current_phrase_start = editor_context[last_punctuation_index + 1:].strip() if last_punctuation_index != -1 else editor_context.strip()
    previous_context = editor_context[:last_punctuation_index + 1].strip() if last_punctuation_index != -1 else ""

    # Store state for potential re-generation or history tracking.
    llm_state._last_llm_action_type = "completion"
    llm_state._last_completion_phrase_start = current_phrase_start

    # Select the appropriate prompt template (user-defined or global default).
    prompt_template = llm_state._completion_prompt_template or llm_state._global_default_prompts.get("completion", "")
    
    # Get keywords for the current file
    keywords_list = keyword_history.get_keywords_for_file(active_file_path)
    keywords_str = ", ".join(keywords_list)

    # Format the full LLM prompt with the extracted context and keywords.
    full_llm_prompt = prompt_template.format(
        previous_context=previous_context,
        current_phrase_start=current_phrase_start,
        keywords=keywords_str
    )
    debug_console.log(f"LLM Completion Request - Formatted Prompt (first 200 chars): '{full_llm_prompt[:200]}...'", level='INFO')

    # Start a new interactive session to handle streaming output and user interaction.
    interactive_session_callbacks = start_new_interactive_session(editor_widget, is_completion=True, completion_phrase=current_phrase_start)

    def run_completion_thread_target():
        """
        Target function for the background thread that performs the LLM completion request.

        It iterates through the streaming response from the LLM API, sending chunks
        back to the main thread via `editor.after()` for UI updates. Handles errors
        and ensures the progress bar is stopped upon completion or failure.
        """
        accumulated_text = ""
        try:
            # Iterate over chunks received from the LLM API client.
            for api_response_chunk in llm_api_client.request_llm_generation(full_llm_prompt, model_name=llm_state.model_completion):
                if llm_state._is_generation_cancelled:
                    break
                if api_response_chunk["success"]:
                    if "chunk" in api_response_chunk: # If a text chunk is received.
                        chunk_text = api_response_chunk["chunk"]
                        accumulated_text += chunk_text
                        # Schedule UI update on the main thread.
                        editor_widget.after(0, lambda c=chunk_text: interactive_session_callbacks['on_chunk'](c))
                    
                    if api_response_chunk.get("done"): # If the generation is complete.
                        # Use the accumulated text as the final text.
                        if not llm_state._is_generation_cancelled:
                            final_text = accumulated_text
                            if "deepseek" in llm_state.model_completion:
                                final_text = llm_utils.strip_think_tags(final_text)
                            editor_widget.after(0, interactive_session_callbacks['on_success'], final_text)
                        return # Exit the thread.
                else:
                    # If an error occurred during generation.
                    error_message = api_response_chunk["error"]
                    if not llm_state._is_generation_cancelled:
                        editor_widget.after(0, lambda e=error_message: interactive_session_callbacks['on_error'](e))
                    return # Exit the thread.
        except Exception as e:
            # Catch any unexpected exceptions during the thread execution.
            error_message = f"An unexpected error occurred in the LLM completion thread: {e}"
            debug_console.log(error_message, level='ERROR')
            if not llm_state._is_generation_cancelled:
                editor_widget.after(0, lambda e_msg=error_message: interactive_session_callbacks['on_error'](e_msg))
        finally:
            # Ensure the progress bar is stopped and hidden regardless of success or failure.
            if llm_state._llm_progress_bar_widget:
                editor_widget.after(0, llm_state._llm_progress_bar_widget.stop)
                editor_widget.after(0, llm_state._llm_progress_bar_widget.pack_forget)
    
    # Display and start the progress bar.
    llm_state._llm_progress_bar_widget.pack(pady=2)
    llm_state._llm_progress_bar_widget.start(10) # Start animation.
    
    # Start the LLM generation in a separate thread to keep the UI responsive.
    threading.Thread(target=run_completion_thread_target, daemon=True).start()
