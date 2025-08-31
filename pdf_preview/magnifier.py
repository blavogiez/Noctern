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
        self.size = 200  # Diameter of the circular magnifier
        self.zoom_factor = 2.0
        self.crop_radius = 50  # Radius of area to magnify
        
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
        
        # Platform-specific transparent color
        if platform.system() == "Windows":
            # On Windows, we'll use a different approach for transparency
            # Create a frame-like border instead
            bg_color = "#f0f0f0"  # Light gray background
        else:
            # On other platforms, try to use transparent color
            bg_color = "systemTransparent"
            try:
                self.window.attributes("-transparentcolor", "systemTransparent")
            except tk.TclError:
                # If transparent color is not supported, use light gray
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
        """Draw the circular frame and glass effect."""
        if not self.canvas:
            return
            
        # Clear previous content
        self.canvas.delete("all")
        
        # Draw outer ring (metallic look)
        self.canvas.create_oval(
            5, 5, self.size-5, self.size-5,
            outline="#a0a0a0", width=3, tags="frame"
        )
        
        # Draw inner ring (glass effect)
        self.canvas.create_oval(
            15, 15, self.size-15, self.size-15,
            outline="#d0d0ff", width=2, tags="frame"
        )
        
        # Draw handle
        handle_x = self.size - 20
        handle_y = self.size - 20
        self.canvas.create_line(
            handle_x, handle_y, 
            handle_x + 15, handle_y + 15,
            fill="#a0a0a0", width=5, tags="frame"
        )
        
        # Draw grip on handle
        self.canvas.create_oval(
            handle_x + 10, handle_y + 10,
            handle_x + 20, handle_y + 20,
            fill="#707070", outline="#505050", tags="frame"
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
            
        # Clear previous content but keep the frame
        for item in self.canvas.find_all():
            if "frame" not in self.canvas.gettags(item):
                self.canvas.delete(item)
        
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
        
        # Create a circular mask
        mask = Image.new('L', magnified.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0) + magnified.size, fill=255)
        
        # Apply the mask to make it circular
        magnified.putalpha(mask)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(magnified)
        
        # Display in magnifier canvas (centered)
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