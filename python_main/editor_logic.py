import tkinter as tk
import re
import os
from tkinter import messagebox
from PIL import ImageGrab

# Import the interface module to get access to the current tab
import interface

outline_tree = None

def initialize_editor_logic(tree_widget):
    """Sets the global reference to the outline tree."""
    global outline_tree
    outline_tree = tree_widget

def update_outline_tree(editor):
    """Updates the Treeview widget with LaTeX section structure."""
    if not outline_tree or not editor:
        return

    outline_tree.delete(*outline_tree.get_children())
    content = editor.get("1.0", tk.END)
    lines = content.split("\n")
    parents = {0: ""} # Map level to parent node ID

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        for level, cmd in enumerate(["section", "subsection", "subsubsection"], 1):
            # Improved regex to handle:
            # - Starred versions (e.g., \section*{...})
            # - Optional arguments (e.g., \section[short]{long})
            # Note: This regex does not support nested braces {} in the title.
            match = re.match(rf"\\{cmd}\*?(?:\[[^\]]*\])?{{([^}}]*)}}", stripped_line)
            if match:
                title = match.group(1).strip() # Get the title from the first capture group
                # Ensure parent exists for the current level
                parent_id = parents.get(level - 1, "")
                node_id = outline_tree.insert(parent_id, "end", text=title, values=(i + 1,))
                parents[level] = node_id
                # Remove descendants from parent map if we move up the hierarchy
                for deeper in range(level + 1, 4):
                    if deeper in parents:
                        del parents[deeper]
                break # Found a section command, move to next line

def go_to_section(editor, event):
    """Scrolls the editor to the selected section in the outline tree."""
    if not editor:
        return

    selected = outline_tree.selection()
    if selected:
        # Get the line number from the item's values
        values = outline_tree.item(selected[0], "values")
        if values:
            line_num = values[0]
            try:
                editor.mark_set("insert", f"{line_num}.0")
                editor.see(f"{line_num}.0")
                editor.focus()
            except tk.TclError:
                # Handle cases where line number might be invalid (e.g., empty file)
                pass

def apply_syntax_highlighting(editor):
    """Applies syntax highlighting to LaTeX commands, braces, and comments."""
    if not editor:
        return

    # Remove existing tags first
    editor.tag_remove("latex_command", "1.0", tk.END)
    editor.tag_remove("latex_brace", "1.0", tk.END)
    editor.tag_remove("latex_comment", "1.0", tk.END)

    content = editor.get("1.0", tk.END)

    # Highlight LaTeX commands (e.g., \section, \textbf)
    for match in re.finditer(r"\\[a-zA-Z@]+", content):
        start = f"1.0 + {match.start()} chars"
        end = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_command", start, end)

    # Highlight braces {}
    for match in re.finditer(r"[{}]", content):
        start = f"1.0 + {match.start()} chars"
        end = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_brace", start, end)

    # Highlight comments %
    for match in re.finditer(r"%[^\n]*", content):
        start = f"1.0 + {match.start()} chars"
        end = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_comment", start, end)

def extract_section_structure(content, position_index):
    """
    Extracts the current section, subsection, subsubsection titles
    based on the cursor position. Used for creating image directories.
    """
    lines = content[:position_index].split("\n")

    section = "default"
    subsection = "default"
    subsubsection = "default"

    for line in lines:
        if r"\section{" in line:
            match = re.search(r"\\section\{(.+?)\}", line)
            if match:
                section = match.group(1).strip()
                subsection = "default"
                subsubsection = "default"
        elif r"\subsection{" in line:
            match = re.search(r"\\subsection\{(.+?)\}", line)
            if match:
                subsection = match.group(1).strip()
                subsubsection = "default"
        elif r"\subsubsection{" in line:
            match = re.search(r"\\subsubsection\{(.+?)\}", line)
            if match:
                subsubsection = match.group(1).strip()
    return section, subsection, subsubsection

# --- NEW: Image Deletion Tracking Logic ---

def _parse_for_images(content):
    """Parses document content to find all \includegraphics paths."""
    image_pattern = re.compile(r"\\includegraphics(?:\[.*?\])?\{(.*?)\}")
    found_paths = image_pattern.findall(content)
    return set(found_paths)

def _resolve_image_path(tex_file_path, image_path_in_tex):
    """Resolves the image path from the .tex file to an absolute path."""
    base_dir = os.path.dirname(tex_file_path) if tex_file_path else os.getcwd()
    absolute_path = os.path.normpath(os.path.join(base_dir, image_path_in_tex))
    return absolute_path

def _cleanup_empty_dirs(path):
    """Recursively deletes empty directories upwards from the given path."""
    try:
        figures_root_parts = path.split("figures")
        if len(figures_root_parts) < 2: return
        figures_root = os.path.join(figures_root_parts[0], "figures")

        while path.startswith(figures_root) and os.path.isdir(path) and path != figures_root:
            if not os.listdir(path):
                try:
                    os.rmdir(path)
                    print(f"Removed empty directory: {path}")
                    path = os.path.dirname(path)
                except OSError: break
            else: break
    except (IndexError, AttributeError):
        print(f"Warning: Could not determine figures root for cleanup of '{path}'")

def _prompt_for_image_deletion(image_path_to_delete, tex_file_path):
    """Shows the confirmation dialog and deletes the file if confirmed."""
    if not os.path.exists(image_path_to_delete):
        return

    base_dir = os.path.dirname(tex_file_path) if tex_file_path else os.getcwd()
    display_path = os.path.relpath(image_path_to_delete, base_dir)

    response = messagebox.askyesno(
        "Delete Associated Image File?",
        f"The reference to the following image file has been removed from your document:\n\n'{display_path}'\n\nDo you want to permanently delete the file itself?",
        icon='warning'
    )
    
    if response:
        try:
            os.remove(image_path_to_delete)
            print(f"Image file deleted: {image_path_to_delete}")
            _cleanup_empty_dirs(os.path.dirname(image_path_to_delete))
        except OSError as e:
            messagebox.showerror("Deletion Error", f"Could not delete the file:\n{e}")

def update_tracked_images(current_tab):
    """Parses the current tab's content and sets the initial list of tracked images."""
    if not current_tab: return
    content = current_tab.get_content()
    current_tab.tracked_image_paths = _parse_for_images(content)

def check_for_deleted_images(current_tab):
    """Compares current images with tracked ones and prompts for deletion if any are missing."""
    if not current_tab or not hasattr(current_tab, 'tracked_image_paths'):
        return

    content = current_tab.get_content()
    new_image_set = _parse_for_images(content)

    deleted_image_paths_relative = current_tab.tracked_image_paths - new_image_set

    if deleted_image_paths_relative:
        for rel_path in deleted_image_paths_relative:
            abs_path = _resolve_image_path(current_tab.file_path, rel_path)
            _prompt_for_image_deletion(abs_path, current_tab.file_path)

    current_tab.tracked_image_paths = new_image_set