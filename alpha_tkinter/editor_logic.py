import tkinter as tk
import re
import os
from tkinter import messagebox
from PIL import ImageGrab

outline_tree = None
get_current_tab_func = None # Callback to get the current tab from the GUI manager

def initialize_editor_logic(tree_widget, get_current_tab_callback):
    """Sets the global reference to the outline tree."""
    global outline_tree
    global get_current_tab_func
    outline_tree = tree_widget
    get_current_tab_func = get_current_tab_callback

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
    """
    Applies syntax highlighting ONLY to the visible portion of the text widget.
    This is a major performance optimization for large files.
    """
    if not editor or not editor.winfo_exists():
        return

    # Define the visible range, with a small buffer for partially visible lines
    visible_start_index = editor.index("@0,0")
    visible_end_index = editor.index(f"@0,{editor.winfo_height()}")
    
    start_line = int(visible_start_index.split('.')[0])
    # Add a buffer of a few lines to handle smooth scrolling and partial lines
    end_line = int(visible_end_index.split('.')[0]) + 2
    
    start_index = f"{start_line}.0"
    end_index = f"{end_line}.end"

    # Remove existing tags from only the visible range to prevent tag buildup
    editor.tag_remove("latex_command", start_index, end_index)
    editor.tag_remove("latex_brace", start_index, end_index)
    editor.tag_remove("latex_comment", start_index, end_index)

    # Get only the content of the visible lines
    content = editor.get(start_index, end_index)

    # Helper function to apply tags based on regex matches within the visible content
    def apply_tags_for_pattern(pattern, tag_name):
        for match in re.finditer(pattern, content):
            # Calculate the absolute start and end indices in the editor from the relative match
            match_start = editor.index(f"{start_index} + {match.start()} chars")
            match_end = editor.index(f"{start_index} + {match.end()} chars")
            editor.tag_add(tag_name, match_start, match_end)

    # Apply highlighting for each pattern on the visible content
    apply_tags_for_pattern(r"\\[a-zA-Z@]+", "latex_command")
    apply_tags_for_pattern(r"[{}]", "latex_brace")
    apply_tags_for_pattern(r"%[^\n]*", "latex_comment")

def extract_section_structure(content, position_index):
    """
    Extracts the current section, subsection, subsubsection titles
    based on the cursor position.
    """
    lines = content[:position_index].split("\n")

    section = "default"
    subsection = "default"
    subsubsection = "default"

    for line in lines:
        if r"\section{" in line:
            match = re.search(r"\\section\{(.+?)\}", line)
            if match:
                section = match.group(1).strip().replace(" ", "_").replace("{", "").replace("}", "")
                subsection = "default"
                subsubsection = "default"
        elif r"\subsection{" in line:
            match = re.search(r"\\subsection\{(.+?)\}", line)
            if match:
                subsection = match.group(1).strip().replace(" ", "_").replace("{", "").replace("}", "")
                subsubsection = "default"
        elif r"\subsubsection{" in line:
            match = re.search(r"\\subsubsection\{(.+?)\}", line)
            if match:
                subsubsection = match.group(1).strip().replace(" ", "_").replace("{", "").replace("}", "")

    # Basic sanitization for path safety
    section = re.sub(r'[^\w\-_\.]', '', section)
    subsection = re.sub(r'[^\w\-_\.]', '', subsection)
    subsubsection = re.sub(r'[^\w\-_\.]', '', subsubsection)

    return section, subsection, subsubsection

def paste_image():
    """Pastes an image from the clipboard into the editor as a LaTeX figure."""
    current_tab = get_current_tab_func()
    if not current_tab: return
    editor = current_tab.editor
    if not editor:
        return

    try:
        image = ImageGrab.grabclipboard()
        if image is None:
            messagebox.showwarning("Warning", "No image found in clipboard.")
            return

        # Determine the base directory for saving figures
        # Use the directory of the current file, or the current working directory if no file is open
        base_dir = os.path.dirname(current_tab.file_path) if current_tab.file_path else "."

        # Get section titles based on cursor position
        content = editor.get("1.0", tk.END)
        cursor_index = editor.index(tk.INSERT)
        # Convert Tkinter index to character index for string slicing
        char_index = int(editor.count("1.0", cursor_index)[0])

        section, subsection, subsubsection = extract_section_structure(content, char_index)

        # Construct the directory path for the figure
        fig_dir_path = os.path.join(base_dir, "figures", section, subsection, subsubsection)
        os.makedirs(fig_dir_path, exist_ok=True)

        # Find a unique filename
        index = 1
        while True:
            file_name = f"fig{index}.png"
            full_file_path = os.path.join(fig_dir_path, file_name)
            if not os.path.exists(full_file_path):
                break
            index += 1

        # Save the image
        image.save(full_file_path, "PNG")

        # Get the relative path for LaTeX \includegraphics
        latex_path = os.path.relpath(full_file_path, base_dir).replace("\\", "/")

        # Insert the LaTeX code for the figure
        latex_code = (
            "\n\\begin{figure}[h!]\n"
            "    \\centering\n"
            f"    \\includegraphics[width=0.8\\textwidth]{{{latex_path}}}\n"
            f"    \\caption{{Caption here}}\n"
            f"    \\label{{fig:{section}_{subsection}_{index}}}\n"
            "\\end{figure}\n"
        )

        editor.insert(tk.INSERT, latex_code)

    except Exception as e:
        messagebox.showerror("Error", f"Error pasting image:\n{str(e)}")