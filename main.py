"""Initialize AutomaTeX application with GUI and subsystems."""

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
    """Start application with GUI setup and subsystem initialization."""
    debug_console.log("AutomaTeX application starting...", level='INFO')
    
    # Configure Windows DPI awareness for HiDPI displays
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            debug_console.log("DPI awareness set for Windows operating system.", level='DEBUG')
        except Exception as e:
            debug_console.log(f"Warning: Could not set DPI awareness for Windows - {e}", level='WARNING')

    # Initialize main GUI window and components
    root_window = main_window.setup_gui()
    if not root_window:
        debug_console.log("GUI setup failed. Exiting application.", level='ERROR')
        return

    # Initialize application subsystems with getter functions for modularity
    
    latex_compiler.initialize_compiler(
        root_window, 
        state.get_current_tab, 
        actions.show_console, 
        actions.hide_console,
        pdf_monitor_setting=state.get_app_config().get("pdf_monitor", "Default")
    )
    
    # Schedule initial heavy updates for syntax highlighting
    root_window.after(100, actions.perform_heavy_updates)
    
    # Defer snippet loading to improve startup performance
    root_window.after(500, snippet_manager.initialize_snippets) 

    llm_service.initialize_llm_service(
        root_window=root_window,
        progress_bar_widget=state.llm_progress_bar,
        theme_setting_getter=state.get_theme_setting,
        active_editor_getter=lambda: state.get_current_tab().editor if state.get_current_tab() else None,
        active_filepath_getter=lambda: state.get_current_tab().file_path if state.get_current_tab() else None,
        app_config=state.get_app_config()
    )

    # Defer translator initialization for faster startup
    latex_translator.initialize_translator(
        root_ref=root_window,
        theme_getter=state.get_theme_setting,
        status_message_func=actions.show_temporary_status_message,
        active_editor_getter=lambda: state.get_current_tab().editor if state.get_current_tab() else None,
        active_filepath_getter=lambda: state.get_current_tab().file_path if state.get_current_tab() else None
    )

    # Schedule syntax highlighting updates
    root_window.after(100, actions.perform_heavy_updates)
    
    # Register cleanup handler for metrics
    def on_closing():
        # Save session metrics before exit
        if hasattr(state, 'metrics_display') and state.metrics_display:
            state.metrics_display.save_current_session()
        root_window.destroy()
    
    root_window.protocol("WM_DELETE_WINDOW", on_closing)
    
    debug_console.log("Entering main Tkinter event loop.", level='INFO')
    root_window.mainloop()
    debug_console.log("Application has exited main event loop. Shutting down.", level='INFO')

if __name__ == "__main__":
    main()