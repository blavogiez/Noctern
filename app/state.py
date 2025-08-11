
"""
This module centralizes the global state of the AutomaTeX application.

It holds references to key Tkinter widgets, application configuration, 
and other state variables that need to be accessible across different modules.
This avoids circular dependencies and provides a single source of truth for the application's state.
"""

import ttkbootstrap as ttk
from tkinter import TclError
from utils import debug_console
import os

# --- Global UI Component References ---
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

# --- Theme and Configuration Variables ---
_theme_settings = {}
current_theme = "litera"
settings_menu = None
_app_config = {}
_status_bar_visible_var = None
_pdf_preview_visible_var = None

# --- Editor and Performance Constants ---
zoom_factor = 1.1
min_font_size = 8
max_font_size = 36
LARGE_FILE_LINE_THRESHOLD = 1000
HEAVY_UPDATE_DELAY_NORMAL = 200
HEAVY_UPDATE_DELAY_LARGE_FILE = 2000
heavy_update_timer_id = None

# --- Status Bar and Tab Management Variables ---
_temporary_status_active = False
_temporary_status_timer_id = None
_closed_tabs_stack = []
_close_button_pressed_on_tab = None
# SESSION_STATE_FILE is now managed in settings.conf

def get_theme_setting(key, default=None):
    """
    Retrieves a specific theme setting value by its key.
    """
    return _theme_settings.get(key, default)

def get_theme_settings():
    """
    Returns the entire dictionary of current theme settings.
    """
    return _theme_settings

def get_current_tab():
    """
    Retrieves the currently selected `EditorTab` instance from the notebook.
    """
    global notebook, tabs
    if not notebook or not tabs:
        return None
    try:
        selected_tab_id = notebook.select()
        if not selected_tab_id:
            return None
        return tabs.get(selected_tab_id)
    except TclError:
        # This can happen if the notebook is being destroyed
        # or no tab is selected.
        # debug_console.log("No tab currently selected in the notebook.", level='DEBUG')
        return None

def get_app_config():
    """
    Returns the application's configuration dictionary.
    """
    return _app_config


