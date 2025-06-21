# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\llm_service.py
"""
Service layer for LLM (Large Language Model) functionalities.

This module coordinates interactions between the UI, LLM API client,
prompt history management, utility functions, and dialogs. It provides
the main entry points for LLM features like text completion, generation,
and keyword management.
"""
import tkinter as tk
from tkinter import messagebox # ttk is used by progressbar if not passed directly
import os
import interface # NEW: Import interface for status messages
import json
import threading

# Import newly created local modules
import llm_prompt_history
import llm_utils
import llm_api_client
import llm_dialogs
import llm_prompt_manager # NEW

# --- Module-level variables to store references from the main application ---
_editor_widget = None
_root_window = None
_llm_progress_bar_widget = None
_theme_setting_getter_func = None
_current_file_path_getter_func = None # Function to get current .tex file path

# --- Prompt Configuration ---
DEFAULT_PROMPTS_FILE = "default_prompts.json"
_global_default_prompts = {} # Loaded once at startup

# --- State managed by this service ---
_llm_keywords_list = []  # Stores user-defined LLM keywords.
_prompt_history_list = [] # Stores tuples: (user_prompt, llm_response)
_completion_prompt_template = "" # Loaded per-file
_generation_prompt_template = "" # Loaded per-file

def initialize_llm_service(editor_widget_ref, root_window_ref, progress_bar_widget_ref,
                           theme_setting_getter_callback, current_file_path_getter_callback):
    """
    Initializes the LLM service with necessary references from the main application.
    This should be called once when the application starts.
    """
    global _editor_widget, _root_window, _llm_progress_bar_widget
    global _theme_setting_getter_func, _current_file_path_getter_func

    _editor_widget = editor_widget_ref
    _root_window = root_window_ref
    _llm_progress_bar_widget = progress_bar_widget_ref
    _theme_setting_getter_func = theme_setting_getter_callback
    _current_file_path_getter_func = current_file_path_getter_callback

    # Load the master default prompts from the JSON file at startup
    _load_global_default_prompts()

    # Load initial prompt history and custom prompts
    load_prompt_history_for_current_file()
    load_prompts_for_current_file()

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
        messagebox.showerror("Critical Error", f"Could not load default prompts from {DEFAULT_PROMPTS_FILE}. Using basic fallbacks.")

def _get_active_tex_filepath():
    """Helper to safely get the current .tex file path using the provided getter."""
    if _current_file_path_getter_func:
        return _current_file_path_getter_func()
    return None

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


# --- LLM Text Completion ---
def request_llm_to_complete_text():
    """Requests sentence completion from the LLM based on preceding text."""
    if not _editor_widget or not _root_window or not _llm_progress_bar_widget:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized.")
        return

    def run_completion_thread_target():
        """Target function for the LLM completion thread."""
        try:
            # Get context: 30 lines backwards, 0 forwards
            context = llm_utils.extract_editor_context(_editor_widget, lines_before_cursor=30, lines_after_cursor=0)

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

            api_response = llm_api_client.request_llm_generation(full_llm_prompt)

            if api_response["success"]:
                completion_raw = api_response["data"].strip('"')
                cleaned_completion = llm_utils.remove_prefix_overlap_from_completion(current_phrase_start, completion_raw)
                _editor_widget.after(0, lambda: _editor_widget.insert(tk.INSERT, cleaned_completion))
            else:
                _editor_widget.after(0, lambda: messagebox.showerror("LLM Completion Error", api_response["error"]))
        except Exception as e:
            _editor_widget.after(0, lambda: messagebox.showerror("LLM Completion Error", f"An unexpected error occurred: {str(e)}"))
        finally:
            if _llm_progress_bar_widget and _editor_widget: # Check if widgets still exist
                _editor_widget.after(0, lambda: _llm_progress_bar_widget.pack_forget())
                _editor_widget.after(0, lambda: _llm_progress_bar_widget.stop())

    _llm_progress_bar_widget.pack(pady=2)
    _llm_progress_bar_widget.start(10)
    threading.Thread(target=run_completion_thread_target, daemon=True).start()

# --- LLM Text Generation via Dialog ---
def open_generate_text_dialog(initial_prompt_text=None):
    """
    Opens a dialog for the user to input a custom prompt for LLM text generation.
    Manages the process of getting user input, calling the LLM, and updating history.
    """
    if not _editor_widget or not _root_window or not _llm_progress_bar_widget or not _theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "LLM Service or UI components not fully initialized.")
        return

    def _handle_generation_request_from_dialog(user_prompt, lines_before, lines_after):
        """Callback for when the dialog requests generation. Runs in main thread initially."""

        def run_generation_thread_target(local_user_prompt, local_lines_before, local_lines_after):
            """Target function for the LLM generation thread."""
            try:
                context = llm_utils.extract_editor_context(_editor_widget, local_lines_before, local_lines_after)
                full_llm_prompt = _generation_prompt_template.format(
                    user_prompt=local_user_prompt,
                    keywords=', '.join(_llm_keywords_list),
                    context=context
                )
                api_response = llm_api_client.request_llm_generation(full_llm_prompt)

                if api_response["success"]:
                    generated_text = api_response["data"]
                    _editor_widget.after(0, lambda: _editor_widget.insert(tk.INSERT, generated_text))
                    _editor_widget.after(0, lambda: _update_history_response_and_save(local_user_prompt, generated_text))
                else:
                    error_msg = api_response["error"]
                    _editor_widget.after(0, lambda: messagebox.showerror("LLM Generation Error", error_msg))
                    _editor_widget.after(0, lambda: _update_history_response_and_save(local_user_prompt, f"❌ Error: {error_msg[:100]}..."))
            except Exception as e:
                error_str = str(e)
                _editor_widget.after(0, lambda: messagebox.showerror("LLM Generation Error", f"An unexpected error occurred: {error_str}"))
                _editor_widget.after(0, lambda: _update_history_response_and_save(local_user_prompt, f"❌ Exception: {error_str[:100]}..."))
            finally:
                if _llm_progress_bar_widget and _editor_widget: # Check if widgets still exist
                    _editor_widget.after(0, lambda: _llm_progress_bar_widget.pack_forget())
                    _editor_widget.after(0, lambda: _llm_progress_bar_widget.stop())

        _llm_progress_bar_widget.pack(pady=2)
        _llm_progress_bar_widget.start(10)
        threading.Thread(target=run_generation_thread_target, args=(user_prompt, lines_before, lines_after), daemon=True).start()

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
        return

    def _handle_keywords_save_from_dialog(new_keywords_list):
        """Callback for when the keywords dialog saves."""
        global _llm_keywords_list
        _llm_keywords_list = new_keywords_list
        if not _llm_keywords_list:
            messagebox.showinfo("Keywords Cleared", "LLM keywords list has been cleared.", parent=_root_window) # Parent might need to be dialog
        else:
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
        prompts_filename = os.path.basename(llm_prompt_manager.get_prompts_filepath(active_filepath))
        interface.show_temporary_status_message(f"✅ Prompts saved: {prompts_filename}")
    else:
        interface.show_temporary_status_message("⚠️ Prompts updated for this session only (no file open).") # Use temporary status

def open_edit_prompts_dialog():
    """Opens a dialog to edit the LLM prompt templates."""
    if not _root_window or not _theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "UI components not fully initialized for prompts dialog.")
        return

    llm_dialogs.show_edit_prompts_dialog(
        root_window=_root_window,
        theme_setting_getter_func=_theme_setting_getter_func,
        current_prompts=get_current_prompts(),
        default_prompts=_global_default_prompts, # Pass the master defaults for the "Restore" button
        on_save_callback=update_prompts
    )