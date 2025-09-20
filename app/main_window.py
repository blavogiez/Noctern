"""Setup main graphical user interface for Noctern application."""
import os
import time
import ttkbootstrap as ttk
from PIL import Image, ImageTk

from app import state, interface, config as app_config, theme as interface_theme
from app.zoom import ZoomManager
from app.topbar import create_top_buttons_frame
from app.panes import create_main_paned_window, create_left_pane, create_outline, create_debug_panel, create_notebook, create_console_pane, create_pdf_preview_pane
from app.panels import PanelManager
from app.status import create_status_bar, start_gpu_status_loop
from app.shortcuts import bind_global_shortcuts
from utils import logs_console, screen as screen_utils
from editor import syntax as editor_syntax
from editor.monaco_optimizer import initialize_monaco_optimization, suppress_monaco_updates
from pdf_preview.interface import PDFPreviewInterface



class MonacoUpdateController:
    """Manage Monaco-based editor updates with throttling."""

    def __init__(self, app_state):
        self.state = app_state
        self._update_pending = False
        self._last_pdf_update = 0.0
        self._last_outline_update = 0.0

    def bind_tab(self, tab):
        if tab and getattr(tab, "editor", None):
            tab.editor.unbind("<<Modified>>")
            tab.editor.bind("<<Modified>>", self._on_text_modified)
            tab.editor.bind("<KeyRelease>", self._on_text_modified, add='+')
            label = tab.file_path if getattr(tab, "file_path", None) else "Untitled"
            logs_console.log(f"Bound <<Modified>> and <KeyRelease> events to tab: {label}", level='TRACE')

    def bind_current_tab(self):
        self.bind_tab(self.state.get_current_tab())

    def handle_tab_change(self):
        current_tab = self.state.get_current_tab()
        if not current_tab or not getattr(current_tab, "editor", None):
            return

        self.bind_tab(current_tab)
        initialize_monaco_optimization(current_tab.editor)
        if getattr(self.state, "root", None):
            self.state.root.after(20, self.apply_updates)

        pdf_interface = getattr(self.state, "pdf_preview_interface", None)
        if pdf_interface:
            pdf_interface.load_existing_pdf_for_tab(current_tab)

        try:
            from app import status_utils
        except ImportError:
            logs_console.log("Status utilities unavailable after tab change.", level='WARNING')
        else:
            status_utils.update_status_bar_text()

    def apply_updates(self):
        current_tab = self.state.get_current_tab()
        if current_tab and getattr(current_tab, "editor", None):
            editor_syntax.apply_differential_syntax_highlighting(current_tab.editor)

            outline = getattr(self.state, "outline", None)
            if outline and hasattr(outline, "update_outline"):
                now = time.time()
                if now - self._last_outline_update > 1.0:
                    outline.update_outline(current_tab.editor)
                    self._last_outline_update = now

        self._update_pending = False

    def _schedule_update(self):
        if self._update_pending or not getattr(self.state, "root", None):
            return
        self._update_pending = True
        self.state.root.after(50, self.apply_updates)

    def _on_text_modified(self, event):
        current_tab = self.state.get_current_tab()
        editor_widget = getattr(current_tab, "editor", None) if current_tab else None
        if not current_tab or event.widget != editor_widget:
            return None

        suppress_monaco_updates(editor_widget, 50)

        line_numbers = getattr(current_tab, "line_numbers", None)
        if line_numbers:
            try:
                from editor.line_number_manager import schedule_line_number_update
                schedule_line_number_update(line_numbers)
            except ImportError:
                logs_console.log("Line number manager unavailable for Monaco updates.", level='WARNING')

        editor_widget.edit_modified(False)
        current_tab.update_tab_title()

        pdf_interface = getattr(self.state, "pdf_preview_interface", None)
        now = time.time()
        if pdf_interface and now - self._last_pdf_update > 0.5:
            pdf_interface.on_editor_content_change()
            self._last_pdf_update = now

        self._schedule_update()
        return None
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

    state.root.title("Noctern")
    
    # Set application icon
    try:
        icon_path = os.path.join("resources", "app_icon.ico")
        if os.path.exists(icon_path):
            state.root.iconbitmap(icon_path)
            logs_console.log("Application icon loaded successfully.", level='DEBUG')
        else:
            logs_console.log(f"Icon file not found at {icon_path}", level='WARNING')
    except Exception as e:
        logs_console.log(f"Failed to load application icon: {e}", level='WARNING')
    
    _apply_startup_window_settings(state.root, state._app_config) # RESTORED THIS CALL
    logs_console.log("GUI initialization process started.", level='INFO')

    
    # Force flatly theme as default instead of litera
    if saved_theme == "litera":
        saved_theme = "flatly"
        
    state.current_theme = saved_theme
    state._theme_settings = interface_theme.get_theme_colors(state.root.style, state.current_theme)

    logs_console.initialize(state.root)
    # configure min log level to reduce console output
    logs_console.set_min_level('INFO')
    create_top_buttons_frame(state.root)
    
    # Check if pdf preview should be enabled before init
    show_pdf_preview = app_config.get_bool(state._app_config.get("show_pdf_preview", "True"))
    
    # setup pdf preview interface only when enabled
    if show_pdf_preview:
        state.pdf_preview_interface = PDFPreviewInterface(state.root, state.get_current_tab)
        
        # load pdf for initial tab after ui completion
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
            # handle end-of-file case (line_number == -1)
            if line_number == -1:
                # navigate to last line
                last_line = int(editor.index('end-1c').split('.')[0])
                editor.yview(f"{last_line}.0")
                editor.mark_set("insert", f"{last_line}.0")
                editor.focus()
                # add navigation highlight for last line
                from editor.highlight_manager import show_navigation_highlight
                show_navigation_highlight(editor, last_line)
            else:
                editor.yview(f"{line_number}.0")
                editor.mark_set("insert", f"{line_number}.0")
                editor.focus()
                # add navigation highlight
                from editor.highlight_manager import show_navigation_highlight
                show_navigation_highlight(editor, line_number)
        except ttk.TclError as e:
            logs_console.log(f"Error navigating to line: {e}", level='ERROR')

    # Initialize optimized debug system with line navigation
    debug_coordinator, debug_panel = create_debug_panel(left_pane, on_goto_line=go_to_line)
    state.debug_coordinator = debug_coordinator
    state.debug_panel = debug_panel
    
    # preserve legacy error_panel reference for compatibility
    state.error_panel = debug_panel
    
    # init integrated panel manager
    state.panel_manager = PanelManager(
        left_pane_container=left_pane,
        outline_widget=state.outline.get_widget(),
        debug_widget=debug_panel,
        theme_getter=state.get_theme_setting
    )
    state.notebook = create_notebook(state.main_pane)
    
    # setup pdf preview pane only when enabled
    if show_pdf_preview and state.pdf_preview_interface:
        pdf_preview_content = create_pdf_preview_pane(state.main_pane)
        state.pdf_preview_interface.create_preview_panel(pdf_preview_content)
        
        # store ui element refs for visibility management
        state.pdf_preview_pane = pdf_preview_content
        state.pdf_preview_parent = state.main_pane
    else:
        state.pdf_preview_pane = None
        state.pdf_preview_parent = None
    
    # attach main pane to vertical layout container
    state.vertical_pane.add(state.main_pane, weight=1)

    # configure pdf preview pane based on user settings
    if show_pdf_preview and state.pdf_preview_pane:
        state.main_pane.add(state.pdf_preview_pane.master, weight=1)
    
    console_frame, state.console_output = create_console_pane(state.vertical_pane)
    state.console_pane = console_frame
    interface.hide_console()

    monaco_controller = MonacoUpdateController(state)

    def on_tab_changed(event):
        interface.on_tab_changed(event)
        monaco_controller.handle_tab_change()

    state.root.after(100, monaco_controller.bind_current_tab)

    state.notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    bind_global_shortcuts(state.root)

    interface.load_session()
    
    # apply startup layout instantly - 15% left, 42.5% editor, 42.5% pdf
    state.root.update_idletasks()
    try:
        # calculate sash positions based on window width
        window_width = state.root.winfo_width()
        left_sash_pos = int(window_width * 0.20) 
        editor_sash_pos = int(window_width * 0.595)
        
        # set main pane sash positions
        state.main_pane.tk.call(state.main_pane._w, 'sashpos', 0, left_sash_pos)
        if len(state.main_pane.panes()) > 2:
            state.main_pane.tk.call(state.main_pane._w, 'sashpos', 1, editor_sash_pos)
    except:
        pass  # silent fail for startup
    
    # plan initial error checking after session restoration
    # setup monaco optimization for initial tab
    first_tab = state.get_current_tab()
    if first_tab and first_tab.editor:
        initialize_monaco_optimization(first_tab.editor)
    state.root.after(100, monaco_controller.apply_updates)
    state.root.protocol("WM_DELETE_WINDOW", interface.on_close_request)
    
    # setup status bar based on user config
    show_status_bar = app_config.get_bool(state._app_config.get("show_status_bar", "True"))
    
    if show_status_bar:
        status_bar_frame, status_label, gpu_status_label, metrics_display = create_status_bar(state.root)
        state.status_bar_frame = status_bar_frame
        state.status_label = status_label
        state.gpu_status_label = gpu_status_label
        state.metrics_display = metrics_display
    else:
        # set status bar vars to none when disabled
        state.status_bar_frame = None
        state.status_label = None
        state.metrics_display = None
        state.gpu_status_label = None
    
    # setup visibility state vars from config
    from app import ui_visibility
    
    state._status_bar_visible_var = ttk.BooleanVar(value=show_status_bar)
    state._pdf_preview_visible_var = ttk.BooleanVar(value=show_pdf_preview)
    
    # init gpu status monitoring when status bar enabled
    if show_status_bar and state.gpu_status_label:
        start_gpu_status_loop(state.gpu_status_label, state.root)
    
    logs_console.log("GUI setup completed successfully.", level='SUCCESS')
    return state.root
