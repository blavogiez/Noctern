"""
This is the main entry point for the AutomaTeX application.
It initializes the Tkinter GUI, sets up various application subsystems (editor logic, LaTeX compiler,
LLM service, and LaTeX translator), and starts the main event loop.
"""

import platform
import ctypes

from app import main_window, state, actions
from editor import outline as editor_outline
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
    4. Schedules an initial heavy update for the editor (e.g., syntax highlighting).
    5. Starts the Tkinter main event loop, which keeps the application running.
    """
    debug_console.log("AutomaTeX application starting...", level='INFO')
    
    # On Windows, set process DPI awareness for better rendering on HiDPI screens.
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            debug_console.log("DPI awareness set for Windows operating system.", level='DEBUG')
        except Exception as e:
            debug_console.log(f"Warning: Could not set DPI awareness for Windows - {e}", level='WARNING')

    # Setup the main GUI window and all its components.
    root_window = main_window.setup_gui()
    if not root_window:
        debug_console.log("GUI setup failed. Exiting application.", level='ERROR')
        return

    # --- Initialize Application Subsystems ---
    # Services are initialized with getter functions (lambdas) to dynamically
    # access the application state. This decouples the subsystems from direct
    # UI implementation details, making them more modular.
    
    latex_compiler.initialize_compiler(
        root_window, 
        state.get_current_tab, 
        actions.show_console, 
        actions.hide_console,
        pdf_monitor_setting=state.get_app_config().get("pdf_monitor", "Default")
    )
    
    # Schedule an initial heavy update to render syntax highlighting, etc.
    root_window.after(100, actions.perform_heavy_updates)
    
    # Defer snippets initialization to improve startup time
    root_window.after(500, snippet_manager.initialize_snippets) 

    llm_service.initialize_llm_service(
        root_window=root_window,
        progress_bar_widget=state.llm_progress_bar,
        theme_setting_getter=state.get_theme_setting,
        active_editor_getter=lambda: state.get_current_tab().editor if state.get_current_tab() else None,
        active_filepath_getter=lambda: state.get_current_tab().file_path if state.get_current_tab() else None,
        app_config=state.get_app_config()
    )

    # Initialize translator service on demand to improve startup time
    latex_translator.initialize_translator(
        root_ref=root_window,
        theme_getter=state.get_theme_setting,
        status_message_func=actions.show_temporary_status_message,
        active_editor_getter=lambda: state.get_current_tab().editor if state.get_current_tab() else None,
        active_filepath_getter=lambda: state.get_current_tab().file_path if state.get_current_tab() else None
    )

    # Schedule an initial heavy update to render syntax highlighting, etc.
    root_window.after(100, actions.perform_heavy_updates)
    
    # Add cleanup handler for metrics
    def on_closing():
        # Save current session metrics before closing
        if hasattr(state, 'metrics_display') and state.metrics_display:
            state.metrics_display.save_current_session()
        root_window.destroy()
    
    root_window.protocol("WM_DELETE_WINDOW", on_closing)
    
    debug_console.log("Entering main Tkinter event loop.", level='INFO')
    root_window.mainloop()
    debug_console.log("Application has exited main event loop. Shutting down.", level='INFO')

if __name__ == "__main__":
    main()