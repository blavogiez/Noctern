import sys
import os
import platform
import json
from PyQt6 import QtWidgets, QtCore, QtGui

# Import newly fragmented GUI modules
from gui import main_window
from gui import file_tab_manager
from gui import theme_manager
from gui import status_bar
from gui import editor_view

# Import services and logic
from services import llm_service
from services import latex_compiler
from services import latex_translator
from editor import editor_logic

if __name__ == "__main__":
    # Improve rendering on HiDPI screens under Windows
    if platform.system() == "Windows":
        try:
            # This is typically handled by Qt itself, but can be explicitly set if needed
            # For PyQt6, it's often better to rely on QApplication's default DPI scaling
            # or set QT_SCALE_FACTOR environment variable.
            # If you still need explicit DPI awareness, you might use ctypes, but it's less common with modern Qt.
            pass
        except Exception as e:
            print(f"Note: Could not set DPI awareness - {e}")

    app = QtWidgets.QApplication(sys.argv)

    # --- Pre-initialization Check ---
    # Before initializing any services that depend on prompts, check if the
    # default prompts file is valid.
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_prompts_file = os.path.join(script_dir, "services", "default_prompts.json")
        with open(default_prompts_file, 'r', encoding='utf-8') as f:
            json.load(f)
    except Exception as e:
        QtWidgets.QMessageBox.critical(
            None, # No parent for critical startup error
            "Critical Configuration Error",
            f"Could not load or parse 'default_prompts.json'.\n\n"
            f"Error: {e}\n\n"
            "The application's AI features will use hardcoded fallback prompts. "
            "If you open a new file, a prompts file will be created for it with these simple fallbacks. "
            "Please fix 'default_prompts.json' and restart the application."
        )

    # Setup the main GUI window and widgets
    main_window_instance = main_window.MainWindow()
    root = main_window_instance # For consistency with Tkinter's 'root' reference

    # --- Main Application Callbacks ---
    # These will be connected to signals in the PyQt world
    def _on_tab_changed():
        """Handles all actions that need to occur when the active tab changes."""
        llm_service.load_prompt_history_for_current_file()
        llm_service.load_keywords_for_current_file()
        llm_service.load_prompts_for_current_file()
        editor_view.perform_heavy_updates()

    # --- Initialize Services ---
    # Initialize GUI sub-modules first, as other services depend on them.
    # The order of initialization below is important due to inter-module dependencies.

    # 1. Initialize Status Bar Manager: Needs root and status_bar widget.
    status_bar.initialize(root_ref=main_window_instance, status_bar_ref=main_window_instance.status_bar_label)

    # 2. Initialize Editor Logic: Needs outline_tree and a way to get the current tab.
    editor_logic.initialize_editor_logic(main_window_instance.outline_tree, lambda: file_tab_manager.get_current_tab())

    # 3. Initialize Editor View Manager: Needs root, a way to get current tab, outline_tree, and editor_logic module.
    editor_view.initialize(
        root_ref=main_window_instance,
        get_current_tab_cb=lambda: file_tab_manager.get_current_tab(),
        outline_tree_ref=main_window_instance.outline_tree,
        editor_logic_module=editor_logic
    )

    # 4. Initialize File/Tab Manager: Needs references to notebook, welcome screen, root,
    #    and callbacks for tab changes and heavy updates.
    file_tab_manager.initialize(
        notebook_ref=main_window_instance.notebook,
        welcome_screen_ref=main_window_instance.welcome_screen,
        root_ref=main_window_instance,
        on_tab_changed_cb=_on_tab_changed,
        schedule_heavy_updates_cb=editor_view.schedule_heavy_updates,
        welcome_button_frame_ref=main_window_instance.welcome_button_frame,
        apply_theme_cb=lambda: theme_manager.apply_theme(theme_manager._current_theme)
    )

    # 5. Initialize Theme Manager: Needs root, the tabs dictionary, and a callback for heavy updates.
    theme_manager.initialize(
        root_ref=main_window_instance,
        perform_heavy_updates_cb=editor_view.perform_heavy_updates
    )

    # Initialize other core application services
    latex_compiler.initialize_compiler(main_window_instance, lambda: file_tab_manager.get_current_tab())

    # LLM Service initialization
    llm_service.initialize_llm_service(
        root_window_ref=main_window_instance,
        progress_bar_widget_ref=main_window_instance.llm_progress_bar,
        theme_setting_getter_func=theme_manager.get_theme_setting,
        active_editor_getter=lambda: file_tab_manager.get_current_tab().editor if file_tab_manager.get_current_tab() else None,
        active_filepath_getter=lambda: file_tab_manager.get_current_tab().file_path if file_tab_manager.get_current_tab() else None,
        show_temporary_status_message_func=status_bar.show_temporary_status_message,
        pause_heavy_updates_cb=editor_view.pause_heavy_updates,
        resume_heavy_updates_cb=editor_view.resume_heavy_updates,
        full_editor_refresh_cb=editor_view.full_editor_refresh
    )

    # LaTeX Translator initialization
    latex_translator.initialize_translator(
        root_ref=main_window_instance,
        theme_getter=theme_manager.get_theme_setting,
        status_message_func=status_bar.show_temporary_status_message,
        active_editor_getter=lambda: file_tab_manager.get_current_tab().editor if file_tab_manager.get_current_tab() else None,
        active_filepath_getter=lambda: file_tab_manager.get_current_tab().file_path if file_tab_manager.get_current_tab() else None
    )

    # Show the welcome screen initially, as no tabs are open
    file_tab_manager.toggle_welcome_screen()

    # Apply the initial theme (e.g., dark mode by default)
    theme_manager.apply_theme("dark")

    # Start the GPU status update loop
    status_bar.update_gpu_status()

    # Initial call to ensure everything is drawn correctly after the window is visible.
    # Use QTimer.singleShot for a deferred call.
    QtCore.QTimer.singleShot(100, editor_view.perform_heavy_updates)

    main_window_instance.show()
    sys.exit(app.exec())