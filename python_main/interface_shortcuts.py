import latex_compiler
import llm_service
import latex_translator
import editor_logic
import interface
import llm_rephrase
import debug_console
import editor_snippets

def bind_shortcuts(root):
    """Binds all global keyboard shortcuts for the application."""
    debug_console.log("Binding global keyboard shortcuts.", level='INFO')
    
    def log_and_run(func, name, pass_event=False):
        """
        Wrapper to log shortcut execution.
        If pass_event is True, it passes the event object to the target function.
        """
        def wrapper(event=None):
            debug_console.log(f"Shortcut triggered: {name}", level='ACTION')
            if pass_event:
                func(event)
            else:
                func() 
            return "break"
        return wrapper

    # A dictionary for standard shortcuts that don't need the event object.
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

    for key, (func, name) in simple_shortcuts.items():
        root.bind_all(key, log_and_run(func, name, pass_event=False))

    # Binding for snippet expansion, which requires the event object.
    root.bind_all("<Control-space>", log_and_run(editor_snippets.handle_snippet_expansion, "Expand Snippet", pass_event=True))
        
    # Zoom shortcuts are kept separate as they don't need the 'break' return value.
    root.bind_all("<Control-equal>", interface.zoom_in)
    root.bind_all("<Control-minus>", interface.zoom_out)