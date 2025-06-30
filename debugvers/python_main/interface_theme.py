import sv_ttk
import tkinter as tk
from tkinter.font import Font

def get_theme_colors(theme_name):
    """Returns a dictionary of colors for a given theme name."""
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
    return get_theme_colors("light") # Default fallback

def apply_theme(theme_name, root, main_pane, tabs, perform_heavy_updates):
    """Applies the specified theme and returns the new theme name and settings."""
    # Set the theme using sv_ttk
    sv_ttk.set_theme(theme_name)

    # Get the color settings for the chosen theme
    theme_settings = get_theme_colors(theme_name)

    # --- Apply colors to non-ttk widgets ---
    root.configure(bg=theme_settings["root_bg"])
    if main_pane:
        main_pane.configure(sashrelief=tk.FLAT, sashwidth=6, bg=theme_settings["panedwindow_sash"])

    # Iterate through all open tabs and apply the theme to each editor and line number canvas
    for tab in tabs.values():
        if tab.editor:
            tab.editor.configure(
                background=theme_settings["editor_bg"], foreground=theme_settings["editor_fg"],
                selectbackground=theme_settings["sel_bg"], selectforeground=theme_settings["sel_fg"],
                insertbackground=theme_settings["editor_insert_bg"],
                relief=tk.FLAT, borderwidth=0
            )
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

    # Trigger a heavy update to redraw syntax highlighting, etc., with new colors
    perform_heavy_updates()
    root.update_idletasks()
    
    # Return the new theme name and settings to the caller
    return theme_name, theme_settings