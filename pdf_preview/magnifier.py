"""
PDF Preview Magnifier Component
A circular magnifier tool for PDF preview with elegant design.
"""

import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk, ImageDraw
import math
import platform


class PDFPreviewMagnifier:
    """
    A circular magnifier tool for PDF preview.
    """
    
    def __init__(self, parent, viewer):
        """
        Initialize the circular magnifier.
        
        Args:
            parent (tk.Widget): Parent widget
            viewer (PDFPreviewViewer): Reference to the PDF viewer
        """
        self.parent = parent
        self.viewer = viewer
        self.window = None
        self.canvas = None
        self.size = 280  # Diameter of the circular magnifier
        self.zoom_factor = 1.6
        self.crop_radius = 60  # Radius of area to magnify
        
        # Create the magnifier window
        self._create_window()
        
    def _create_window(self):
        """Create the circular magnifier window."""
        if self.window:
            return
            
        # Create magnifier window
        self.window = tk.Toplevel(self.parent)
        self.window.title("Magnifier")
        self.window.geometry(f"{self.size}x{self.size}")
        self.window.resizable(False, False)
        self.window.overrideredirect(True)  # Remove window decorations for a cleaner look
        
        # Make it stay on top
        self.window.attributes("-topmost", True)
        
        # Use a unique color for transparency
        transparent_color = "#FF00FF"  # Magenta - will be made transparent
        bg_color = transparent_color
        
        # Set transparent color for all platforms
        try:
            self.window.attributes("-transparentcolor", transparent_color)
        except tk.TclError:
            # Fallback if transparency not supported
            bg_color = "#f0f0f0"
        
        # Create canvas with no border
        self.canvas = Canvas(
            self.window,
            width=self.size,
            height=self.size,
            highlightthickness=0,
            bg=bg_color
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Draw the circular magnifier
        self._draw_magnifier_frame()
        
        # Bind events
        self.canvas.bind("<Button-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag)
        
        # Position near the main window initially
        x = self.parent.winfo_rootx() + 50
        y = self.parent.winfo_rooty() + 50
        self.window.geometry(f"+{x}+{y}")
        
    def _draw_magnifier_frame(self):
        """Draw the circular frame and glass effect with transparency mask."""
        if not self.canvas:
            return
            
        # Clear previous content
        self.canvas.delete("all")
        
        # Get transparent color
        transparent_color = self.canvas['bg']
        
        # Create a full transparent background first
        self.canvas.create_rectangle(
            0, 0, self.size, self.size,
            fill=transparent_color, outline="", tags="background"
        )
        
        # Draw the visible circular area (this will show the magnified content)
        # We create a circle that will be filled with the magnified image later
        self.canvas.create_oval(
            20, 20, self.size-20, self.size-20,
            outline="#a0a0a0", width=3, fill="white", tags="lens"
        )
        
        # Draw inner ring for glass effect
        self.canvas.create_oval(
            25, 25, self.size-25, self.size-25,
            outline="#d0d0ff", width=1, fill="", tags="frame"
        )
        
        # Draw handle (positioned outside the main circle but still visible)
        handle_x = self.size - 25
        handle_y = self.size - 25
        self.canvas.create_line(
            handle_x - 5, handle_y - 5, 
            handle_x + 10, handle_y + 10,
            fill="#a0a0a0", width=4, tags="frame"
        )
        
        # Draw grip on handle
        self.canvas.create_oval(
            handle_x + 5, handle_y + 5,
            handle_x + 15, handle_y + 15,
            fill="#707070", outline="#505050", width=2, tags="frame"
        )
        
    def _start_drag(self, event):
        """Start dragging the magnifier."""
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
    def _drag(self, event):
        """Drag the magnifier window."""
        # Calculate new position
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        
        x = self.window.winfo_x() + dx
        y = self.window.winfo_y() + dy
        
        # Move window
        self.window.geometry(f"+{x}+{y}")
        
    def update_position(self, x, y):
        """
        Update the magnifier position.
        
        Args:
            x (int): X coordinate (screen coordinates)
            y (int): Y coordinate (screen coordinates)
        """
        if not self.window:
            return
            
        # Position the magnifier near the cursor but not directly on it
        # Avoid hiding content being magnified
        offset = self.size // 2 + 10
        self.window.geometry(f"+{x + offset}+{y + offset}")
        
    def update_view(self, image, center_x, center_y):
        """
        Update the magnified view.
        
        Args:
            image (PIL.Image): The full page image
            center_x (int): X coordinate of center point to magnify (in image coordinates)
            center_y (int): Y coordinate of center point to magnify (in image coordinates)
        """
        if not self.canvas or not image:
            return
            
        # Clear previous magnified content but keep frame elements
        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if "magnified" in tags or "lens" in tags or "background" in tags:
                self.canvas.delete(item)
        
        # Redraw transparent background and lens area
        transparent_color = self.canvas['bg']
        self.canvas.create_rectangle(
            0, 0, self.size, self.size,
            fill=transparent_color, outline="", tags="background"
        )
        
        # Calculate crop area
        img_width, img_height = image.size
        
        # Ensure we don't go out of bounds
        left = max(0, center_x - self.crop_radius)
        top = max(0, center_y - self.crop_radius)
        right = min(img_width, center_x + self.crop_radius)
        bottom = min(img_height, center_y + self.crop_radius)
        
        # Crop the region
        cropped = image.crop((left, top, right, bottom))
        
        # Resize for magnification
        magnified = cropped.resize(
            (int(cropped.width * self.zoom_factor), int(cropped.height * self.zoom_factor)),
            Image.Resampling.LANCZOS
        )
        
        # Calculate the lens circle dimensions
        lens_size = self.size - 40  # 20px margin on each side
        
        # Resize the magnified image to fit the lens circle
        magnified = magnified.resize((lens_size, lens_size), Image.Resampling.LANCZOS)
        
        # Create a circular mask for the lens area
        mask = Image.new('L', (lens_size, lens_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, lens_size, lens_size), fill=255)
        
        # Apply the mask to make it circular
        magnified.putalpha(mask)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(magnified)
        
        # Display in magnifier canvas (centered in the lens area)
        self.canvas.create_image(
            self.size // 2,
            self.size // 2,
            image=photo,
            tags="magnified"
        )
        
        # Keep a reference to prevent garbage collection
        self.canvas.image = photo
        
    def show(self):
        """Show the magnifier."""
        if self.window:
            self.window.deiconify()
            
    def hide(self):
        """Hide the magnifier."""
        if self.window:
            self.window.withdraw()
            
    def destroy(self):
        """Destroy the magnifier window."""
        if self.window:
            self.window.destroy()
            self.window = None
            self.canvas = None