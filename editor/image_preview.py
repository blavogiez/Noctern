import os
import tkinter as tk
from PIL import Image, ImageTk

class ImagePreview(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        # Make the window frameless and like a tooltip
        self.overrideredirect(True)
        
        # The label that will hold the image
        self.label = tk.Label(self, background="white", borderwidth=1, relief="solid")
        self.label.pack()
        
        # Hide the window initially
        self.withdraw()

    def show_image(self, image_path, position):
        """
        Load an image, display it in the preview window, and show it at the given position.
        """
        try:
            if not os.path.exists(image_path):
                self.hide()
                return

            # Open the image with Pillow
            image = Image.open(image_path)
            
            # Define max size for the preview
            max_size = (300, 300)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to a PhotoImage that tkinter can use
            self.photo = ImageTk.PhotoImage(image)
            self.label.config(image=self.photo)
            
            # Update window geometry and position
            self.geometry(f"+{position[0]}+{position[1]}")
            
            # Deiconify makes the window visible
            self.deiconify()
        except Exception:
            # In case of any error (e.g., invalid image file), hide the window
            self.hide()

    def hide(self):
        """
        Hide the preview window.
        """
        self.withdraw()