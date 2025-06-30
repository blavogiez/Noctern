import tkinter as tk
from tkinter import messagebox
import os
import re
from PIL import ImageGrab, Image
import interface
import editor_logic
import debug_console

def paste_image_from_clipboard():
    """
    Pastes an image from the clipboard, saves it to a structured directory,
    and inserts the corresponding LaTeX code. Tracking is handled externally.
    """
    debug_console.log("Paste from clipboard triggered.", level='ACTION')

    current_tab = interface.get_current_tab()
    if not current_tab:
        debug_console.log("Paste aborted: No active tab.", level='WARNING')
        return
    editor = current_tab.editor

    try:
        image = ImageGrab.grabclipboard()
        if not isinstance(image, Image.Image):
             if image is None:
                 debug_console.log("Paste info: Clipboard is empty, no image found.", level='INFO')
                 messagebox.showwarning("Clipboard Empty", "No image found in the clipboard.")
             else:
                 debug_console.log("Paste info: Clipboard content is not an image.", level='INFO')
                 messagebox.showinfo("Information", "The clipboard does not contain an image.")
             return

        base_dir = os.path.dirname(current_tab.file_path) if current_tab.file_path else os.getcwd()
        content = editor.get("1.0", tk.END)
        cursor_index = editor.index(tk.INSERT)
        
        char_index = editor.count("1.0", cursor_index)[0]
        
        section, subsection, subsubsection = editor_logic.extract_section_structure(content, char_index)
        debug_console.log(f"Determined section structure: {section}/{subsection}/{subsubsection}", level='DEBUG')

        def sanitize(text):
            text = text.lower().replace(" ", "_")
            return re.sub(r'[^\w\-_.]', '', text)
        
        section, subsection, subsubsection = sanitize(section), sanitize(subsection), sanitize(subsubsection)

        fig_dir_path = os.path.join(base_dir, "figures", section, subsection, subsubsection)
        os.makedirs(fig_dir_path, exist_ok=True)
        debug_console.log(f"Ensured directory exists: {fig_dir_path}", level='DEBUG')

        index = 1
        while True:
            file_name = f"fig_{index}.png"
            full_file_path = os.path.join(fig_dir_path, file_name)
            if not os.path.exists(full_file_path): break
            index += 1

        image.save(full_file_path, "PNG")
        debug_console.log(f"Image saved to: {full_file_path}", level='SUCCESS')

        latex_path = os.path.relpath(full_file_path, base_dir).replace("\\", "/")
        
        latex_code = (
            f"\n\\begin{{figure}}[h!]\n"
            f"    \\centering\n"
            f"    \\includegraphics[width=0.8\\textwidth]{{{latex_path}}}\n"
            f"    \\caption{{Caption here}}\n"
            f"    \\label{{fig:{section}_{subsection}_{index}}}\n"
            f"\\end{{figure}}\n"
        )
        
        editor.insert(tk.INSERT, latex_code)
        debug_console.log("LaTeX code inserted into editor.", level='INFO')

    except Exception as e:
        debug_console.log(f"An unexpected error occurred during paste: {str(e)}", level='ERROR')
        messagebox.showerror("Error Pasting Image", f"An unexpected error occurred:\n{str(e)}")