"""
This module manages the process of generating text using a Large Language Model (LLM).
It provides the functionality to open a dialog for custom text generation requests,
extracts context from the editor, constructs the LLM prompt, and handles the streaming
response from the LLM, integrating the generated text back into the editor.
"""

from llm import state as llm_state
from llm.dialogs.generation import show_generate_text_dialog
from llm import utils as llm_utils
from llm import api_client as llm_api_client
from llm import keyword_history
from utils import debug_console
from llm.history import _add_entry_to_history_and_save, _update_history_response_and_save
from llm.interactive import start_new_interactive_session
import threading
from tkinter import messagebox

def open_generate_text_dialog(initial_prompt_text=None):
    """
    Opens a dialog window that allows the user to configure and initiate a custom LLM text generation request.

    This dialog collects the user's prompt, specifies the amount of editor context to include,
    and offers an option for LaTeX-oriented generation. It also displays a history of past
    generation requests and their responses.

    Args:
        initial_prompt_text (str, optional): An optional string to pre-fill the user prompt
                                             input field in the dialog. Defaults to None.
    """
    debug_console.log("Opening LLM text generation dialog.", level='ACTION')
    
    # Pre-check for essential LLM service components and UI elements.
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not initialized: Active editor getter is missing.")
        debug_console.log("LLM Generation dialog failed to open: Active editor getter function is not callable.", level='ERROR')
        return
        
    editor_widget = llm_state._active_editor_getter_func()
    if not editor_widget or not llm_state._root_window or not llm_state._llm_progress_bar_widget or not llm_state._theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized: Missing core UI components.")
        debug_console.log("LLM Generation dialog failed to open: One or more core UI components are missing.", level='ERROR')
        return
    
    # Check if prompt templates for generation are available.
    if not (llm_state._generation_prompt_template or (llm_state._global_default_prompts and llm_state._global_default_prompts.get("generation"))):
        messagebox.showerror("LLM Service Error", "LLM prompt templates for generation are not initialized. Please reload your file or restart the application.")
        debug_console.log("LLM Generation dialog failed to open: Prompt templates are not initialized.", level='ERROR')
        return

    def _handle_generation_request_from_dialog(user_prompt, lines_before_cursor, lines_after_cursor, is_latex_mode):
        """
        Callback function executed when the user confirms a generation request from the dialog.

        This function prepares the LLM prompt, initiates the streaming generation process
        in a separate thread, and manages the interactive display of the LLM's output.

        Args:
            user_prompt (str): The custom prompt text entered by the user.
            lines_before_cursor (int): Number of lines before the cursor to include as context.
            lines_after_cursor (int): Number of lines after the cursor to include as context.
            is_latex_mode (bool): True if LaTeX-oriented generation is requested, False otherwise.
        """
        if llm_state._is_generating:
            interface.show_temporary_status_message("LLM is already generating. Please wait for the current operation to complete.")
            debug_console.log("LLM Generation aborted: Another generation process is already in progress.", level='WARNING')
            return

        llm_model_to_use = llm_api_client.DEFAULT_LLM_MODEL
        prompt_template_to_use = ""

        if is_latex_mode:
            # Use a specific prompt template and model for LaTeX-oriented generation.
            prompt_template_to_use = llm_state._global_default_prompts.get("generation_latex")
            llm_model_to_use = llm_state._global_default_prompts.get("model_for_latex_generation", "codellama")
            if not prompt_template_to_use:
                messagebox.showerror("Configuration Error", "The 'generation_latex' prompt is missing from default_prompts.json. Cannot perform LaTeX-oriented generation.")
                debug_console.log("LLM Generation failed: 'generation_latex' prompt missing from default_prompts.json.", level='ERROR')
                return
            debug_console.log(f"Using LaTeX generation mode with model: '{llm_model_to_use}'.", level='INFO')
        else:
            # Use the standard generation prompt template.
            prompt_template_to_use = llm_state._generation_prompt_template or llm_state._global_default_prompts.get("generation", "")
        
        # Store the last LLM action type and user prompt for history and re-generation purposes.
        llm_state._last_llm_action_type = "generation"
        llm_state._last_generation_user_prompt = user_prompt
        
        # Extract relevant context from the editor based on user-defined line counts.
        editor_context = llm_utils.extract_editor_context(editor_widget, lines_before_cursor, lines_after_cursor)
        
        # Get keywords for the current file
        active_file_path = llm_state._active_filepath_getter_func()
        keywords_list = keyword_history.get_keywords_for_file(active_file_path)
        keywords_str = ", ".join(keywords_list)

        # Format the full LLM prompt using the selected template, user prompt, keywords, and editor context.
        full_llm_prompt = prompt_template_to_use.format(
            user_prompt=user_prompt,
            keywords=keywords_str,
            context=editor_context
        )
        debug_console.log(f"LLM Generation Request - Formatted Prompt (first 200 chars): '{full_llm_prompt[:200]}...'", level='INFO')
        
        # Start a new interactive session to manage the display of streaming LLM output.
        interactive_session_callbacks = start_new_interactive_session(editor_widget)

        def run_generation_thread_target():
            """
            Target function for the background thread that performs the LLM generation request.

            It iterates through the streaming response from the LLM API, sending chunks
            back to the main thread via `editor_widget.after()` for UI updates. Handles errors
            and ensures the progress bar is stopped upon completion or failure.
            """
            accumulated_generated_text = "" # Accumulator for the full generated text.
            try:
                # Request LLM generation from the API client.
                for api_response_chunk in llm_api_client.request_llm_generation(full_llm_prompt, model_name=llm_model_to_use):
                    if api_response_chunk["success"]:
                        if "chunk" in api_response_chunk: # If a text chunk is received.
                            chunk = api_response_chunk["chunk"]
                            
                            # Perform basic, real-time cleaning on the chunk.
                            cleaned_chunk = llm_utils.clean_llm_output(chunk)
                            
                            accumulated_generated_text += cleaned_chunk
                            # Schedule UI update on the main thread.
                            editor_widget.after(0, lambda c=cleaned_chunk: interactive_session_callbacks['on_chunk'](c))
                        
                        if api_response_chunk.get("done"): # If the generation is complete.
                            # Perform a final, more thorough cleaning on the entire response.
                            final_cleaned_text = llm_utils.clean_full_llm_response(accumulated_generated_text)
                            
                            # Pass the final, cleaned text to the success handler.
                            editor_widget.after(0, lambda text=final_cleaned_text: interactive_session_callbacks['on_success'](text))
                            
                            # Update history with the same final, cleaned response.
                            editor_widget.after(0, lambda: _update_history_response_and_save(user_prompt, final_cleaned_text))
                            return # Exit the thread.
                    else:
                        # If an error occurred during generation.
                        error_message = api_response_chunk["error"]
                        editor_widget.after(0, lambda e=error_message: interactive_session_callbacks['on_error'](e))
                        # Update history with an error message.
                        editor_widget.after(0, lambda: _update_history_response_and_save(user_prompt, f"❌ Error: {error_message[:100]}..."))
                        return # Exit the thread.
            except Exception as e:
                # Catch any unexpected exceptions during the thread execution.
                error_message = f"An unexpected error occurred in the LLM generation thread: {e}"
                debug_console.log(error_message, level='ERROR')
                editor_widget.after(0, lambda e_msg=error_message: interactive_session_callbacks['on_error'](e_msg))
                editor_widget.after(0, lambda: _update_history_response_and_save(user_prompt, f"❌ Exception: {str(e)[:100]}..."))
            finally:
                # Ensure the progress bar is stopped and hidden regardless of success or failure.
                if llm_state._llm_progress_bar_widget:
                    editor_widget.after(0, llm_state._llm_progress_bar_widget.stop)
                    editor_widget.after(0, llm_state._llm_progress_bar_widget.pack_forget)
        
        # Display and start the progress bar to indicate ongoing generation.
        llm_state._llm_progress_bar_widget.pack(pady=2)
        llm_state._llm_progress_bar_widget.start(10) # Start animation.
        
        # Start the LLM generation in a separate thread to keep the UI responsive.
        threading.Thread(target=run_generation_thread_target, daemon=True).start()

    def _handle_history_entry_addition_from_dialog(user_prompt_text):
        """
        Callback function to add a new entry to the prompt history when generation starts.
        It marks the response as "Generating..." initially.

        Args:
            user_prompt_text (str): The user's prompt that initiated the generation.
        """
        _add_entry_to_history_and_save(user_prompt_text, "⏳ Generating...")

    # Display the generation dialog, passing all necessary callbacks and initial data.
    show_generate_text_dialog(
        root_window=llm_state._root_window,
        theme_setting_getter_func=llm_state._theme_setting_getter_func,
        current_prompt_history_list=llm_state._prompt_history_list,
        on_generate_request_callback=_handle_generation_request_from_dialog,
        on_history_entry_add_callback=_handle_history_entry_addition_from_dialog,
        initial_prompt_text=initial_prompt_text
    )
