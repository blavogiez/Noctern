import tkinter as tk
import re
import os
from editor.tab import EditorTab
from utils import debug_console

def apply_syntax_highlighting(editor):
    """
    Applies syntax highlighting to LaTeX elements within the editor.
    This function no longer checks for missing files.
    """
    if not editor:
        debug_console.log("Editor not available for syntax highlighting.", level='WARNING')
        return

    current_tab = editor.master
    if not isinstance(current_tab, EditorTab):
        return

    # --- Font and Tag Configuration ---
    base_font = current_tab.editor_font
    try:
        font_family = base_font.cget("family")
        font_size = base_font.cget("size")
        bold_font = (font_family, font_size, "bold")
        italic_font = (font_family, font_size, "italic")
        normal_font = (font_family, font_size, "normal")
    except tk.TclError:
        bold_font, italic_font, normal_font = ("Arial", 12, "bold"), ("Arial", 12, "italic"), ("Arial", 12, "normal")

    editor.tag_configure("latex_command", font=bold_font)
    editor.tag_configure("latex_brace", font=normal_font)
    editor.tag_configure("latex_comment", foreground="gray")
    editor.tag_configure("latex_bold", font=bold_font)
    editor.tag_configure("latex_italic", font=italic_font)

    # --- Tag Removal ---
    tags_to_remove = ["latex_command", "latex_brace", "latex_comment", "latex_bold", "latex_italic"]
    for tag in tags_to_remove:
        editor.tag_remove(tag, "1.0", tk.END)

    try:
        content = editor.get("1.0", tk.END)
    except tk.TclError:
        debug_console.log("Could not get editor content", level='ERROR')
        return

    # --- Syntax Highlighting Application ---
    # Comments
    for match in re.finditer(r"%[^\n]*", content):
        editor.tag_add("latex_comment", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
    # Bold
    for match in re.finditer(r"\\textbf\{([^}]+)", content):
        editor.tag_add("latex_bold", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
    # Italic
    for match in re.finditer(r"\\textit\{([^}]+)", content):
        editor.tag_add("latex_italic", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
    # Commands
    for match in re.finditer(r"\\[a-zA-Z@]+", content):
        editor.tag_add("latex_command", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
    # Braces
    for match in re.finditer(r"[{}]", content):
        editor.tag_add("latex_brace", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")


def _resolve_image_path(tex_file_path, image_path_in_tex):
    if not tex_file_path:
        base_directory = os.getcwd()
    else:
        base_directory = os.path.dirname(tex_file_path)
    clean_image_path = image_path_in_tex.strip().replace('\n', '').replace('\r', '')
    normalized_path = os.path.normpath(clean_image_path.replace("/", os.sep))
    return os.path.join(base_directory, normalized_path)

def clear_syntax_highlighting(editor):
    if not editor: return
    tags = ["latex_command", "latex_brace", "latex_comment", "image_error", "latex_bold", "latex_italic"]
    for tag in tags:
        try: editor.tag_remove(tag, "1.0", tk.END)
        except tk.TclError: pass

def refresh_syntax_highlighting(editor):
    clear_syntax_highlighting(editor)
    apply_syntax_highlighting(editor)