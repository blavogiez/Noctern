import tkinter as tk
from tkinter import messagebox
import os
import re
from PIL import ImageGrab, Image
import interface
import editor_logic

def paste_image_from_clipboard():
    """
    Pastes an image from the clipboard, saves it to a structured directory,
    and inserts the corresponding LaTeX code. Tracking is handled externally.
    """
    current_tab = interface.get_current_tab()
    if not current_tab: return
    editor = current_tab.editor

    try:
        image = ImageGrab.grabclipboard()
        if not isinstance(image, Image.Image):
             if image is None: messagebox.showwarning("Clipboard Empty", "No image found in the clipboard.")
             else: messagebox.showinfo("Information", "The clipboard does not contain an image.")
             return

        base_dir = os.path.dirname(current_tab.file_path) if current_tab.file_path else os.getcwd()
        content = editor.get("1.0", tk.END)
        cursor_index = editor.index(tk.INSERT)
        
        char_index = editor.count("1.0", cursor_index)[0]
        
        section, subsection, subsubsection = editor_logic.extract_section_structure(content, char_index)

        def sanitize(text):
            text = text.lower().replace(" ", "_")
            return re.sub(r'[^\w\-_.]', '', text)
        
        section, subsection, subsubsection = sanitize(section), sanitize(subsection), sanitize(subsubsection)

        fig_dir_path = os.path.join(base_dir, "figures", section, subsection, subsubsection)
        os.makedirs(fig_dir_path, exist_ok=True)

        index = 1
        while True:
            file_name = f"fig_{index}.png"
            full_file_path = os.path.join(fig_dir_path, file_name)
            if not os.path.exists(full_file_path): break
            index += 1

        image.save(full_file_path, "PNG")
        print(f"Image saved to: {full_file_path}")

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

    except Exception as e:
        messagebox.showerror("Error Pasting Image", f"An unexpected error occurred:\n{str(e)}")