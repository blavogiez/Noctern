"""Initialize Noctern application with GUI and subsystems."""

import platform
import ctypes

from app import main_window, state, interface
from editor import outline as editor_outline
from latex import compiler as latex_compiler
from latex import translator as latex_translator
from llm import service as llm_service
from utils import logs_console
from snippets import manager as snippet_manager 

def main():
    """Start application with GUI setup and subsystem initialization."""
    logs_console.log("Noctern application starting...", level='INFO')
    
    # configure windows dpi stuff for high res displays
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            logs_console.log("DPI awareness set for Windows operating system.", level='DEBUG')
        except Exception as e:
            logs_console.log(f"Warning: Could not set DPI awareness for Windows - {e}", level='WARNING')

    # Setup main window and all the gui parts
    root_window = main_window.setup_gui()
    if not root_window:
        logs_console.log("GUI setup failed. Exiting application.", level='ERROR')
        return

    # init app subsystems with getter functions for modularity
    
    latex_compiler.initialize_compiler(
        root_window, 
        state.get_current_tab, 
        interface.show_console, 
        interface.hide_console,
        pdf_monitor_setting=state.get_app_config().get("pdf_monitor", "Default")
    )
    
    # schedule the heavy syntax highlighting updates at startup
    root_window.after(100, interface.perform_heavy_updates)
    
    # defer snippet loading to improve startup performance
    root_window.after(500, snippet_manager.initialize_snippets) 

    llm_service.initialize_llm_service(
        root_window=root_window,
        progress_bar_widget=state.llm_progress_bar,
        theme_setting_getter=state.get_theme_setting,
        active_editor_getter=state.get_active_editor,
        active_filepath_getter=state.get_active_file_path,
        app_config=state.get_app_config()
    )

    # defer translator init for faster startup
    latex_translator.initialize_translator(
        root_ref=root_window,
        theme_getter=state.get_theme_setting,
        status_message_func=interface.show_temporary_status_message,
        active_editor_getter=state.get_active_editor,
        active_filepath_getter=state.get_active_file_path
    )

    # schedule syntax highlighting updates
    root_window.after(100, interface.perform_heavy_updates)
    
    # register clean exit handler
    from app.exit_handler import exit_application
    root_window.protocol("WM_DELETE_WINDOW", exit_application)
    
    logs_console.log("Entering main Tkinter event loop.", level='INFO')
    root_window.mainloop()
    logs_console.log("Application has exited main event loop. Shutting down.", level='INFO')

if __name__ == "__main__":
    main()
