
"""Centralize global application state and widget references."""

import ttkbootstrap as ttk
from tkinter import TclError
import os

# global ui component refs
root = None
notebook = None
tabs = {}
outline_tree = None
llm_progress_bar = None
status_bar_frame = None
status_label = None
gpu_status_label = None
main_pane = None
vertical_pane = None
console_pane = None
console_output = None
pdf_preview_interface = None
pdf_preview_pane = None
pdf_preview_parent = None

# Panel system refs
panel_manager = None
outline = None
debug_panel = None

# theme and config state
_theme_settings = {}
current_theme = "litera"
settings_menu = None
_app_config = {}
_status_bar_visible_var = None
_pdf_preview_visible_var = None

# editor performance config constants
zoom_factor = 1.1
min_font_size = 8
max_font_size = 36
LARGE_FILE_LINE_THRESHOLD = 1000
HEAVY_UPDATE_DELAY_NORMAL = 200
HEAVY_UPDATE_DELAY_LARGE_FILE = 2000
heavy_update_timer_id = None

# status bar and tab management state
_temporary_status_active = False
_temporary_status_timer_id = None
_closed_tabs_stack = []
_close_button_pressed_on_tab = None
# session state file managed in settings config

def get_theme_setting(key, default=None):
    """Retrieve theme setting value by key."""
    return _theme_settings.get(key, default)

def get_theme_settings():
    """Return complete theme settings dictionary."""
    return _theme_settings

def get_current_tab():
    """Retrieve currently selected editor tab instance."""
    global notebook, tabs
    if not notebook or not tabs:
        return None
    try:
        selected_tab_id = notebook.select()
        if not selected_tab_id:
            return None
        return tabs.get(selected_tab_id)
    except TclError:
        # handle notebook destruction or no tab selection state
        return None

def get_app_config():
    """Return application configuration dictionary."""
    return _app_config

def get_active_editor():
    """Return the editor widget for the active tab when available."""
    current_tab = get_current_tab()
    return getattr(current_tab, "editor", None) if current_tab else None


def get_active_file_path():
    """Return the file path of the active tab when available."""
    current_tab = get_current_tab()
    return getattr(current_tab, "file_path", None) if current_tab else None

