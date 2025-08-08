import os
import tkinter as tk
from PIL import Image, ImageTk
import re
from utils import debug_console

class ImagePreview(tk.Toplevel):
    def __init__(self, parent, file_path_getter=None):
        super().__init__(parent)
        # Make the window frameless and like a tooltip
        self.overrideredirect(True)
        
        # The label that will hold the image
        self.label = tk.Label(self, background="white", borderwidth=1, relief="solid")
        self.label.pack()
        
        # Hide the window initially
        self.withdraw()
        
        # Store reference to parent and file path getter
        self.parent = parent
        self.file_path_getter = file_path_getter
        
        # Timer for hover delay
        self._hover_timer_id = None
        self._hover_path = None
        
        # Bind events
        self.bind("<Leave>", self._on_mouse_leave)
        
    def attach_to_editor(self, editor):
        """Attach the image preview functionality to a text editor widget."""
        editor.bind("<Motion>", self._on_mouse_motion)
        
    def _on_mouse_motion(self, event):
        """Handle mouse motion events to detect \\includegraphics commands."""
        # Cancel any existing timer
        if self._hover_timer_id:
            self.after_cancel(self._hover_timer_id)
            self._hover_timer_id = None
        
        self.hide()

        # Get the editor widget from the event
        editor = event.widget
        
        index = editor.index(f"@{event.x},{event.y}")
        line_content = editor.get(f"{index.split('.')[0]}.0", f"{index.split('.')[0]}.end")

        if r"\includegraphics" in line_content:
            debug_console.log(f"Found \\includegraphics in line: {line_content}", level='DEBUG')
            match = re.search(r'\\includegraphics(?:\[[^]]*\])?\{(.*?)\}', line_content)
            if match:
                image_path = match.group(1)
                debug_console.log(f"Extracted image path: {image_path}", level='DEBUG')
                
                # If the file_path is not set, we can't resolve relative paths
                if not self.file_path_getter or not self.file_path_getter():
                    debug_console.log("No file path available to resolve relative paths", level='DEBUG')
                    return

                # Resolve the absolute path
                base_dir = os.path.dirname(self.file_path_getter())
                absolute_image_path = os.path.join(base_dir, image_path)
                debug_console.log(f"Resolved absolute path: {absolute_image_path}", level='DEBUG')
                
                if os.path.exists(absolute_image_path):
                    debug_console.log(f"Image file exists, scheduling preview", level='DEBUG')
                    self._hover_path = absolute_image_path
                    # Schedule the preview to appear after 0.2 seconds
                    self._hover_timer_id = self.after(200, self._show_image_preview, event.x_root, event.y_root)
                else:
                    debug_console.log(f"Image file does not exist: {absolute_image_path}", level='DEBUG')

    def _on_mouse_leave(self, event):
        """Handle mouse leave events to hide the preview."""
        debug_console.log("Mouse left editor area, hiding preview", level='DEBUG')
        if self._hover_timer_id:
            self.after_cancel(self._hover_timer_id)
            self._hover_timer_id = None
        self.hide()

    def _show_image_preview(self, x_root, y_root):
        """Show the image preview at the specified position."""
        debug_console.log(f"Showing image preview for: {self._hover_path}", level='DEBUG')
        if self._hover_path:
            # Position the preview near the cursor
            self.show_image(self._hover_path, (x_root + 10, y_root + 10))
        self._hover_timer_id = None
        self._hover_path = None

    def show_image(self, image_path, position):
        """
        Load an image, display it in the preview window, and show it at the given position.
        """
        try:
            if not os.path.exists(image_path):
                debug_console.log(f"Image file does not exist: {image_path}", level='DEBUG')
                self.hide()
                return

            debug_console.log(f"Loading image: {image_path}", level='DEBUG')
            # Open the image with Pillow
            image = Image.open(image_path)
            
            # Define max size for the preview
            max_size = (700, 700)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to a PhotoImage that tkinter can use
            self.photo = ImageTk.PhotoImage(image)
            self.label.config(image=self.photo)
            
            # Update window geometry and position
            self.geometry(f"+{position[0]}+{position[1]}")
            
            # Deiconify makes the window visible
            self.deiconify()
            debug_console.log(f"Image preview displayed at position: {position}", level='DEBUG')
        except Exception as e:
            debug_console.log(f"Error showing image preview: {e}", level='ERROR')
            # In case of any error (e.g., invalid image file), hide the window
            self.hide()

    def hide(self):
        """
        Hide the preview window.
        """
        debug_console.log("Hiding image preview", level='DEBUG')
        self.withdraw()