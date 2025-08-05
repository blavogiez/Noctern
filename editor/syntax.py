import tkinter as tk
import re
import os
from editor.tab import EditorTab
from utils import debug_console

def apply_syntax_highlighting(editor):
    """
    Applies syntax highlighting to LaTeX elements within the editor.

    This function handles:
    - Standard commands, braces, and comments.
    - Bold and italic text via \textbf{} and \textit{}.
    - Highlighting references to missing image files.

    Args:
        editor (tk.Text): The Tkinter Text widget to apply highlighting to.
    """
    if not editor:
        debug_console.log("Editor not available for syntax highlighting.", level='WARNING')
        return

    debug_console.log("Applying syntax highlighting.", level='DEBUG')

    current_tab = editor.master
    if not isinstance(current_tab, EditorTab):
        return

    # Destroy and clear any previously embedded error labels.
    if hasattr(current_tab, 'error_labels'):
        for label in current_tab.error_labels:
            try:
                label.destroy()
            except tk.TclError:
                pass  # Label might already be destroyed
        current_tab.error_labels.clear()
    else:
        current_tab.error_labels = []

    # --- Font and Tag Configuration ---
    base_font = current_tab.editor_font
    
    try:
        # Get the actual font configuration
        font_family = base_font.cget("family")
        font_size = base_font.cget("size")
        
        bold_font = (font_family, font_size, "bold")
        italic_font = (font_family, font_size, "italic")
        normal_font = (font_family, font_size, "normal")
    except tk.TclError:
        # Fallback fonts if base_font is not available
        bold_font = ("Arial", 12, "bold")
        italic_font = ("Arial", 12, "italic")
        normal_font = ("Arial", 12, "normal")

    editor.tag_configure("latex_command", font=bold_font)
    editor.tag_configure("latex_brace", font=normal_font)
    editor.tag_configure("latex_comment", foreground="gray")
    editor.tag_configure("image_error", background="#FFF0F0", foreground="#D00000")
    editor.tag_configure("latex_bold", font=bold_font)
    editor.tag_configure("latex_italic", font=italic_font)

    # --- Tag Removal ---
    tags_to_remove = ["latex_command", "latex_brace", "latex_comment", 
                      "image_error", "latex_bold", "latex_italic"]
    for tag in tags_to_remove:
        editor.tag_remove(tag, "1.0", tk.END)

    try:
        content = editor.get("1.0", tk.END)
    except tk.TclError:
        debug_console.log("Could not get editor content", level='ERROR')
        return

    # --- Syntax Highlighting Application ---
    
    # Apply comments FIRST so other tags can override if needed
    # 1. Comments
    for match in re.finditer(r"%[^\n]*", content):
        start_index = f"1.0 + {match.start()} chars"
        end_index = f"1.0 + {match.end()} chars"
        try:
            editor.tag_add("latex_comment", start_index, end_index)
        except tk.TclError:
            pass

    # 2. Bold and Italic Text - Fixed regex patterns
    for match in re.finditer(r"\\textbf\{([^}]+)\}", content):
        start_index = f"1.0 + {match.start(1)} chars"
        end_index = f"1.0 + {match.end(1)} chars"
        try:
            editor.tag_add("latex_bold", start_index, end_index)
        except tk.TclError:
            pass  # Index might be invalid

    for match in re.finditer(r"\\textit\{([^}]+)\}", content):
        start_index = f"1.0 + {match.start(1)} chars"
        end_index = f"1.0 + {match.end(1)} chars"
        try:
            editor.tag_add("latex_italic", start_index, end_index)
        except tk.TclError:
            pass  # Index might be invalid

    # 3. Standard LaTeX Commands - Fixed regex pattern
    for match in re.finditer(r"\\[a-zA-Z@]+", content):
        start_index = f"1.0 + {match.start()} chars"
        end_index = f"1.0 + {match.end()} chars"
        try:
            editor.tag_add("latex_command", start_index, end_index)
        except tk.TclError:
            pass

    # 4. Braces - Fixed regex pattern
    for match in re.finditer(r"[{}]", content):
        start_index = f"1.0 + {match.start()} chars"
        end_index = f"1.0 + {match.end()} chars"
        try:
            editor.tag_add("latex_brace", start_index, end_index)
        except tk.TclError:
            pass

    # 5. Check for Missing \includegraphics Files - Fixed regex pattern
    image_inclusion_pattern = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    missing_image_count = 0
    
    for match in image_inclusion_pattern.finditer(content):
        relative_image_path = match.group(1).strip()
        if not relative_image_path:
            continue
            
        absolute_image_path = _resolve_image_path(current_tab.file_path, relative_image_path)

        if not os.path.exists(absolute_image_path):
            missing_image_count += 1
            path_start_index = f"1.0 + {match.start(1)} chars"
            path_end_index = f"1.0 + {match.end(1)} chars"
            
            try:
                editor.tag_add("image_error", path_start_index, path_end_index)

                # Get line number for error label placement
                line_index = editor.index(path_start_index).split('.')[0]
                
                error_label = tk.Label(
                    editor, 
                    text=" ⚠ File not found", 
                    font=("Segoe UI", 8),
                    bg="#FFF0F0", 
                    fg="#D00000", 
                    padx=2,
                    relief="flat"
                )
                current_tab.error_labels.append(error_label)
                
                # Insert the error label at the end of the line
                try:
                    editor.window_create(f"{line_index}.end", window=error_label, align="top")
                except tk.TclError:
                    # If window_create fails, just destroy the label
                    error_label.destroy()
                    current_tab.error_labels.remove(error_label)
                    
            except tk.TclError as e:
                debug_console.log(f"Error adding image error highlight: {e}", level='WARNING')
            
    if missing_image_count > 0:
        debug_console.log(f"Detected {missing_image_count} missing image reference(s).", level='WARNING')

def _resolve_image_path(tex_file_path, image_path_in_tex):
    """
    Resolves a relative image path found in a .tex file to an absolute filesystem path.
    
    Args:
        tex_file_path (str): The absolute path to the .tex file.
        image_path_in_tex (str): The image path as specified in the LaTeX document.
        
    Returns:
        str: The absolute path to the image file.
    """
    if not tex_file_path:
        base_directory = os.getcwd()
    else:
        base_directory = os.path.dirname(tex_file_path)
    
    # Clean the image path
    clean_image_path = image_path_in_tex.strip().replace('\n', '').replace('\r', '')
    
    # Normalize the path for cross-platform compatibility
    normalized_path = os.path.normpath(clean_image_path.replace("/", os.sep))
    absolute_path = os.path.join(base_directory, normalized_path)
    
    return absolute_path

def clear_syntax_highlighting(editor):
    """
    Clears all syntax highlighting from the editor.
    
    Args:
        editor (tk.Text): The Tkinter Text widget to clear highlighting from.
    """
    if not editor:
        return
        
    tags_to_remove = ["latex_command", "latex_brace", "latex_comment", 
                      "image_error", "latex_bold", "latex_italic"]
    
    for tag in tags_to_remove:
        try:
            editor.tag_remove(tag, "1.0", tk.END)
        except tk.TclError:
            pass

def refresh_syntax_highlighting(editor):
    """
    Refreshes syntax highlighting by clearing and reapplying it.
    
    Args:
        editor (tk.Text): The Tkinter Text widget to refresh highlighting for.
    """
    clear_syntax_highlighting(editor)
    apply_syntax_highlighting(editor)