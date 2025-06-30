# interface_shortcuts.py

import latex_compiler
import llm_service
import latex_translator
import editor_logic
import interface
import llm_rephrase
import debug_console
import editor_enhancements

def bind_shortcuts(root):
    """Binds all global keyboard shortcuts for the application."""
    debug_console.log("Binding global keyboard shortcuts.", level='INFO')
    
    # FIXED: The wrapper now consistently passes the event object to the target function.
    # This makes the system uniform and allows functions like the snippet handler
    # to know which widget triggered the event.
    def log_and_run(func, name):
        """Wrapper to log shortcut execution and pass the event object."""
        def wrapper(event=None):
            debug_console.log(f"Shortcut triggered: {name}", level='ACTION')
            # Pass the event to the function. The target function must accept it (e.g., with a default value).
            func(event) 
            return "break" # Prevent default behavior for the shortcut
        return wrapper

    # FIXED: The shortcuts dictionary is now the single, logical source of truth for all shortcuts.
    # The snippet handler is now included here, using Ctrl+Tab.
    shortcuts = {
        # LLM Shortcuts
        "<Control-Shift-G>": (llm_service.open_generate_text_dialog, "LLM Generate Dialog"),
        "<Control-Shift-C>": (llm_service.request_llm_to_complete_text, "LLM Complete"),
        "<Control-Shift-K>": (llm_service.open_set_keywords_dialog, "Set LLM Keywords"),
        "<Control-Shift-P>": (llm_service.open_edit_prompts_dialog, "Edit LLM Prompts"),
        "<Control-r>": (llm_rephrase.open_rephrase_dialog, "Rephrase Dialog"),
        
        # File Operation Shortcuts
        "<Control-o>": (interface.open_file, "Open File"),
        "<Control-s>": (interface.save_file, "Save File"),
        "<Control-w>": (interface.close_current_tab, "Close Tab"),
        
        # Tooling Shortcuts
        "<Control-Shift-D>": (latex_compiler.run_chktex_check, "Chktex Check"),
        "<Control-Shift-V>": (interface.paste_image, "Paste Image"),
        "<Control-t>": (latex_translator.open_translate_dialog, "Translate Dialog"),

        # NEW: Snippet expansion shortcut, now logically placed with the others.
        "<Control-m>": (editor_enhancements.handle_tab_key, "Expand Snippet"),
    }

    # Bind all shortcuts from the dictionary using the improved wrapper.
    for key, (func, name) in shortcuts.items():
        root.bind_all(key, log_and_run(func, name))
        
    # Zoom shortcuts are kept separate as they don't need the 'break' return value
    # and are bound to keys that can be held down.
    root.bind_all("<Control-equal>", interface.zoom_in)
    root.bind_all("<Control-minus>", interface.zoom_out)

    # REMOVED: The old, separate binding for Tab is no longer needed.