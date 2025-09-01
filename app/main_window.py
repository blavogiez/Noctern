"""Setup main graphical user interface for AutomaTeX application."""
import os
import time
import ttkbootstrap as ttk

from app import state, interface, config as app_config, theme as interface_theme
from app.zoom import ZoomManager
from app.topbar import create_top_buttons_frame
from app.panes import create_main_paned_window, create_left_pane, create_outline, create_debug_panel, create_notebook, create_console_pane, create_pdf_preview_pane
from app.panels import PanelManager
from app.status import create_status_bar, start_gpu_status_loop
from app.shortcuts import bind_global_shortcuts
from utils import logs_console, screen as screen_utils
from editor import syntax as editor_syntax
from editor.monaco_optimizer import initialize_monaco_optimization, apply_monaco_highlighting, suppress_monaco_updates
from pdf_preview.interface import PDFPreviewInterface

def _apply_startup_window_settings(window, config):
    """Apply window geometry and state from configuration."""
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
            logs_console.log(f"Could not parse monitor name '{monitor_name}'. Falling back to primary.", level='WARNING')

    window_state = config.get("window_state", "Normal")
    x, y = selected_monitor.x, selected_monitor.y
    if window_state == "Maximized":
        window.geometry(f"+{x}+{y}")
        window.state('zoomed')
    elif window_state == "Fullscreen":
        window.geometry(f"+{x}+{y}")
        window.attributes("-fullscreen", True)
    else: # Normal
        # Use better default sizing for modern screens
        min_width, min_height = 1400, 900
        width = min(min_width, int(selected_monitor.width * 0.8))
        height = min(min_height, int(selected_monitor.height * 0.8))
        x += (selected_monitor.width - width) // 2
        y += (selected_monitor.height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.minsize(1200, 700)

def setup_gui():
    """Initialize and setup main graphical user interface."""
    state._app_config = app_config.load_config()
    state.zoom_manager = ZoomManager(state)
    # Pre-compiler checker removed for performance optimization

    state.root = ttk.Window(themename="litera")
    
    valid_themes = state.root.style.theme_names()
    saved_theme = state._app_config.get("theme", "litera")
    if saved_theme in ["light", "dark"]: saved_theme = "litera" if saved_theme == "light" else "darkly"
    if saved_theme not in valid_themes and saved_theme != "original":
        saved_theme = "litera"
    state.root.style.theme_use(saved_theme if saved_theme != "original" else "litera")

    state.root.title("AutomaTeX v1.0")
    _apply_startup_window_settings(state.root, state._app_config) # RESTORED THIS CALL
    logs_console.log("GUI initialization process started.", level='INFO')

    
    # Force flatly theme as default instead of litera
    if saved_theme == "litera":
        saved_theme = "flatly"
        
    state.current_theme = saved_theme
    state._theme_settings = interface_theme.get_theme_colors(state.root.style, state.current_theme)

    logs_console.initialize(state.root)
    # Configure minimum log level to reduce console output
    logs_console.set_min_level('INFO')
    create_top_buttons_frame(state.root)
    
    # Check if PDF preview should be enabled before initialization
    show_pdf_preview = app_config.get_bool(state._app_config.get("show_pdf_preview", "True"))
    
    # Setup PDF preview interface only when enabled
    if show_pdf_preview:
        state.pdf_preview_interface = PDFPreviewInterface(state.root, state.get_current_tab)
        
        # Load PDF for initial tab after UI completion
        def load_initial_pdf():
            current_tab = state.get_current_tab()
            if current_tab and hasattr(state, 'pdf_preview_interface') and state.pdf_preview_interface:
                state.pdf_preview_interface.load_existing_pdf_for_tab(current_tab)
        
        state.root.after(300, load_initial_pdf)
    else:
        state.pdf_preview_interface = None

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
            # Handle end-of-file case (line_number == -1)
            if line_number == -1:
                # Navigate to last line
                last_line = int(editor.index('end-1c').split('.')[0])
                editor.yview(f"{last_line}.0")
                editor.mark_set("insert", f"{last_line}.0")
                editor.focus()
                # Add navigation highlight for last line
                from editor.highlight_manager import show_navigation_highlight
                show_navigation_highlight(editor, last_line)
            else:
                editor.yview(f"{line_number}.0")
                editor.mark_set("insert", f"{line_number}.0")
                editor.focus()
                # Add navigation highlight
                from editor.highlight_manager import show_navigation_highlight
                show_navigation_highlight(editor, line_number)
        except ttk.TclError as e:
            logs_console.log(f"Error navigating to line: {e}", level='ERROR')

    # Initialize optimized debug system with line navigation
    debug_coordinator, debug_panel = create_debug_panel(left_pane, on_goto_line=go_to_line)
    state.debug_coordinator = debug_coordinator
    state.debug_panel = debug_panel
    
    # Preserve legacy error_panel reference for compatibility
    state.error_panel = debug_panel
    
    # Initialize integrated panel manager
    state.panel_manager = PanelManager(
        left_pane_container=left_pane,
        outline_widget=state.outline.get_widget(),
        debug_widget=debug_panel,
        theme_getter=state.get_theme_setting
    )
    state.notebook = create_notebook(state.main_pane)
    
    # Setup PDF preview pane only when enabled
    if show_pdf_preview and state.pdf_preview_interface:
        pdf_preview_content = create_pdf_preview_pane(state.main_pane)
        state.pdf_preview_interface.create_preview_panel(pdf_preview_content)
        
        # Store UI element references for visibility management
        state.pdf_preview_pane = pdf_preview_content
        state.pdf_preview_parent = state.main_pane
    else:
        state.pdf_preview_pane = None
        state.pdf_preview_parent = None
    
    # Attach main pane to vertical layout container
    state.vertical_pane.add(state.main_pane, weight=1)

    # Configure PDF preview pane based on user settings
    if show_pdf_preview and state.pdf_preview_pane:
        state.main_pane.add(state.pdf_preview_pane.master, weight=1)
    
    console_frame, state.console_output = create_console_pane(state.vertical_pane)
    state.console_pane = console_frame
    interface.hide_console()

    # Track timing for update throttling
    last_update_time = 0
    update_pending = False

    def apply_monaco_updates(event=None):
        nonlocal update_pending
        
        current_tab = state.get_current_tab()
        if current_tab and current_tab.editor:
            # Apply differential highlighting for performance
            from editor import syntax as editor_syntax
            editor_syntax.apply_differential_syntax_highlighting(current_tab.editor)
            # Throttle outline updates to once per second maximum
            if time.time() - last_update_time > 1.0:  # Max once per second
                state.outline.update_outline(current_tab.editor)
            
        # Clear update pending status
        update_pending = False

    def on_text_modified(event):
        nonlocal last_update_time, update_pending
        
        # Handle text modification events with Monaco optimization
        current_tab = state.get_current_tab()
        if not current_tab or event.widget != current_tab.editor:
            return None
            
        # Throttle updates during continuous typing
        suppress_monaco_updates(current_tab.editor, 50)
        
        # Update line numbers with performance optimization
        if hasattr(current_tab, 'line_numbers') and current_tab.line_numbers:
            from editor.line_number_manager import schedule_line_number_update
            schedule_line_number_update(current_tab.line_numbers)
        
        # Reset modified flag to prevent event recursion
        current_tab.editor.edit_modified(False)
        
        # Update tab title to show dirty state
        current_tab.update_tab_title()
        
        # Trigger PDF preview updates with rate limiting
        current_time = time.time()
        if current_time - last_update_time > 0.5:  # Max twice per second
            if hasattr(state, 'pdf_preview_interface') and state.pdf_preview_interface:
                state.pdf_preview_interface.on_editor_content_change()
            last_update_time = current_time
        
        # Prevent duplicate updates when one is pending
        if update_pending:
            return None
            
        update_pending = True
        
        # Schedule delayed update with minimal debouncing
        delay = 50  # Very short delay since we only process changed lines
        state.root.after(delay, apply_monaco_updates)
        return None

    def bind_text_modified_event(tab):
        """Bind text modification events to editor tab."""
        if tab and tab.editor:
            # Remove existing bindings to prevent conflicts
            tab.editor.unbind("<<Modified>>")
            tab.editor.bind("<<Modified>>", on_text_modified)
            # Bind KeyRelease for comprehensive change detection
            tab.editor.bind("<KeyRelease>", on_text_modified, add='+')
            logs_console.log(f"Bound <<Modified>> and <KeyRelease> events to tab: {tab.file_path if tab.file_path else 'Untitled'}", level='TRACE')

    def on_tab_changed(event):
        interface.on_tab_changed(event)
        current_tab = state.get_current_tab()
        if current_tab:
            bind_text_modified_event(current_tab)
            # Setup Monaco optimization for newly selected tab
            initialize_monaco_optimization(current_tab.editor)
            # Trigger syntax highlighting for tab switch
            state.root.after(20, apply_monaco_updates)
            
            # Load associated PDF document for current tab
            if hasattr(state, 'pdf_preview_interface') and state.pdf_preview_interface:
                state.pdf_preview_interface.load_existing_pdf_for_tab(current_tab)
            
            # Refresh status bar with current file information
            from app import status_utils
            status_utils.update_status_bar_text()
            
    # Bind modification events to initial tab
    state.root.after(100, lambda: bind_text_modified_event(state.get_current_tab()))

    state.notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    bind_global_shortcuts(state.root)
    
    interface.load_session()
    
    def set_window_proportions():
        """Set precise window proportions: 15% left, 42.5% editor, 42.5% PDF"""
        try:
            # Force window update to get real dimensions
            state.root.update_idletasks()
            
            # Get main pane width
            main_pane_width = state.main_pane.winfo_width()
            if main_pane_width <= 1:
                # Retry if width not ready
                state.root.after(100, set_window_proportions)
                return
                
            # Calculate exact positions for 15%/42.5%/42.5%
            left_pos = int(main_pane_width * 0.15)
            editor_pos = int(main_pane_width * 0.575)  # 15% + 42.5%
            
            # Force sash positions using correct TTK PanedWindow syntax
            try:
                # Use sashpos instead of sash place for ttk PanedWindow
                state.main_pane.tk.call(state.main_pane._w, 'sashpos', 0, left_pos)
                if len(state.main_pane.panes()) > 2:  # PDF preview exists
                    state.main_pane.tk.call(state.main_pane._w, 'sashpos', 1, editor_pos)
            except Exception as sash_error:
                logs_console.log(f"Sash positioning failed: {sash_error}", level='ERROR')
                
            logs_console.log(f"Window proportions set: {left_pos}px left, {editor_pos - left_pos}px editor, {main_pane_width - editor_pos}px PDF", level='INFO')
        except Exception as e:
            logs_console.log(f"Error setting proportions: {e}", level='ERROR')
    
    def maintain_proportions(event=None):
        """Maintain proportions on window resize"""
        if event and event.widget == state.main_pane:
            state.root.after(50, set_window_proportions)
    
    # Bind resize event to maintain proportions
    state.main_pane.bind("<Configure>", maintain_proportions)
    
    # Set initial proportions with proper timing
    state.root.after(200, set_window_proportions)
    
    # Plan initial error checking after session restoration
    # Setup Monaco optimization for initial tab
    first_tab = state.get_current_tab()
    if first_tab and first_tab.editor:
        initialize_monaco_optimization(first_tab.editor)
    state.root.after(100, apply_monaco_updates)
    state.root.protocol("WM_DELETE_WINDOW", interface.on_close_request)
    
    # Setup status bar based on user configuration
    show_status_bar = app_config.get_bool(state._app_config.get("show_status_bar", "True"))
    
    if show_status_bar:
        status_bar_frame, status_label, gpu_status_label, metrics_display = create_status_bar(state.root)
        state.status_bar_frame = status_bar_frame
        state.status_label = status_label
        state.gpu_status_label = gpu_status_label
        state.metrics_display = metrics_display
    else:
        # Set status bar variables to None when disabled
        state.status_bar_frame = None
        state.status_label = None
        state.metrics_display = None
        state.gpu_status_label = None
    
    # Setup visibility state variables from configuration
    from app import ui_visibility
    
    state._status_bar_visible_var = ttk.BooleanVar(value=show_status_bar)
    state._pdf_preview_visible_var = ttk.BooleanVar(value=show_pdf_preview)
    
    # Initialize GPU status monitoring when status bar enabled
    if show_status_bar and state.gpu_status_label:
        start_gpu_status_loop(state.gpu_status_label, state.root)
    
    logs_console.log("GUI setup completed successfully.", level='SUCCESS')
    return state.root
