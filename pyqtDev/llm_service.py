# File: llm_service.py
# automa_tex_pyqt/services/llm_service.py
"""
Service layer for LLM (Large Language Model) functionalities.

This module coordinates interactions between the UI, LLM API client,
prompt history management, utility functions, and dialogs. It provides
the main entry points for LLM features like text completion, generation,
and keyword management.
"""

from PyQt6 import QtWidgets, QtCore, QtGui
from datetime import datetime
import os
import json
import requests
import threading

# Import local modules (flat import)
import llm_prompt_history
import llm_utils
import llm_api_client
import llm_dialogs
import llm_prompt_manager
import llm_keyword_manager

# --- Module-level variables to store references from the main application ---
_root_window = None
_llm_progress_bar_widget = None
_theme_setting_getter_func = None
_active_editor_getter_func = None
_show_temporary_status_message_func = None
_active_filepath_getter_func = None
_pause_heavy_updates_func = None
_resume_heavy_updates_func = None
_full_editor_refresh_cb = None

# --- State for generation ---
_generation_thread = None
_cancel_event = threading.Event()

# --- Prompt Configuration ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROMPTS_FILE = os.path.join(_SCRIPT_DIR, "default_prompts.json")
_global_default_prompts = {} # Loaded once at startup

# --- State managed by this service ---
_llm_keywords_list = []
_prompt_history_list = []
_completion_prompt_template = ""
_generation_prompt_template = ""
_latex_code_generation_prompt_template = ""

def _load_global_default_prompts():
    """Loads the master default prompts from the default_prompts.json file."""
    global _global_default_prompts
    try:
        with open(DEFAULT_PROMPTS_FILE, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            if not isinstance(loaded_data, dict) or not loaded_data:
                raise json.JSONDecodeError("File is empty or not a valid dictionary.", "", 0)
            _global_default_prompts = loaded_data
            print("="*50)
            print(f"Successfully loaded default prompts from: {os.path.basename(DEFAULT_PROMPTS_FILE)}")
            for key, value in _global_default_prompts.items():
                print(f"  - {key}: '{value[:70].replace(chr(10), ' ')}...'")
            print("="*50)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        filename = os.path.basename(DEFAULT_PROMPTS_FILE)
        print(f"WARNING: Could not load {filename}. Using hardcoded defaults. {e}")
        _global_default_prompts = {
            "completion": "Complete this: {current_phrase_start}",
            "generation": "Generate text for this prompt: {user_prompt}\n\n**Keywords:** {keywords}\n\n**IMPORTANT: The response MUST be in the following language:** {language}",
            "latex_code_generation": "You are a LaTeX coding assistant embedded within a LaTeX editor. Your task is to generate valid LaTeX code that fulfills the user's instruction.\n\n**Primary Goal:**\nProduce syntactically correct and logically coherent LaTeX code that integrates cleanly with the surrounding context.\n\n**Key Instructions:**\n- **Output only LaTeX code.** Do not include any explanatory text, comments, or formatting outside the LaTeX syntax.\n- **Language Adherence:** You MUST generate the response in the language specified below. This is a strict requirement. All explanatory text within the code (e.g., comments) must also be in this language.\n- Ensure that all commands and environments are properly opened and closed.\n- Use appropriate LaTeX packages if implied by the context (e.g., `amsmath`, `graphicx`, `tikz`).\n- Match the style of the surrounding context.\n- Be concise and avoid unnecessary boilerplate unless requested.\n- Maintain compatibility with standard LaTeX compilers.\n\n**Context (existing LaTeX code around the cursor):**\n---\n{context}\n---\n\n**User's Instruction:**\n\"{user_prompt}\"\n\n**Keywords:**\n{keywords}\n\n**Response Language (Strict Requirement):**\n{language}\n\n**Generated LaTeX code:"
        }

def initialize_llm_service(root_window_ref, progress_bar_widget_ref,
                           theme_setting_getter_func, active_editor_getter,
                           active_filepath_getter, show_temporary_status_message_func,
                           pause_heavy_updates_cb, resume_heavy_updates_cb,
                           full_editor_refresh_cb):
    """Initializes the LLM service with necessary references from the main application."""
    global _root_window, _llm_progress_bar_widget, _theme_setting_getter_func
    global _active_editor_getter_func, _active_filepath_getter_func, _show_temporary_status_message_func
    global _pause_heavy_updates_func, _resume_heavy_updates_func, _full_editor_refresh_cb
    
    _show_temporary_status_message_func = show_temporary_status_message_func
    _root_window = root_window_ref
    _llm_progress_bar_widget = progress_bar_widget_ref
    _theme_setting_getter_func = theme_setting_getter_func
    _active_editor_getter_func = active_editor_getter
    _active_filepath_getter_func = active_filepath_getter
    _pause_heavy_updates_func = pause_heavy_updates_cb
    _resume_heavy_updates_cb = resume_heavy_updates_cb
    _full_editor_refresh_cb = full_editor_refresh_cb

    # Connect buttons and actions
    _root_window.btn_complete.clicked.connect(request_llm_to_complete_text)
    _root_window.btn_generate.clicked.connect(open_generate_text_dialog)
    _root_window.btn_keywords.clicked.connect(open_set_keywords_dialog)
    _root_window.btn_prompts.clicked.connect(open_edit_prompts_dialog)

    _root_window.action_complete.triggered.connect(request_llm_to_complete_text)
    _root_window.action_generate.triggered.connect(open_generate_text_dialog)
    _root_window.action_keywords.triggered.connect(open_set_keywords_dialog)
    _root_window.action_prompts.triggered.connect(open_edit_prompts_dialog)

    load_prompt_history_for_current_file()
    load_keywords_for_current_file()
    load_prompts_for_current_file()

def _get_active_tex_filepath():
    """Helper to safely get the current .tex file path using the provided getter."""
    if _active_filepath_getter_func:
        return _active_filepath_getter_func()
    return None

# --- Prompt History Management ---
def load_prompt_history_for_current_file():
    """
    Loads the prompt history associated with the currently active .tex file.
    """
    global _prompt_history_list
    active_filepath = _get_active_tex_filepath()
    _prompt_history_list = llm_prompt_history.load_prompt_history_from_file(active_filepath)

def _add_entry_to_history_and_save(user_prompt, response_placeholder="⏳ Generating..."):
    """Internal helper to add a new entry and save the history. (Now accepts optional response_placeholder)"""
    global _prompt_history_list
    _prompt_history_list = [item for item in _prompt_history_list if item[0] != user_prompt]
    _prompt_history_list.insert(0, (user_prompt, response_placeholder))

    if len(_prompt_history_list) > llm_prompt_history.MAX_PROMPT_HISTORY_SIZE:
        _prompt_history_list = _prompt_history_list[:llm_prompt_history.MAX_PROMPT_HISTORY_SIZE]

    active_filepath = _get_active_tex_filepath()
    llm_prompt_history.save_prompt_history_to_file(_prompt_history_list, active_filepath)

def _update_history_response_and_save(user_prompt_key, new_response_text):
    """Internal helper to update a response in history and save."""
    global _prompt_history_list
    llm_prompt_history.update_response_in_history(_prompt_history_list, user_prompt_key, new_response_text)
    active_filepath = _get_active_tex_filepath()
    llm_prompt_history.save_prompt_history_to_file(_prompt_history_list, active_filepath)

# --- Centralized LLM API Error Handling ---
def _handle_llm_api_error(error_type, exception_obj, active_editor, user_prompt=None):
    """
    Centralized error handling for LLM API requests.
    Displays an error message and updates the status bar.
    Optionally updates history if a user_prompt is provided.
    """
    error_msg = ""
    status_msg = ""
    history_update_text = ""

    if error_type == "ConnectionError":
        error_msg = "Connection Error: Could not connect to LLM API. Is the backend running?"
        status_msg = "❌ LLM connection failed."
        history_update_text = "❌ Connection Error"
    elif error_type == "RequestException":
        error_msg = f"API Error: {str(exception_obj)}"
        status_msg = "❌ LLM API request failed."
        history_update_text = f"❌ API Error: {str(exception_obj)[:50]}..."
    else: # Catch-all for other unexpected errors
        error_msg = f"An unexpected error occurred: {str(exception_obj)}"
        status_msg = "❌ LLM operation failed unexpectedly."
        history_update_text = f"❌ Unexpected Error: {str(exception_obj)[:50]}..."

    QtWidgets.QMessageBox.critical(_root_window, "LLM Error", error_msg)
    _show_temporary_status_message_func(status_msg)

    if user_prompt and _update_history_response_and_save:
        _update_history_response_and_save(user_prompt, history_update_text)

    # Ensure progress bar is hidden and updates are resumed
    if _llm_progress_bar_widget:
        _llm_progress_bar_widget.hide()
    if _resume_heavy_updates_func:
        _resume_heavy_updates_func()

# --- Keywords Management ---
def load_keywords_for_current_file():
    """Loads the keywords associated with the currently active .tex file."""
    global _llm_keywords_list
    active_filepath = _get_active_tex_filepath()
    _llm_keywords_list = llm_keyword_manager.load_keywords_from_file(active_filepath)

# --- Custom Prompts Management ---
def load_prompts_for_current_file():
    """Loads custom prompts for the current file. If no custom prompt file
    exists, it creates one with default values."""
    global _completion_prompt_template, _generation_prompt_template, _latex_code_generation_prompt_template
    active_filepath = _get_active_tex_filepath()
    loaded_prompts = llm_prompt_manager.load_prompts_from_file(active_filepath, _global_default_prompts)
    _completion_prompt_template = loaded_prompts.get("completion", "")
    _generation_prompt_template = loaded_prompts.get("generation", "")
    _latex_code_generation_prompt_template = loaded_prompts.get("latex_code_generation", "")

# --- Call the loader at module import time to ensure defaults are always available ---
_load_global_default_prompts()

# --- LLM Text Generation (Non-interactive) ---
def _execute_llm_generation(full_llm_prompt, user_prompt_for_history, model_name=llm_api_client.DEFAULT_LLM_MODEL, text_for_completion_cleanup=None):
    """
    The main function to execute an LLM generation.
    It inserts text directly into the editor and handles progress/status updates.
    It does NOT provide an interactive UI for accepting/rejecting/rephrasing.
    """
    global _generation_thread, _cancel_event

    editor = _active_editor_getter_func()
    if not editor:
        print("[LLM] No active editor found.")
        _show_temporary_status_message_func("❌ No active editor found.")
        return

    if _generation_thread and _generation_thread.is_alive():
        print("[LLM] Generation already in progress.")
        _show_temporary_status_message_func("⚠️ Another LLM generation is already in progress.")
        return

    _cancel_event.clear()

    # Store the initial cursor position where the text will be inserted
    insert_start_cursor = editor.textCursor()
    insert_position = insert_start_cursor.position()

    def run_generation_in_thread():
        got_any_chunk = False
        inserted_length = 0

        def insert_chunk_main_thread(chunk, pos, length):
            cursor = editor.textCursor()
            cursor.setPosition(pos + length)
            editor.setTextCursor(cursor)
            editor.insertPlainText(chunk)

        try:
            if _llm_progress_bar_widget:
                QtCore.QTimer.singleShot(0, _llm_progress_bar_widget.show)
            _show_temporary_status_message_func("⏳ Generating text...")
            print("[LLM] Sending prompt to backend...")
            print(f"[LLM] Model: {model_name}")
            print(f"[LLM] Prompt (first 200 chars): {full_llm_prompt[:200]}{'...' if len(full_llm_prompt) > 200 else ''}")

            for chunk in llm_api_client.request_llm_generation(full_llm_prompt, model_name):
                got_any_chunk = True
                print(f"[LLM] Got chunk: {repr(chunk[:60])}...")
                # Schedule each chunk for insertion in the main thread
                QtCore.QTimer.singleShot(
                    0,
                    lambda chunk=chunk, pos=insert_position, length=inserted_length: insert_chunk_main_thread(chunk, pos, length)
                )
                inserted_length += len(chunk)

            def postprocess_and_finalize():
                if not got_any_chunk:
                    print("[LLM] No response received from backend. (Model may not be loaded, or prompt is empty, or model is not compatible.)")
                    _show_temporary_status_message_func("❌ No response from LLM backend. Try a different model or check your prompt.")
                    _update_history_response_and_save(user_prompt_for_history, "❌ No response from LLM backend.")
                    return
                # Select the inserted text region for post-processing
                cursor = editor.textCursor()
                cursor.setPosition(insert_position)
                cursor.setPosition(insert_position + inserted_length, QtGui.QTextCursor.MoveMode.KeepAnchor)
                editor.setTextCursor(cursor)
                raw_inserted_text = cursor.selectedText()
                final_generated_text = raw_inserted_text
                if text_for_completion_cleanup:
                    cleaned_text = llm_utils.remove_prefix_overlap_from_completion(
                        text_before_completion=text_for_completion_cleanup,
                        llm_generated_completion=raw_inserted_text
                    )
                    if cleaned_text != raw_inserted_text:
                        cursor.removeSelectedText()
                        cursor.insertText(cleaned_text)
                        final_generated_text = cleaned_text
                print(f"[LLM] Generation complete. Inserted {len(final_generated_text)} chars.")
                print(f"[LLM] Final inserted text (first 200 chars): {final_generated_text[:200]!r}")
                _show_temporary_status_message_func("✅ Generation complete.")
                _update_history_response_and_save(user_prompt_for_history, final_generated_text)

            QtCore.QTimer.singleShot(0, postprocess_and_finalize)

        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            print(f"[LLM] Request error: {e}")
            QtCore.QTimer.singleShot(0, lambda: _handle_llm_api_error(type(e).__name__, e, editor, user_prompt_for_history))
        except Exception as e:
            print(f"[LLM] Unexpected error: {e}")
            QtCore.QTimer.singleShot(0, lambda: _handle_llm_api_error("UnexpectedError", e, editor, user_prompt_for_history))
        finally:
            if _llm_progress_bar_widget:
                QtCore.QTimer.singleShot(0, _llm_progress_bar_widget.hide)
            if _resume_heavy_updates_func:
                QtCore.QTimer.singleShot(0, _resume_heavy_updates_func)
            _generation_thread = None

    if _pause_heavy_updates_func:
        _pause_heavy_updates_func()

    _generation_thread = threading.Thread(target=run_generation_in_thread, daemon=True)
    _generation_thread.start()

# --- LLM Text Completion ---
def request_llm_to_complete_text():
    """Requests sentence completion from the LLM based on preceding text."""
    editor = _active_editor_getter_func()
    if not editor or not _root_window or not _llm_progress_bar_widget:
        QtWidgets.QMessageBox.critical(_root_window, "LLM Service Error", "LLM Service not fully initialized.")
        return

    _show_temporary_status_message_func("⏳ Requesting LLM completion...")

    context = llm_utils.extract_editor_context(editor, lines_before_cursor=30, lines_after_cursor=0)

    last_dot_index = max(context.rfind("."), context.rfind("!"), context.rfind("?"))
    if last_dot_index == -1:
        current_phrase_start = context.strip()
        previous_context = ""
    else:
        current_phrase_start = context[last_dot_index + 1:].strip()
        previous_context = context[:last_dot_index + 1].strip()

    full_llm_prompt = _completion_prompt_template.format(
        previous_context=previous_context,
        current_phrase_start=current_phrase_start,
        keywords=', '.join(_llm_keywords_list)
    )

    user_prompt_for_history = f"Complete: \"{current_phrase_start.strip()[:60]}...\""
    _add_entry_to_history_and_save(user_prompt_for_history)
    _execute_llm_generation(full_llm_prompt, user_prompt_for_history, text_for_completion_cleanup=current_phrase_start)

# --- LLM Text Generation via Dialog ---
def open_generate_text_dialog(initial_prompt_text=None):
    """
    Opens a dialog for the user to input a custom prompt for LLM text generation.
    """
    editor = _active_editor_getter_func()
    if not editor or not _root_window or not _llm_progress_bar_widget or not _theme_setting_getter_func:
        QtWidgets.QMessageBox.critical(_root_window, "LLM Service Error", "LLM Service or UI components not fully initialized.")
        return

    _show_temporary_status_message_func("⏳ Opening LLM generation dialog...")

    def _handle_generation_request_from_dialog(user_prompt, lines_before, lines_after, is_latex_oriented, language):
        model_to_use = llm_api_client.DEFAULT_LLM_MODEL
        prompt_template_to_use = _generation_prompt_template
        status_message = "⏳ Requesting LLM generation..."

        if is_latex_oriented:
            model_to_use = llm_api_client.LATEX_CODE_MODEL
            prompt_template_to_use = _latex_code_generation_prompt_template
            status_message = "⏳ Requesting LLM LaTeX code generation..."

        _show_temporary_status_message_func(status_message)
        context = llm_utils.extract_editor_context(editor, lines_before, lines_after)
        full_llm_prompt = prompt_template_to_use.format(
            user_prompt=user_prompt,
            keywords=', '.join(_llm_keywords_list),
            context=context,
            language=language
        )
        _execute_llm_generation(full_llm_prompt, user_prompt, model_name=model_to_use)

    def _handle_history_entry_add_from_dialog(user_prompt, is_latex_oriented):
        placeholder = "⏳ Generating LaTeX code..." if is_latex_oriented else "⏳ Generating..."
        _add_entry_to_history_and_save(user_prompt, placeholder)

    llm_dialogs.show_generate_text_dialog(
        root_window=_root_window,
        theme_setting_getter_func=_theme_setting_getter_func,
        current_prompt_history_list=_prompt_history_list,
        on_generate_request_callback=_handle_generation_request_from_dialog,
        on_history_entry_add_callback=_handle_history_entry_add_from_dialog,
        initial_prompt_text=initial_prompt_text
    )

# --- LLM Keywords Management ---
def open_set_keywords_dialog():
    """Opens a dialog for the user to set or update LLM keywords."""
    global _llm_keywords_list
    if not _root_window or not _theme_setting_getter_func:
        QtWidgets.QMessageBox.critical(_root_window, "LLM Service Error", "UI components not fully initialized for keywords dialog.")
        _show_temporary_status_message_func("❌ LLM Keywords dialog failed to open.")
        return

    def _handle_keywords_save_from_dialog(new_keywords_list):
        global _llm_keywords_list
        _llm_keywords_list = new_keywords_list
        llm_keyword_manager.save_keywords_to_file(_llm_keywords_list, _get_active_tex_filepath())
        if not _llm_keywords_list:
            _show_temporary_status_message_func("✅ LLM keywords cleared.")
            QtWidgets.QMessageBox.information(_root_window, "Keywords Cleared", "LLM keywords list has been cleared.")
        else:
            _show_temporary_status_message_func("✅ LLM keywords saved.")
            QtWidgets.QMessageBox.information(_root_window, "Keywords Saved", f"LLM keywords registered:\n- {', '.join(_llm_keywords_list)}")

    llm_dialogs.show_set_llm_keywords_dialog(
        root_window=_root_window,
        theme_setting_getter_func=_theme_setting_getter_func,
        current_llm_keywords_list=_llm_keywords_list,
        on_save_keywords_callback=_handle_keywords_save_from_dialog
    )

# --- LLM Prompt Management ---
def get_current_prompts():
    """Returns the current prompt templates."""
    return {
        "completion": _completion_prompt_template,
        "generation": _generation_prompt_template,
        "latex_code_generation": _latex_code_generation_prompt_template
    }

def update_prompts(completion_template, generation_template, latex_code_generation_template):
    """Updates the prompt templates and saves them to a custom file."""
    global _completion_prompt_template, _generation_prompt_template, _latex_code_generation_prompt_template
    _latex_code_generation_prompt_template = latex_code_generation_template
    _completion_prompt_template = completion_template
    _generation_prompt_template = generation_template

    active_filepath = _get_active_tex_filepath()
    if active_filepath:
        prompts_to_save = {
            "completion": _completion_prompt_template,
            "generation": _generation_prompt_template,
            "latex_code_generation": _latex_code_generation_prompt_template
        }
        llm_prompt_manager.save_prompts_to_file(prompts_to_save, active_filepath)
        _show_temporary_status_message_func(f"✅ Prompts saved: {os.path.basename(llm_prompt_manager.get_prompts_filepath(active_filepath))}")
    else:
        _show_temporary_status_message_func("⚠️ Prompts updated for this session only (no file open).")

def open_edit_prompts_dialog():
    """Opens a dialog to edit the LLM prompt templates."""
    if not _root_window or not _theme_setting_getter_func:
        QtWidgets.QMessageBox.critical(_root_window, "LLM Service Error", "UI components not fully initialized for prompts dialog.")
        return

    _show_temporary_status_message_func("⏳ Opening LLM prompt templates dialog...")
    llm_dialogs.show_edit_prompts_dialog(
        root_window=_root_window,
        theme_setting_getter_func=_theme_setting_getter_func,
        current_prompts=get_current_prompts(),
        default_prompts=_global_default_prompts,
        on_save_callback=update_prompts
    )
    llm_dialogs.show_edit_prompts_dialog(
        root_window=_root_window,
        theme_setting_getter_func=_theme_setting_getter_func,
        current_prompts=get_current_prompts(),
        default_prompts=_global_default_prompts,
        on_save_callback=update_prompts
    )