"""
Manage application visual themes using ttkbootstrap.
Provide functions to apply chosen theme to all relevant GUI components including editor elements and custom widgets.
"""

import ttkbootstrap as ttk
from tkinter.font import Font
from app.config import get_treeview_font_settings

def get_theme_colors(style, theme_name):
    """
    Return dictionary of color settings derived from current ttkbootstrap theme.
    """
    colors = style.colors

    if theme_name == "original":
        return {
            "root_bg": "#FFF8F0", "fg_color": "#4A4238",
            "sel_bg": "#A8DDA8", "sel_fg": "#000000",
            "editor_bg": "#FFF8F0", "editor_fg": "#4A4238", "editor_insert_bg": "#4A4238",
            "comment_color": "#6B8E23",
            "command_color": "#E88216",
            "brace_color": "#FF8242",
            "ln_text_color": "#A9A9A9", "ln_bg_color": "#FFF8F0",
            "panedwindow_sash": "#F6B092",
            "llm_generated_bg": "#F0FFF0", "llm_generated_fg": "#4A4238",
            "statusbar_bg": "#F6B092", "statusbar_fg": "#4A4238",
            "button_bg": "#F6B092", "button_fg": "#4A4238",
            "treeview_bg": "#FFFFFF", "treeview_fg": "#4A4238", "treeview_heading_bg": "#F6B092",
            "notebook_bg": "#FFF8F0", "notebook_tab_bg": "#F6B092", "notebook_active_tab_bg": "#FF8242", "notebook_active_tab_fg": "#FFFFFF"
        }

    is_dark = style.lookup('TLabel', 'background') == colors.dark
    
    if is_dark:
        return {
            "root_bg": colors.dark, "fg_color": colors.light,
            "sel_bg": colors.primary, "sel_fg": colors.light,
            "editor_bg": colors.dark, "editor_fg": colors.light, "editor_insert_bg": colors.light,
            "comment_color": "#608b4e",
            "command_color": "#569cd6",
            "brace_color": "#c586c0",
            "ln_text_color": colors.secondary, "ln_bg_color": "#252526",
            "panedwindow_sash": colors.dark,
            "llm_generated_bg": "#2c3a4a", "llm_generated_fg": colors.light,
            "statusbar_bg": colors.primary, "statusbar_fg": colors.light,
            "button_bg": colors.primary, "button_fg": colors.light,
            "treeview_bg": colors.dark, "treeview_fg": colors.light, "treeview_heading_bg": colors.primary,
            "notebook_bg": colors.dark, "notebook_tab_bg": "#3c3c3c", "notebook_active_tab_bg": colors.primary, "notebook_active_tab_fg": colors.light
        }
    else: # Light themes
        return {
            "root_bg": colors.light, "fg_color": colors.dark,
            "sel_bg": colors.primary, "sel_fg": colors.light,
            "editor_bg": colors.light, "editor_fg": colors.dark, "editor_insert_bg": colors.dark,
            "comment_color": "#008000",
            "command_color": "#0000ff",
            "brace_color": "#ff007f",
            "ln_text_color": colors.secondary, "ln_bg_color": colors.light,
            "panedwindow_sash": colors.light,
            "llm_generated_bg": "#eaf2fa", "llm_generated_fg": colors.dark,
            "statusbar_bg": colors.primary, "statusbar_fg": colors.light,
            "button_bg": colors.primary, "button_fg": colors.light,
            "treeview_bg": colors.light, "treeview_fg": colors.dark, "treeview_heading_bg": colors.primary,
            "notebook_bg": colors.light, "notebook_tab_bg": "#f0f0f0", "notebook_active_tab_bg": colors.primary, "notebook_active_tab_fg": colors.light
        }

def apply_theme(theme_name, root_window, main_paned_window, open_tabs_dict, perform_heavy_updates_callback, console_widget, status_bar_frame=None, status_label=None, gpu_status_label=None, config_settings=None):
    style = root_window.style
    
    base_theme = "litera" if theme_name == "original" else theme_name
    style.theme_use(base_theme)
    
    theme_settings = get_theme_colors(style, theme_name)
    
    # Get validated font settings from config
    if config_settings:
        font_settings = get_treeview_font_settings(config_settings)
        treeview_font_family = font_settings["family"]
        treeview_font_size = font_settings["size"]
        treeview_row_height = font_settings["row_height"]
    else:
        treeview_font_family = "Segoe UI"
        treeview_font_size = 10
        treeview_row_height = 30

    # --- Global Style Configurations ---
    style.configure("TFrame", background=theme_settings["root_bg"])
    style.configure("TLabel", background=theme_settings["root_bg"], foreground=theme_settings["fg_color"])
    style.configure("TPanedwindow", background=theme_settings["panedwindow_sash"])
    
    # --- Title Box Configurations ---
    style.configure(
        "Title.TLabel",
        background=theme_settings["notebook_tab_bg"],
        foreground=theme_settings["fg_color"],
        relief="solid",
        borderwidth=1
    )

    # --- Button Configurations ---
    style.configure("TButton", 
                    background=theme_settings["button_bg"], 
                    foreground=theme_settings["button_fg"], 
                    borderwidth=1, 
                    focusthickness=0,
                    relief="flat")
    style.map("TButton", 
              background=[("active", theme_settings["sel_bg"]), ("pressed", theme_settings["sel_bg"])],
              relief=[("pressed", "sunken"), ("active", "raised")])

    # --- Treeview (Outline) Configurations ---
    # Redefine the Treeview item layout to completely remove the indicator space
    style.layout("Treeview.Item", 
                 [('Treeitem.padding', {'sticky': 'nswe', 'children': 
                     [('Treeitem.image', {'side': 'left', 'sticky': ''}), 
                      ('Treeitem.text', {'side': 'left', 'sticky': ''})]})])
    
    style.configure("Treeview", 
                    background=theme_settings["treeview_bg"], 
                    foreground=theme_settings["treeview_fg"], 
                    fieldbackground=theme_settings["treeview_bg"],
                    font=(treeview_font_family, treeview_font_size), 
                    rowheight=treeview_row_height)
    style.map("Treeview", 
              background=[("selected", theme_settings["sel_bg"])], 
              foreground=[("selected", theme_settings["sel_fg"])])
    style.configure("Treeview.Heading", 
                    background=theme_settings["treeview_heading_bg"], 
                    foreground=theme_settings["fg_color"],
                    font=("Segoe UI", 9))

    # --- Notebook (Tabs) Configurations ---
    style.configure("TNotebook", 
                    background=theme_settings["notebook_bg"],
                    borderwidth=1,
                    relief="flat")
    style.configure("TNotebook.Tab", 
                    background=theme_settings["notebook_tab_bg"], 
                    foreground=theme_settings["fg_color"],
                    padding=(12, 8),
                    borderwidth=1)
    style.map("TNotebook.Tab", 
              background=[("selected", theme_settings["notebook_active_tab_bg"]), ("active", theme_settings["sel_bg"])], 
              foreground=[("selected", theme_settings["notebook_active_tab_fg"])])
    style.configure("Closable.TNotebook.Tab", 
                    background=theme_settings["notebook_tab_bg"], 
                    foreground=theme_settings["fg_color"],
                    padding=(12, 8),
                    borderwidth=1)
    style.map("Closable.TNotebook.Tab", 
              background=[("selected", theme_settings["notebook_active_tab_bg"]), ("active", theme_settings["sel_bg"])], 
              foreground=[("selected", theme_settings["notebook_active_tab_fg"])])

    # --- Status Bar ---
    if status_bar_frame and status_label and gpu_status_label:
        status_bar_frame.configure(style="TFrame")
        status_label.configure(background=theme_settings["statusbar_bg"], foreground=theme_settings["statusbar_fg"])
        gpu_status_label.configure(background=theme_settings["statusbar_bg"], foreground=theme_settings["statusbar_fg"])

    # --- Console Widget ---
    if console_widget:
        console_widget.configure(
            background=theme_settings["editor_bg"],
            foreground=theme_settings["editor_fg"],
            insertbackground=theme_settings["editor_insert_bg"]
        )

    # --- Editor Tabs ---
    for tab in open_tabs_dict.values():
        if tab.editor:
            tab.editor.configure(
                background=theme_settings["editor_bg"], foreground=theme_settings["editor_fg"],
                selectbackground=theme_settings["sel_bg"], selectforeground=theme_settings["sel_fg"],
                insertbackground=theme_settings["editor_insert_bg"],
                relief="flat", borderwidth=0
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

    perform_heavy_updates_callback()
    root_window.update_idletasks()
    
    return theme_name, theme_settings
