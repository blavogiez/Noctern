"""
This module is responsible for binding global keyboard shortcuts.
"""
from latex import compiler as latex_compiler
from llm import service as llm_service
from latex import translator as latex_translator
from app import interface, state
from llm import rephrase as llm_rephrase
from utils import logs_console
from editor import snippets as editor_snippets
from editor import search as editor_search
import tkinter as tk

def bind_global_shortcuts(root):
    """Binds all global keyboard shortcuts for the application."""
    # Initialize the search bar
    editor_search.initialize_search_bar(root)
    
    # Panel management functions
    def switch_to_next_panel():
        """Switch to the next panel in the tab order."""
        if state.panel_manager:
            state.panel_manager.switch_to_next_panel()
    
    def switch_to_previous_panel():
        """Switch to the previous panel in the tab order."""
        if state.panel_manager:
            state.panel_manager.switch_to_previous_panel()
    
    def close_current_panel():
        """Close the currently visible panel."""
        if state.panel_manager:
            state.panel_manager.close_current_panel()
    
    def close_all_panels():
        """Close all active panels."""
        if state.panel_manager:
            state.panel_manager.close_all_panels()
    
    def log_and_run(func, name, pass_event=False):
        """
        Wrapper to log shortcut execution and prevent conflicts by checking focus.
        """
        def wrapper(event=None):
            if pass_event:
                func(event)
            else:
                func()
            # We return "break" only if the focus is not on the editor,
            # Allow editor-specific bindings to continue working
            if not isinstance(root.focus_get(), tk.Text):
                return "break"
        return wrapper

    def toggle_search_bar():
        """Toggle the search bar visibility."""
        if editor_search._search_bar and editor_search._search_bar.is_visible:
            editor_search.hide_search_bar()
        else:
            editor_search.show_search_bar()
    
    def close_search_if_open():
        """Close search bar if it's open, otherwise do nothing."""
        if editor_search._search_bar and editor_search._search_bar.is_visible:
            editor_search.hide_search_bar()

    simple_shortcuts = {
        "<Control-n>": (interface.create_new_tab, "New File"),
        "<Control-o>": (interface.open_file, "Open File"),
        "<Control-s>": (interface.save_file, "Save File"),
        "<Control-w>": (interface.close_current_tab, "Close Tab"),
        "<Control-Shift-T>": (interface.restore_last_closed_tab, "Restore Closed Tab"),
        "<Control-Shift-G>": (interface.open_generate_text_panel, "LLM Generate Panel"),
        "<Control-Shift-C>": (llm_service.request_llm_to_complete_text, "LLM Complete"),
        "<Control-Shift-K>": (interface.open_set_keywords_panel, "Set LLM Keywords"),
        "<Control-Shift-P>": (interface.open_proofreading_panel, "Proofread Document"),
        "<Control-Shift-E>": (interface.open_edit_prompts_panel, "Edit LLM Prompts"),
        "<Control-Shift-S>": (interface.style_selected_text, "Smart Style"),
        "<Control-r>": (interface.open_rephrase_panel, "Rephrase Panel"),
        "<Control-Shift-V>": (interface.paste_image, "Paste Image"),
        "<Control-Shift-B>": (interface.insert_table, "Insert Table"),
        "<Control-t>": (latex_translator.open_translate_panel, "Translate Panel"),
        "<Control-f>": (toggle_search_bar, "Find"),
        # Panel navigation shortcuts
        "<Control-Tab>": (switch_to_next_panel, "Next Panel"),
        "<Control-Shift-Tab>": (switch_to_previous_panel, "Previous Panel"),
        "<Control-Shift-W>": (close_current_panel, "Close Current Panel"),
        "<Control-Shift-Alt-W>": (close_all_panels, "Close All Panels"),
    }

    for key, (func, name) in simple_shortcuts.items():
        root.bind_all(key, log_and_run(func, name, pass_event=False))

    # Snippets are a special case that needs to work in the editor
    root.bind_all("<Control-space>", editor_snippets.handle_snippet_expansion)
    
    # Zoom shortcuts are safe to be global without the wrapper
    root.bind_all("<Control-equal>", interface.zoom_in)
    root.bind_all("<Control-minus>", interface.zoom_out)
    
    # Global ESC key to close search bar
    root.bind_all("<Escape>", lambda event: close_search_if_open())

