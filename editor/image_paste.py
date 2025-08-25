import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
from PIL import ImageGrab, Image
from editor import structure as editor_structure
from utils import debug_console
from app.panels import show_image_details_panel


def paste_image_from_clipboard(root, get_current_tab, get_theme_setting):
    """Handle pasting image from clipboard with structured directory and LaTeX generation."""
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
        
        section, subsection, subsubsection = editor_structure.extract_section_structure(document_content, char_index)
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
        
        # Store image data and paths for later use in callback
        image_data = {
            'image': image,
            'full_file_path': full_file_path,
            'latex_image_path': None,  # Will be calculated later
            'base_directory': base_directory,
            'editor': editor
        }
        
        def on_image_details_ok(caption, label):
            """Handle OK from image details panel."""
            try:
                # Save the image
                image_data['image'].save(image_data['full_file_path'], "PNG")
                debug_console.log(f"Image saved to: {image_data['full_file_path']}", level='SUCCESS')

                # Calculate LaTeX path
                latex_image_path = os.path.relpath(image_data['full_file_path'], image_data['base_directory']).replace("\\", "/")
                
                # Use provided caption or default
                caption_text = caption or "Caption here"
                
                # Generate LaTeX code
                latex_code = (
                    f"\n\\begin{{figure}}[h!]\n"
                    f"    \\centering\n"
                    f"    \\includegraphics[width=0.8\\textwidth]{{{latex_image_path}}}\n"
                    f"    \\caption{{{caption_text}}}\n"
                    f"    \\label{{{label}}}\n"
                    f"\\end{{figure}}\n"
                )
                
                # Insert LaTeX code
                image_data['editor'].insert(tk.INSERT, latex_code)
                debug_console.log("LaTeX figure code inserted into editor.", level='INFO')
                
            except Exception as e:
                error_message = f"An unexpected error occurred during the image paste operation: {str(e)}"
                debug_console.log(error_message, level='ERROR')
                messagebox.showerror("Error Pasting Image", error_message)
        
        def on_image_details_cancel():
            """Handle cancel from image details panel."""
            debug_console.log("Image paste cancelled by user via details panel.", level='INFO')
        
        # Show the integrated image details panel
        show_image_details_panel(suggested_label, on_image_details_ok, on_image_details_cancel)

    except Exception as e:
        error_message = f"An unexpected error occurred during the image paste operation: {str(e)}"
        debug_console.log(error_message, level='ERROR')
        messagebox.showerror("Error Pasting Image", error_message)
