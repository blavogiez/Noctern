"""
This module manages the application's visual themes using ttkbootstrap,
providing functions to apply a chosen theme to all relevant GUI components,
including editor elements and custom widgets.
"""

import ttkbootstrap as ttk
from tkinter.font import Font

def get_theme_colors(style, theme_name):
    """
    Returns a dictionary of color settings derived from the current ttkbootstrap theme.

    Args:
        style (ttk.Style): The ttkbootstrap style object.
        theme_name (str): The name of the current theme (e.g., "litera", "darkly").

    Returns:
        dict: A dictionary of color settings for the application.
    """
    colors = style.colors

    if theme_name == "original":
        return {
            "root_bg": "#FAF0E6", "fg_color": "#3D3D3D",
            "sel_bg": "#d4a37f", "sel_fg": "#FFFFFF",
            "editor_bg": "#FAF0E6", "editor_fg": "#3D3D3D", "editor_insert_bg": "#3D3D3D",
            "comment_color": "#008000",
            "command_color": "#0000ff",
            "brace_color": "#ff007f",
            "ln_text_color": "#3D3D3D", "ln_bg_color": "#FAF0E6",
            "panedwindow_sash": "#e5c8b2",
            "llm_generated_bg": "#e0e0e0", "llm_generated_fg": "#3D3D3D",
            "statusbar_bg": "#e5c8b2", "statusbar_fg": "#3D3D3D"
        }

    # Check if the theme is dark by inspecting the default background color
    is_dark = style.lookup('TLabel', 'background') == colors.dark
    
    if is_dark:
        return {
            "root_bg": colors.dark, "fg_color": colors.light,
            "sel_bg": colors.primary, "sel_fg": colors.light,
            "editor_bg": colors.dark, "editor_fg": colors.light, "editor_insert_bg": colors.light,
            "comment_color": "#608b4e",  # Greenish for comments
            "command_color": "#569cd6",  # VSCode-like blue for commands
            "brace_color": "#c586c0",    # VSCode-like magenta for braces
            "ln_text_color": colors.secondary, "ln_bg_color": "#252526",
            "panedwindow_sash": colors.dark,
            "llm_generated_bg": "#3a3a3a", "llm_generated_fg": colors.light,
            "statusbar_bg": colors.primary, "statusbar_fg": colors.light
        }
    else: # Light themes
        return {
            "root_bg": colors.light, "fg_color": colors.dark,
            "sel_bg": colors.primary, "sel_fg": colors.light,
            "editor_bg": colors.light, "editor_fg": colors.dark, "editor_insert_bg": colors.dark,
            "comment_color": "#008000",  # Dark green for comments
            "command_color": "#0000ff",  # Bright blue for commands
            "brace_color": "#ff007f",    # Hot pink for braces
            "ln_text_color": colors.secondary, "ln_bg_color": colors.light,
            "panedwindow_sash": colors.light,
            "llm_generated_bg": "#e0e0e0", "llm_generated_fg": colors.dark,
            "statusbar_bg": colors.primary, "statusbar_fg": colors.light
        }

def apply_theme(theme_name, root_window, main_paned_window, open_tabs_dict, perform_heavy_updates_callback, console_widget, status_bar_frame=None, status_label=None, gpu_status_label=None):
    """
    Applies the specified ttkbootstrap theme to the entire application's GUI.

    Args:
        theme_name (str): The name of the theme to apply (e.g., "litera", "darkly").
        root_window (ttk.Window): The main ttkbootstrap application window.
        main_paned_window (ttk.PanedWindow): The main paned window widget.
        open_tabs_dict (dict): A dictionary mapping tab IDs to EditorTab instances.
        perform_heavy_updates_callback (callable): A callback to re-render editor content.
        console_widget (ttk.Text): The console text widget to style.
        status_bar_frame (ttk.Frame, optional): The frame for the status bar.
        status_label (ttk.Label, optional): The label for status messages.
        gpu_status_label (ttk.Label, optional): The label for GPU status.

    Returns:
        tuple: A tuple containing the applied theme name (str) and its settings (dict).
    """
    style = root_window.style
    
    # Use 'litera' as the base for our 'original' theme, but don't change the theme name yet.
    base_theme = "litera" if theme_name == "original" else theme_name
    style.theme_use(base_theme)
    
    theme_settings = get_theme_colors(style, theme_name)

    # Apply theme to status bar
    if status_bar_frame and status_label and gpu_status_label:
        status_bar_frame.configure(style="TFrame")
        status_label.configure(background=theme_settings["statusbar_bg"], foreground=theme_settings["statusbar_fg"])
        gpu_status_label.configure(background=theme_settings["statusbar_bg"], foreground=theme_settings["statusbar_fg"])


    # Apply theme to the console widget
    if console_widget:
        console_widget.configure(
            background=theme_settings["editor_bg"],
            foreground=theme_settings["editor_fg"],
            insertbackground=theme_settings["editor_insert_bg"]
        )

    # Apply theme to all open editor tabs
    for tab in open_tabs_dict.values():
        if tab.editor:
            tab.editor.configure(
                background=theme_settings["editor_bg"], foreground=theme_settings["editor_fg"],
                selectbackground=theme_settings["sel_bg"], selectforeground=theme_settings["sel_fg"],
                insertbackground=theme_settings["editor_insert_bg"],
                relief="flat", borderwidth=0
            )
            # Reconfigure syntax highlighting tags
            tab.editor.tag_configure("latex_command", foreground=theme_settings["command_color"], font=tab.editor_font)
            tab.editor.tag_configure("latex_brace", foreground=theme_settings["brace_color"], font=tab.editor_font)
            
            comment_font = tab.editor_font.copy()
            comment_font.configure(slant="italic")
            tab.editor.tag_configure("latex_comment", foreground=theme_settings["comment_color"], font=comment_font)

            llm_generated_font = tab.editor_font.copy()
            llm_generated_font.configure(slant="italic")
            tab.editor.tag_configure("llm_generated_text", background=theme_settings["llm_generated_bg"], foreground=theme_settings["llm_generated_fg"], font=llm_generated_font)

        if tab.line_numbers:
            tab.line_numbers.update_theme(text_color=theme_settings["ln_text_color"], bg_color=theme_settings["ln_bg_color"])

    perform_heavy_updates_callback()
    root_window.update_idletasks()
    
    return theme_name, theme_settings
