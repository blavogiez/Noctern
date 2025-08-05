import tkinter as tk
import re
import os
from editor.tab import EditorTab
from utils import debug_console

def apply_syntax_highlighting(editor):
    """
    Applies syntax highlighting to LaTeX commands, braces, and comments within the editor.
    Also checks for and highlights references to missing image files.

    This function iterates through the editor's content, applying specific Tkinter text tags
    to different LaTeX elements for visual distinction. It also performs a check for
    \includegraphics commands and verifies if the referenced image files exist on the filesystem.
    Missing image references are highlighted, and an error indicator is embedded.

    Args:
        editor (tk.Text): The Tkinter Text widget to apply highlighting to.
    """
    if not editor:
        debug_console.log("Editor not available for syntax highlighting.", level='WARNING')
        return

    debug_console.log("Applying syntax highlighting and checking for missing image files.", level='DEBUG')

    current_tab = editor.master
    # Ensure the editor's master is an EditorTab instance to access its properties.
    if isinstance(current_tab, EditorTab):
        # Destroy and clear any previously embedded error labels to prevent accumulation.
        for label in current_tab.error_labels:
            label.destroy()
        current_tab.error_labels.clear()

    # Get the current font from the editor to ensure zoom is respected
    current_font = current_tab.editor_font
    
    # Configure tags based on the current font to ensure zoom is respected
    editor.tag_configure("latex_command", font=(current_font.cget("family"), current_font.cget("size"), "bold"))
    editor.tag_configure("latex_brace", font=(current_font.cget("family"), current_font.cget("size")))
    editor.tag_configure("latex_comment", font=(current_font.cget("family"), current_font.cget("size")))
    editor.tag_configure("image_error", font=(current_font.cget("family"), current_font.cget("size")))

    # Remove all existing syntax highlighting tags to ensure a clean re-application.
    editor.tag_remove("latex_command", "1.0", tk.END)
    editor.tag_remove("latex_brace", "1.0", tk.END)
    editor.tag_remove("latex_comment", "1.0", tk.END)
    editor.tag_remove("image_error", "1.0", tk.END) 

    content = editor.get("1.0", tk.END) # Get the entire content for parsing. 

    # --- 1. Standard LaTeX Syntax Highlighting ---
    # Highlight LaTeX commands (e.g., \command, \@command).
    for match in re.finditer(r"\\[a-zA-Z@]+", content):
        start_index = f"1.0 + {match.start()} chars"
        end_index = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_command", start_index, end_index)

    # Highlight LaTeX braces ({}).
    for match in re.finditer(r"[{}]", content):
        start_index = f"1.0 + {match.start()} chars"
        end_index = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_brace", start_index, end_index)

    # Highlight LaTeX comments (lines starting with %). 
    for match in re.finditer(r"%[^\n]*", content):
        start_index = f"1.0 + {match.start()} chars"
        end_index = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_comment", start_index, end_index)

    # --- 2. Check for Missing \includegraphics Files ---
    if isinstance(current_tab, EditorTab):
        # Regex to find \includegraphics commands and capture the image path.
        image_inclusion_pattern = re.compile(r"\\includegraphics(?:\\\\[.*?\\\\])?\\\{(.*?)\\" ) # Corrected regex for optional brackets and escaped curly braces
        missing_image_count = 0
        for match in image_inclusion_pattern.finditer(content):
            relative_image_path = match.group(1) # Extract the path as written in the LaTeX document.
            # Resolve the relative path to an absolute path on the filesystem.
            absolute_image_path = _resolve_image_path(current_tab.file_path, relative_image_path)

            # Check if the resolved image file actually exists.
            if not os.path.exists(absolute_image_path):
                missing_image_count += 1
                
                # Highlight the missing image path in the editor.
                path_start_index = f"1.0 + {match.start(1)} chars"
                path_end_index = f"1.0 + {match.end(1)} chars"
                editor.tag_add("image_error", path_start_index, path_end_index)

                # Create and embed a visual error indicator (label) at the end of the line.
                line_index = editor.index(path_start_index).split('.')[0]
                error_label = tk.Label(
                    editor,
                    text=" ⚠ Fichier introuvable", # "File not found" in French.
                    font=("Segoe UI", 8),
                    bg="#FFF0F0", # Light red background for the label.
                    fg="#D00000", # Dark red text for the label.
                    padx=2
                )
                # Add the label to the tab's list for proper cleanup when the tab is closed.
                current_tab.error_labels.append(error_label);
                # Embed the label widget directly into the text editor at the end of the line.
                editor.window_create(f"{line_index}.end", window=error_label, align="top")
        if missing_image_count > 0:
            debug_console.log(f"Detected {missing_image_count} missing image reference(s) in the document.", level='WARNING')

def _resolve_image_path(tex_file_path, image_path_in_tex):
    """
    Resolves a relative image path found in a .tex file to an absolute filesystem path.

    This function takes the path of the .tex file and the image path as written
    in the LaTeX document (which can be relative) and converts it into an absolute
    path that can be used to locate the file on the system.

    Args:
        tex_file_path (str): The absolute path to the .tex file.
        image_path_in_tex (str): The image path as specified in the \includegraphics command.

    Returns:
        str: The absolute path to the image file.
    """
    if not tex_file_path:
        # If the .tex file path is not available, assume current working directory as base.
        base_directory = os.getcwd()
    else:
        # Otherwise, the base directory is where the .tex file is located.
        base_directory = os.path.dirname(tex_file_path)
    # Normalize the path to handle '..' and resolve to an absolute path.
    # Also, replace forward slashes with backslashes for OS compatibility if needed.
    normalized_path = os.path.normpath(image_path_in_tex.replace("/", os.sep))
    absolute_path = os.path.join(base_directory, normalized_path)
    return absolute_path
