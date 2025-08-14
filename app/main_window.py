"""
This module is responsible for setting up the main graphical user interface (GUI)
of the AutomaTeX application.
"""
import os
import time
import ttkbootstrap as ttk

from app import state, actions, config as app_config, theme as interface_theme
from app.zoom import ZoomManager
from app.topbar import create_top_buttons_frame
from app.panes import create_main_paned_window, create_left_pane, create_outline, create_debug_panel, create_notebook, create_console_pane, create_pdf_preview_pane
from app.status import create_status_bar, start_gpu_status_loop
from app.shortcuts import bind_global_shortcuts
from utils import debug_console, screen as screen_utils
from editor import syntax as editor_syntax
from editor.monaco_optimizer import initialize_monaco_optimization, apply_monaco_highlighting, suppress_monaco_updates
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
    # Removed pre-compiler checker for performance

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

    
    # Ensure we use flatly as default theme
    if saved_theme == "litera":
        saved_theme = "flatly"
        
    state.current_theme = saved_theme
    state._theme_settings = interface_theme.get_theme_colors(state.root.style, state.current_theme)

    debug_console.initialize(state.root)
    # Set minimum log level to reduce verbosity
    debug_console.set_min_level('INFO')
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
    
    state.outline = create_outline(left_pane, state.get_current_tab, state._app_config)
    
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

    # Créer le nouveau système de debug ultra-rapide
    debug_coordinator, debug_panel = create_debug_panel(left_pane, on_goto_line=go_to_line)
    state.debug_coordinator = debug_coordinator
    state.debug_panel = debug_panel
    
    # Maintenir la compatibilité avec l'ancien nom
    state.error_panel = debug_panel
    state.notebook = create_notebook(state.main_pane)
    
    # Create PDF preview pane
    pdf_preview_content = create_pdf_preview_pane(state.main_pane)
    state.pdf_preview_interface.create_preview_panel(pdf_preview_content)
    
    # Store references to UI elements we want to be able to hide
    state.pdf_preview_pane = pdf_preview_content
    state.pdf_preview_parent = state.main_pane
    
    # Add main pane to vertical pane
    state.vertical_pane.add(state.main_pane, weight=1)

    # Add PDF preview pane according to user preferences
    show_pdf_preview = app_config.get_bool(state._app_config.get("show_pdf_preview", "True"))
    if show_pdf_preview:
        state.main_pane.add(state.pdf_preview_pane.master, weight=3)  # Increased weight for larger default size
    
    console_frame, state.console_output = create_console_pane(state.vertical_pane)
    state.console_pane = console_frame
    actions.hide_console()

    # Variable to track the last update time
    last_update_time = 0
    update_pending = False

    def apply_monaco_updates(event=None):
        nonlocal update_pending
        
        current_tab = state.get_current_tab()
        if current_tab and current_tab.editor:
            # ULTRA-FAST differential highlighting - no debouncing needed!
            from editor import syntax as editor_syntax
            editor_syntax.apply_differential_syntax_highlighting(current_tab.editor)
            # Only update outline occasionally, not every keystroke
            if time.time() - last_update_time > 1.0:  # Max once per second
                state.outline.update_outline(current_tab.editor)
            
        # Reset the pending flag
        update_pending = False

    def on_text_modified(event):
        nonlocal last_update_time, update_pending
        
        # Ultra-fast event handling - Monaco style
        current_tab = state.get_current_tab()
        if not current_tab or event.widget != current_tab.editor:
            return None
            
        # Suppress updates during rapid typing
        suppress_monaco_updates(current_tab.editor, 50)
        
        # Set the modified flag to False to avoid infinite loop
        current_tab.editor.edit_modified(False)
        
        # Ultra-lightweight PDF preview trigger (only occasionally)
        current_time = time.time()
        if current_time - last_update_time > 0.5:  # Max twice per second
            if hasattr(state, 'pdf_preview_interface') and state.pdf_preview_interface:
                state.pdf_preview_interface.on_editor_content_change()
            last_update_time = current_time
        
        # Skip if update already pending
        if update_pending:
            return None
            
        update_pending = True
        
        # Ultra-fast debouncing - differential highlighting is so fast we can be responsive
        delay = 50  # Very short delay since we only process changed lines
        state.root.after(delay, apply_monaco_updates)
        return None

    def bind_text_modified_event(tab):
        """Bind the text modified event to a tab."""
        if tab and tab.editor:
            # Unbind any existing binding first to avoid duplicates
            tab.editor.unbind("<<Modified>>")
            tab.editor.bind("<<Modified>>", on_text_modified)
            # Also bind KeyRelease to ensure we catch all changes
            tab.editor.bind("<KeyRelease>", on_text_modified)
            debug_console.log(f"Bound <<Modified>> and <KeyRelease> events to tab: {tab.file_path if tab.file_path else 'Untitled'}", level='TRACE')

    def on_tab_changed(event):
        actions.on_tab_changed(event)
        current_tab = state.get_current_tab()
        if current_tab:
            bind_text_modified_event(current_tab)
            # Initialize Monaco optimization for new tab
            initialize_monaco_optimization(current_tab.editor)
            # Apply syntax highlighting when tab changes
            state.root.after(20, apply_monaco_updates)
            
            # Load existing PDF for the tab if it exists
            if hasattr(state, 'pdf_preview_interface') and state.pdf_preview_interface:
                state.pdf_preview_interface.load_existing_pdf_for_tab(current_tab)
            
            # Update status bar with file info
            from app import status_utils
            status_utils.update_status_bar_text()
            
    # Also bind the text modified event to the initial tab
    state.root.after(100, lambda: bind_text_modified_event(state.get_current_tab()))

    state.notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    bind_global_shortcuts(state.root)
    
    actions.load_session()
    # Schedule an initial error check after loading session
    # Initialize first tab with Monaco optimization
    first_tab = state.get_current_tab()
    if first_tab and first_tab.editor:
        initialize_monaco_optimization(first_tab.editor)
    state.root.after(100, apply_monaco_updates)
    state.root.protocol("WM_DELETE_WINDOW", actions.on_close_request)
    
    # Create the status bar according to user preferences
    show_status_bar = app_config.get_bool(state._app_config.get("show_status_bar", "True"))
    
    if show_status_bar:
        status_bar_frame, status_label, gpu_status_label, metrics_display = create_status_bar(state.root)
        state.status_bar_frame = status_bar_frame
        state.status_label = status_label
        state.gpu_status_label = gpu_status_label
        state.metrics_display = metrics_display
    else:
        # Initialize variables to None if status bar is not shown
        state.status_bar_frame = None
        state.status_label = None
        state.metrics_display = None
        state.gpu_status_label = None
    
    # Initialize visibility tracking variables with saved settings
    from app import ui_visibility
    show_pdf_preview = app_config.get_bool(state._app_config.get("show_pdf_preview", "True"))
    
    state._status_bar_visible_var = ttk.BooleanVar(value=show_status_bar)
    state._pdf_preview_visible_var = ttk.BooleanVar(value=show_pdf_preview)
    
    # Apply initial visibility settings for PDF preview (status bar is already handled above)
    if not show_pdf_preview:
        ui_visibility.toggle_pdf_preview()
    
    # Start the GPU status update loop if status bar is shown
    if show_status_bar and state.gpu_status_label:
        start_gpu_status_loop(state.gpu_status_label, state.root)
    
    debug_console.log("GUI setup completed successfully.", level='SUCCESS')
    return state.root
