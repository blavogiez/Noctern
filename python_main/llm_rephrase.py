
"""
This module provides functionality for rephrasing selected text using a Large Language Model (LLM).
It allows users to provide an instruction for rephrasing, sends the request to the LLM,
and displays the rephrased text interactively in the editor.
"""

import llm_state
import llm_utils
import llm_api_client
import tkinter as tk
from tkinter import messagebox
import interface
import llm_interactive
import debug_console
import threading

def open_rephrase_dialog():
    """
    Initiates the rephrasing process for user-selected text in the active editor.

    This function first checks if any text is selected. If so, it extracts the selected
    text and its position, then calls `request_rephrase_for_text` to proceed with
    the rephrasing workflow. If no text is selected, it displays a warning message.
    """
    debug_console.log("Rephrase dialog initiated from text selection.", level='ACTION')
    
    # Ensure the active editor getter function is initialized.
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not initialized: Active editor getter is missing.")
        debug_console.log("Rephrase failed: Active editor getter function is not callable.", level='ERROR')
        return
    
    editor_widget = llm_state._active_editor_getter_func()
    if not editor_widget:
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized: Editor widget is missing.")
        debug_console.log("Rephrase failed: Editor widget is missing.", level='ERROR')
        return

    try:
        # Get the start and end indices of the currently selected text.
        selection_start_index = editor_widget.index(tk.SEL_FIRST)
        selection_end_index = editor_widget.index(tk.SEL_LAST)
        selected_text = editor_widget.get(selection_start_index, selection_end_index)
        debug_console.log(f"User selected text to rephrase: '{selected_text[:80]}...'", level='DEBUG')
    except tk.TclError:
        # Handle case where no text is selected.
        debug_console.log("Rephrase dialog: No text selected by the user.", level='INFO')
        messagebox.showwarning("Rephrase", "Please select text in the editor to rephrase.")
        return

    # Proceed with the rephrasing request for the selected text.
    request_rephrase_for_text(editor_widget, selected_text, selection_start_index, selection_end_index, on_validate_callback=None)

def request_rephrase_for_text(editor, text_to_rephrase, start_index, end_index, on_validate_callback=None):
    """
    Prompts the user for a rephrasing instruction and initiates an interactive LLM rephrase session.

    This function displays a small dialog asking for user instruction. Upon receiving the instruction,
    it constructs an LLM prompt and starts a streaming generation process to rephrase the text.

    Args:
        editor (tk.Text): The Tkinter Text widget where the rephrasing will occur.
        text_to_rephrase (str): The original text that needs to be rephrased.
        start_index (str): The Tkinter index where the original text begins.
        end_index (str): The Tkinter index where the original text ends.
        on_validate_callback (callable, optional): A callback function to execute after the user
                                                  validates the rephrase instruction. This is used
                                                  by `llm_interactive` to clean up the previous session.
                                                  Defaults to None.
    """
    if llm_state._is_generating:
        interface.show_temporary_status_message("LLM is currently generating. Please wait for the current operation to complete.")
        debug_console.log("Rephrase aborted: Another generation process is already in progress.", level='WARNING')
        return

    user_instruction_validated = False # Flag to track if the user provided a valid instruction.

    def _show_instruction_dialog():
        """
        Displays a dialog to get a rephrasing instruction from the user.
        """
        nonlocal user_instruction_validated

        def on_dialog_validate(entry_widget, dialog_window):
            """
            Callback for the instruction dialog's validate button.
            """
            nonlocal user_instruction_validated
            user_instruction = entry_widget.get().strip()
            if not user_instruction:
                messagebox.showwarning("Missing Instruction", "Please enter an instruction for rephrasing.", parent=dialog_window)
                return
            
            user_instruction_validated = True
            dialog_window.destroy() # Close the instruction dialog.
            _handle_rephrase_request(user_instruction) # Proceed with the rephrase request.

        instruction_dialog = tk.Toplevel(llm_state._root_window)
        instruction_dialog.title("Rephrase Text")
        instruction_dialog.transient(llm_state._root_window)
        instruction_dialog.grab_set() # Grab all input until this dialog is closed.
        instruction_dialog.geometry("500x200")
        instruction_dialog.configure(bg=llm_state._theme_setting_getter_func("root_bg", "#f0f0f0"))

        tk.Label(instruction_dialog, text=f"Instruction for rephrasing:\n\"{text_to_rephrase[:80]}...\"", bg=instruction_dialog["bg"]).pack(pady=(10, 5))
        instruction_entry = tk.Entry(instruction_dialog, width=60)
        instruction_entry.pack(padx=10, pady=10, ipady=4)
        instruction_entry.focus_set() # Set initial focus to the entry field.

        validate_button = tk.Button(instruction_dialog, text="Rephrase", command=lambda: on_dialog_validate(instruction_entry, instruction_dialog))
        validate_button.pack(pady=10)
        instruction_dialog.bind("<Return>", lambda e: on_dialog_validate(instruction_entry, instruction_dialog)) # Bind Enter key.
        
        instruction_dialog.wait_window() # Wait for the dialog to be closed.

    def _handle_rephrase_request(user_instruction):
        """
        Constructs the LLM prompt for rephrasing and starts the generation in a new thread.
        """
        debug_console.log(f"Rephrase request validated with instruction: '{user_instruction}'", level='ACTION')
        
        # Execute the provided callback if available (e.g., to clean up previous LLM output).
        if on_validate_callback:
            on_validate_callback()
        else:
            # If no callback, delete the original text from the editor.
            editor.delete(start_index, end_index)

        # Store LLM action type and relevant data for history/re-generation.
        llm_state._last_llm_action_type = "rephrase"
        llm_state._last_generation_user_prompt = user_instruction
        llm_state._last_completion_phrase_start = text_to_rephrase # Using this field to store original text for rephrase.

        # Construct the LLM prompt for rephrasing.
        rephrase_prompt = (
            f"Rephrase the following text according to the user instruction, without changing the meaning, "
            f"and respecting the original language and tone. "
            f"Text to rephrase: \n\"\"\"{text_to_rephrase}\"\"\"\n"
            f"User instruction: {user_instruction}\n"
            f"Respond only with the rephrased text, without explanation or markdown."
        )
        debug_console.log(f"LLM Rephrase Request - Formatted Prompt (first 200 chars): '{rephrase_prompt[:200]}...'", level='INFO')

        # Set the editor's insertion point to where the rephrased text should appear.
        editor.mark_set(tk.INSERT, start_index)
        # Start a new interactive session to handle the streaming LLM response.
        interactive_session_callbacks = llm_interactive.start_new_interactive_session(editor)

        def run_rephrase_thread():
            """
            Target function for the background thread that performs the LLM rephrasing request.
            """
            try:
                # Iterate over chunks received from the LLM API client.
                for api_response_chunk in llm_api_client.request_llm_generation(rephrase_prompt):
                    if api_response_chunk.get("success"):
                        if "chunk" in api_response_chunk:
                            # Schedule UI update on the main thread for each chunk.
                            editor.after(0, lambda chunk=api_response_chunk["chunk"]: interactive_session_callbacks['on_chunk'](chunk))
                        if api_response_chunk.get("done"):
                            # Schedule success callback on the main thread when generation is complete.
                            editor.after(0, interactive_session_callbacks['on_success'])
                            return # Exit the thread.
                    else:
                        # Handle errors received from the API.
                        error_message = api_response_chunk.get("error", "Unknown error during rephrasing.")
                        editor.after(0, lambda: interactive_session_callbacks['on_error'](error_message))
                        return # Exit the thread.
            except Exception as e:
                # Catch any unexpected exceptions during the thread execution.
                error_message = f"An unexpected error occurred in the rephrase thread: {e}"
                debug_console.log(error_message, level='ERROR')
                editor.after(0, lambda: interactive_session_callbacks['on_error'](error_message))

        # Start the rephrasing process in a new daemon thread to keep the UI responsive.
        threading.Thread(target=run_rephrase_thread, daemon=True).start()

    _show_instruction_dialog() # Display the instruction dialog to the user.
    
    # If the user cancelled the instruction dialog, log the cancellation.
    if not user_instruction_validated:
        debug_console.log("Rephrase operation was cancelled by the user (instruction dialog closed).", level='INFO')
