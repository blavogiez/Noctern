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
# Construct an absolute path to the prompts file to avoid CWD issues.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROMPTS_FILE = os.path.join(_SCRIPT_DIR, "default_prompts.json")
_global_default_prompts = {} # Loaded once at startup

# --- State managed by this service ---
_llm_keywords_list = []  # Stores user-defined LLM keywords.
_prompt_history_list = [] # Stores tuples: (user_prompt, llm_response)
_completion_prompt_template = "" # Loaded per-file
_generation_prompt_template = "" # Loaded per-file
_latex_code_generation_prompt_template = "" # NEW: Loaded per-file for LaTeX code

def _load_global_default_prompts():
    """Loads the master default prompts from the default_prompts.json file."""
    global _global_default_prompts
    try:
        with open(DEFAULT_PROMPTS_FILE, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            # Add a check to ensure the loaded data is a dictionary with content.
            # An empty file or a file with just "{}" would cause issues.
            if not isinstance(loaded_data, dict) or not loaded_data:
                raise json.JSONDecodeError("File is empty or not a valid dictionary.", "", 0)
            _global_default_prompts = loaded_data
            # NEW: Print loaded prompts to console for verification at startup
            print("="*50)
            print(f"Successfully loaded default prompts from: {os.path.basename(DEFAULT_PROMPTS_FILE)}")
            for key, value in _global_default_prompts.items():
                # Truncate and remove newlines for clean console output
                print(f"  - {key}: '{value[:70].replace(chr(10), ' ')}...'")
            print("="*50)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        filename = os.path.basename(DEFAULT_PROMPTS_FILE)
        print(f"WARNING: Could not load {filename}. Using hardcoded defaults. {e}")
        _global_default_prompts = {
            "completion": "Complete this: {current_phrase_start}",
            "generation": "Generate text for this prompt: {user_prompt}",
            "latex_code_generation": "You are a LaTeX coding assistant embedded within a LaTeX editor. Your task is to generate valid LaTeX code that fulfills the user's instruction.\n\n**Primary Goal:**\nProduce syntactically correct and logically coherent LaTeX code that integrates cleanly with the surrounding context.\n\n**Key Instructions:**\n- **Output only LaTeX code.** Do not include any explanatory text, comments, or formatting outside the LaTeX syntax.\n- Ensure that all commands and environments are properly opened and closed.\n- Use appropriate LaTeX packages if implied by the context (e.g., `amsmath`, `graphicx`, `tikz`).\n- Match the **language** and **style** of the surrounding context.\n- Be concise and avoid unnecessary boilerplate unless requested.\n- Maintain compatibility with standard LaTeX compilers.\n\n**Context (existing LaTeX code around the cursor):**\n---\n{context}\n---\n\n**User's Instruction:**\n\"{user_prompt}\"\n\n**Keywords:**\n{keywords}\n\n**Generated LaTeX code:"
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
    # load_generation_history_for_current_file() # REMOVED: This feature is now disabled.
    load_keywords_for_current_file() # NEW: Load keywords on service initialization
    load_prompts_for_current_file()

def _get_active_tex_filepath(): # Renamed from _get_active_tex_filepath to _get_active_tex_filepath
    """Helper to safely get the current .tex file path using the provided getter."""
    if _active_filepath_getter_func:
        return _active_filepath_getter_func()
    return None

# --- Generation History Management (REMOVED) ---
def load_generation_history_for_current_file():
    """
    (This feature is now disabled)
    Loads the generation history for the current file and applies styling
    by searching for the saved text content in the editor.
    """
    pass

def _add_entry_to_generation_history_and_save(content):
    """(This feature is now disabled) Internal helper to add a new entry and save the generation history."""
    pass

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
    """Internal helper to add a new entry and save the history. (Now accepts optional response_placeholder)"""
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
    global _completion_prompt_template, _generation_prompt_template, _latex_code_generation_prompt_template
    active_filepath = _get_active_tex_filepath()
    # The logic to load or create is handled by the prompt manager, using the globally loaded defaults.
    loaded_prompts = llm_prompt_manager.load_prompts_from_file(active_filepath, _global_default_prompts)
    # Use .get() for robustness, in case a prompt file is malformed but still valid JSON.
    _completion_prompt_template = loaded_prompts.get("completion", "")
    _generation_prompt_template = loaded_prompts.get("generation", "")
    # Also load the latex code generation prompt.
    _latex_code_generation_prompt_template = loaded_prompts.get("latex_code_generation", "")

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

        _generation_ui.cleanup(is_accept=not discard_text)
        _generation_ui = None
        return generated_text

    _generation_thread = None
    return ""

def _execute_llm_generation(full_llm_prompt, user_prompt_for_history, model_name=llm_api_client.DEFAULT_LLM_MODEL, text_for_completion_cleanup=None):
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
        # Before cleaning up the UI, which will destroy the marks, get their positions.
        start_index = _generation_ui.get_start_index()
        end_index = _generation_ui.get_end_index()

        # This gets the raw text from the editor and cleans up the UI (removes buttons, etc.)
        # but leaves the text in place because discard_text=False.
        raw_generated_text = _cancel_current_generation(discard_text=False)

        final_text = raw_generated_text
        # If this was a completion task, clean up any repeated text from the prompt.
        if text_for_completion_cleanup:
            final_text = llm_utils.remove_prefix_overlap_from_completion(
                text_before_completion=text_for_completion_cleanup,
                llm_generated_completion=raw_generated_text
            )
            # If the text was changed, we need to update the editor content.
            if final_text != raw_generated_text and editor:
                editor.delete(start_index, end_index)
                editor.insert(start_index, final_text)

        # NEW: Print prompt and response to console for validation
        print("="*80)
        print(f"[LLM Generation Accepted]")
        print(f"  PROMPT SENT TO API:\n---\n{full_llm_prompt}\n---")
        print(f"  LLM RESPONSE:\n---\n{final_text}\n---")
        print("="*80)

        _show_temporary_status_message_func("✅ Generation accepted.")
        _update_history_response_and_save(user_prompt_for_history, final_text)

    def on_rephrase(text_to_rephrase):
        _cancel_current_generation(discard_text=True) # Cleanup UI, ignore return value
        rephrase_user_prompt = f"Rephrase the following text: \"{text_to_rephrase}\""
        rephrase_full_prompt = _generation_prompt_template.format(
            user_prompt=rephrase_user_prompt,
            keywords=', '.join(_llm_keywords_list),
            context="" # No context for rephrasing
        )
        _add_entry_to_history_and_save(rephrase_user_prompt)
        _execute_llm_generation(rephrase_full_prompt, rephrase_user_prompt)

    def on_cancel(): # Renamed from on_cancel to on_cancel
        _cancel_current_generation(discard_text=True) # Cleanup UI, ignore return value
        _show_temporary_status_message_func("❌ Generation cancelled.")
        _update_history_response_and_save(user_prompt_for_history, "❌ Cancelled by user.")

    _generation_ui.accept_callback = on_accept
    _generation_ui.rephrase_callback = on_rephrase
    _generation_ui.cancel_callback = on_cancel

    def run_thread(prompt, ui_controller, cancel_event, user_prompt_key):
        try: # Renamed from run_thread to run_thread
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
    _generation_ui.show_generating_state() # Renamed from show_generating_state to show_generating_state
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

    # For consistency with the generation dialog, use a shorter, more readable
    # prompt for the history. The full prompt is still sent to the API.
    # We also truncate the phrase to avoid overly long history entries.
    user_prompt_for_history = f"Complete: \"{current_phrase_start.strip()[:60]}...\""
    _add_entry_to_history_and_save(user_prompt_for_history)
    _execute_llm_generation(full_llm_prompt, user_prompt_for_history, text_for_completion_cleanup=current_phrase_start)

# --- LLM Text Generation via Dialog ---
def open_generate_text_dialog(initial_prompt_text=None):
    """ # Renamed from open_generate_text_dialog to open_generate_text_dialog
    Opens a dialog for the user to input a custom prompt for LLM text generation.
    Manages the process of getting user input, calling the LLM, and updating history.
    """
    editor = _active_editor_getter_func()
    if not editor or not _root_window or not _llm_progress_bar_widget or not _theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "LLM Service or UI components not fully initialized.")
        return

    _show_temporary_status_message_func("⏳ Opening LLM generation dialog...")
    # The callback now accepts the is_latex_oriented boolean
    def _handle_generation_request_from_dialog(user_prompt, lines_before, lines_after, is_latex_oriented):
        """Callback for when the dialog requests generation. Runs in main thread initially."""

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
            context=context
        )
        _execute_llm_generation(full_llm_prompt, user_prompt, model_name=model_to_use)

    def _handle_history_entry_add_from_dialog(user_prompt, is_latex_oriented):
        """Callback to add 'Generating...' to history when dialog's Generate is clicked."""
        placeholder = "⏳ Generating LaTeX code..." if is_latex_oriented else "⏳ Generating..."
        _add_entry_to_history_and_save(user_prompt, placeholder)

    # Show the dialog
    llm_dialogs.show_generate_text_dialog( # Reusing the same dialog for now
        root_window=_root_window,
        theme_setting_getter_func=_theme_setting_getter_func,
        current_prompt_history_list=_prompt_history_list,
        on_generate_request_callback=_handle_generation_request_from_dialog, # Now handles both types
        on_history_entry_add_callback=_handle_history_entry_add_from_dialog,
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
        "generation": _generation_prompt_template,
        "latex_code_generation": _latex_code_generation_prompt_template # NEW
    }

def update_prompts(completion_template, generation_template, latex_code_generation_template):
    """Updates the prompt templates and saves them to a custom file."""
    global _completion_prompt_template, _generation_prompt_template, _latex_code_generation_prompt_template
    _latex_code_generation_prompt_template = latex_code_generation_template # NEW
    _completion_prompt_template = completion_template
    _generation_prompt_template = generation_template

    # Save to file
    active_filepath = _get_active_tex_filepath()
    if active_filepath:
        prompts_to_save = {
            "completion": _completion_prompt_template, # Renamed from completion to completion
            "generation": _generation_prompt_template, # Renamed from generation to generation
            "latex_code_generation": _latex_code_generation_prompt_template # NEW
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
        current_prompts=get_current_prompts(), # Renamed from current_prompts to current_prompts
        default_prompts=_global_default_prompts, # Pass the master defaults for the "Restore" button
        on_save_callback=update_prompts
    )