"""
This module is responsible for binding global keyboard shortcuts to various application functionalities.
It centralizes shortcut definitions and provides a logging wrapper for tracking shortcut activations.
"""

from latex import compiler as latex_compiler
from llm import service as llm_service
from latex import translator as latex_translator
from app import actions as interface
from llm import rephrase as llm_rephrase
from utils import debug_console
from editor import snippets as editor_snippets

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
            # The editor has its own bindings; don't run global shortcuts if an editor is focused.
            if isinstance(root.focus_get(), tk.Text):
                return
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
        # "<Control-w>": (interface.close_current_tab, "Close Tab"), # Removed to allow local editor binding
        "<Control-Shift-T>": (interface.restore_last_closed_tab, "Restore Closed Tab"),
        "<Control-Shift-G>": (llm_service.open_generate_text_dialog, "LLM Generate Dialog"),
        "<Control-Shift-C>": (llm_service.request_llm_to_complete_text, "LLM Complete"),
        "<Control-Shift-K>": (llm_service.open_set_keywords_dialog, "Set LLM Keywords"),
        "<Control-Shift-P>": (llm_service.open_edit_prompts_dialog, "Edit LLM Prompts"),
        "<Control-Shift-S>": (llm_service.start_autostyle_process, "Smart Style"),
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