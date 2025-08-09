"""
This module is responsible for setting up the main graphical user interface (GUI)
of the AutomaTeX application.
"""
import os
import ttkbootstrap as ttk

from app import state, actions, config as app_config, theme as interface_theme
from app.zoom import ZoomManager
from app.topbar import create_top_buttons_frame
from app.panes import create_main_paned_window, create_left_pane, create_outline, create_error_panel, create_notebook, create_console_pane, create_pdf_preview_pane
from app.status import create_status_bar, start_gpu_status_loop
from app.shortcuts import bind_global_shortcuts
from utils import debug_console, screen as screen_utils
from pre_compiler.checker import Checker
from editor import syntax as editor_syntax
from pdf_preview.interface import PDFPreviewInterface

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
    state.checker = Checker()

    state.root = ttk.Window(themename="litera")
    
    valid_themes = state.root.style.theme_names()
    saved_theme = state._app_config.get("theme", "litera")
    if saved_theme in ["light", "dark"]: saved_theme = "litera" if saved_theme == "light" else "darkly"
    if saved_theme not in valid_themes and saved_theme != "original":
        saved_theme = "litera"
    state.root.style.theme_use(saved_theme if saved_theme != "original" else "litera")

    state.root.title("AutomaTeX v1.0")
    _apply_startup_window_settings(state.root, state._app_config) # RESTORED THIS CALL
    debug_console.log("GUI initialization process started.", level='INFO')

    state._auto_open_pdf_var = ttk.BooleanVar(value=app_config.get_bool(state._app_config.get('auto_open_pdf', 'False')))
    state.current_theme = saved_theme
    state._theme_settings = interface_theme.get_theme_colors(state.root.style, state.current_theme)

    debug_console.initialize(state.root)
    create_top_buttons_frame(state.root)
    
    # Initialize PDF preview interface
    state.pdf_preview_interface = PDFPreviewInterface(state.root, state.get_current_tab)
    
    # After UI is set up, load PDF for initial tab
    def load_initial_pdf():
        current_tab = state.get_current_tab()
        if current_tab and hasattr(state, 'pdf_preview_interface') and state.pdf_preview_interface:
            state.pdf_preview_interface.load_existing_pdf_for_tab(current_tab)
    
    state.root.after(300, load_initial_pdf)

    state.vertical_pane = ttk.PanedWindow(state.root, orient=ttk.VERTICAL)
    state.vertical_pane.pack(fill="both", expand=True)

    state.main_pane = create_main_paned_window(state.vertical_pane)
    left_pane = create_left_pane(state.main_pane)
    
    state.outline = create_outline(left_pane, state.get_current_tab)
    
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
    
    # Create PDF preview pane
    pdf_preview_content = create_pdf_preview_pane(state.main_pane)
    
    state.vertical_pane.add(state.main_pane, weight=1)

    console_frame, state.console_output = create_console_pane(state.vertical_pane)
    state.console_pane = console_frame
    actions.hide_console()

    # Variable to track the last update time
    last_update_time = 0
    update_pending = False

    def check_document_and_highlight(event=None):
        nonlocal last_update_time, update_pending
        
        current_tab = state.get_current_tab()
        if current_tab and current_tab.editor:
            editor_syntax.apply_syntax_highlighting(current_tab.editor)
            state.outline.update_outline(current_tab.editor) # Update outline
            content = current_tab.editor.get("1.0", "end-1c")
            errors = state.checker.check(content, current_tab.file_path)
            errors.sort(key=lambda e: e.get('line', 0))
            state.error_panel.update_errors(errors)
            # Force the update of the UI
            state.root.update_idletasks()
            
        # Reset the pending flag
        update_pending = False

    def on_text_modified(event):
        nonlocal last_update_time, update_pending
        
        # Log to debug
        current_tab = state.get_current_tab()
        if current_tab and current_tab.file_path:
            debug_console.log(f"Text modified in tab: {os.path.basename(current_tab.file_path)}", level='DEBUG')
        
        # Check if the event is from the current tab
        if not current_tab or event.widget != current_tab.editor:
            return None
            
        # Set the modified flag to False to avoid infinite loop
        current_tab.editor.edit_modified(False)
        debug_console.log(f"Reset edit_modified flag for tab: {os.path.basename(current_tab.file_path) if current_tab.file_path else 'Untitled'}", level='DEBUG')
        
        # Trigger PDF preview update
        if hasattr(state, 'pdf_preview_interface') and state.pdf_preview_interface:
            state.pdf_preview_interface.on_editor_content_change()
        
        # If an update is already pending, skip this one
        if update_pending:
            debug_console.log(f"Skipping update for tab: {os.path.basename(current_tab.file_path) if current_tab.file_path else 'Untitled'} - update already pending", level='DEBUG')
            return None
            
        # Set the pending flag
        update_pending = True
        
        # Schedule the update
        state.root.after(100, check_document_and_highlight)
        return None

    def bind_text_modified_event(tab):
        """Bind the text modified event to a tab."""
        if tab and tab.editor:
            # Unbind any existing binding first to avoid duplicates
            tab.editor.unbind("<<Modified>>")
            tab.editor.bind("<<Modified>>", on_text_modified)
            # Also bind KeyRelease to ensure we catch all changes
            tab.editor.bind("<KeyRelease>", on_text_modified)
            debug_console.log(f"Bound <<Modified>> and <KeyRelease> events to tab: {tab.file_path if tab.file_path else 'Untitled'}", level='DEBUG')

    def on_tab_changed(event):
        actions.on_tab_changed(event)
        current_tab = state.get_current_tab()
        if current_tab:
            bind_text_modified_event(current_tab)
            # Always check document when tab changes
            state.root.after(50, check_document_and_highlight)
            
            # Load existing PDF for the tab if it exists
            if hasattr(state, 'pdf_preview_interface') and state.pdf_preview_interface:
                state.pdf_preview_interface.load_existing_pdf_for_tab(current_tab)
            
    # Also bind the text modified event to the initial tab
    state.root.after(100, lambda: bind_text_modified_event(state.get_current_tab()))

    state.notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    bind_global_shortcuts(state.root)
    
    actions.load_session()
    # Schedule an initial error check after loading session
    state.root.after(200, check_document_and_highlight)
    state.root.protocol("WM_DELETE_WINDOW", actions.on_close_request)
    
    # Create the status bar
    status_bar_frame, status_label, gpu_status_label = create_status_bar(state.root)
    state.status_bar_frame = status_bar_frame
    state.status_label = status_label
    state.gpu_status_label = gpu_status_label
    
    # Start the GPU status update loop
    start_gpu_status_loop(state.gpu_status_label, state.root)
    
    debug_console.log("GUI setup completed successfully.", level='SUCCESS')
    return state.root
