import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
from PIL import ImageGrab, Image
import interface
import editor_logic
import debug_console

class ImageDetailsDialog(tk.Toplevel):
    """
    A dialog window for collecting image details (caption and label) from the user.

    This dialog is displayed when an image is pasted into the editor, allowing
    the user to provide a descriptive caption and a unique LaTeX label for the image.
    """
    def __init__(self, parent, suggested_label):
        """
        Initializes the ImageDetailsDialog.

        Args:
            parent (tk.Tk or tk.Toplevel): The parent window of this dialog.
            suggested_label (str): A pre-filled suggestion for the image label,
                                   typically derived from the document structure.
        """
        super().__init__(parent)
        self.transient(parent)  # Set the dialog to be transient to its parent.
        self.title("Image Details")
        self.geometry("400x180")
        self.grab_set()  # Grab all input events until the dialog is closed.

        self.caption = ""  # Stores the user-entered caption.
        self.label = ""    # Stores the user-entered label.

        # Attempt to apply the parent's theme settings for visual consistency.
        try:
            bg_color = interface.get_theme_setting("root_bg", "#f0f0f0")
            self.configure(bg=bg_color)
        except Exception:
            # Fallback to a default background color if theme settings are unavailable.
            self.configure(bg="#f0f0f0")

        # Create a frame for better layout management within the dialog.
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Widgets for image caption input.
        ttk.Label(frame, text="Image Caption:").grid(row=0, column=0, sticky="w", pady=2)
        self.caption_entry = ttk.Entry(frame, width=50)
        self.caption_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Widgets for image label input.
        ttk.Label(frame, text="Image Label:").grid(row=2, column=0, sticky="w", pady=2)
        self.label_entry = ttk.Entry(frame, width=50)
        self.label_entry.grid(row=3, column=0, sticky="ew")
        self.label_entry.insert(0, suggested_label)  # Pre-fill with the suggested label.

        # Frame for action buttons (OK, Cancel).
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, pady=(15, 0), sticky="e")
        
ok_button = ttk.Button(button_frame, text="OK", command=self.on_ok)
ok_button.pack(side="left", padx=5)
cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy)
cancel_button.pack(side="left")
        
self.caption_entry.focus_set()  # Set initial focus to the caption entry field.
self.bind("<Return>", lambda e: self.on_ok())  # Bind Enter key to the OK action.
self.protocol("WM_DELETE_WINDOW", self.destroy)  # Handle window close button.

self.wait_window(self)  # Pause execution until the dialog is closed.

    def on_ok(self):
        """
        Retrieves the entered caption and label, then closes the dialog.

        This method is called when the 'OK' button is pressed or the Enter key
        is activated. It strips leading/trailing whitespace from the inputs.
        """
        self.caption = self.caption_entry.get().strip()
        self.label = self.label_entry.get().strip()
        self.destroy()  # Close the dialog window.

def paste_image_from_clipboard():
    """
    Handles the pasting of an image from the system clipboard into the editor.

    This function performs the following steps:
    1. Checks for an active editor tab.
    2. Retrieves the image from the clipboard.
    3. Prompts the user for image details (caption and label) via a dialog.
    4. Determines the appropriate directory structure based on the current
       document's sectioning (e.g., \section, \subsection).
    5. Saves the image as a PNG file within the determined directory.
    6. Generates and inserts the corresponding LaTeX \figure environment code
       into the editor at the current cursor position.
    7. Provides user feedback and error handling through debug console logs
       and message boxes.
    """
    debug_console.log("Attempting to paste image from clipboard.", level='ACTION')

    current_tab = interface.get_current_tab()
    if not current_tab:
        debug_console.log("Image paste aborted: No active editor tab found.", level='WARNING')
        messagebox.showwarning("No Active Tab", "Please open a document tab before pasting an image.")
        return
    editor = current_tab.editor

    try:
        image = ImageGrab.grabclipboard()
        # Check if the clipboard content is an image.
        if not isinstance(image, Image.Image):
             if image is None:
                 debug_console.log("Clipboard is empty or does not contain data.", level='INFO')
                 messagebox.showwarning("Clipboard Empty", "No image found in the clipboard.")
             else:
                 debug_console.log("Clipboard content is not a recognized image format.", level='INFO')
                 messagebox.showinfo("Information", "The clipboard does not contain an image.")
             return

        # Determine the base directory for saving the image.
        base_directory = os.path.dirname(current_tab.file_path) if current_tab.file_path else os.getcwd()
        document_content = editor.get("1.0", tk.END)
        cursor_position = editor.index(tk.INSERT)
        
        # Convert the Tkinter index to a character index for section structure extraction.
        char_index = editor.count("1.0", cursor_position)[0]
        
        # Extract the current section, subsection, and subsubsection from the document.
        section, subsection, subsubsection = editor_logic.extract_section_structure(document_content, char_index)
        debug_console.log(f"Identified document structure for image placement: Section='{section}', Subsection='{subsection}', Subsubsection='{subsubsection}'.", level='DEBUG')

        def sanitize_text_for_path(text):
            """
            Sanitizes a given string to be suitable for use in file paths.
            Converts to lowercase, replaces spaces with underscores, and removes
            any characters that are not alphanumeric, underscores, hyphens, or periods.
            """
            text = text.lower().replace(" ", "_")
            return re.sub(r'[^\w\-_.]', '', text)
        
        # Sanitize the extracted section names for directory creation.
        sanitized_section = sanitize_text_for_path(section)
        sanitized_subsection = sanitize_text_for_path(subsection)
        sanitized_subsubsection = sanitize_text_for_path(subsubsection)

        # Construct the full path for the image directory.
        image_directory_path = os.path.join(base_directory, "figures", sanitized_section, sanitized_subsection, sanitized_subsubsection)
        os.makedirs(image_directory_path, exist_ok=True) # Create the directory if it doesn't exist.
        debug_console.log(f"Ensured image directory exists at: {image_directory_path}", level='DEBUG')

        # Determine a unique filename for the new image.
        image_index = 1
        while True:
            file_name = f"fig_{image_index}.png"
            full_file_path = os.path.join(image_directory_path, file_name)
            if not os.path.exists(full_file_path): # Check if the file already exists.
                break
            image_index += 1

        # Prompt the user for image caption and label.
        suggested_label = f"fig:{sanitized_section}_{sanitized_subsection}_{image_index}"
        details_dialog = ImageDetailsDialog(interface.root, suggested_label)
        
        # If the user cancels the dialog, abort the image paste operation.
        if not details_dialog.caption and not details_dialog.label:
            debug_console.log("Image paste cancelled by user via details dialog.", level='INFO')
            return
            
        # Use user-provided caption/label or fall back to defaults.
        caption_text = details_dialog.caption or "Caption here" # Default caption if none provided.
        label_text = details_dialog.label or suggested_label   # Default label if none provided.

        # Save the image to the determined file path.
        image.save(full_file_path, "PNG")
        debug_console.log(f"Image successfully saved to: {full_file_path}", level='SUCCESS')

        # Calculate the relative path for LaTeX inclusion.
        latex_image_path = os.path.relpath(full_file_path, base_directory).replace("\\", "/")
        
        # Construct the LaTeX \figure environment code.
        latex_code = (
            f"\n\\begin{{figure}}[h!]\n"
            f"    \\centering\n"
            f"    \\includegraphics[width=0.8\\textwidth]{{{latex_image_path}}}\n"
            f"    \\caption{{{caption_text}}}\n"
            f"    \\label{{{label_text}}}\n"
            f"\\end{{figure}}\n"
        )
        
        # Insert the generated LaTeX code into the editor.
        editor.insert(tk.INSERT, latex_code)
        debug_console.log("LaTeX code for image successfully inserted into editor.", level='INFO')

    except Exception as e:
        debug_console.log(f"An unexpected error occurred during image paste operation: {str(e)}", level='ERROR')
        messagebox.showerror("Error Pasting Image", f"An unexpected error occurred:\n{str(e)}")