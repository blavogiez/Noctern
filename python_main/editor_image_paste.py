# editor_image_paste.py

import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
from PIL import ImageGrab, Image
import interface
import editor_logic
import debug_console

class ImageDetailsDialog(tk.Toplevel):
    """A dialog to get caption and label for a pasted image."""
    def __init__(self, parent, suggested_label):
        super().__init__(parent)
        self.transient(parent)
        self.title("Image Details")
        self.geometry("400x180")
        self.grab_set()

        self.caption = ""
        self.label = ""

        # Use the parent's theme settings for consistency if possible
        try:
            bg_color = interface.get_theme_setting("root_bg", "#f0f0f0")
            self.configure(bg=bg_color)
        except Exception:
            self.configure(bg="#f0f0f0")

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Image Caption:").grid(row=0, column=0, sticky="w", pady=2)
        self.caption_entry = ttk.Entry(frame, width=50)
        self.caption_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame, text="Image Label:").grid(row=2, column=0, sticky="w", pady=2)
        self.label_entry = ttk.Entry(frame, width=50)
        self.label_entry.grid(row=3, column=0, sticky="ew")
        self.label_entry.insert(0, suggested_label)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, pady=(15, 0), sticky="e")
        
        ok_button = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_button.pack(side="left", padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side="left")
        
        self.caption_entry.focus_set()
        self.bind("<Return>", lambda e: self.on_ok())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.wait_window(self)

    def on_ok(self):
        """Store the values and close the dialog."""
        self.caption = self.caption_entry.get().strip()
        self.label = self.label_entry.get().strip()
        self.destroy()

def paste_image_from_clipboard():
    """
    Pastes an image from the clipboard, prompts for details, saves it to a 
    structured directory, and inserts the corresponding LaTeX code.
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
        
        # We need the character index, not a tuple, for extract_section_structure
        char_index = editor.count("1.0", cursor_index)[0]
        
        section, subsection, subsubsection = editor_logic.extract_section_structure(content, char_index)
        debug_console.log(f"Determined section structure: {section}/{subsection}/{subsubsection}", level='DEBUG')

        def sanitize(text):
            text = text.lower().replace(" ", "_")
            return re.sub(r'[^\w\-_.]', '', text)
        
        s_section, s_subsection, s_subsubsection = sanitize(section), sanitize(subsection), sanitize(subsubsection)

        fig_dir_path = os.path.join(base_dir, "figures", s_section, s_subsection, s_subsubsection)
        os.makedirs(fig_dir_path, exist_ok=True)
        debug_console.log(f"Ensured directory exists: {fig_dir_path}", level='DEBUG')

        index = 1
        while True:
            file_name = f"fig_{index}.png"
            full_file_path = os.path.join(fig_dir_path, file_name)
            if not os.path.exists(full_file_path): break
            index += 1

        # --- NEW: Prompt for caption and label ---
        suggested_label = f"fig:{s_section}_{s_subsection}_{index}"
        dialog = ImageDetailsDialog(interface.root, suggested_label)
        
        # If the user cancels the dialog, the caption will be empty. Abort the paste.
        if not dialog.caption and not dialog.label:
            debug_console.log("Image paste cancelled by user at details dialog.", level='INFO')
            return
            
        caption_text = dialog.caption or "Caption here"
        label_text = dialog.label or suggested_label
        # --- END NEW ---

        image.save(full_file_path, "PNG")
        debug_console.log(f"Image saved to: {full_file_path}", level='SUCCESS')

        latex_path = os.path.relpath(full_file_path, base_dir).replace("\\", "/")
        
        latex_code = (
            f"\n\\begin{{figure}}[h!]\n"
            f"    \\centering\n"
            f"    \\includegraphics[width=0.8\\textwidth]{{{latex_path}}}\n"
            f"    \\caption{{{caption_text}}}\n"
            f"    \\label{{{label_text}}}\n"
            f"\\end{{figure}}\n"
        )
        
        editor.insert(tk.INSERT, latex_code)
        debug_console.log("LaTeX code inserted into editor.", level='INFO')

    except Exception as e:
        debug_console.log(f"An unexpected error occurred during paste: {str(e)}", level='ERROR')
        messagebox.showerror("Error Pasting Image", f"An unexpected error occurred:\n{str(e)}")