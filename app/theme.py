"""
Manage application visual themes using ttkbootstrap.
Provide functions to apply chosen theme to all relevant GUI components including editor elements and custom widgets.
"""

import ttkbootstrap as ttk
from tkinter.font import Font
from app.config import get_treeview_font_settings

def get_theme_colors(style, theme_name):
    """
    Return dictionary of color settings using ttkbootstrap semantic colors.
    """
    colors = style.colors

    if theme_name == "original":
        return {
            "root_bg": "#FFF8F0", "fg_color": "#4A4238",
            "sel_bg": "#A8DDA8", "sel_fg": "#000000",
            "editor_bg": "#FFF8F0", "editor_fg": "#4A4238", "editor_insert_bg": "#4A4238",
            "comment_color": "#6B8E23", "command_color": "#E88216", "brace_color": "#FF8242",
            "ln_text_color": "#A9A9A9", "ln_bg_color": "#FFF8F0",
            "panedwindow_sash": "#F6B092", "llm_generated_bg": "#F0FFF0", "llm_generated_fg": "#4A4238",
            "statusbar_bg": "#F6B092", "statusbar_fg": "#4A4238",
            "button_bg": "#F6B092", "button_fg": "#4A4238", "button_hover_bg": "#FF8242",
            "treeview_bg": "#FFFFFF", "treeview_fg": "#4A4238", "treeview_heading_bg": "#F6B092",
            "notebook_bg": "#FFF8F0", "notebook_tab_bg": "#F6B092", "notebook_active_tab_bg": "#FF8242", "notebook_active_tab_fg": "#FFFFFF",
            "placeholder_color": "#FF1744", "accent_color": "#FF8242", "border_color": "#E0E0E0"
        }

    # detect theme characteristics
    is_dark = _is_dark_theme(style, colors)
    
    # get semantic color variations
    base_bg = colors.dark if is_dark else colors.light
    base_fg = colors.light if is_dark else colors.dark
    secondary_bg = _adjust_brightness(base_bg, 0.1 if is_dark else -0.05)
    
    # theme-specific syntax highlighting
    syntax_colors = _get_syntax_colors(theme_name, is_dark, colors)
    
    # debug center colors
    debug_colors = _get_debug_colors(theme_name, is_dark, colors)
    
    return {
        "root_bg": base_bg, "fg_color": base_fg,
        "sel_bg": colors.primary, "sel_fg": colors.light,
        "editor_bg": base_bg, "editor_fg": base_fg, "editor_insert_bg": colors.primary,
        "comment_color": syntax_colors["comment"],
        "command_color": syntax_colors["command"],
        "brace_color": syntax_colors["brace"],
        "ln_text_color": _get_contrasted_secondary(colors, is_dark), "ln_bg_color": secondary_bg,
        "panedwindow_sash": secondary_bg,
        "llm_generated_bg": _adjust_brightness(colors.info, 0.8), "llm_generated_fg": base_fg,
        "statusbar_bg": colors.primary, "statusbar_fg": colors.light,
        "button_bg": colors.primary, "button_fg": colors.light, "button_hover_bg": _adjust_brightness(colors.primary, 0.1),
        "treeview_bg": base_bg, "treeview_fg": base_fg, "treeview_heading_bg": colors.secondary,
        "notebook_bg": base_bg, "notebook_tab_bg": secondary_bg, "notebook_active_tab_bg": colors.primary, "notebook_active_tab_fg": colors.light,
        "placeholder_color": colors.danger, "accent_color": colors.success, "border_color": colors.secondary,
        "debug_bg": debug_colors["bg"], "debug_fg": debug_colors["fg"],
        "debug_heading_bg": debug_colors["heading_bg"], "debug_heading_fg": debug_colors["heading_fg"]
    }

def _is_dark_theme(style, colors):
    """Detect if theme is dark by analyzing background luminance."""
    bg = style.lookup('TLabel', 'background') or colors.bg
    if bg == colors.dark:
        return True
    # additional luminance check for edge cases
    return _get_luminance(bg) < 0.5

def _get_luminance(color):
    """Calculate relative luminance of a color."""
    try:
        if color.startswith('#'):
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            return (0.299 * r + 0.587 * g + 0.114 * b) / 255
    except (ValueError, TypeError):
        pass
    return 0.5

def _adjust_brightness(color, factor):
    """Adjust color brightness by factor (-1 to 1)."""
    try:
        if color.startswith('#'):
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            if factor > 0:  # lighten
                r = min(255, int(r + (255 - r) * factor))
                g = min(255, int(g + (255 - g) * factor))
                b = min(255, int(b + (255 - b) * factor))
            else:  # darken
                factor = abs(factor)
                r = max(0, int(r * (1 - factor)))
                g = max(0, int(g * (1 - factor)))
                b = max(0, int(b * (1 - factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, TypeError):
        pass
    return color

def _get_contrasted_secondary(colors, is_dark):
    """Get a well-contrasted secondary color for text visibility with minimum 4:1 contrast."""
    base_bg = colors.dark if is_dark else colors.light
    
    # use high-contrast colors optimized for each theme type
    if is_dark:
        # for dark themes: use bright white-ish gray for maximum visibility
        return "#E8E8E8"  # very light gray for dark backgrounds
    else:
        # for light themes: use dark charcoal for maximum readability  
        return "#2A2A2A"  # very dark gray for light backgrounds

def _calculate_contrast_ratio(color1, color2):
    """Calculate WCAG contrast ratio between two colors."""
    lum1 = _get_luminance(color1)
    lum2 = _get_luminance(color2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)

def _get_syntax_colors(theme_name, is_dark, colors):
    """Get theme-appropriate syntax highlighting colors."""
    if is_dark:
        return {
            "comment": colors.success if hasattr(colors, 'success') else "#6A9955",
            "command": colors.info if hasattr(colors, 'info') else "#569CD6", 
            "brace": colors.warning if hasattr(colors, 'warning') else "#DA70D6"
        }
    else:
        return {
            "comment": colors.success if hasattr(colors, 'success') else "#008000",
            "command": colors.primary if hasattr(colors, 'primary') else "#0000FF",
            "brace": colors.danger if hasattr(colors, 'danger') else "#FF1493"
        }

def _get_debug_colors(theme_name, is_dark, colors):
    """Get debug-specific colors that preserve exact debug_ui look."""
    debug_colors = {
        'darkly': {
            'bg': '#2d2d2d', 'fg': '#ffffff',
            'heading_bg': '#3d3d3d', 'heading_fg': '#cccccc'
        },
        'superhero': {
            'bg': '#2b3e50', 'fg': '#ffffff', 
            'heading_bg': '#34495e', 'heading_fg': '#ecf0f1'
        },
        'solar': {
            'bg': '#002b36', 'fg': '#839496',
            'heading_bg': '#073642', 'heading_fg': '#93a1a1'
        },
        'cyborg': {
            'bg': '#222222', 'fg': '#ffffff',
            'heading_bg': '#2a2a2a', 'heading_fg': '#cccccc'
        },
        'vapor': {
            'bg': '#190a26', 'fg': '#f8f8ff',
            'heading_bg': '#2a1b3d', 'heading_fg': '#e6e6fa'
        }
    }
    
    # light themes default
    light_default = {
        'bg': '#ffffff', 'fg': '#333333',
        'heading_bg': '#f5f5f5', 'heading_fg': '#666666'
    }
    
    return debug_colors.get(theme_name, light_default)

def apply_theme(theme_name, root_window, main_paned_window, open_tabs_dict, perform_heavy_updates_callback, console_widget, status_bar_frame=None, status_label=None, gpu_status_label=None, config_settings=None):
    style = root_window.style
    
    base_theme = "litera" if theme_name == "original" else theme_name
    style.theme_use(base_theme)
    
    theme_settings = get_theme_colors(style, theme_name)
    
    # update state immediately before widget updates
    try:
        from app import state
        state._theme_settings = theme_settings
    except:
        pass
    
    # get colors and theme type for enhanced styling
    colors = style.colors
    is_dark = _is_dark_theme(style, colors)
    
    # get validated font settings from config
    if config_settings:
        font_settings = get_treeview_font_settings(config_settings)
        treeview_font_family = font_settings["family"]
        treeview_font_size = font_settings["size"]
        treeview_row_height = font_settings["row_height"]
    else:
        treeview_font_family = "Segoe UI"
        treeview_font_size = 10
        treeview_row_height = 30

    # --- Enhanced Global Style Configurations ---
    style.configure("TFrame", background=theme_settings["root_bg"], relief="flat")
    style.configure("TLabel", 
                    background=theme_settings["root_bg"], 
                    foreground=theme_settings["fg_color"],
                    font=("Segoe UI", 9))
    
    # enhanced label variants for better contrast
    style.configure("Contrast.TLabel",
                    background=theme_settings["root_bg"],
                    foreground=_get_contrasted_secondary(colors, is_dark),
                    font=("Segoe UI", 8))
    
    style.configure("Bold.TLabel",
                    background=theme_settings["root_bg"],
                    foreground=theme_settings["fg_color"],
                    font=("Segoe UI", 9, "bold"))
    style.configure("TPanedwindow", 
                    background=theme_settings["panedwindow_sash"],
                    borderwidth=1,
                    relief="flat")
    
    # add enhanced entry and text widget styling
    style.configure("TEntry",
                    fieldbackground=theme_settings["editor_bg"],
                    foreground=theme_settings["editor_fg"],
                    borderwidth=1,
                    relief="flat")
    style.map("TEntry",
              bordercolor=[("focus", theme_settings["accent_color"])],
              lightcolor=[("focus", theme_settings["accent_color"])])
    
    # --- Enhanced Title Box Configurations ---
    style.configure(
        "Title.TLabel",
        background=theme_settings["notebook_tab_bg"],
        foreground=theme_settings["fg_color"],
        relief="flat",
        borderwidth=1,
        padding=(10, 6),
        font=("Segoe UI", 9, "bold")
    )
    
    # subtitle/description labels with better contrast
    style.configure(
        "Subtitle.TLabel",
        background=theme_settings["root_bg"],
        foreground=_get_contrasted_secondary(colors, is_dark),
        font=("Segoe UI", 8),
        padding=(2, 2)
    )

    # --- Enhanced Button Configurations ---
    style.configure("TButton", 
                    background=theme_settings["button_bg"], 
                    foreground=theme_settings["button_fg"], 
                    borderwidth=1, 
                    focusthickness=0,
                    relief="flat",
                    padding=(8, 6))
    style.map("TButton", 
              background=[("active", theme_settings.get("button_hover_bg", theme_settings["sel_bg"])), 
                         ("pressed", theme_settings["accent_color"])],
              relief=[("pressed", "sunken"), ("active", "flat")],
              bordercolor=[("focus", theme_settings["accent_color"])])

    # --- Enhanced Treeview (Outline) Configurations ---
    style.layout("Treeview.Item", 
                 [('Treeitem.padding', {'sticky': 'nswe', 'children': 
                     [('Treeitem.image', {'side': 'left', 'sticky': ''}), 
                      ('Treeitem.text', {'side': 'left', 'sticky': ''})]})])
    
    style.configure("Treeview", 
                    background=theme_settings["treeview_bg"], 
                    foreground=theme_settings["treeview_fg"], 
                    fieldbackground=theme_settings["treeview_bg"],
                    font=(treeview_font_family, treeview_font_size), 
                    rowheight=treeview_row_height,
                    borderwidth=0,
                    relief="flat")
    style.map("Treeview", 
              background=[("selected", theme_settings["accent_color"]), 
                         ("focus", theme_settings["sel_bg"])], 
              foreground=[("selected", theme_settings["fg_color"])])
    style.configure("Treeview.Heading", 
                    background=theme_settings["treeview_heading_bg"], 
                    foreground=theme_settings["fg_color"],
                    font=("Segoe UI", 9),
                    relief="flat",
                    borderwidth=1)

    # --- Enhanced Notebook (Tabs) Configurations ---
    style.configure("TNotebook", 
                    background=theme_settings["notebook_bg"],
                    borderwidth=0,
                    relief="flat")
    style.configure("TNotebook.Tab", 
                    background=theme_settings["notebook_tab_bg"], 
                    foreground=theme_settings["fg_color"],
                    padding=(14, 10),
                    borderwidth=1,
                    relief="flat")
    style.map("TNotebook.Tab", 
              background=[("selected", theme_settings["notebook_active_tab_bg"]), 
                         ("active", theme_settings["accent_color"])], 
              foreground=[("selected", theme_settings["notebook_active_tab_fg"])],
              bordercolor=[("selected", theme_settings["accent_color"])])
    style.configure("Closable.TNotebook.Tab", 
                    background=theme_settings["notebook_tab_bg"], 
                    foreground=theme_settings["fg_color"],
                    padding=(14, 10),
                    borderwidth=1,
                    relief="flat")
    style.map("Closable.TNotebook.Tab", 
              background=[("selected", theme_settings["notebook_active_tab_bg"]), 
                         ("active", theme_settings["accent_color"])], 
              foreground=[("selected", theme_settings["notebook_active_tab_fg"])],
              bordercolor=[("selected", theme_settings["accent_color"])])
    
    # update notebook fonts and close button color after theme change
    from app import state
    if hasattr(state, 'notebook') and state.notebook:
        if hasattr(state.notebook, 'update_fonts'):
            state.notebook.update_fonts()
        if hasattr(state.notebook, 'update_close_button_color'):
            # use foreground color for close button to match theme
            state.notebook.update_close_button_color(theme_settings["fg_color"])

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

    # --- Debug Center Theme Update ---
    def update_all_widgets(widget):
        if hasattr(widget, 'update_theme_colors'):
            widget.update_theme_colors()
        for child in widget.winfo_children():
            update_all_widgets(child)
    
    try:
        update_all_widgets(root_window)
        root_window.event_generate('<<ThemeChanged>>')
        
        # refresh pdf preview with new theme if available
        from app import state
        from utils import logs_console
        
        if (state.pdf_preview_interface and 
            hasattr(state.pdf_preview_interface, 'preview_manager') and 
            state.pdf_preview_interface.preview_manager and
            state.pdf_preview_interface.preview_manager.viewer):
            logs_console.log(f"Theme: Scheduling PDF refresh for theme {theme_name}", level='INFO')
            # schedule pdf refresh after theme application
            root_window.after(50, state.pdf_preview_interface.preview_manager.viewer.refresh_theme)
        else:
            logs_console.log("Theme: No PDF viewer available for refresh", level='DEBUG')
    except:
        pass
    
    perform_heavy_updates_callback()
    root_window.update_idletasks()
    
    return theme_name, theme_settings
