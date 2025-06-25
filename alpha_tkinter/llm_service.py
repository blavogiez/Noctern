# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\llm_service.py
"""
Service layer for LLM (Large Language Model) functionalities.

This module coordinates interactions between the UI, LLM API client,
prompt history management, utility functions, and dialogs. It provides
the main entry points for LLM features like text completion, generation,
and keyword management.
"""
import tkinter as tk
from tkinter import messagebox, ttk
import os
import json
import requests # Import the requests library to handle its exceptions
import threading

# Import newly created local modules
import llm_prompt_history
import llm_utils
import llm_api_client
import llm_dialogs
import llm_prompt_manager # NEW
import llm_generation_history # NEW
import llm_keyword_manager # NEW
from gui_generation_controller import GenerationUIController # NEW

# --- Module-level variables to store references from the main application ---
_root_window = None
_llm_progress_bar_widget = None
_theme_setting_getter_func = None
_active_editor_getter_func = None # Function to get the active tk.Text widget
_show_temporary_status_message_func = None # Callback for status messages
_active_filepath_getter_func = None # Function to get current .tex file path

# --- NEW: State for interactive generation ---
_generation_thread = None
_cancel_event = threading.Event()
_generation_ui = None

# --- Prompt Configuration ---
DEFAULT_PROMPTS_FILE = "default_prompts.json"
_global_default_prompts = {} # Loaded once at startup

# --- State managed by this service ---
_llm_keywords_list = []  # Stores user-defined LLM keywords.
_prompt_history_list = [] # Stores tuples: (user_prompt, llm_response)
_generation_history_list = [] # NEW: Stores list of [start, end] for generated text
_completion_prompt_template = "" # Loaded per-file
_generation_prompt_template = "" # Loaded per-file

def _load_global_default_prompts():
    """Loads the master default prompts from the default_prompts.json file."""
    global _global_default_prompts
    try:
        with open(DEFAULT_PROMPTS_FILE, 'r', encoding='utf-8') as f:
            _global_default_prompts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"CRITICAL ERROR: Could not load {DEFAULT_PROMPTS_FILE}. {e}")
        _global_default_prompts = {
            "completion": "Complete this: {current_phrase_start}",
            "generation": "Generate text for this prompt: {user_prompt}"
        }
        # Cannot show messagebox here as Tk root may not exist yet.
        # The error will be printed to the console.

def initialize_llm_service(root_window_ref, progress_bar_widget_ref,
                           theme_setting_getter_func, active_editor_getter,
                           active_filepath_getter, show_temporary_status_message_func):
    """Initializes the LLM service with necessary references from the main application."""
    global _root_window, _llm_progress_bar_widget, _theme_setting_getter_func
    global _active_editor_getter_func, _active_filepath_getter_func, _show_temporary_status_message_func

    _show_temporary_status_message_func = show_temporary_status_message_func
    _root_window = root_window_ref
    _llm_progress_bar_widget = progress_bar_widget_ref
    _theme_setting_getter_func = theme_setting_getter_func
    _active_editor_getter_func = active_editor_getter
    _active_filepath_getter_func = active_filepath_getter

    # Load initial prompt history and custom prompts
    load_prompt_history_for_current_file()
    load_generation_history_for_current_file() # NEW
    load_keywords_for_current_file() # NEW: Load keywords on service initialization
    load_prompts_for_current_file()

def _get_active_tex_filepath():
    """Helper to safely get the current .tex file path using the provided getter."""
    if _active_filepath_getter_func:
        return _active_filepath_getter_func()
    return None

# --- Generation History Management (NEW) ---
def load_generation_history_for_current_file():
    """
    Loads the generation history for the current file and applies styling.
    NOTE: This method has a side effect of modifying the editor view.
    """
    global _generation_history_list
    active_filepath = _get_active_tex_filepath()
    _generation_history_list = llm_generation_history.load_generation_history_from_file(active_filepath)

    editor = _active_editor_getter_func()
    if editor and _generation_history_list:
        # The "generated_text" tag is configured in EditorTab.__init__
        # Clear any previous styling before applying, in case the history file changed.
        editor.tag_remove("generated_text", "1.0", tk.END)
        for start_index, end_index in _generation_history_list:
            try:
                editor.tag_add("generated_text", start_index, end_index)
            except tk.TclError:
                # This can happen if indices are invalid due to file edits.
                # This is a known limitation of this approach.
                print(f"Warning: Could not apply 'generated' style for range {start_index}-{end_index}. File may have been edited since generation.")

def _add_entry_to_generation_history_and_save(indices):
    """Internal helper to add a new entry and save the generation history."""
    global _generation_history_list
    llm_generation_history.add_generation_to_history(_generation_history_list, indices)
    active_filepath = _get_active_tex_filepath()
    llm_generation_history.save_generation_history_to_file(_generation_history_list, active_filepath)

# --- Prompt History Management ---
def load_prompt_history_for_current_file():
    """
    Loads the prompt history associated with the currently active .tex file.
    This is typically called when a file is opened or the application starts.
    """
    global _prompt_history_list
    active_filepath = _get_active_tex_filepath()
    _prompt_history_list = llm_prompt_history.load_prompt_history_from_file(active_filepath)

def _add_entry_to_history_and_save(user_prompt, response_placeholder="⏳ Generating..."):
    """Internal helper to add a new entry and save the history."""
    global _prompt_history_list
    # Remove existing entry for this user_prompt to move it to the top or update status
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

    active_editor.after(0, lambda: messagebox.showerror("LLM Error", error_msg))
    _show_temporary_status_message_func(status_msg)

    # NEW: Clean up the interactive UI on error
    if active_editor:
        active_editor.after(0, lambda: _cancel_current_generation(discard_text=True))

    if user_prompt and _update_history_response_and_save:
        active_editor.after(0, lambda: _update_history_response_and_save(user_prompt, history_update_text))

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
    global _completion_prompt_template, _generation_prompt_template
    active_filepath = _get_active_tex_filepath()
    # The logic to load or create is handled by the prompt manager, using the globally loaded defaults.
    loaded_prompts = llm_prompt_manager.load_prompts_from_file(active_filepath, _global_default_prompts)
    _completion_prompt_template = loaded_prompts["completion"]
    _generation_prompt_template = loaded_prompts["generation"]

# --- Call the loader at module import time to ensure defaults are always available ---
_load_global_default_prompts()


def _cancel_current_generation(discard_text=True):
    """Stops any active generation thread and cleans up the UI."""
    global _generation_thread, _cancel_event, _generation_ui

    if _generation_thread and _generation_thread.is_alive():
        _cancel_event.set() # Signal thread to stop

    if _generation_ui:
        # get text before cleanup for history
        generated_text = _generation_ui.get_text()
        indices = None
        if not discard_text: # if accepted
            # Get indices before cleanup
            start_index = _generation_ui.get_start_index()
            end_index = _generation_ui.get_end_index()
            indices = (start_index, end_index)

        _generation_ui.cleanup(is_accept=not discard_text)
        _generation_ui = None
        return generated_text, indices

    _generation_thread = None
    return "", None

def _execute_llm_generation(full_llm_prompt, user_prompt_for_history):
    """
    The main function to execute an LLM generation with an interactive UI.
    """
    global _generation_thread, _cancel_event, _generation_ui

    editor = _active_editor_getter_func()
    if not editor: return

    _cancel_current_generation(discard_text=True)
    _cancel_event.clear()

    _generation_ui = GenerationUIController(editor, _theme_setting_getter_func)

    def on_accept():
        generated_text, indices = _cancel_current_generation(discard_text=False)
        if indices:
            # Convert tuple to list for JSON serialization
            _add_entry_to_generation_history_and_save(list(indices))
        _show_temporary_status_message_func("✅ Generation accepted.")
        _update_history_response_and_save(user_prompt_for_history, generated_text)

    def on_rephrase(text_to_rephrase):
        _cancel_current_generation(discard_text=True) # Cleanup UI, ignore return values
        rephrase_user_prompt = f"Rephrase the following text: \"{text_to_rephrase}\""
        rephrase_full_prompt = _generation_prompt_template.format(
            user_prompt=rephrase_user_prompt,
            keywords=', '.join(_llm_keywords_list),
            context="" # No context for rephrasing
        )
        _add_entry_to_history_and_save(rephrase_user_prompt)
        _execute_llm_generation(rephrase_full_prompt, rephrase_user_prompt)

    def on_cancel():
        _cancel_current_generation(discard_text=True) # Cleanup UI, ignore return values
        _show_temporary_status_message_func("❌ Generation cancelled.")
        _update_history_response_and_save(user_prompt_for_history, "❌ Cancelled by user.")

    _generation_ui.accept_callback = on_accept
    _generation_ui.rephrase_callback = on_rephrase
    _generation_ui.cancel_callback = on_cancel

    def run_thread(prompt, ui_controller, cancel_event, user_prompt_key):
        try:
            for chunk in llm_api_client.request_llm_generation(prompt):
                if cancel_event.is_set(): break
                if editor and ui_controller: editor.after(0, lambda c=chunk: ui_controller.insert_chunk(c))
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            _handle_llm_api_error(type(e).__name__, e, editor, user_prompt_key)
        except Exception as e:
            _handle_llm_api_error("UnexpectedError", e, editor, user_prompt_key)
        finally:
            if editor and ui_controller and not cancel_event.is_set():
                editor.after(0, ui_controller.show_finished_state)
            if _llm_progress_bar_widget and editor:
                editor.after(0, lambda: (_llm_progress_bar_widget.pack_forget(), _llm_progress_bar_widget.stop()))

    _llm_progress_bar_widget.pack(pady=2)
    _llm_progress_bar_widget.start(10)
    _generation_ui.show_generating_state()
    _generation_thread = threading.Thread(target=run_thread, args=(full_llm_prompt, _generation_ui, _cancel_event, user_prompt_for_history), daemon=True)
    _generation_thread.start()

# --- LLM Text Completion ---
def request_llm_to_complete_text():
    """Requests sentence completion from the LLM based on preceding text."""
    editor = _active_editor_getter_func()
    if not editor or not _root_window or not _llm_progress_bar_widget:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized.")
        return

    _show_temporary_status_message_func("⏳ Requesting LLM completion...")

    # Get context: 30 lines backwards, 0 forwards
    context = llm_utils.extract_editor_context(editor, lines_before_cursor=30, lines_after_cursor=0)

    # Find the last sentence ending to isolate the current sentence fragment
    last_dot_index = max(context.rfind("."), context.rfind("!"), context.rfind("?"))
    if last_dot_index == -1:
        current_phrase_start = context.strip()
        previous_context = ""
    else:
        current_phrase_start = context[last_dot_index + 1:].strip()
        previous_context = context[:last_dot_index + 1].strip()

    # Construct the prompt for the LLM API
    full_llm_prompt = _completion_prompt_template.format(
        previous_context=previous_context,
        current_phrase_start=current_phrase_start,
        keywords=', '.join(_llm_keywords_list)
    )

    # Use the full prompt as the key for history
    _add_entry_to_history_and_save(full_llm_prompt)
    _execute_llm_generation(full_llm_prompt, full_llm_prompt)

# --- LLM Text Generation via Dialog ---
def open_generate_text_dialog(initial_prompt_text=None):
    """
    Opens a dialog for the user to input a custom prompt for LLM text generation.
    Manages the process of getting user input, calling the LLM, and updating history.
    """
    editor = _active_editor_getter_func()
    if not editor or not _root_window or not _llm_progress_bar_widget or not _theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "LLM Service or UI components not fully initialized.")
        return

    _show_temporary_status_message_func("⏳ Opening LLM generation dialog...")

    def _handle_generation_request_from_dialog(user_prompt, lines_before, lines_after):
        """Callback for when the dialog requests generation. Runs in main thread initially."""

        _show_temporary_status_message_func("⏳ Requesting LLM generation...")
        context = llm_utils.extract_editor_context(editor, lines_before, lines_after)
        full_llm_prompt = _generation_prompt_template.format(
            user_prompt=user_prompt,
            keywords=', '.join(_llm_keywords_list),
            context=context
        )
        _execute_llm_generation(full_llm_prompt, user_prompt)

    def _handle_history_entry_addition_from_dialog(user_prompt):
        """Callback to add 'Generating...' to history when dialog's Generate is clicked."""
        _add_entry_to_history_and_save(user_prompt, "⏳ Generating...")

    # Show the dialog
    llm_dialogs.show_generate_text_dialog(
        root_window=_root_window,
        theme_setting_getter_func=_theme_setting_getter_func,
        current_prompt_history_list=_prompt_history_list, # Pass a copy or manage updates carefully
        on_generate_request_callback=_handle_generation_request_from_dialog,
        on_history_entry_add_callback=_handle_history_entry_addition_from_dialog,
        initial_prompt_text=initial_prompt_text
    )

# --- LLM Keywords Management ---
def open_set_keywords_dialog():
    """Opens a dialog for the user to set or update LLM keywords."""
    global _llm_keywords_list # Keywords are managed globally within this service
    if not _root_window or not _theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "UI components not fully initialized for keywords dialog.")
        _show_temporary_status_message_func("❌ LLM Keywords dialog failed to open.")
        return

    def _handle_keywords_save_from_dialog(new_keywords_list):
        """Callback for when the keywords dialog saves."""
        global _llm_keywords_list
        _llm_keywords_list = new_keywords_list
        llm_keyword_manager.save_keywords_to_file(_llm_keywords_list, _get_active_tex_filepath()) # Save to file
        if not _llm_keywords_list:
            _show_temporary_status_message_func("✅ LLM keywords cleared.")
            messagebox.showinfo("Keywords Cleared", "LLM keywords list has been cleared.", parent=_root_window) # Parent might need to be dialog
        else:
            _show_temporary_status_message_func("✅ LLM keywords saved.")
            messagebox.showinfo("Keywords Saved", f"LLM keywords registered:\n- {', '.join(_llm_keywords_list)}", parent=_root_window)

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
        "generation": _generation_prompt_template
    }

def update_prompts(completion_template, generation_template):
    """Updates the prompt templates and saves them to a custom file."""
    global _completion_prompt_template, _generation_prompt_template
    _completion_prompt_template = completion_template
    _generation_prompt_template = generation_template

    # Save to file
    active_filepath = _get_active_tex_filepath()
    if active_filepath:
        prompts_to_save = {
            "completion": _completion_prompt_template,
            "generation": _generation_prompt_template
        }
        llm_prompt_manager.save_prompts_to_file(prompts_to_save, active_filepath)
        _show_temporary_status_message_func(f"✅ Prompts saved: {os.path.basename(llm_prompt_manager.get_prompts_filepath(active_filepath))}")
    else:
        _show_temporary_status_message_func("⚠️ Prompts updated for this session only (no file open).")

def open_edit_prompts_dialog():
    """Opens a dialog to edit the LLM prompt templates."""
    if not _root_window or not _theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "UI components not fully initialized for prompts dialog.")
        return

    _show_temporary_status_message_func("⏳ Opening LLM prompt templates dialog...")
    llm_dialogs.show_edit_prompts_dialog(
        root_window=_root_window,
        theme_setting_getter_func=_theme_setting_getter_func,
        current_prompts=get_current_prompts(),
        default_prompts=_global_default_prompts, # Pass the master defaults for the "Restore" button
        on_save_callback=update_prompts
    )