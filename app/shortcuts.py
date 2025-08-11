"""
This module is responsible for binding global keyboard shortcuts.
"""
from latex import compiler as latex_compiler
from llm import service as llm_service
from latex import translator as latex_translator
from app import actions as interface
from llm import rephrase as llm_rephrase
from utils import debug_console
from editor import snippets as editor_snippets
from editor import search as editor_search
import tkinter as tk

def bind_global_shortcuts(root):
    """Binds all global keyboard shortcuts for the application."""
    debug_console.log("Binding global shortcuts.", level='INFO')
    
    # Initialize the search bar
    editor_search.initialize_search_bar(root)
    
    def log_and_run(func, name, pass_event=False):
        """
        Wrapper to log shortcut execution and prevent conflicts by checking focus.
        """
        def wrapper(event=None):
            debug_console.log(f"Global Shortcut: {name}", level='ACTION')
            if pass_event:
                func(event)
            else:
                func()
            # We return "break" only if the focus is not on the editor,
            # to allow editor-specific bindings to still work.
            if not isinstance(root.focus_get(), tk.Text):
                return "break"
        return wrapper

    def toggle_search_bar():
        """Toggle the search bar visibility."""
        if editor_search._search_bar and editor_search._search_bar.is_visible:
            editor_search.hide_search_bar()
        else:
            editor_search.show_search_bar()

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
        "<Control-Shift-S>": (llm_service.start_autostyle_process, "Smart Style"),
        "<Control-r>": (llm_rephrase.open_rephrase_dialog, "Rephrase Dialog"),
        "<Control-Shift-D>": (latex_compiler.run_chktex_check, "Chktex Check"),
        "<Control-Shift-V>": (interface.paste_image, "Paste Image"),
        "<Control-t>": (latex_translator.open_translate_dialog, "Translate Dialog"),
        "<Control-f>": (toggle_search_bar, "Find"),
    }

    for key, (func, name) in simple_shortcuts.items():
        root.bind_all(key, log_and_run(func, name, pass_event=False))

    # Snippets are a special case that needs to work in the editor
    root.bind_all("<Control-space>", editor_snippets.handle_snippet_expansion)
    
    # Zoom shortcuts are safe to be global without the wrapper
    root.bind_all("<Control-equal>", interface.zoom_in)
    root.bind_all("<Control-minus>", interface.zoom_out)

    debug_console.log("Global shortcuts have been bound.", level='INFO')
