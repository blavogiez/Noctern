import llm_state
import tkinter as tk
import datetime
import interface

# This module is now drastically simplified and more robust by using `window_create`.

def show_llm_buttons(editor, insert_index):
    """
    Creates and embeds an interactive button frame directly into the text editor
    at the specified index, making it a part of the text flow.
    """
    _destroy_buttons_frame()  # Clear any previous buttons first
    current_tab = interface.get_current_tab()
    if not current_tab or not editor:
        return

    # --- A more compact and modern "pill" style for the button container ---
    buttons_frame = tk.Frame(
        editor,
        bg="#404040",
        bd=1,
        relief=tk.SOLID,
        highlightbackground="#606060",
        highlightcolor="#007bff",
        highlightthickness=1,
    )

    # --- Button styling for a cleaner look ---
    btn_style = {
        "relief": tk.FLAT,
        "bd": 0,
        "fg": "#FFFFFF",
        "font": ("Segoe UI", 9),
        "cursor": "hand2",
        "padx": 10,
        "pady": 3,
        "activeforeground": "#FFFFFF",
    }

    # --- Create Buttons ---
    accept_button = tk.Button(
        buttons_frame, text="Accept", command=accept_generated_text,
        bg="#28a745", activebackground="#218838", **btn_style
    )
    rephrase_button = tk.Button(
        buttons_frame, text="Rephrase", command=rephrase_generated_text,
        bg="#17a2b8", activebackground="#138496", **btn_style
    )
    discard_button = tk.Button(
        buttons_frame, text="Discard", command=discard_generated_text,
        bg="#dc3545", activebackground="#c82333", **btn_style
    )

    # Arrange buttons side-by-side
    accept_button.pack(side=tk.LEFT, padx=(2, 1))
    rephrase_button.pack(side=tk.LEFT, padx=1)
    discard_button.pack(side=tk.LEFT, padx=(1, 2))

    # --- The Core Magic: Embed the button frame into the Text widget ---
    # We create a "window" at the insert_index, containing our buttons_frame.
    # This makes the buttons behave like a character in the text.
    # We add a tag so we can easily find and manage it.
    editor.window_create(insert_index, window=buttons_frame, padx=5, align="center")
    editor.mark_set("llm_buttons_start", insert_index) # Mark the start of the button block

    current_tab.llm_buttons_frame = buttons_frame
    llm_state._generated_text_range = (
        editor.index("llm_buttons_start"),
        editor.index("llm_buttons_start")
    )

def _destroy_buttons_frame():
    """Destroys the buttons frame if it exists."""
    current_tab = interface.get_current_tab()
    if current_tab and getattr(current_tab, "llm_buttons_frame", None):
        try:
            # The frame is destroyed when the text representing it is deleted,
            # but we can also destroy it directly if needed.
            current_tab.llm_buttons_frame.destroy()
        except tk.TclError:
            pass  # Widget might already be gone
        current_tab.llm_buttons_frame = None

# POSITIONING LOGIC IS NO LONGER NEEDED!
# The `_position_buttons_frame` and `update_button_position` functions are removed
# because the Text widget now manages the position automatically.

def clear_generated_text_state():
    """Clear the generated text state and destroy buttons."""
    # We don't need to explicitly destroy the frame here anymore.
    # Discarding/Accepting will delete the text range which includes the buttons.
    llm_state._generated_text_range = None
    llm_state._is_generating = False


def accept_generated_text(event=None):
    """Accept the generated text by simply removing the button controls."""
    if llm_state._is_generating:
        return "break"

    current_tab = interface.get_current_tab()
    if llm_state._generated_text_range and current_tab and current_tab.editor:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Accepted LLM generated text.")
        editor = current_tab.editor
        # Delete only the embedded button window, keeping the text
        button_start_index = editor.index("llm_buttons_start")
        button_end_index = editor.index(f"{button_start_index} + 1 char")
        editor.delete(button_start_index, button_end_index)
        
        clear_generated_text_state()
        editor.focus_set()
        return "break"
    return None


def discard_generated_text(event=None):
    """Discard the entire generated block, including buttons and text."""
    if llm_state._is_generating:
        return "break"
    
    current_tab = interface.get_current_tab()
    if llm_state._generated_text_range and current_tab and current_tab.editor:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Discarded LLM generated text.")
        editor = current_tab.editor
        try:
            # The range now includes the buttons, so deleting it cleans up everything.
            start_index, end_index = llm_state._generated_text_range
            editor.delete(start_index, end_index)
        except tk.TclError:
            pass  # Text/widget might already be gone
        finally:
            clear_generated_text_state()
            editor.focus_set()
        return "break"
    return None


def rephrase_generated_text(event=None):
    """Rephrase the generated text by triggering a new request."""
    if llm_state._is_generating:
        return "break"
    
    if llm_state._generated_text_range:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Rephrasing LLM generated text.")
        import llm_completion
        import llm_generation
        
        # Store the necessary context before discarding the current generation
        last_action_type = llm_state._last_llm_action_type
        last_completion_phrase_start = llm_state._last_completion_phrase_start
        last_generation_user_prompt = llm_state._last_generation_user_prompt
        
        discard_generated_text()
        
        if last_action_type == "completion" and last_completion_phrase_start is not None:
            llm_completion.request_llm_to_complete_text()
        elif last_action_type == "generation" and last_generation_user_prompt is not None:
            llm_generation.open_generate_text_dialog(initial_prompt_text=last_generation_user_prompt)
        else:
            interface.show_temporary_status_message("No previous LLM action to rephrase.")
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} WARNING: No previous LLM action to rephrase.")
        return "break"
    return None


def bind_keyboard_shortcuts(editor):
    """Bind keyboard shortcuts for LLM button actions."""
    editor.bind("<Tab>", accept_generated_text, add='+')
    editor.bind("<Escape>", discard_generated_text, add='+') # Escape is more intuitive for discard

# NOTE: The other key bindings are removed to prevent accidental triggers.
# The user should explicitly use Tab, Escape, or click the buttons.