import tkinter as tk
import re
import os
from datetime import datetime
from tkinter import messagebox
from PIL import ImageGrab

outline_tree = None
get_current_tab_func = None

def initialize_editor_logic(tree_widget, get_current_tab_callback):
    global outline_tree
    global get_current_tab_func
    outline_tree = tree_widget
    get_current_tab_func = get_current_tab_callback

def update_outline_tree(editor):
    if not outline_tree or not editor:
        return
    current_tab = get_current_tab_func()
    if not current_tab or current_tab.editor != editor:
        return
    content = editor.get("1.0", tk.END)
    if content == current_tab.last_content_for_outline_parsing:
        return
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [Perf] update_outline_tree: Re-parsing document structure.")
    lines = content.split("\n")
    current_outline_structure = []
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        for level, cmd in enumerate(["section", "subsection", "subsubsection"], 1):
            match = re.match(rf"\\{cmd}\*?(?:\[[^\]]*\])?{{([^}}]*)}}", stripped_line)
            if match:
                title = match.group(1).strip()
                current_outline_structure.append((level, title, i + 1))
                break
    if current_outline_structure != current_tab.last_parsed_outline_structure:
        outline_tree.delete(*outline_tree.get_children())
        parents_for_tree = {0: ""}
        for level, title, line_num in current_outline_structure:
            parent_id = parents_for_tree.get(level - 1, "")
            node_id = outline_tree.insert(parent_id, "end", text=title, values=(line_num,))
            parents_for_tree[level] = node_id
            for deeper in range(level + 1, 4):
                if deeper in parents_for_tree:
                    del parents_for_tree[deeper]
        current_tab.last_parsed_outline_structure = current_outline_structure
    current_tab.last_content_for_outline_parsing = content

def go_to_section(editor, event):
    if not editor:
        return
    selected = outline_tree.selection()
    if selected:
        values = outline_tree.item(selected[0], "values")
        if values:
            line_num = values[0]
            try:
                editor.mark_set("insert", f"{line_num}.0")
                editor.see(f"{line_num}.0")
                editor.focus()
            except tk.TclError:
                pass

def extract_section_structure(content, position_index):
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
    section = re.sub(r'[^\w\-_\.]', '', section)
    subsection = re.sub(r'[^\w\-_\.]', '', subsection)
    subsubsection = re.sub(r'[^\w\-_\.]', '', subsubsection)
    return section, subsection, subsubsection

def paste_image():
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
        base_dir = os.path.dirname(current_tab.file_path) if current_tab.file_path else "."
        content = editor.get("1.0", tk.END)
        cursor_index = editor.index(tk.INSERT)
        char_index = int(editor.count("1.0", cursor_index)[0])
        section, subsection, subsubsection = extract_section_structure(content, char_index)
        fig_dir_path = os.path.join(base_dir, "figures", section, subsection, subsubsection)
        os.makedirs(fig_dir_path, exist_ok=True)
        index = 1
        while True:
            file_name = f"fig{index}.png"
            full_file_path = os.path.join(fig_dir_path, file_name)
            if not os.path.exists(full_file_path):
                break
            index += 1
        image.save(full_file_path, "PNG")
        latex_path = os.path.relpath(full_file_path, base_dir).replace("\\", "/")
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
    finally:
        if 'image' in locals() and image is not None:
            del image