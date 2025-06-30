import tkinter as tk
import re
import os
from tkinter import messagebox
from PIL import ImageGrab

# Import the interface module to get access to the current tab
import interface
from editor_tab import EditorTab # Import EditorTab to use type hinting and access master
import debug_console # Import the new console

outline_tree = None

def initialize_editor_logic(tree_widget):
    """Sets the global reference to the outline tree."""
    global outline_tree
    outline_tree = tree_widget
    debug_console.log("Editor logic initialized.", level='INFO')

def update_outline_tree(editor):
    """Updates the Treeview widget with LaTeX section structure."""
    if not outline_tree or not editor:
        return

    debug_console.log("Updating outline tree.", level='DEBUG')
    outline_tree.delete(*outline_tree.get_children())
    content = editor.get("1.0", tk.END)
    lines = content.split("\n")
    parents = {0: ""} # Map level to parent node ID

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        for level, cmd in enumerate(["section", "subsection", "subsubsection"], 1):
            match = re.match(rf"\\{cmd}\*?(?:\[[^\]]*\])?{{([^}}]*)}}", stripped_line)
            if match:
                title = match.group(1).strip()
                parent_id = parents.get(level - 1, "")
                node_id = outline_tree.insert(parent_id, "end", text=title, values=(i + 1,))
                parents[level] = node_id
                for deeper in range(level + 1, 4):
                    if deeper in parents:
                        del parents[deeper]
                break

def go_to_section(editor, event):
    """Scrolls the editor to the selected section in the outline tree."""
    if not editor:
        return
    selected = outline_tree.selection()
    if selected:
        values = outline_tree.item(selected[0], "values")
        if values:
            line_num = values[0]
            debug_console.log(f"Navigating to section on line {line_num}.", level='ACTION')
            try:
                editor.mark_set("insert", f"{line_num}.0")
                editor.see(f"{line_num}.0")
                editor.focus()
            except tk.TclError:
                pass

def apply_syntax_highlighting(editor):
    """
    Applies syntax highlighting and checks for missing image files.
    """
    if not editor:
        return

    debug_console.log("Applying syntax highlighting and checking for missing images.", level='DEBUG')

    # --- 1. Cleanup old tags and error widgets ---
    current_tab = editor.master
    if isinstance(current_tab, EditorTab):
        # Destroy and clear any previous error labels
        for label in current_tab.error_labels:
            label.destroy()
        current_tab.error_labels.clear()

    editor.tag_remove("latex_command", "1.0", tk.END)
    editor.tag_remove("latex_brace", "1.0", tk.END)
    editor.tag_remove("latex_comment", "1.0", tk.END)
    editor.tag_remove("image_error", "1.0", tk.END) # Remove old error tags

    content = editor.get("1.0", tk.END)

    # --- 2. Standard Syntax Highlighting ---
    for match in re.finditer(r"\\[a-zA-Z@]+", content):
        start, end = f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars"
        editor.tag_add("latex_command", start, end)

    for match in re.finditer(r"[{}]", content):
        start, end = f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars"
        editor.tag_add("latex_brace", start, end)

    for match in re.finditer(r"%[^\n]*", content):
        start, end = f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars"
        editor.tag_add("latex_comment", start, end)

    # --- 3. Check for missing \includegraphics files ---
    if isinstance(current_tab, EditorTab):
        image_pattern = re.compile(r"\\includegraphics(?:\[.*?\])?\{(.*?)\}")
        missing_count = 0
        for match in image_pattern.finditer(content):
            relative_path = match.group(1)
            # Use the helper function to resolve the absolute path
            absolute_path = _resolve_image_path(current_tab.file_path, relative_path)

            if not os.path.exists(absolute_path):
                missing_count += 1
                # File does not exist, apply error highlighting
                
                # Highlight the path in red
                path_start = f"1.0 + {match.start(1)} chars"
                path_end = f"1.0 + {match.end(1)} chars"
                editor.tag_add("image_error", path_start, path_end)

                # Create and embed an error label at the end of the line
                line_index = editor.index(path_start).split('.')[0]
                error_label = tk.Label(
                    editor,
                    text=" ⚠ Fichier introuvable",
                    font=("Segoe UI", 8),
                    bg="#FFF0F0", # Light red background
                    fg="#D00000", # Dark red text
                    padx=2
                )
                # Add to the tab's list for later cleanup
                current_tab.error_labels.append(error_label)
                # Embed the widget in the text editor
                editor.window_create(f"{line_index}.end", window=error_label, align="top")
        if missing_count > 0:
            debug_console.log(f"Found {missing_count} missing image reference(s).", level='WARNING')


def extract_section_structure(content, position_index):
    """
    Extracts the current section, subsection, subsubsection titles
    based on the cursor position. Used for creating image directories.
    """
    lines = content[:position_index].split("\n")
    section, subsection, subsubsection = "default", "default", "default"
    for line in lines:
        if r"\section{" in line:
            match = re.search(r"\\section\{(.+?)\}", line)
            if match:
                section, subsection, subsubsection = match.group(1).strip(), "default", "default"
        elif r"\subsection{" in line:
            match = re.search(r"\\subsection\{(.+?)\}", line)
            if match:
                subsection, subsubsection = match.group(1).strip(), "default"
        elif r"\subsubsection{" in line:
            match = re.search(r"\\subsubsection\{(.+?)\}", line)
            if match:
                subsubsection = match.group(1).strip()
    return section, subsection, subsubsection

# --- Intelligent Image Deletion Logic ---

def _parse_for_images(content):
    """Parses document content to find all \includegraphics paths."""
    image_pattern = re.compile(r"\\includegraphics(?:\[.*?\])?\{(.*?)\}")
    found_paths = image_pattern.findall(content)
    return set(found_paths)

def _resolve_image_path(tex_file_path, image_path_in_tex):
    """Resolves the image path from the .tex file to an absolute path."""
    if not tex_file_path:
        base_dir = os.getcwd()
    else:
        base_dir = os.path.dirname(tex_file_path)
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
                    debug_console.log(f"Removed empty directory: {path}", level='INFO')
                    path = os.path.dirname(path)
                except OSError: break
            else: break
    except (IndexError, AttributeError):
        debug_console.log(f"Could not determine figures root for cleanup of '{path}'", level='WARNING')


def _prompt_for_image_deletion(image_path_to_delete, tex_file_path):
    """Shows the confirmation dialog and deletes the file if confirmed."""
    if not os.path.exists(image_path_to_delete):
        return
    base_dir = os.path.dirname(tex_file_path) if tex_file_path else os.getcwd()
    display_path = os.path.relpath(image_path_to_delete, base_dir)
    debug_console.log(f"Prompting user to delete file: {display_path}", level='ACTION')
    response = messagebox.askyesno(
        "Delete Associated Image File?",
        f"The reference to the following image file has been removed from your document:\n\n'{display_path}'\n\nDo you want to permanently delete the file itself?",
        icon='warning'
    )
    if response:
        debug_console.log(f"User chose YES to delete file.", level='ACTION')
        try:
            os.remove(image_path_to_delete)
            debug_console.log(f"Image file deleted: {image_path_to_delete}", level='SUCCESS')
            _cleanup_empty_dirs(os.path.dirname(image_path_to_delete))
        except OSError as e:
            messagebox.showerror("Deletion Error", f"Could not delete the file:\n{e}")
            debug_console.log(f"Could not delete file '{image_path_to_delete}': {e}", level='ERROR')
    else:
        debug_console.log(f"User chose NO to delete file.", level='ACTION')


def check_for_deleted_images(current_tab):
    """
    Compares the current editor content with the last saved content to find
    deleted image references and prompts the user to delete the associated files.
    """
    debug_console.log("Checking for deleted image references on save.", level='INFO')
    if not current_tab or not current_tab.is_dirty():
        debug_console.log("Aborting check, tab is not dirty or invalid.", level='DEBUG')
        return
    last_saved_content = current_tab.last_saved_content
    if last_saved_content == "\n":
        debug_console.log("Aborting check, last saved content is empty.", level='DEBUG')
        return
    old_image_set = _parse_for_images(last_saved_content)
    current_content = current_tab.get_content()
    new_image_set = _parse_for_images(current_content)
    deleted_image_paths_relative = old_image_set - new_image_set
    if deleted_image_paths_relative:
        debug_console.log(f"Found {len(deleted_image_paths_relative)} deleted image reference(s). Prompting user.", level='DEBUG')
        for rel_path in deleted_image_paths_relative:
            abs_path = _resolve_image_path(current_tab.file_path, rel_path)
            _prompt_for_image_deletion(abs_path, current_tab.file_path)