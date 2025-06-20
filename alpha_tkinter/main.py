#### AutomaTeX, a LaTeX editor powered by AI Tools
#### Baptiste Lavogiez, June 2025

#### https://github.com/blavogiez/AutomaTeX
#### AutomaTeX, a LaTeX editor powered by AI Tools
#### Baptiste Lavogiez, June 2025

#### https://github.com/blavogiez/AutomaTeX

import tkinter as tk

# Import modules for different functionalities
import interface
import editor_logic
import latex_compiler
import llm_service # MODIFIED: Import new llm_service

# Global variables (defined and managed primarily in interface.py)
# We declare them here to make it clear they are part of the application state
# and accessed across modules.
root = None
editor = None
outline_tree = None
llm_progress_bar = None
line_numbers_canvas = None
editor_font = None
current_file_path = None
current_theme = "light" # Initial theme state
heavy_update_timer_id = None # Timer ID for scheduled updates

### --- MAIN APPLICATION ENTRY POINT --- ###

### --- MAIN --- ###

if __name__ == "__main__":
    # Setup the main GUI window and widgets
    root = interface.setup_gui()

    # Assign global variables from the interface module
    editor = interface.editor
    outline_tree = interface.outline_tree
    llm_progress_bar = interface.llm_progress_bar
    line_numbers_canvas = interface.line_numbers_canvas
    editor_font = interface.editor_font
    current_file_path = interface.current_file_path
    current_theme = interface.current_theme
    heavy_update_timer_id = interface.heavy_update_timer_id

    # Pass global references to other modules
    # This allows them to interact with the main GUI elements
    editor_logic.set_editor_globals(editor, outline_tree, current_file_path)
    latex_compiler.set_compiler_globals(editor, root, current_file_path)
    # MODIFIED: Call the new initialization function for llm_service
    llm_service.initialize_llm_service(
        editor_widget_ref=editor,
        root_window_ref=root,
        progress_bar_widget_ref=llm_progress_bar,
        theme_setting_getter_callback=interface.get_theme_setting,
        current_file_path_getter_callback=interface.get_current_file_path_for_llm)

    # Apply the initial theme (e.g., dark mode by default)
    interface.apply_theme("dark")

    # Appel initial pour s'assurer que tout est dessiné correctement
    # interface.perform_heavy_updates() is already called at the end of apply_theme
    # Mais un appel direct à redraw peut être utile après que la fenêtre soit visible.
    # We can schedule a small delay to ensure the window is fully mapped before drawing
    root.after(100, interface.perform_heavy_updates) # Schedule initial drawing/updates

    # Start the Tkinter event loop
    root.mainloop()
