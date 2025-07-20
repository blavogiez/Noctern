import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
from PIL import ImageGrab, Image
from editor import logic as editor_logic
from utils import debug_console

class ImageDetailsDialog(tk.Toplevel):
    """
    A dialog window for collecting image details (caption and label) from the user.

    This dialog is displayed when an image is pasted into the editor, allowing
    the user to provide a descriptive caption and a unique LaTeX label for the image.
    It is a modal window that blocks interaction with the main application until it is closed.
    """
    def __init__(self, parent, suggested_label, get_theme_setting):
        """
        Initializes the ImageDetailsDialog.

        Args:
            parent (tk.Tk or tk.Toplevel): The parent window for this dialog.
            suggested_label (str): A pre-filled suggestion for the image label.
        """
        super().__init__(parent)
        self.transient(parent)
        self.title("Image Details")
        self.geometry("400x180")
        self.grab_set()

        self.caption = ""
        self.label = ""
        self.cancelled = True # Assume cancellation until OK is pressed
        self.get_theme_setting = get_theme_setting

        self._configure_styles()
        self._create_widgets(suggested_label)
        
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.wait_window(self)

    def _configure_styles(self):
        """Configures the dialog's appearance based on the application's theme."""
        try:
            bg_color = self.get_theme_setting("root_bg", "#f0f0f0")
            self.configure(bg=bg_color)
        except Exception:
            self.configure(bg="#f0f0f0")

    def _create_widgets(self, suggested_label):
        """Creates and lays out the widgets for the dialog."""
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
        
        ok_button = ttk.Button(button_frame, text="OK", command=self._on_ok)
        ok_button.pack(side="left", padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self._on_cancel)
        cancel_button.pack(side="left")
        
        self.caption_entry.focus_set()
        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _on_ok(self):
        """Handles the OK button click, storing values and closing the dialog."""
        self.caption = self.caption_entry.get().strip()
        self.label = self.label_entry.get().strip()
        if not self.label:
            messagebox.showwarning("Missing Label", "The image label cannot be empty.", parent=self)
            return
        self.cancelled = False
        self.destroy()

    def _on_cancel(self):
        """Handles the Cancel button click or window close, closing the dialog."""
        self.cancelled = True
        self.destroy()

def paste_image_from_clipboard(root, get_current_tab, get_theme_setting):
    """
    Handles pasting an image from the clipboard into the editor.

    This function orchestrates the process of retrieving an image from the
    clipboard, prompting the user for details, saving the image to a structured
    directory, and inserting the corresponding LaTeX code into the editor.
    """
    debug_console.log("Attempting to paste image from clipboard.", level='ACTION')

    
    current_tab = get_current_tab()
    if not current_tab:
        debug_console.log("Image paste aborted: No active editor tab.", level='WARNING')
        messagebox.showwarning("No Active Tab", "Please open a document before pasting an image.")
        return

    editor = current_tab.editor

    try:
        image = ImageGrab.grabclipboard()
        if not isinstance(image, Image.Image):
            message = "No image found in the clipboard." if image is None else "The clipboard content is not a recognizable image."
            debug_console.log(f"Image paste aborted: {message}", level='INFO')
            messagebox.showinfo("Clipboard Information", message)
            return

        base_directory = os.path.dirname(current_tab.file_path) if current_tab.file_path else os.getcwd()
        document_content = editor.get("1.0", tk.END)
        char_index = editor.count("1.0", editor.index(tk.INSERT))[0]
        
        section, subsection, subsubsection = editor_logic.extract_section_structure(document_content, char_index)
        debug_console.log(f"Document structure for image: Section='{section}', Subsection='{subsection}', Subsubsection='{subsubsection}'.", level='DEBUG')

        def sanitize_for_path(text):
            text = text.lower().replace(" ", "_")
            return re.sub(r'[^\w\-_.]', '', text)
        
        path_components = ["figures", sanitize_for_path(section), sanitize_for_path(subsection), sanitize_for_path(subsubsection)]
        image_directory_path = os.path.join(base_directory, *path_components)
        os.makedirs(image_directory_path, exist_ok=True)
        debug_console.log(f"Image directory ensured at: {image_directory_path}", level='DEBUG')

        image_index = 1
        while True:
            file_name = f"fig_{image_index}.png"
            full_file_path = os.path.join(image_directory_path, file_name)
            if not os.path.exists(full_file_path):
                break
            image_index += 1

        suggested_label = f"fig:{sanitize_for_path(section)}_{sanitize_for_path(subsection)}_{image_index}"
        details_dialog = ImageDetailsDialog(root, suggested_label, get_theme_setting)
        
        if details_dialog.cancelled:
            debug_console.log("Image paste cancelled by user via details dialog.", level='INFO')
            return
            
        caption_text = details_dialog.caption or "Caption here"
        label_text = details_dialog.label # Already validated in dialog

        image.save(full_file_path, "PNG")
        debug_console.log(f"Image saved to: {full_file_path}", level='SUCCESS')

        latex_image_path = os.path.relpath(full_file_path, base_directory).replace("\\", "/")
        
        latex_code = (
            f"\n\\begin{{figure}}[h!]\n"
            f"    \\centering\n"
            f"    \\includegraphics[width=0.8\\textwidth]{{{latex_image_path}}}\n"
            f"    \\caption{{{caption_text}}}\n"
            f"    \\label{{{label_text}}}\n"
            f"\\end{{figure}}\n"
        )
        
        editor.insert(tk.INSERT, latex_code)
        debug_console.log("LaTeX figure code inserted into editor.", level='INFO')

    except Exception as e:
        error_message = f"An unexpected error occurred during the image paste operation: {str(e)}"
        debug_console.log(error_message, level='ERROR')
        messagebox.showerror("Error Pasting Image", error_message)
