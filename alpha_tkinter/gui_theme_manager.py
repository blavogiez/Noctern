import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
import platform
import sv_ttk # Import sv_ttk

# References to main GUI components and callbacks
_root = None
_tabs_dict = None # Reference to the global tabs dictionary
_perform_heavy_updates_callback = None # Callback to trigger syntax highlighting, outline updates etc.
_theme_settings = {} # Store current theme colors and properties
_current_theme = "light" # Initial theme state

def initialize(root_ref, tabs_dict_ref, perform_heavy_updates_cb):
    """Initializes the theme manager with necessary references."""
    global _root, _tabs_dict, _perform_heavy_updates_callback
    _root = root_ref
    _tabs_dict = tabs_dict_ref
    _perform_heavy_updates_callback = perform_heavy_updates_cb

def get_theme_setting(key, default=None):
    """Gets a value from the current theme settings."""
    return _theme_settings.get(key, default)

def apply_theme(theme_name):
    """Applies the specified theme (light or dark) to the GUI."""
    global _current_theme, _theme_settings, _root

    if not _root: # Guard against calling too early
        return

    # Set the theme using sv_ttk
    sv_ttk.set_theme(theme_name)
    _current_theme = theme_name

    # Define colors based on theme
    if theme_name == "light":
        _theme_settings = {
            "root_bg": "#fdfdfd", # Adjusted to match typical sv_ttk light theme
            "fg_color": "#000000", # General foreground for non-ttk elements
            "sel_bg": "#0078d4", "sel_fg": "#ffffff", # Selection colors for editor (inspired by Windows)
            "editor_bg": "#ffffff", "editor_fg": "#1e1e1e", "editor_insert_bg": "#333333",
            "comment_color": "#008000", "command_color": "#0000ff", "brace_color": "#ff007f",
            "ln_text_color": "#888888", "ln_bg_color": "#f7f7f7", "ln_current_text_color": "#000000", # Black for light theme
            "current_line_bg": "#f8f8f8", # Very subtle light grey
            "panedwindow_sash": "#e6e6e6", # Light sash for PanedWindow if sv_ttk doesn't fully style it
        }
    elif theme_name == "dark":
        _theme_settings = {
            "root_bg": "#202020", # Adjusted to match typical sv_ttk dark theme
            "fg_color": "#ffffff", # General foreground for non-ttk elements
            "sel_bg": "#0078d4", "sel_fg": "#ffffff", # Selection colors for editor
            "editor_bg": "#1e1e1e", "editor_fg": "#d4d4d4", "editor_insert_bg": "#d4d4d4",
            "comment_color": "#608b4e", "command_color": "#569cd6", "brace_color": "#c586c0",
            "ln_text_color": "#6a6a6a", "ln_bg_color": "#252526", "ln_current_text_color": "#ffffff", # White for dark theme
            "current_line_bg": "#222222", # Very subtle dark grey
            "panedwindow_sash": "#333333", # Dark sash for PanedWindow
        }
    else:
        return

    # Apply colors to the root window
    _root.configure(bg=_theme_settings["root_bg"])

    # Apply theme to all open editor tabs (tk.Text widgets)
    if _tabs_dict:
        for tab_widget in _tabs_dict.values():
            if tab_widget.editor: # Check if the tab has an editor (it should)
                tab_widget.editor.configure(
                    background=_theme_settings["editor_bg"], foreground=_theme_settings["editor_fg"],
                    selectbackground=_theme_settings["sel_bg"], selectforeground=_theme_settings["sel_fg"],
                    insertbackground=_theme_settings["editor_insert_bg"],
                    relief=tk.FLAT, borderwidth=0
                )

                # Update the generated_text tag font
                generated_text_font = tab_widget.editor_font.copy()
                generated_text_font.configure(slant="italic")
                tab_widget.editor.tag_configure("generated_text", font=generated_text_font)

                tab_widget.editor.tag_configure("current_line", background=_theme_settings["current_line_bg"])
                # Configure tags for each editor instance
                tab_widget.editor.tag_configure("latex_command", foreground=_theme_settings["command_color"], font=tab_widget.editor_font)
                tab_widget.editor.tag_configure("latex_brace", foreground=_theme_settings["brace_color"], font=tab_widget.editor_font)
                comment_font = tab_widget.editor_font.copy()
                comment_font.configure(slant="italic")
                tab_widget.editor.tag_configure("latex_comment", foreground=_theme_settings["comment_color"], font=comment_font)
            
            # Update the theme of the line numbers canvas for each tab
            if tab_widget.line_numbers:
                tab_widget.line_numbers.update_theme(
                    text_color=_theme_settings["ln_text_color"], bg_color=_theme_settings["ln_bg_color"],
                    current_line_text_color=_theme_settings["ln_current_text_color"]
                )

    # Trigger a heavy update to redraw syntax highlighting, outline, and line numbers
    _perform_heavy_updates_callback()
    _root.update_idletasks()