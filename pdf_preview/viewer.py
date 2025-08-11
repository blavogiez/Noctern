"""
PDF Preview Viewer Component
Handles the display and navigation of PDF documents with continuous scrolling.
"""

import tkinter as tk
import ttkbootstrap as ttk
from tkinter import Canvas, Scrollbar
from PIL import Image, ImageTk
import os
import threading
import time
from utils import debug_console

# Import the new navigator component
from pdf_preview.navigator import PDFTextNavigator
from pdf_preview.sync import PDFSyncManager
# Import the new circular magnifier component
from pdf_preview.magnifier import CircularMagnifier


class PDFPreviewViewer:
    """
    A PDF preview viewer component that displays PDF documents with continuous scrolling.
    """
    
    def __init__(self, parent, pdf_path=None):
        """
        Initialize the PDF preview viewer.
        
        Args:
            parent (tk.Widget): Parent widget to place the viewer in
            pdf_path (str, optional): Path to the PDF file to display
        """
        self.parent = parent
        self.pdf_path = pdf_path
        self.zoom_level = 0.7  # Start with a smaller zoom level for better initial view
        
        # Caching and performance
        self.page_images = {}  # Cache for page images
        self.page_photos = {}  # Cache for PhotoImage objects
        self.page_layouts = {}  # Layout information for each page
        self.total_height = 0
        self.render_thread = None
        self.RENDER_DPI = 150
        
        # Status tracking
        self.last_compilation_time = None
        self.compilation_status = "Not yet compiled"
        self.status_update_job = None
        
        # Text navigator component
        self.text_navigator = PDFTextNavigator(self)
        
        # Sync manager for text search
        self.sync_manager = PDFSyncManager()
        
        # Magnifier properties
        self.magnifier_active = False
        self.magnifier = None
        
        self._create_widgets()
        if pdf_path and os.path.exists(pdf_path):
            self.load_pdf(pdf_path)
    
    def _create_widgets(self):
        """Create and configure the viewer widgets."""
        # Main frame
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)
        
        # Status label (replaces "PDF Preview" title)
        self.status_label = ttk.Label(self.frame, text="Not yet compiled", anchor="w")
        self.status_label.pack(fill="x", padx=5, pady=(5, 0))
        
        # Toolbar (with previous/next buttons)
        self._create_toolbar()
        
        # Canvas for PDF display with scrollbars
        canvas_frame = ttk.Frame(self.frame)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create canvas with scrollbars
        self.canvas = Canvas(canvas_frame, bg="lightgray")
        v_scrollbar = Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        h_scrollbar = Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind events for zooming and scrolling
        self.canvas.bind("<Control-MouseWheel>", self._on_zoom)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel_up)
        self.canvas.bind("<Button-5>", self._on_mouse_wheel_down)
    
    def _create_toolbar(self):
        """Create the toolbar with navigation controls."""
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # Zoom controls
        ttk.Label(toolbar, text="Zoom:").pack(side="left", padx=(0, 5))
        
        self.zoom_out_button = ttk.Button(toolbar, text="−", width=3, command=self.zoom_out, state="disabled")
        self.zoom_out_button.pack(side="left", padx=(0, 2))
        
        self.zoom_label = ttk.Label(toolbar, text="100%")
        self.zoom_label.pack(side="left", padx=5)
        
        self.zoom_in_button = ttk.Button(toolbar, text="+", width=3, command=self.zoom_in, state="disabled")
        self.zoom_in_button.pack(side="left", padx=(2, 10))
        
        # Magnifier button
        self.magnifier_button = ttk.Button(toolbar, text="🔍 Magnifier", command=self.toggle_magnifier)
        self.magnifier_button.pack(side="left", padx=(0, 10))
        
        # Refresh button
        self.refresh_button = ttk.Button(toolbar, text="Refresh", command=self.refresh)
        self.refresh_button.pack(side="right")
        
        # Magnifier state
        self.magnifier_active = False
        self.magnifier = None
    
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        
    def _on_mouse_wheel_up(self, event):
        """Handle mouse wheel up scrolling (Linux)."""
        self.canvas.yview_scroll(-1, "units")
        
    def _on_mouse_wheel_down(self, event):
        """Handle mouse wheel down scrolling (Linux)."""
        self.canvas.yview_scroll(1, "units")
    
    def _on_zoom(self, event):
        """Handle zoom with mouse wheel."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def _create_placeholder(self):
        """Create a placeholder display when no PDF is loaded."""
        self.canvas.delete("all")
        self._clear_caches()
        self.zoom_level = 1.0
        self.zoom_label.configure(text="100%")
        self._disable_toolbar()
        
        width, height = 600, 800
        self.canvas.configure(scrollregion=(0, 0, width, height))
        
        # Background
        self.canvas.create_rectangle(0, 0, width, height, fill="white", outline="gray")
        
        # Placeholder text
        self.canvas.create_text(
            width // 2, height // 2,
            text="No PDF document loaded",
            font=("Arial", 16),
            fill="lightgray"
        )
        
        self._update_status_label()
    
    def _clear_caches(self):
        """Clear all page caches."""
        self.page_images.clear()
        self.page_photos.clear()
        self.page_layouts.clear()
    
    def load_pdf(self, pdf_path):
        """
        Load a PDF file for preview.
        
        Args:
            pdf_path (str): Path to the PDF file
        """
        if not os.path.exists(pdf_path):
            self._create_placeholder()
            return
            
        self.pdf_path = pdf_path
        self._clear_caches()
        
        # Clear any text highlights
        if hasattr(self, 'text_navigator'):
            self.text_navigator.clear_highlights()
        
        # Cancel any existing render thread
        if self.render_thread and self.render_thread.is_alive():
            return
            
        # Start rendering in a separate thread
        self.render_thread = threading.Thread(target=self._render_all_pages, daemon=True)
        self.render_thread.start()
    
    def _render_all_pages(self):
        """Render all pages of the PDF in a separate thread."""
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(self.pdf_path, dpi=self.RENDER_DPI)
            
            # Store images in cache
            for i, img in enumerate(images):
                self.page_images[i + 1] = img
                
            # Update UI in main thread
            self.parent.after(0, self._display_pages, len(images))
        except Exception as e:
            debug_console.log(f"Error rendering PDF: {e}", level='ERROR')
            self.parent.after(0, self._create_placeholder)
    
    def _display_pages(self, num_pages):
        """Display all rendered pages on the canvas."""
        self.canvas.delete("all")
        self.page_layouts.clear()
        self.page_photos.clear()
        
        y_offset = 10
        max_width = 0
        
        # Display each page
        for page_num in range(1, num_pages + 1):
            if page_num not in self.page_images:
                continue
                
            img = self.page_images[page_num]
            w, h = img.size
            
            # Calculate display dimensions
            disp_w = int(w * self.zoom_level)
            disp_h = int(h * self.zoom_level)
            
            if disp_w == 0 or disp_h == 0:
                continue
                
            # Resize image for display
            display_img = img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(display_img)
            
            # Store photo to prevent garbage collection
            self.page_photos[page_num] = photo
            
            # Draw image on canvas
            self.canvas.create_image(10, y_offset, anchor="nw", image=photo)
            
            # Store layout information
            self.page_layouts[page_num] = {
                'y_offset': y_offset,
                'height': disp_h,
                'width': disp_w
            }
            
            # Update offset and width
            y_offset += disp_h + 10
            if disp_w > max_width:
                max_width = disp_w
                
        # Set scroll region
        self.total_height = y_offset
        self.canvas.configure(scrollregion=(0, 0, max_width + 20, self.total_height))
        
        # Enable toolbar
        self._enable_toolbar()
        
        # Update status
        self._update_status_label()
    
    def _enable_toolbar(self):
        """Enable toolbar buttons."""
        for btn in [self.zoom_in_button, self.zoom_out_button]:
            btn.configure(state="normal")
    
    def _disable_toolbar(self):
        """Disable toolbar buttons."""
        for btn in [self.zoom_in_button, self.zoom_out_button]:
            btn.configure(state="disabled")
    
    def zoom_in(self):
        """Zoom in on the PDF."""
        if self.zoom_level < 3.0:
            self.zoom_level *= 1.2
            self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
            self._display_pages(len(self.page_images))
    
    def zoom_out(self):
        """Zoom out on the PDF."""
        if self.zoom_level > 0.3:
            self.zoom_level /= 1.2
            self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
            self._display_pages(len(self.page_images))
    
    def previous_page(self):
        """Scroll to the previous page."""
        if not self.page_layouts:
            return
            
        # Get current view position
        current_y = self.canvas.yview()[0] * self.total_height
        
        # Find current page
        current_page = 1
        for page_num, layout in self.page_layouts.items():
            if layout['y_offset'] <= current_y < layout['y_offset'] + layout['height']:
                current_page = page_num
                break
                
        # Scroll to previous page
        if current_page > 1:
            prev_layout = self.page_layouts[current_page - 1]
            self.canvas.yview_moveto(prev_layout['y_offset'] / self.total_height)
    
    def next_page(self):
        """Scroll to the next page."""
        if not self.page_layouts:
            return
            
        # Get current view position
        current_y = self.canvas.yview()[0] * self.total_height
        
        # Find current page
        current_page = 1
        for page_num, layout in self.page_layouts.items():
            if layout['y_offset'] <= current_y < layout['y_offset'] + layout['height']:
                current_page = page_num
                
        # Scroll to next page
        if current_page < len(self.page_layouts):
            next_layout = self.page_layouts[current_page + 1]
            self.canvas.yview_moveto(next_layout['y_offset'] / self.total_height)
    
    def refresh(self):
        """Refresh the PDF display."""
        if self.pdf_path:
            self.load_pdf(self.pdf_path)
    
    def _update_status_label(self):
        """Update the status label with compilation information."""
        status_text = self.compilation_status
        time_ago = ""
        
        if self.last_compilation_time:
            seconds = int(time.time() - self.last_compilation_time)
            if seconds < 60:
                time_ago = "Last compiled less than a minute ago"
            else:
                minutes = seconds // 60
                if minutes == 1:
                    time_ago = "Last compiled about a minute ago"
                else:
                    time_ago = f"Last compiled {minutes} minutes ago"
        
        full_text = f"{time_ago}\n{status_text}" if time_ago else status_text
        self.status_label.config(text=full_text)
    
    def set_compilation_status(self, status, last_compilation_time=None):
        """
        Set the compilation status and update the display.
        
        Args:
            status (str): Compilation status ("Compilable", "Compiling...", "Not compilable")
            last_compilation_time (float, optional): Timestamp of last compilation
        """
        self.compilation_status = status
        if last_compilation_time:
            self.last_compilation_time = last_compilation_time
        self._update_status_label()
    
    def get_widget(self):
        """
        Get the main widget for this viewer.
        
        Returns:
            ttk.Frame: The main frame widget
        """
        return self.frame
        
    def go_to_text(self, text, context_before="", context_after=""):
        """
        Navigate to the specified text in the PDF using the text navigator component.
        
        Args:
            text (str): Text to search for in the PDF
            context_before (str): Text before the target text
            context_after (str): Text after the target text
        """
        self.text_navigator.go_to_text(text, context_before, context_after)
        
    def toggle_magnifier(self):
        """Toggle the magnifier tool."""
        self.magnifier_active = not self.magnifier_active
        if self.magnifier_active:
            self.magnifier_button.configure(style="primary.TButton")  # Highlight when active
            self._create_magnifier()
        else:
            self.magnifier_button.configure(style="secondary.TButton")  # Normal when inactive
            self._destroy_magnifier()

    def _create_magnifier(self):
        """Create the magnifier window."""
        if self.magnifier:
            return
            
        # Create new circular magnifier
        self.magnifier = CircularMagnifier(self.parent, self)
        
        # Bind mouse motion to update magnifier
        self.canvas.bind("<Motion>", self._update_magnifier)
        self.canvas.bind("<Leave>", self._hide_magnifier)

    def _destroy_magnifier(self):
        """Destroy the magnifier window."""
        if self.magnifier:
            self.magnifier.destroy()
            self.magnifier = None
            
        # Unbind mouse events
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<Leave>")

    def _update_magnifier(self, event):
        """Update the magnifier view based on mouse position."""
        if not self.magnifier_active or not self.magnifier:
            return
            
        # Get mouse position relative to canvas
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Update magnifier window position
        self.magnifier.update_position(event.x_root, event.y_root)
        
        # Find which page we're hovering over
        current_page = None
        for page_num, layout in self.page_layouts.items():
            if (layout['y_offset'] <= canvas_y <= layout['y_offset'] + layout['height'] and
                10 <= canvas_x <= layout['width'] + 10):  # 10px margin
                current_page = page_num
                break
                
        if current_page and current_page in self.page_images:
            # Get the original image
            original_img = self.page_images[current_page]
            
            # Calculate the region to magnify
            # Convert canvas coordinates to image coordinates
            img_x = int((canvas_x - 10) / self.zoom_level)
            img_y = int((canvas_y - layout['y_offset']) / self.zoom_level)
            
            # Update the magnified view
            self.magnifier.update_view(original_img, img_x, img_y)

    def _hide_magnifier(self, event):
        """Hide the magnifier when mouse leaves the canvas."""
        if self.magnifier:
            self.magnifier.hide()