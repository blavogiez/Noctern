import os
import tkinter as tk
from PIL import Image, ImageTk
import re
from utils import debug_console

class ImagePreview(tk.Toplevel):
    def __init__(self, parent, file_path_getter=None):
        super().__init__(parent)
        # Setting: make window frameless and tooltip-like
        self.overrideredirect(True)
        
        # Create label for image display
        self.label = tk.Label(self, background="white", borderwidth=1, relief="solid")
        self.label.pack()
        
        # Hide window initially
        self.withdraw()
        
        # Store references for path resolution
        self.parent = parent
        self.file_path_getter = file_path_getter
        
        # Initialize hover state variables
        self._hover_timer_id = None
        self._hover_path = None
        
        # Cache line checking to avoid redundant processing
        self._last_line_index = None
        self._last_line_content = None
        
        # Bind mouse leave event
        self.bind("<Leave>", self._on_mouse_leave)
        
    def attach_to_editor(self, editor):
        """Attach image preview functionality to text editor widget."""
        editor.bind("<Motion>", self._on_mouse_motion)
        
    def _on_mouse_motion(self, event):
        """Handle mouse motion to detect includegraphics commands."""
        # Get editor widget and cursor position
        editor = event.widget
        
        # Extract line index and content
        index = editor.index(f"@{event.x},{event.y}")
        line_index = index.split('.')[0]
        
        # Skip processing if on same line as before
        if line_index == self._last_line_index:
            return
            
        # Update line cache
        self._last_line_index = line_index
        self._last_line_content = editor.get(f"{line_index}.0", f"{line_index}.end")
        
        # Cancel pending timer
        if self._hover_timer_id:
            self.after_cancel(self._hover_timer_id)
            self._hover_timer_id = None
        
        # Hide preview when moving to different line
        self.hide()

        # Process includegraphics commands
        if r"\includegraphics" in self._last_line_content:
            match = re.search(r'\\includegraphics(?:\[[^]]*\])?\{(.*?)\}', self._last_line_content)
            if match:
                image_path = match.group(1)
                
                # Skip if no file path available for resolution
                if not self.file_path_getter or not self.file_path_getter():
                    return

                # Resolve relative path to absolute
                base_dir = os.path.dirname(self.file_path_getter())
                absolute_image_path = os.path.join(base_dir, image_path)
                
                if os.path.exists(absolute_image_path):
                    self._hover_path = absolute_image_path
                    # Schedule preview after 200ms delay
                    self._hover_timer_id = self.after(200, self._show_image_preview, event.x_root, event.y_root)

    def _on_mouse_leave(self, event):
        """Handle mouse leave to hide preview."""
        if self._hover_timer_id:
            self.after_cancel(self._hover_timer_id)
            self._hover_timer_id = None
        self.hide()
        # Clear line cache on exit
        self._last_line_index = None
        self._last_line_content = None

    def _show_image_preview(self, x_root, y_root):
        """Show image preview at specified position."""
        if self._hover_path:
            # Position preview near cursor
            self.show_image(self._hover_path, (x_root + 10, y_root + 10))
        self._hover_timer_id = None

    def show_image(self, image_path, position):
        """Load and display image in preview window at given position."""
        try:
            if not os.path.exists(image_path):
                self.hide()
                return

            # Load image with Pillow
            image = Image.open(image_path)
            
            # Limit preview size to 300x300
            max_size = (300, 300)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to tkinter-compatible format
            self.photo = ImageTk.PhotoImage(image)
            self.label.config(image=self.photo)
            
            # Position and show window
            self.geometry(f"+{position[0]}+{position[1]}")
            
            # Make window visible
            self.deiconify()
            debug_console.log(f"Image preview displayed at position: {position}", level='INFO')
        except Exception as e:
            # Hide on any error (invalid image file, etc.)
            self.hide()

    def hide(self):
        """Hide preview window."""
        self.withdraw()