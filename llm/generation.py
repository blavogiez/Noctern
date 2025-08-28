"""
Text generation using LLM - Pure business logic.
Handle custom generation requests and coordinate with streaming service for response handling.
UI integration through callbacks provided by app layer.
"""
from tkinter import messagebox
from llm import state as llm_state
from llm import utils as llm_utils
from llm import keyword_history
from llm.history import _add_entry_to_history_and_save, _update_history_response_and_save
from llm.interactive import start_new_interactive_session
from llm.streaming_service import start_streaming_request
from utils import logs_console

def prepare_text_generation(initial_prompt_text=None, panel_callback=None):
    """
    Prepare text generation - pure business logic.
    
    Args:
        initial_prompt_text: Optional initial prompt text
        panel_callback: Callback to show the UI panel
    """
    logs_console.log("Preparing LLM text generation.", level='ACTION')
    
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized.")
        return
        
    editor = llm_state._active_editor_getter_func()
    if not editor:
        messagebox.showerror("LLM Error", "No active editor found.")
        return

    def _on_generate_request(user_prompt, lines_before, lines_after, is_latex_mode, is_math_mode=False):
        """
        Callback executed when user confirms generation request from panel.
        Prepare prompt and call streaming service.
        """
        # Determine prompt template and model - math mode takes precedence over latex mode
        if is_math_mode:
            prompt_template = llm_state._global_default_prompts.get("generation_math")
            model_name = llm_state.model_generation
            logs_console.log(f"Using math mode template: {prompt_template is not None}", level='DEBUG')
        elif is_latex_mode:
            prompt_template = llm_state._global_default_prompts.get("generation_latex")
            model_name = llm_state.model_generation
            logs_console.log(f"Using LaTeX mode template: {prompt_template is not None}", level='DEBUG')
        else:
            prompt_template = llm_state._generation_prompt_template or llm_state._global_default_prompts.get("generation", "")
            model_name = llm_state.model_generation
            logs_console.log(f"Using regular template: {prompt_template is not None}", level='DEBUG')

        # 2. Prepare context and full prompt
        llm_state._last_llm_action_type = "generation"
        llm_state._last_generation_user_prompt = user_prompt
        
        editor_context = llm_utils.extract_editor_context(editor, lines_before, lines_after)
        
        if not prompt_template:
            messagebox.showerror("LLM Error", "Generation prompt template is not configured.")
            return
            
        active_file_path = llm_state._active_filepath_getter_func()
        keywords_str = ", ".join(keyword_history.get_keywords_for_file(active_file_path))

        try:
            full_prompt = prompt_template.format(
                user_prompt=user_prompt,
                keywords=keywords_str,
                context=editor_context
            )
        except (KeyError, IndexError, ValueError) as e:
            logs_console.log(f"Prompt formatting error: {e}, template: '{prompt_template[:100]}...'", level='ERROR')
            messagebox.showerror("LLM Error", f"Prompt template formatting failed: {e}")
            return
        logs_console.log(f"LLM Generation Request - Prompt (first 200 chars): '{full_prompt[:200]}...'", level='INFO')
        
        # 3. Start interactive session and define callbacks
        session_callbacks = start_new_interactive_session(editor)
        
        # We need to keep track of the full response for history
        accumulated_text = ""

        def on_chunk(chunk):
            nonlocal accumulated_text
            cleaned_chunk = llm_utils.clean_llm_output(chunk)
            accumulated_text += cleaned_chunk
            session_callbacks['on_chunk'](cleaned_chunk)

        def on_success(final_text):
            # Streaming service already handles deepseek stripping
            final_cleaned_text = llm_utils.clean_full_llm_response(final_text)
            session_callbacks['on_success'](final_cleaned_text)
            _update_history_response_and_save(user_prompt, final_cleaned_text)

        def on_error(error_msg):
            session_callbacks['on_error'](error_msg)
            _update_history_response_and_save(user_prompt, f"❌ Error: {error_msg[:100]}...")

        # Call streaming service with generation settings
        start_streaming_request(
            editor=editor,
            prompt=full_prompt,
            model_name=model_name,
            on_chunk=on_chunk,
            on_success=on_success,
            on_error=on_error,
            task_type="generation"  # Optimized for generation tasks
        )

    # Call UI callback if provided
    if panel_callback:
        panel_callback(
            prompt_history=llm_state._prompt_history_list,
            on_generate_callback=_on_generate_request,
            on_history_add_callback=lambda p: _add_entry_to_history_and_save(p, "⏳ Generating..."),
            initial_prompt=initial_prompt_text
        )


# Backward compatibility wrapper
def open_generate_text_panel(initial_prompt_text=None):
    """Legacy function name for backward compatibility."""
    prepare_text_generation(initial_prompt_text)