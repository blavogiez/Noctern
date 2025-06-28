#### AutomaTeX, a LaTeX editor powered by AI Tools
#### Baptiste Lavogiez, June 2025

#### https://github.com/blavogiez/AutomaTeX

import tkinter as tk
import platform
import ctypes

# Import modules for different functionalities
import interface
import editor_logic
import latex_compiler  # MODIFIED: Import new llm_service
import latex_translator # NEW: Import latex_translator
import llm_service # MODIFIED: Import new llm_service

# Global variables (defined and managed primarily in interface.py)
# We declare them here to make it clear they are part of the application state
# and accessed across modules.
root = None # The main Tkinter window

heavy_update_timer_id = None # Timer ID for scheduled updates, managed by interface.py

### --- MAIN APPLICATION ENTRY POINT --- ###

### --- MAIN --- ###

if __name__ == "__main__":
    # Améliorer le rendu sur les écrans HiDPI sous Windows
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception as e:
            print(f"Note: Could not set DPI awareness - {e}")

    # Setup the main GUI window and widgets
    root = interface.setup_gui()
    if root:  # Check if root is successfully initialized
        # --- Initialize Services ---
        # The services are initialized with getter functions to dynamically access
        # the state of the currently active tab from the interface.

        editor_logic.initialize_editor_logic(interface.outline_tree)
        latex_compiler.initialize_compiler(root)

        llm_service.initialize_llm_service(
            root=root,
            progress_bar=interface.llm_progress_bar,
            theme_getter=interface.get_theme_setting,
            # Provide functions to get the active editor and its file path
            editor_getter=lambda: interface.get_current_tab().editor if interface.get_current_tab() else None,
            filepath_getter=lambda: interface.get_current_tab().file_path if interface.get_current_tab() else None
        )

    latex_translator.initialize_translator(
        root_ref=root,
        theme_getter=interface.get_theme_setting,
        status_message_func=interface.show_temporary_status_message,
        # Provide functions to get the active editor and its file path
        active_editor_getter=lambda: interface.get_current_tab().editor if interface.get_current_tab() else None,
        active_filepath_getter=lambda: interface.get_current_tab().file_path if interface.get_current_tab() else None
    )

    # Apply the initial theme (e.g., dark mode by default)
    interface.apply_theme("dark")

    # Appel initial pour s'assurer que tout est dessiné correctement
    # interface.perform_heavy_updates() is already called at the end of apply_theme
    # Mais un appel direct à redraw peut être utile après que la fenêtre soit visible.
    # We can schedule a small delay to ensure the window is fully mapped before drawing
    root.after(100, interface.perform_heavy_updates) # Schedule initial drawing/updates

    # Start the Tkinter event loop
    root.mainloop()
