"""
This module is responsible for setting up the main graphical user interface (GUI)
of the AutomaTeX application. It constructs the main window, assembles the
various UI components (like panes, toolbars, and status bars), and connects
UI events to their corresponding handlers in the `actions` module.
"""
import os
import ttkbootstrap as ttk

from app import state, actions, config as app_config, theme as interface_theme
from app.zoom import ZoomManager
from app.topbar import create_top_buttons_frame
from app.panes import create_main_paned_window, create_left_pane, create_outline_tree, create_error_panel, create_notebook, create_console_pane
from app.status import create_status_bar, start_gpu_status_loop
from app.shortcuts import bind_shortcuts
from utils import debug_console, screen as screen_utils
from pre_compiler.checker import Checker
from editor import syntax as editor_syntax

def _apply_startup_window_settings(window, config):
    """Applies window geometry and state from config at startup."""
    monitors = screen_utils.get_monitors()
    if not monitors:
        window.geometry("1200x800")
        return

    monitor_name = config.get("app_monitor", "Default")
    selected_monitor = next((m for m in monitors if m.is_primary), monitors[0])
    if monitor_name != "Default":
        try:
            monitor_index = int(monitor_name.split(':')[0].split(' ')[1]) - 1
            if 0 <= monitor_index < len(monitors):
                selected_monitor = monitors[monitor_index]
        except (ValueError, IndexError):
            debug_console.log(f"Could not parse monitor name '{monitor_name}'. Falling back to primary.", level='WARNING')

    window_state = config.get("window_state", "Normal")
    x, y = selected_monitor.x, selected_monitor.y
    if window_state == "Maximized":
        window.geometry(f"+{x}+{y}")
        window.state('zoomed')
    elif window_state == "Fullscreen":
        window.geometry(f"+{x}+{y}")
        window.attributes("-fullscreen", True)
    else: # Normal
        width, height = 1200, 800
        x += (selected_monitor.width - width) // 2
        y += (selected_monitor.height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

def setup_gui():
    """
    Initializes and sets up the main graphical user interface (GUI).
    """
    state._app_config = app_config.load_config()
    state.zoom_manager = ZoomManager(state)
    state.checker = Checker() # Checker no longer needs project_root

    state.root = ttk.Window(themename="litera")
    
    valid_themes = state.root.style.theme_names()
    saved_theme = state._app_config.get("theme", "litera")
    if saved_theme in ["light", "dark"]: saved_theme = "litera" if saved_theme == "light" else "darkly"
    if saved_theme not in valid_themes and saved_theme != "original":
        saved_theme = "litera"
    state.root.style.theme_use(saved_theme if saved_theme != "original" else "litera")

    state.root.title("AutomaTeX v1.0")
    _apply_startup_window_settings(state.root, state._app_config)
    debug_console.log("GUI initialization process started.", level='INFO')

    state._auto_open_pdf_var = ttk.BooleanVar(value=app_config.get_bool(state._app_config.get('auto_open_pdf', 'False')))
    state.current_theme = saved_theme
    state._theme_settings = interface_theme.get_theme_colors(state.root.style, state.current_theme)

    debug_console.initialize(state.root)
    create_top_buttons_frame(state.root)

    state.vertical_pane = ttk.PanedWindow(state.root, orient=ttk.VERTICAL)
    state.vertical_pane.pack(fill="both", expand=True)

    state.main_pane = create_main_paned_window(state.vertical_pane)
    left_pane = create_left_pane(state.main_pane)
    
    state.outline_tree = create_outline_tree(left_pane, state.get_current_tab)
    
    def go_to_line(line_number):
        current_tab = state.get_current_tab()
        if not current_tab or not hasattr(current_tab, 'editor'): return
        editor = current_tab.editor
        try:
            editor.yview(f"{line_number}.0")
            editor.mark_set("insert", f"{line_number}.0")
            editor.focus()
        except ttk.TclError as e:
            debug_console.log(f"Error navigating to line: {e}", level='ERROR')

    state.error_panel = create_error_panel(left_pane, on_goto_line=go_to_line)
    state.notebook = create_notebook(state.main_pane)
    state.vertical_pane.add(state.main_pane, weight=1)

    console_frame, state.console_output = create_console_pane(state.vertical_pane)
    state.console_pane = console_frame
    actions.hide_console()

    def check_document_and_highlight(event=None):
        current_tab = state.get_current_tab()
        if current_tab and current_tab.editor:
            # Perform syntax highlighting
            editor_syntax.apply_syntax_highlighting(current_tab.editor)
            
            # Get all errors from the checker, providing the file path
            content = current_tab.editor.get("1.0", "end-1c")
            errors = state.checker.check(content, current_tab.file_path)
            errors.sort(key=lambda e: e.get('line', 0))
            
            # Update the error panel
            state.error_panel.update_errors(errors)

    def on_text_modified(event):
        state.root.after_idle(check_document_and_highlight)
        state.get_current_tab().editor.edit_modified(False)
        return None

    def on_tab_changed(event):
        actions.on_tab_changed(event)
        current_tab = state.get_current_tab()
        if current_tab:
            current_tab.editor.bind("<<Modified>>", on_text_modified)
            check_document_and_highlight()

    state.notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    state.llm_progress_bar = ttk.Progressbar(state.root, mode="indeterminate", length=200)
    state.status_bar_frame, state.status_label, state.gpu_status_label = create_status_bar(state.root)
    start_gpu_status_loop(state.gpu_status_label, state.root)
    
    bind_shortcuts(state.root)
    actions.load_session()
    state.root.protocol("WM_DELETE_WINDOW", actions.on_close_request)
    
    debug_console.log("GUI setup completed successfully.", level='SUCCESS')
    return state.root