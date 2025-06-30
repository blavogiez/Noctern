# main.py

import tkinter as tk
import platform
import ctypes

import interface
import editor_logic
import latex_compiler
import latex_translator
import llm_service
import debug_console
import snippet_manager 

def main():
    """Main application entry point."""
    debug_console.log("Application starting...", level='INFO')
    
    # On Windows, set process DPI awareness for better rendering on HiDPI screens.
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            debug_console.log("DPI awareness set for Windows.", level='DEBUG')
        except Exception as e:
            debug_console.log(f"Note: Could not set DPI awareness - {e}", level='WARNING')

    # Setup the main GUI window and all its components.
    root = interface.setup_gui()
    if not root:
        debug_console.log("GUI setup failed. Exiting.", level='ERROR')
        return

    # --- Initialize Subsystems ---
    # Services are initialized with getter functions (lambdas) to dynamically
    # access the state of the currently active tab from the interface. This
    # decouples the subsystems from the UI implementation details.

    editor_logic.initialize_editor_logic(interface.outline_tree)
    latex_compiler.initialize_compiler(root)
    snippet_manager.initialize_snippets() 

    llm_service.initialize_llm_service(
        root=root,
        progress_bar=interface.llm_progress_bar,
        theme_getter=interface.get_theme_setting, # CORRECTED: Changed to singular version
        editor_getter=lambda: interface.get_current_tab().editor if interface.get_current_tab() else None,
        filepath_getter=lambda: interface.get_current_tab().file_path if interface.get_current_tab() else None
    )

    latex_translator.initialize_translator(
        root_ref=root,
        theme_getter=interface.get_theme_setting, # CORRECTED: Changed to singular version
        status_message_func=interface.show_temporary_status_message,
        active_editor_getter=lambda: interface.get_current_tab().editor if interface.get_current_tab() else None,
        active_filepath_getter=lambda: interface.get_current_tab().file_path if interface.get_current_tab() else None
    )

    # Apply the initial theme.
    interface.apply_theme("dark")

    # Schedule an initial draw/update after the window is fully mapped.
    root.after(100, interface.perform_heavy_updates)
    
    debug_console.log("Entering main event loop.", level='INFO')
    root.mainloop()
    debug_console.log("Application has exited main loop.", level='INFO')

if __name__ == "__main__":
    main()