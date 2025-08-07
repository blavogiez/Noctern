"""
This module is responsible for setting up the main graphical user interface (GUI)
of the AutomaTeX application. It constructs the main window, assembles the
various UI components (like panes, toolbars, and status bars), and connects
UI events to their corresponding handlers in the `actions` module.
"""

import ttkbootstrap as ttk

from app import state, actions, config as app_config, theme as interface_theme
from app.zoom import ZoomManager
from app.topbar import create_top_buttons_frame
from app.panes import create_main_paned_window, create_left_pane, create_outline_tree, create_error_panel, create_notebook, create_console_pane
from app.status import create_status_bar, start_gpu_status_loop
from app.shortcuts import bind_shortcuts
from utils import debug_console, screen as screen_utils
from pre_compiler.checker import Checker

def _apply_startup_window_settings(window, config):
    """Applies window geometry and state from config at startup."""
    monitors = screen_utils.get_monitors()
    if not monitors:
        debug_console.log("No monitors detected, using default geometry.", level='WARNING')
        window.geometry("1200x800")
        return

    monitor_name = config.get("app_monitor", "Default")
    selected_monitor = None

    if monitor_name == "Default":
        selected_monitor = next((m for m in monitors if m.is_primary), monitors[0])
    else:
        try:
            monitor_index = int(monitor_name.split(':')[0].split(' ')[1]) - 1
            if 0 <= monitor_index < len(monitors):
                selected_monitor = monitors[monitor_index]
            else:
                selected_monitor = monitors[0]
        except (ValueError, IndexError):
            debug_console.log(f"Could not parse monitor name '{monitor_name}'. Falling back to primary.", level='WARNING')
            selected_monitor = next((m for m in monitors if m.is_primary), monitors[0])

    window_state = config.get("window_state", "Normal")

    if window_state == "Maximized":
        x, y = selected_monitor.x, selected_monitor.y
        window.geometry(f"+{x}+{y}")
        window.state('zoomed')
    elif window_state == "Fullscreen":
        x, y = selected_monitor.x, selected_monitor.y
        window.geometry(f"+{x}+{y}")
        window.attributes("-fullscreen", True)
    else: # Normal
        width, height = 1200, 800
        x = selected_monitor.x + (selected_monitor.width - width) // 2
        y = selected_monitor.y + (selected_monitor.height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

def setup_gui():
    """
    Initializes and sets up the main graphical user interface (GUI).
    """
    state._app_config = app_config.load_config()
    state.zoom_manager = ZoomManager(state)
    state.checker = Checker()


    # Create the window with a default theme first.
    state.root = ttk.Window(themename="litera")
    
    valid_themes = state.root.style.theme_names()
    saved_theme = state._app_config.get("theme", "litera")
    if saved_theme == "light": saved_theme = "litera"
    if saved_theme == "dark": saved_theme = "darkly"

    if saved_theme not in valid_themes and saved_theme != "original":
        debug_console.log(f"Theme '{saved_theme}' not found. Falling back to 'litera'.", level='WARNING')
        saved_theme = "litera"
    
    state.root.style.theme_use(saved_theme if saved_theme != "original" else "litera")

    state.root.title("AutomaTeX v1.0")
    _apply_startup_window_settings(state.root, state._app_config)
    debug_console.log("GUI initialization process started.", level='INFO')

    state._auto_open_pdf_var = ttk.BooleanVar(value=app_config.get_bool(state._app_config.get('auto_open_pdf', 'False')))
    
    state.current_theme = saved_theme
    state._theme_settings = interface_theme.get_theme_colors(state.root.style, state.current_theme)

    debug_console.initialize(state.root)

    top_frame, state.settings_menu = create_top_buttons_frame(state.root)

    state.vertical_pane = ttk.PanedWindow(state.root, orient=ttk.VERTICAL)
    state.vertical_pane.pack(fill="both", expand=True)

    state.main_pane = create_main_paned_window(state.vertical_pane)
    
    left_pane = create_left_pane(state.main_pane)
    
    state.outline_tree = create_outline_tree(left_pane, state.get_current_tab)
    
    state.error_panel = create_error_panel(left_pane)
    
    state.notebook = create_notebook(state.main_pane)
    
    state.vertical_pane.add(state.main_pane, weight=1)

    console_frame, state.console_output = create_console_pane(state.vertical_pane)
    state.console_pane = console_frame
    state.vertical_pane.add(state.console_pane)
    actions.hide_console()

    def check_document(event=None):
        current_tab = state.get_current_tab()
        if current_tab:
            content = current_tab.editor.get("1.0", "end-1c")
            errors = state.checker.check(content)
            state.error_panel.update_errors(errors)

    def on_text_modified(event):
        check_document()
        # We need to call the original handler too
        state.get_current_tab().editor.edit_modified(False)
        return None

    def on_tab_changed(event):
        actions.on_tab_changed(event)
        current_tab = state.get_current_tab()
        if current_tab:
            # Re-bind the modified event to the new tab's editor
            current_tab.editor.bind("<<Modified>>", on_text_modified)
            check_document()


    state.notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    state.llm_progress_bar = ttk.Progressbar(state.root, mode="indeterminate", length=200)
    
    state.status_bar_frame, state.status_label, state.gpu_status_label = create_status_bar(state.root)
    start_gpu_status_loop(state.gpu_status_label, state.root)
    
    bind_shortcuts(state.root)
    
    actions.load_session()
    
    state.root.protocol("WM_DELETE_WINDOW", actions.on_close_request)
    
    debug_console.log("GUI setup completed successfully.", level='SUCCESS')
    
    return state.root