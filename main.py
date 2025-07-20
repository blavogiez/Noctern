"""
This is the main entry point for the AutomaTeX application.
It initializes the Tkinter GUI, sets up various application subsystems (editor logic, LaTeX compiler,
LLM service, and LaTeX translator), and starts the main event loop.
"""

import tkinter as tk
import platform
import ctypes

from app import main_window as interface
from editor import logic as editor_logic
from latex import compiler as latex_compiler
from latex import translator as latex_translator
from llm import service as llm_service
from utils import debug_console
from snippets import manager as snippet_manager 

def main():
    """
    Main application entry point.

    This function performs the following key steps:
    1. Configures DPI awareness for Windows to ensure proper scaling on HiDPI displays.
    2. Sets up the main graphical user interface (GUI) window and its components.
    3. Initializes various application subsystems, passing necessary references and callbacks.
    4. Applies the initial theme to the application.
    5. Schedules an initial heavy update for the editor (e.g., syntax highlighting).
    6. Starts the Tkinter main event loop, which keeps the application running.
    """
    debug_console.log("AutomaTeX application starting...", level='INFO')
    
    # On Windows, set process DPI awareness for better rendering on HiDPI screens.
    # This prevents the application from appearing blurry on high-resolution displays.
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            debug_console.log("DPI awareness set for Windows operating system.", level='DEBUG')
        except Exception as e:
            debug_console.log(f"Warning: Could not set DPI awareness for Windows - {e}", level='WARNING')

    # Setup the main GUI window and all its components (top bar, paned window, notebook, status bar).
    root_window = interface.setup_gui()
    if not root_window:
        debug_console.log("GUI setup failed. Exiting application.", level='ERROR')
        return

    # --- Initialize Application Subsystems ---
    # Services are initialized with getter functions (lambdas) to dynamically
    # access the state of the currently active tab from the `interface` module.
    # This design pattern decouples the subsystems from direct UI implementation details,
    # making them more modular and testable.

    # Initialize editor logic, passing the outline tree for document structure display.
    editor_logic.initialize_editor_logic(interface.outline_tree)
    # Initialize the LaTeX compiler, providing the root window for message boxes.
    latex_compiler.initialize_compiler(
        root_window, 
        interface.get_current_tab, 
        interface.show_console, 
        interface.hide_console,
        pdf_monitor_setting=interface._app_config.get("pdf_monitor", "Default")
    )
    # Initialize the snippet manager to load available code snippets.
    snippet_manager.initialize_snippets() 

    # Initialize the LLM service with references to UI components and data getters.
    llm_service.initialize_llm_service(
        root_window=root_window,
        progress_bar_widget=interface.llm_progress_bar,
        theme_setting_getter=interface.get_theme_setting, # Function to get theme-specific settings.
        active_editor_getter=lambda: interface.get_current_tab().editor if interface.get_current_tab() else None, # Dynamically get active editor.
        active_filepath_getter=lambda: interface.get_current_tab().file_path if interface.get_current_tab() else None # Dynamically get active file path.
    )

    # Initialize the LaTeX translator service with necessary UI references and callbacks.
    latex_translator.initialize_translator(
        root_ref=root_window,
        theme_getter=interface.get_theme_setting, # Function to get theme-specific settings.
        status_message_func=interface.show_temporary_status_message, # Function to display temporary status messages.
        active_editor_getter=lambda: interface.get_current_tab().editor if interface.get_current_tab() else None, # Dynamically get active editor.
        active_filepath_getter=lambda: interface.get_current_tab().file_path if interface.get_current_tab() else None # Dynamically get active file path.
    )

    # Apply the initial theme to the application (e.g., "dark" theme).
    interface.apply_theme("dark")

    # Schedule an initial heavy update after a short delay.
    # This ensures that UI elements like syntax highlighting and word count are updated
    # once the window is fully rendered and mapped.
    root_window.after(100, interface.perform_heavy_updates)
    
    debug_console.log("Entering main Tkinter event loop.", level='INFO')
    root_window.mainloop() # Start the Tkinter event loop, which processes all GUI events.
    debug_console.log("Application has exited main event loop. Shutting down.", level='INFO')

if __name__ == "__main__":
    main()
