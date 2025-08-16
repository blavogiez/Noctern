"""
Handle logic for requesting text completion from Large Language Model (LLM).
Extract context from editor, construct prompt, and use centralized streaming service to integrate generated text back into editor.
"""
from tkinter import messagebox
from llm import state as llm_state
from llm import utils as llm_utils
from llm import keyword_history
from llm.interactive import start_new_interactive_session
from llm.streaming_service import start_streaming_request
from utils import debug_console

def request_llm_to_complete_text():
    """
    Initiate streaming text completion request to LLM.
    """
    debug_console.log("LLM Text Completion request initiated.", level='ACTION')
    
    # Validate state and get editor
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized.")
        return
    editor = llm_state._active_editor_getter_func()
    if not editor:
        messagebox.showerror("LLM Error", "No active editor found.")
        return
        
    # Prepare prompt
    active_file_path = llm_state._active_filepath_getter_func()
    editor_context = llm_utils.extract_editor_context(editor, lines_before_cursor=30, lines_after_cursor=0)
    
    last_punctuation_index = max(editor_context.rfind("."), editor_context.rfind("!"), editor_context.rfind("?"))
    current_phrase_start = editor_context[last_punctuation_index + 1:].strip() if last_punctuation_index != -1 else editor_context.strip()
    previous_context = editor_context[:last_punctuation_index + 1].strip() if last_punctuation_index != -1 else ""

    llm_state._last_llm_action_type = "completion"
    llm_state._last_completion_phrase_start = current_phrase_start

    prompt_template = llm_state._completion_prompt_template or llm_state._global_default_prompts.get("completion", "")
    if not prompt_template:
        messagebox.showerror("LLM Error", "Completion prompt template is not configured.")
        return

    keywords_list = keyword_history.get_keywords_for_file(active_file_path)
    keywords_str = ", ".join(keywords_list)

    full_llm_prompt = prompt_template.format(
        previous_context=previous_context,
        current_phrase_start=current_phrase_start,
        keywords=keywords_str
    )
    debug_console.log(f"LLM Completion Request - Formatted Prompt (first 200 chars): '{full_llm_prompt[:200]}...'", level='INFO')

    # 3. Start interactive session to get callbacks
    session_callbacks = start_new_interactive_session(editor, is_completion=True, completion_phrase=current_phrase_start)

    # 4. Call the high-performance streaming service with completion profile
    start_streaming_request(
        editor=editor,
        prompt=full_llm_prompt,
        model_name=llm_state.model_completion,
        on_chunk=session_callbacks['on_chunk'],
        on_success=session_callbacks['on_success'],
        on_error=session_callbacks['on_error'],
        task_type="completion"  # Optimized for completion tasks
    )
