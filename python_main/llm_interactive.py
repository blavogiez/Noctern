import llm_state
import tkinter as tk
import datetime
import interface


def show_llm_buttons(editor, insert_index):
    """Public API to create and show the LLM interaction buttons at the given index."""
    _create_buttons_frame(editor, insert_index)


def _create_buttons_frame(editor, insert_index):
    """Creates and places the LLM interaction buttons frame."""
    # First, ensure any old frame is gone.
    _destroy_buttons_frame(editor)

    current_tab = interface.get_current_tab()
    if not current_tab or not editor:
        return

    buttons_frame = tk.Frame(editor, bg="#f0f0f0", bd=1, relief=tk.RIDGE)

    accept_button = tk.Button(buttons_frame, text="Accept", command=accept_generated_text)
    rephrase_button = tk.Button(buttons_frame, text="Rephrase", command=rephrase_generated_text)
    discard_button = tk.Button(buttons_frame, text="Discard", command=discard_generated_text)

    accept_button.pack(side=tk.LEFT, padx=2)
    rephrase_button.pack(side=tk.LEFT, padx=2)
    discard_button.pack(side=tk.LEFT, padx=2)

    # Position the buttons frame relative to the insert index
    try:
        bbox = editor.bbox(insert_index)
        if bbox:
            x, y, width, height = bbox
            buttons_frame.place(x=x, y=y + height + 2)
        else:
            buttons_frame.place(x=5, y=20)
    except Exception:
        buttons_frame.place(x=5, y=20)

    current_tab.llm_buttons_frame = buttons_frame
    return buttons_frame


def _destroy_buttons_frame(editor):
    """Destroys the LLM interaction buttons frame."""
    current_tab = interface.get_current_tab()
    if current_tab and getattr(current_tab, "llm_buttons_frame", None):
        current_tab.llm_buttons_frame.destroy()
        current_tab.llm_buttons_frame = None


def update_button_position(event=None):
    current_tab = interface.get_current_tab()
    if current_tab and getattr(current_tab, "llm_buttons_frame", None):
        editor = current_tab.editor
        if editor and llm_state._generated_text_range:
            try:
                bbox = editor.bbox(llm_state._generated_text_range[1])
                if bbox:
                    x, y, width, height = bbox
                    current_tab.llm_buttons_frame.place(x=x, y=y + height + 2)
            except Exception:
                pass


def clear_generated_text_state():
    current_tab = interface.get_current_tab()
    if current_tab:
        editor = current_tab.editor
        if editor and llm_state._generated_text_range:
            editor.tag_remove("llm_generated_text", llm_state._generated_text_range[0], llm_state._generated_text_range[1])
        _destroy_buttons_frame(editor)
    llm_state._generated_text_range = None
    llm_state._is_generating = False


def accept_generated_text(event=None):
    if llm_state._is_generating:
        return "break"
    if llm_state._generated_text_range:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Accepted LLM generated text.")
        clear_generated_text_state()
        # Remove focus from buttons and set it back to the editor if needed
        current_tab = interface.get_current_tab()
        if current_tab:
            current_tab.editor.focus_set()
        return "break"
    return None


def discard_generated_text(event=None):
    if llm_state._is_generating:
        return "break"
    if llm_state._generated_text_range:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Discarded LLM generated text.")
        current_tab = interface.get_current_tab()
        if current_tab:
            editor = current_tab.editor
            if editor:
                editor.delete(llm_state._generated_text_range[0], llm_state._generated_text_range[1])
            clear_generated_text_state()
            # Remove focus from buttons and set it back to the editor if needed
            current_tab.editor.focus_set()
        return "break"
    return None


def rephrase_generated_text(event=None):
    if llm_state._is_generating:
        return "break"
    if llm_state._generated_text_range:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Rephrasing LLM generated text.")
        # Local imports to prevent circular dependency
        import llm_completion
        import llm_generation

        discard_generated_text()

        # Now, trigger a new request based on the last action
        if llm_state._last_llm_action_type == "completion" and llm_state._last_completion_phrase_start is not None:
            llm_completion.request_llm_to_complete_text()
        elif llm_state._last_llm_action_type == "generation" and llm_state._last_generation_user_prompt is not None:
            llm_generation.open_generate_text_dialog(initial_prompt_text=llm_state._last_generation_user_prompt)
        else:
            interface.show_temporary_status_message("No previous LLM action to rephrase.")
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} WARNING: No previous LLM action to rephrase.")

        return "break"
    return None
