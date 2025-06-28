from tkinter.font import Font
import platform
import sv_ttk
import tkinter as tk  # Ajout nécessaire pour utiliser tk.FLAT
import datetime       # Ajout pour print datetime dans perform_heavy_updates si appelé ici

def apply_theme(theme_name, current_theme, _theme_settings, root, outline_tree, status_bar, main_pane, tabs, perform_heavy_updates):
    """Applies the specified theme (light or dark) to the GUI."""
    

    # Set the theme using sv_ttk
    sv_ttk.set_theme(theme_name)
    current_theme = theme_name

    # Font for non-ttk widgets (like tk.Text in dialogs if not using editor_font)
    # sv_ttk will handle fonts for ttk widgets.
    ui_font_family = "Segoe UI" if platform.system() == "Windows" else "Helvetica"
    ui_font_button = Font(family=ui_font_family, size=9, weight="normal")

    # Define colors based on theme
    if theme_name == "light":
        _theme_settings = {
            # sv_ttk typically uses a very light grey or white for root_bg in light mode
            "root_bg": "#fdfdfd", # Adjusted to match typical sv_ttk light theme
            "fg_color": "#000000", # General foreground for non-ttk elements
            "sel_bg": "#0078d4", "sel_fg": "#ffffff", # Selection colors for editor (inspired by Windows)
            "editor_bg": "#ffffff", "editor_fg": "#1e1e1e", "editor_insert_bg": "#333333",
            "comment_color": "#008000", "command_color": "#0000ff", "brace_color": "#ff007f",
            "ln_text_color": "#888888", "ln_bg_color": "#f7f7f7",
            "panedwindow_sash": "#e6e6e6", # Light sash for PanedWindow if sv_ttk doesn't fully style it
            # NEW: LLM generated text colors
            "llm_generated_bg": "#e0e0e0", # Light grey for generated text background
            "llm_generated_fg": "#000000", # Black text on light background
            # Status bar will now be styled by sv_ttk. If specific colors are needed, they should be harmonious.
            # "status_bar_bg": "#f0f0f0", "status_bar_fg": "#000000", # Example: neutral status bar
        }
    elif theme_name == "dark":
        _theme_settings = {
            # sv_ttk uses dark greys for root_bg in dark mode
            "root_bg": "#202020", # Adjusted to match typical sv_ttk dark theme
            "fg_color": "#ffffff", # General foreground for non-ttk elements
            "sel_bg": "#0078d4", "sel_fg": "#ffffff", # Selection colors for editor
            "editor_bg": "#1e1e1e", "editor_fg": "#d4d4d4", "editor_insert_bg": "#d4d4d4",
            "comment_color": "#608b4e", "command_color": "#569cd6", "brace_color": "#c586c0",
            "ln_text_color": "#6a6a6a", "ln_bg_color": "#252526",
            "panedwindow_sash": "#333333", # Dark sash for PanedWindow
            # NEW: LLM generated text colors
            "llm_generated_bg": "#3a3a3a", # Dark grey for generated text background
            "llm_generated_fg": "#d4d4d4", # Light text on dark background
            # "status_bar_bg": "#2b2b2b", "status_bar_fg": "#d0d0d0", # Example: neutral status bar
        }
    else:
        return

    # Apply colors to the root window
    root.configure(bg=_theme_settings["root_bg"])

    # --- ttk Widget Theming ---
    # All ttk widget styling (buttons, treeview, scrollbars, progressbar, status_bar, etc.)
    # is now primarily handled by sv_ttk.set_theme() called above.

    # The status_bar (ttk.Label) will be styled by sv_ttk.
    # If you need to override its font or specific aspects not covered by sv_ttk's theme:
    # if 'status_bar' in globals() and status_bar:
    #     status_bar.configure(font=Font(family=ui_font_family, size=9)) # Example: ensure font

    # PanedWindow sash color: sv_ttk usually styles sashes well.
    # or if you want a specific color. sv_ttk usually styles sashes.
    if 'main_pane' in globals() and main_pane:
         main_pane.configure(sashrelief=tk.FLAT, sashwidth=6, bg=_theme_settings["panedwindow_sash"])

    # --- tk Widget Theming (Manual - These are not ttk widgets) ---
    # These remain essential as sv_ttk only themes ttk widgets.
    # We now need to iterate through all open tabs and apply the theme to each one.
    for tab in tabs.values():
        if tab.editor:
            tab.editor.configure(
                background=_theme_settings["editor_bg"], foreground=_theme_settings["editor_fg"],
                selectbackground=_theme_settings["sel_bg"], selectforeground=_theme_settings["sel_fg"],
                insertbackground=_theme_settings["editor_insert_bg"],
                relief=tk.FLAT, borderwidth=0
            )
            # Configure tags for each editor instance
            tab.editor.tag_configure("latex_command", foreground=_theme_settings["command_color"], font=tab.editor_font)
            tab.editor.tag_configure("latex_brace", foreground=_theme_settings["brace_color"], font=tab.editor_font)
            comment_font = tab.editor_font.copy()
            comment_font.configure(slant="italic")
            tab.editor.tag_configure("latex_comment", foreground=_theme_settings["comment_color"], font=comment_font)
            
            # NEW: Tag for LLM generated text
            llm_generated_font = tab.editor_font.copy()
            llm_generated_font.configure(slant="italic")
            tab.editor.tag_configure("llm_generated_text", background=_theme_settings.get("llm_generated_bg", "#e0e0e0" if theme_name == "light" else "#3a3a3a"), foreground=_theme_settings.get("llm_generated_fg", _theme_settings["editor_fg"]), font=llm_generated_font)
        
        # Update the theme of the line numbers canvas for each tab
        if tab.line_numbers:
            tab.line_numbers.update_theme(text_color=_theme_settings["ln_text_color"], bg_color=_theme_settings["ln_bg_color"])

    # Handle temporary status bar message styling
    # If a temporary message is active, its specific styling (if any) should be applied


    # Trigger a heavy update to redraw syntax highlighting, outline, and line numbers
    perform_heavy_updates()
    if root:
        # Ensure the status bar padding is set correctly after theme application
        if 'status_bar' in globals() and status_bar:
             # sv_ttk should handle padding for ttk.Label.
             pass
        # Update the background of the root window itself
        root.configure(bg=_theme_settings["root_bg"])

        # Force an update to apply all configuration changes immediately
        root.update_idletasks()
    elif theme_name == "dark":
        _theme_settings = {
            # sv_ttk uses dark greys for root_bg in dark mode
            "root_bg": "#202020", # Adjusted to match typical sv_ttk dark theme
            "fg_color": "#ffffff", # General foreground for non-ttk elements
            "sel_bg": "#0078d4", "sel_fg": "#ffffff", # Selection colors for editor
            "editor_bg": "#1e1e1e", "editor_fg": "#d4d4d4", "editor_insert_bg": "#d4d4d4",
            "comment_color": "#608b4e", "command_color": "#569cd6", "brace_color": "#c586c0",
            "ln_text_color": "#6a6a6a", "ln_bg_color": "#252526",
            "panedwindow_sash": "#333333", # Dark sash for PanedWindow
            # NEW: LLM generated text colors
            "llm_generated_bg": "#3a3a3a", # Dark grey for generated text background
            "llm_generated_fg": "#d4d4d4", # Light text on dark background
            # "status_bar_bg": "#2b2b2b", "status_bar_fg": "#d0d0d0", # Example: neutral status bar
        }
    else:
        return

    # Apply colors to the root window
    root.configure(bg=_theme_settings["root_bg"])

    # --- ttk Widget Theming ---
    # All ttk widget styling (buttons, treeview, scrollbars, progressbar, status_bar, etc.)
    # is now primarily handled by sv_ttk.set_theme() called above.

    # The status_bar (ttk.Label) will be styled by sv_ttk.
    # If you need to override its font or specific aspects not covered by sv_ttk's theme:
    # if 'status_bar' in globals() and status_bar:
    #     status_bar.configure(font=Font(family=ui_font_family, size=9)) # Example: ensure font

    # PanedWindow sash color: sv_ttk usually styles sashes well.
    # or if you want a specific color. sv_ttk usually styles sashes.
    if 'main_pane' in globals() and main_pane:
         main_pane.configure(sashrelief=tk.FLAT, sashwidth=6, bg=_theme_settings["panedwindow_sash"])

    # --- tk Widget Theming (Manual - These are not ttk widgets) ---
    # These remain essential as sv_ttk only themes ttk widgets.
    # We now need to iterate through all open tabs and apply the theme to each one.
    for tab in tabs.values():
        if tab.editor:
            tab.editor.configure(
                background=_theme_settings["editor_bg"], foreground=_theme_settings["editor_fg"],
                selectbackground=_theme_settings["sel_bg"], selectforeground=_theme_settings["sel_fg"],
                insertbackground=_theme_settings["editor_insert_bg"],
                relief=tk.FLAT, borderwidth=0
            )
            # Configure tags for each editor instance
            tab.editor.tag_configure("latex_command", foreground=_theme_settings["command_color"], font=tab.editor_font)
            tab.editor.tag_configure("latex_brace", foreground=_theme_settings["brace_color"], font=tab.editor_font)
            comment_font = tab.editor_font.copy()
            comment_font.configure(slant="italic")
            tab.editor.tag_configure("latex_comment", foreground=_theme_settings["comment_color"], font=comment_font)
            
            # NEW: Tag for LLM generated text
            llm_generated_font = tab.editor_font.copy()
            llm_generated_font.configure(slant="italic")
            tab.editor.tag_configure("llm_generated_text", background=_theme_settings.get("llm_generated_bg", "#e0e0e0" if theme_name == "light" else "#3a3a3a"), foreground=_theme_settings.get("llm_generated_fg", _theme_settings["editor_fg"]), font=llm_generated_font)
        
        # Update the theme of the line numbers canvas for each tab
        if tab.line_numbers:
            tab.line_numbers.update_theme(text_color=_theme_settings["ln_text_color"], bg_color=_theme_settings["ln_bg_color"])

    # Handle temporary status bar message styling
    # If a temporary message is active, its specific styling (if any) should be applied


    # Trigger a heavy update to redraw syntax highlighting, outline, and line numbers
    perform_heavy_updates()
    if root:
        # Ensure the status bar padding is set correctly after theme application
        if 'status_bar' in globals() and status_bar:
             # sv_ttk should handle padding for ttk.Label.
             pass
        # Update the background of the root window itself
        root.configure(bg=_theme_settings["root_bg"])

        # Force an update to apply all configuration changes immediately
        root.update_idletasks()
        # Update the background of the root window itself
        root.configure(bg=_theme_settings["root_bg"])

        # Force an update to apply all configuration changes immediately
        root.update_idletasks()
    else:
        pass