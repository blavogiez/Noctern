"""
This module manages the application's visual themes, providing functions to retrieve
color settings for different themes and to apply a chosen theme to all relevant
GUI components, including editor elements and custom widgets.
"""

import sv_ttk
import tkinter as tk
from tkinter.font import Font

def get_theme_colors(theme_name):
    """
    Returns a dictionary of color settings for a specified theme.

    This function defines the color palette for 'light' and 'dark' themes,
    including colors for background, foreground, selections, editor elements,
    syntax highlighting, line numbers, and LLM-generated text.

    Args:
        theme_name (str): The name of the theme to retrieve colors for (e.g., "light", "dark").

    Returns:
        dict: A dictionary where keys are color roles (e.g., "root_bg", "editor_fg")
              and values are hexadecimal color codes. Defaults to 'light' theme colors.
    """
    if theme_name == "light":
        return {
            "root_bg": "#fdfdfd", "fg_color": "#000000",
            "sel_bg": "#0078d4", "sel_fg": "#ffffff",
            "editor_bg": "#ffffff", "editor_fg": "#1e1e1e", "editor_insert_bg": "#333333",
            "comment_color": "#008000", "command_color": "#0000ff", "brace_color": "#ff007f",
            "ln_text_color": "#888888", "ln_bg_color": "#f7f7f7",
            "panedwindow_sash": "#e6e6e6",
            "llm_generated_bg": "#e0e0e0", "llm_generated_fg": "#000000",
        }
    elif theme_name == "dark":
        return {
            "root_bg": "#202020", "fg_color": "#ffffff",
            "sel_bg": "#0078d4", "sel_fg": "#ffffff",
            "editor_bg": "#1e1e1e", "editor_fg": "#d4d4d4", "editor_insert_bg": "#d4d4d4",
            "comment_color": "#608b4e", "command_color": "#569cd6", "brace_color": "#c586c0",
            "ln_text_color": "#6a6a6a", "ln_bg_color": "#252526",
            "panedwindow_sash": "#333333",
            "llm_generated_bg": "#3a3a3a", "llm_generated_fg": "#d4d4d4",
        }
    # Fallback to light theme if an unknown theme name is provided.
    return get_theme_colors("light") 

def apply_theme(theme_name, root_window, main_paned_window, open_tabs_dict, perform_heavy_updates_callback):
    """
    Applies the specified theme to the entire application's GUI.

    This function sets the base theme using `sv_ttk`, retrieves the corresponding
    color settings, and then iteratively applies these colors to various Tkinter
    widgets, including the root window, paned window, and all active editor tabs.
    It also reconfigures syntax highlighting tags with the new theme colors.

    Args:
        theme_name (str): The name of the theme to apply (e.g., "light", "dark").
        root_window (tk.Tk): The main Tkinter application window.
        main_paned_window (tk.PanedWindow): The main paned window widget.
        open_tabs_dict (dict): A dictionary mapping tab IDs to EditorTab instances.
        perform_heavy_updates_callback (callable): A callback function to trigger
                                                  a re-render of editor content (e.g., syntax highlighting).

    Returns:
        tuple: A tuple containing the applied theme name (str) and its settings (dict).
    """
    # Apply the base theme using the sv_ttk library.
    sv_ttk.set_theme(theme_name)

    # Retrieve the detailed color settings for the chosen theme.
    theme_settings = get_theme_colors(theme_name)

    # --- Apply colors to non-ttk widgets and specific components ---
    # Configure the background color of the root window.
    root_window.configure(bg=theme_settings["root_bg"])
    # Configure the main paned window's sash appearance.
    if main_paned_window:
        main_paned_window.configure(sashrelief=tk.FLAT, sashwidth=6, bg=theme_settings["panedwindow_sash"])

    # Iterate through all currently open editor tabs to apply theme settings.
    for tab in open_tabs_dict.values():
        if tab.editor:
            # Configure the editor's background, foreground, selection colors, and insert cursor color.
            tab.editor.configure(
                background=theme_settings["editor_bg"], foreground=theme_settings["editor_fg"],
                selectbackground=theme_settings["sel_bg"], selectforeground=theme_settings["sel_fg"],
                insertbackground=theme_settings["editor_insert_bg"],
                relief=tk.FLAT, borderwidth=0 # Ensure flat relief and no border for consistent look.
            )
            # Reconfigure syntax highlighting tags with the new theme colors.
            tab.editor.tag_configure("latex_command", foreground=theme_settings["command_color"], font=tab.editor_font)
            tab.editor.tag_configure("latex_brace", foreground=theme_settings["brace_color"], font=tab.editor_font)
            
            # Configure comment tag with italic font style.
            comment_font = tab.editor_font.copy()
            comment_font.configure(slant="italic")
            tab.editor.tag_configure("latex_comment", foreground=theme_settings["comment_color"], font=comment_font)

            # Configure LLM generated text tag with italic font style and specific background/foreground.
            llm_generated_font = tab.editor_font.copy()
            llm_generated_font.configure(slant="italic")
            tab.editor.tag_configure("llm_generated_text", background=theme_settings["llm_generated_bg"], foreground=theme_settings["llm_generated_fg"], font=llm_generated_font)

        # Update the line numbers canvas with the new theme colors.
        if tab.line_numbers:
            tab.line_numbers.update_theme(text_color=theme_settings["ln_text_color"], bg_color=theme_settings["ln_bg_color"])

    # Trigger a heavy update to force a redraw of editor content, ensuring all new colors are applied.
    perform_heavy_updates_callback()
    # Update idle tasks to ensure all pending GUI updates are processed immediately.
    root_window.update_idletasks()
    
    # Return the applied theme name and its settings for external use (e.g., by `interface.py`).
    return theme_name, theme_settings
