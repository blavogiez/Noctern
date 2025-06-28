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
import datetime # NEW: Import datetime for timestamps

# Import newly created local modules
import llm_prompt_history
import llm_utils
import llm_api_client
import llm_dialogs
import llm_prompt_manager # NEW

# --- Module-level variables to store references from the main application ---
_root_window = None
_llm_progress_bar_widget = None
_theme_setting_getter_func = None
_active_editor_getter_func = None # Function to get the active tk.Text widget
_active_filepath_getter_func = None # Function to get current .tex file path

# --- Prompt Configuration ---
_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROMPTS_FILE = os.path.join(_SERVICE_DIR, "default_prompts.json")
_global_default_prompts = {} # Loaded once at startup

# --- State managed by this service ---
_llm_keywords_list = []  # Stores user-defined LLM keywords.
_prompt_history_list = [] # Stores tuples: (user_prompt, llm_response)
_completion_prompt_template = "" # Loaded per-file
_generation_prompt_template = "" # Loaded per-file

# NEW: State for interactive LLM generation
_generated_text_range = None # Stores (start_index, end_index) of the currently highlighted text
_is_generating = False # Flag to prevent new generations while one is active
_last_llm_action_type = None # "completion" or "generation"
_last_completion_phrase_start = None # For rephrasing completion
_last_generation_user_prompt = None # For rephrasing generation
_last_generation_lines_before = None # For rephrasing generation
_last_generation_lines_after = None # For rephrasing generation

def _load_global_default_prompts():
    """Loads the master default prompts from the default_prompts.json file."""
    global _global_default_prompts
    try:
        with open(DEFAULT_PROMPTS_FILE, 'r', encoding='utf-8') as f:
            _global_default_prompts = json.load(f)
        print(f"INFO: Successfully loaded global default prompts from {DEFAULT_PROMPTS_FILE}.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"CRITICAL ERROR: Could not load {DEFAULT_PROMPTS_FILE}. {e}")
        _global_default_prompts = {
            "completion": "Complete this: {current_phrase_start}",
            "generation": "Generate text for this prompt: {user_prompt}"
        }
        # Cannot show messagebox here as Tk root may not exist yet.
        # The error will be printed to the console.

def initialize_llm_service(root_window_ref, progress_bar_widget_ref,
                           theme_setting_getter_func, active_editor_getter, active_filepath_getter):
    """
    Initializes the LLM service with necessary references from the main application.
    This should be called once when the application starts.
    """
    global _root_window, _llm_progress_bar_widget
    global _theme_setting_getter_func, _active_editor_getter_func, _active_filepath_getter_func

    _root_window = root_window_ref
    _llm_progress_bar_widget = progress_bar_widget_ref
    _theme_setting_getter_func = theme_setting_getter_func
    _active_editor_getter_func = active_editor_getter
    _active_filepath_getter_func = active_filepath_getter

    # Bind global interaction keys
    _root_window.bind_all("<Tab>", accept_generated_text)
    _root_window.bind_all("r", rephrase_generated_text) # 'r' for rephrase
    _root_window.bind_all("c", discard_generated_text) # 'c' for cancel/discard

    # Load initial prompt history and custom prompts
    load_prompt_history_for_current_file()
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
    if active_filepath:
        print(f"INFO: Loaded prompts for '{os.path.basename(active_filepath)}'.")
    else:
        print("INFO: Loaded prompts for current session (no file open).")
    _completion_prompt_template = loaded_prompts["completion"]
    _generation_prompt_template = loaded_prompts["generation"]

# NEW: Helper to update the end index of the generated text range
def _update_generated_text_end_index(editor):
    """Updates the end index of the currently tracked generated text range."""
    global _generated_text_range
    if _generated_text_range:
        _generated_text_range = (_generated_text_range[0], editor.index(tk.INSERT))

# NEW: Functions for interactive LLM generation
def _clear_generated_text_state():
    """Clears the state related to the currently generated text."""
    global _generated_text_range, _is_generating
    active_editor = _active_editor_getter_func()
    if active_editor and _generated_text_range:
        # Remove the highlight tag
        active_editor.tag_remove("llm_generated_text", _generated_text_range[0], _generated_text_range[1])
    _generated_text_range = None
    _is_generating = False # Generation is no longer active for user interaction

def accept_generated_text(event=None):
    """Accepts the currently generated text, removing its highlight."""
    if _is_generating: # Don't accept if still generating
        return "break" # Consume event
    if _generated_text_range:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Accepted LLM generated text.")
        _clear_generated_text_state()
        return "break" # Consume event
    return None # Let event propagate if no generated text

def discard_generated_text(event=None):
    """Discards the currently generated text, deleting it from the editor."""
    if _is_generating: # Don't discard if still generating
        return "break" # Consume event
    if _generated_text_range:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Discarded LLM generated text.")
        active_editor = _active_editor_getter_func()
        if active_editor:
            active_editor.delete(_generated_text_range[0], _generated_text_range[1])
        _clear_generated_text_state()
        return "break" # Consume event
    return None # Let event propagate

def rephrase_generated_text(event=None):
    """Discards the current generated text and attempts to rephrase/regenerate."""
    if _is_generating: # Don't rephrase if still generating
        return "break" # Consume event
    if _generated_text_range:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Rephrasing LLM generated text.")
        discard_generated_text() # Discard current text first

        if _last_llm_action_type == "completion" and _last_completion_phrase_start is not None:
            request_llm_to_complete_text()
        elif _last_llm_action_type == "generation" and _last_generation_user_prompt is not None:
            open_generate_text_dialog(initial_prompt_text=_last_generation_user_prompt)
        else:
            interface.show_temporary_status_message("No previous LLM action to rephrase.")
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} WARNING: No previous LLM action to rephrase.")
        return "break" # Consume event
    return None # Let event propagate

# --- Call the loader at module import time to ensure defaults are always available ---
_load_global_default_prompts()


# --- LLM Text Completion ---
def request_llm_to_complete_text():
    """Requests sentence completion from the LLM based on preceding text."""
    global _is_generating, _last_llm_action_type, _last_completion_phrase_start
    editor = _active_editor_getter_func()
    if not editor or not _root_window or not _llm_progress_bar_widget:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized.")
        return

    if _is_generating:
        interface.show_temporary_status_message("LLM is already generating. Please wait or interact with current generation.")
        return

    # Clear any previous generated text state before starting a new one
    _clear_generated_text_state()
    _is_generating = True
    _last_llm_action_type = "completion"

    def run_completion_thread_target():
        """Target function for the LLM completion thread."""
        active_editor = _active_editor_getter_func() # Get it again inside thread
        if not active_editor: # Editor might have been closed
            _clear_generated_text_state()
            return

        try:
            # Record the starting point for generated text
            start_index = active_editor.index(tk.INSERT)
            global _generated_text_range
            _generated_text_range = (start_index, start_index) # Initialize range

            # Get context: 30 lines backwards, 0 forwards
            context = llm_utils.extract_editor_context(active_editor, lines_before_cursor=30, lines_after_cursor=0)

            # Find the last sentence ending to isolate the current sentence fragment
            last_dot_index = max(context.rfind("."), context.rfind("!"), context.rfind("?"))
            if last_dot_index == -1:
                current_phrase_start = context.strip()
                previous_context = ""
            else:
                current_phrase_start = context[last_dot_index + 1:].strip()
                previous_context = context[:last_dot_index + 1].strip()
            
            _last_completion_phrase_start = current_phrase_start # Store for rephrase

            # Construct the prompt for the LLM API
            full_llm_prompt = _completion_prompt_template.format(
                previous_context=previous_context,
                current_phrase_start=current_phrase_start,
                keywords=', '.join(_llm_keywords_list)
            )

            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Completion Request - Prompt: '{full_llm_prompt[:200]}...'")

            final_api_response_status = {"success": False, "error": "No response received."}
            full_generated_text = "" # Initialize to empty string
            # Iterate over the streamed response
            for api_response_chunk in llm_api_client.request_llm_generation(full_llm_prompt):
                if api_response_chunk["success"]:
                    if "chunk" in api_response_chunk:
                        chunk = api_response_chunk["chunk"]
                        full_generated_text += chunk
                        # Insert chunk into editor on the main thread
                        active_editor.after(0, lambda c=chunk: active_editor.insert(tk.INSERT, c, "llm_generated_text"))
                        # Update the end index of the generated text range
                        active_editor.after(0, lambda: _update_generated_text_end_index(active_editor))
                    if api_response_chunk.get("done"):
                        final_api_response_status = api_response_chunk # Store the final status
                        break # Exit loop, generation is done
                else:
                    # Handle error during streaming
                    final_api_response_status = api_response_chunk # Store the error status
                    error_msg = api_response_chunk["error"]
                    active_editor.after(0, lambda: messagebox.showerror("LLM Completion Error", error_msg))
                    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ERROR: LLM Completion Response - Failed: {final_api_response_status['error']}")
                    _clear_generated_text_state() # Clear state on error
                    return # Stop processing on error

            # After the loop, process the full generated text for history and final cleaning
            if final_api_response_status["success"]:
                completion_raw = full_generated_text.strip('"')
                cleaned_completion = llm_utils.remove_prefix_overlap_from_completion(current_phrase_start, completion_raw)

                def _replace_with_cleaned_text(start_idx, end_idx, cleaned_text):
                    editor = _active_editor_getter_func()
                    if editor and editor.winfo_exists():
                        editor.delete(start_idx, end_idx)
                        editor.insert(start_idx, cleaned_text, "llm_generated_text")
                        global _generated_text_range
                        new_end_idx = editor.index(f"{start_idx} + {len(cleaned_text)} chars")
                        _generated_text_range = (start_idx, new_end_idx)

                if _generated_text_range:
                    active_editor.after(0, lambda: _replace_with_cleaned_text(
                        _generated_text_range[0], _generated_text_range[1], cleaned_completion
                    ))
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Completion Response - Success. Generated: '{cleaned_completion[:200]}...'")
            else:
                # Error already handled and printed inside the loop, but ensure final log if no chunks were received
                if not full_generated_text:
                    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ERROR: LLM Completion Response - No text generated due to error: {final_api_response_status.get('error', 'Unknown error')}")
            
        except Exception as e:
            active_editor.after(0, lambda: messagebox.showerror("LLM Completion Error", f"An unexpected error occurred: {str(e)}"))
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} CRITICAL ERROR: LLM Completion Exception: {str(e)}")
        finally:
            # Generation finished, allow interaction
            global _is_generating
            _is_generating = False
            if _llm_progress_bar_widget and active_editor: # Check if widgets still exist
                active_editor.after(0, lambda: _llm_progress_bar_widget.pack_forget())
                active_editor.after(0, lambda: _llm_progress_bar_widget.stop())

    _llm_progress_bar_widget.pack(pady=2)
    _llm_progress_bar_widget.start(10)
    threading.Thread(target=run_completion_thread_target, daemon=True).start()

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

    def _handle_generation_request_from_dialog(user_prompt, lines_before, lines_after):
        """Callback for when the dialog requests generation. Runs in main thread initially."""
        global _is_generating, _last_llm_action_type, _last_generation_user_prompt, _last_generation_lines_before, _last_generation_lines_after

        if _is_generating:
            interface.show_temporary_status_message("LLM is already generating. Please wait or interact with current generation.")
            return

        # Clear any previous generated text state before starting a new one
        _clear_generated_text_state()
        _is_generating = True
        _last_llm_action_type = "generation"
        _last_generation_user_prompt = user_prompt
        _last_generation_lines_before = lines_before
        _last_generation_lines_after = lines_after

        def run_generation_thread_target(local_user_prompt, local_lines_before, local_lines_after):
            """Target function for the LLM generation thread."""
            active_editor = _active_editor_getter_func() # Get it again inside thread
            if not active_editor: # Editor might have been closed
                _clear_generated_text_state()
                return

            try:
                # Record the starting point for generated text
                start_index = active_editor.index(tk.INSERT)
                global _generated_text_range
                _generated_text_range = (start_index, start_index) # Initialize range

                context = llm_utils.extract_editor_context(active_editor, local_lines_before, local_lines_after)
                full_llm_prompt = _generation_prompt_template.format(
                    user_prompt=local_user_prompt,
                    keywords=', '.join(_llm_keywords_list),
                    context=context
                )

                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Generation Request - Prompt: '{full_llm_prompt[:200]}...'")

                final_api_response_status = {"success": False, "error": "No response received."}
                full_generated_text = "" # Initialize to empty string
                # Iterate over the streamed response
                for api_response_chunk in llm_api_client.request_llm_generation(full_llm_prompt):
                    if api_response_chunk["success"]:
                        if "chunk" in api_response_chunk:
                            chunk = api_response_chunk["chunk"]
                            full_generated_text += chunk
                            # Insert chunk into editor on the main thread
                            active_editor.after(0, lambda c=chunk: active_editor.insert(tk.INSERT, c, "llm_generated_text"))
                            # Update the end index of the generated text range
                            active_editor.after(0, lambda: _update_generated_text_end_index(active_editor))
                        if api_response_chunk.get("done"):
                            final_api_response_status = api_response_chunk # Store the final status
                            break # Exit loop, generation is done
                    else:
                        # Handle error during streaming
                        final_api_response_status = api_response_chunk # Store the error status
                        error_msg = api_response_chunk["error"]
                        active_editor.after(0, lambda: messagebox.showerror("LLM Generation Error", error_msg))
                        active_editor.after(0, lambda: _update_history_response_and_save(local_user_prompt, f"❌ Error: {error_msg[:100]}..."))
                        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ERROR: LLM Generation Response - Failed: {error_msg}")
                        _clear_generated_text_state() # Clear state on error
                        return # Stop processing on error

                # After the loop, update history with the full generated text
                if final_api_response_status["success"]:
                    if full_generated_text:
                        active_editor.after(0, lambda: _update_history_response_and_save(local_user_prompt, full_generated_text))
                        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Generation Response - Success. Generated: '{full_generated_text[:200]}...'")
                    else:
                        active_editor.after(0, lambda: _update_history_response_and_save(local_user_prompt, "No text generated."))
                        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM Generation Response - No text generated.")
                else:
                    # Error already handled and printed inside the loop
                    pass
                
            except Exception as e:
                error_str = str(e)
                active_editor.after(0, lambda: messagebox.showerror("LLM Generation Error", f"An unexpected error occurred: {error_str}"))
                active_editor.after(0, lambda: _update_history_response_and_save(local_user_prompt, f"❌ Exception: {error_str[:100]}..."))
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} CRITICAL ERROR: LLM Generation Exception: {error_str}")
                _clear_generated_text_state() # Clear state on exception
            finally:
                # Generation finished, allow interaction
                global _is_generating
                _is_generating = False
                if _llm_progress_bar_widget and active_editor: # Check if widgets still exist
                    active_editor.after(0, lambda: _llm_progress_bar_widget.pack_forget())
                    active_editor.after(0, lambda: _llm_progress_bar_widget.stop())

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
        print(f"INFO: Prompts saved to '{prompts_filename}'.")
    else:
        interface.show_temporary_status_message("⚠️ Prompts updated for this session only (no file open).") # Use temporary status
        print("INFO: Prompts updated for this session only (no file open).")

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
