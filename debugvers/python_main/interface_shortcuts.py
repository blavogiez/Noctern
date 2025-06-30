import latex_compiler
import llm_service
import latex_translator
import editor_logic
import interface
import llm_rephrase
import debug_console

def bind_shortcuts(root):
    """Binds all global keyboard shortcuts for the application."""
    debug_console.log("Binding global keyboard shortcuts.", level='INFO')
    
    def log_and_run(func, name):
        """Wrapper to log shortcut execution."""
        def wrapper(event=None):
            debug_console.log(f"Shortcut triggered: {name}", level='ACTION')
            func()
            return "break" # Prevent default behavior for some shortcuts
        return wrapper

    # Use a dictionary for easier management
    shortcuts = {
        "<Control-Shift-G>": (llm_service.open_generate_text_dialog, "LLM Generate Dialog"),
        "<Control-Shift-C>": (llm_service.request_llm_to_complete_text, "LLM Complete"),
        "<Control-Shift-D>": (latex_compiler.run_chktex_check, "Chktex Check"),
        "<Control-Shift-V>": (interface.paste_image, "Paste Image"),
        "<Control-Shift-K>": (llm_service.open_set_keywords_dialog, "Set LLM Keywords"),
        "<Control-Shift-P>": (llm_service.open_edit_prompts_dialog, "Edit LLM Prompts"),
        "<Control-o>": (interface.open_file, "Open File"),
        "<Control-s>": (interface.save_file, "Save File"),
        "<Control-w>": (interface.close_current_tab, "Close Tab"),
        "<Control-t>": (latex_translator.open_translate_dialog, "Translate Dialog"),
        "<Control-r>": (llm_rephrase.open_rephrase_dialog, "Rephrase Dialog"),
    }

    for key, (func, name) in shortcuts.items():
        root.bind_all(key, log_and_run(func, name))
        
    # Zoom shortcuts don't need the break and have a different signature
    root.bind_all("<Control-equal>", interface.zoom_in)
    root.bind_all("<Control-minus>", interface.zoom_out)