"""
This module is responsible for binding global keyboard shortcuts to various application functionalities.
It centralizes shortcut definitions and provides a logging wrapper for tracking shortcut activations.
"""

import latex_compiler
import llm_service
import latex_translator
import editor_logic
import interface
import llm_rephrase
import debug_console
import editor_snippets

def bind_shortcuts(root):
    """
    Binds all global keyboard shortcuts for the application to their respective functions.

    This function sets up key bindings at the root window level, ensuring that these
    shortcuts are active across the entire application, regardless of which widget
    currently has focus.

    Args:
        root (tk.Tk): The root Tkinter window of the application.
    """
    debug_console.log("Initiating global keyboard shortcut binding.", level='INFO')
    
    def log_and_run(func, name, pass_event=False):
        """
        A wrapper function that logs the execution of a shortcut and then calls the target function.

        This provides a centralized way to log shortcut activations for debugging and monitoring.
        It can optionally pass the Tkinter event object to the wrapped function.

        Args:
            func (callable): The function to be executed when the shortcut is triggered.
            name (str): A descriptive name for the shortcut, used in logging.
            pass_event (bool, optional): If True, the Tkinter event object will be passed
                                         as an argument to `func`. Defaults to False.

        Returns:
            callable: A wrapper function suitable for binding to Tkinter events.
        """
        def wrapper(event=None):
            debug_console.log(f"Keyboard shortcut triggered: {name}", level='ACTION')
            if pass_event:
                func(event)
            else:
                func() 
            return "break" # Prevents the event from propagating further.
        return wrapper

    # Define a dictionary of standard shortcuts that do not require the event object.
    # Each entry maps a Tkinter event string to a tuple: (function_to_call, shortcut_name_for_logging).
    simple_shortcuts = {
        "<Control-n>": (interface.create_new_tab, "New File"),
        "<Control-o>": (interface.open_file, "Open File"),
        "<Control-s>": (interface.save_file, "Save File"),
        "<Control-w>": (interface.close_current_tab, "Close Tab"),
        "<Control-Shift-T>": (interface.restore_last_closed_tab, "Restore Closed Tab"),
        "<Control-Shift-G>": (llm_service.open_generate_text_dialog, "LLM Generate Dialog"),
        "<Control-Shift-C>": (llm_service.request_llm_to_complete_text, "LLM Complete"),
        "<Control-Shift-K>": (llm_service.open_set_keywords_dialog, "Set LLM Keywords"),
        "<Control-Shift-P>": (llm_service.open_edit_prompts_dialog, "Edit LLM Prompts"),
        "<Control-r>": (llm_rephrase.open_rephrase_dialog, "Rephrase Dialog"),
        "<Control-Shift-D>": (latex_compiler.run_chktex_check, "Chktex Check"),
        "<Control-Shift-V>": (interface.paste_image, "Paste Image"),
        "<Control-t>": (latex_translator.open_translate_dialog, "Translate Dialog"),
    }

    # Bind the simple shortcuts using the logging wrapper.
    for key_binding, (function, name) in simple_shortcuts.items():
        root.bind_all(key_binding, log_and_run(function, name, pass_event=False))

    # Special binding for snippet expansion, which requires the event object
    # to determine the text editor context.
    root.bind_all("<Control-space>", log_and_run(editor_snippets.handle_snippet_expansion, "Expand Snippet", pass_event=True))
        
    # Zoom shortcuts are bound separately as they do not need the 'break' return value
    # (they don't interfere with text input directly).
    root.bind_all("<Control-equal>", interface.zoom_in)  # Ctrl + = for zoom in.
    root.bind_all("<Control-minus>", interface.zoom_out) # Ctrl + - for zoom out.

    debug_console.log("All global keyboard shortcuts have been bound.", level='INFO')


def bind_editor_specific_shortcuts(editor_widget):
    """
    Binds shortcuts that are specific to the text editor widget.

    This function is intended to be called for each new editor tab created.
    These shortcuts should only be active when the editor widget has focus.

    Args:
        editor_widget (tk.Text): The Tkinter Text widget to bind the shortcuts to.
    """
    editor_widget.bind("<Control-BackSpace>", lambda event: delete_word_back(editor_widget))
    editor_widget.bind("<Control-d>", lambda event: duplicate_line(editor_widget))
    editor_widget.bind("<Control-y>", lambda event: delete_line(editor_widget))

def delete_word_back(editor):
    """
    Deletes the word immediately preceding the cursor in the text editor.

    This function emulates the common "Ctrl+Backspace" behavior found in many text editors.
    It identifies the start of the word before the cursor and deletes from that point
    up to the cursor's current position.

    Args:
        editor (tk.Text): The Tkinter Text widget where the deletion should occur.
    """
    cursor_index = editor.index(tk.INSERT) # Get the current cursor position.
    # Find the starting position of the word to the left of the cursor.
    # "insert-1c wordstart" moves the index to the beginning of the word before the cursor.
    start_of_word = editor.index(f"{cursor_index}-1c wordstart")
    # Delete the text from the start of the word to the cursor.
    editor.delete(start_of_word, cursor_index)
    debug_console.log(f"Deleted word backwards from cursor position {cursor_index}.", level='ACTION')
    editor.master.on_key_release()
    return "break" # Prevent the default Backspace behavior from also firing.

def duplicate_line(editor):
    """
    Duplicates the current line or selected block of lines.
    """
    if editor.tag_ranges("sel"):
        start, end = editor.index("sel.first"), editor.index("sel.last")
        start_line = int(start.split('.')[0])
        end_line = int(end.split('.')[0])
        if end.split('.')[1] == '0':
            end_line -= 1
        
        lines = editor.get(f"{start_line}.0", f"{end_line}.end")
        editor.insert(f"{end_line}.end", "\n" + lines)
    else:
        line_number = int(editor.index(tk.INSERT).split('.')[0])
        line_content = editor.get(f"{line_number}.0", f"{line_number}.end")
        editor.insert(f"{line_number}.end", "\n" + line_content)
    editor.master.on_key_release()
    return "break"

def delete_line(editor):
    """
    Deletes the current line.
    """
    if editor.tag_ranges("sel"):
        start, end = editor.index("sel.first"), editor.index("sel.last")
        start_line = int(start.split('.')[0])
        end_line = int(end.split('.')[0])
        if end.split('.')[1] == '0':
            end_line -= 1
        
        editor.delete(f"{start_line}.0", f"{end_line+1}.0")
    else:
        line_number = int(editor.index(tk.INSERT).split('.')[0])
        editor.delete(f"{line_number}.0", f"{line_number+1}.0")
    
    if not editor.get("1.0", tk.END).strip():
        editor.insert("1.0", "\n")
        
    editor.master.on_key_release()
    editor.mark_set(tk.INSERT, f"{editor.index(tk.INSERT).split('.')[0]}.0")
    return "break"
