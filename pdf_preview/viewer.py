"""
PDF Preview Viewer Component
Handles the display and navigation of PDF documents with synchronization features.
"""

import tkinter as tk
import ttkbootstrap as ttk
from tkinter import Canvas, Scrollbar
from PIL import Image, ImageTk
import os
from utils import debug_console


class PDFPreviewViewer:
    """
    A PDF preview viewer component that displays PDF documents and provides
    navigation and synchronization features.
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
        self.current_page = 1
        self.total_pages = 1
        self.zoom_level = 1.0
        self.page_images = {}  # Cache for rendered page images
        self.page_sizes = {}   # Cache for page sizes
        
        self._create_widgets()
        if pdf_path and os.path.exists(pdf_path):
            self.load_pdf(pdf_path)
    
    def _create_widgets(self):
        """Create and configure the viewer widgets."""
        # Main frame
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)
        
        # Toolbar
        self._create_toolbar()
        
        # Canvas for PDF display with scrollbars
        self.canvas_frame = ttk.Frame(self.frame)
        self.canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create canvas with scrollbars
        self.canvas = Canvas(self.canvas_frame, bg="lightgray")
        self.v_scrollbar = Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind events for zooming
        self.canvas.bind("<Control-MouseWheel>", self._on_zoom)
        self.canvas.bind("<Control-Button-4>", self._on_zoom_in)
        self.canvas.bind("<Control-Button-5>", self._on_zoom_out)
    
    def _create_toolbar(self):
        """Create the toolbar with navigation controls."""
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # Navigation buttons
        self.prev_button = ttk.Button(toolbar, text="◀ Previous", command=self.previous_page, state="disabled")
        self.prev_button.pack(side="left", padx=(0, 5))
        
        self.page_label = ttk.Label(toolbar, text="Page 1 of 1")
        self.page_label.pack(side="left", padx=10)
        
        self.next_button = ttk.Button(toolbar, text="Next ▶", command=self.next_page, state="disabled")
        self.next_button.pack(side="left", padx=(5, 10))
        
        # Zoom controls
        ttk.Label(toolbar, text="Zoom:").pack(side="left", padx=(10, 5))
        
        self.zoom_out_button = ttk.Button(toolbar, text="−", width=3, command=self.zoom_out, state="disabled")
        self.zoom_out_button.pack(side="left", padx=(0, 2))
        
        self.zoom_label = ttk.Label(toolbar, text="100%")
        self.zoom_label.pack(side="left", padx=5)
        
        self.zoom_in_button = ttk.Button(toolbar, text="+", width=3, command=self.zoom_in, state="disabled")
        self.zoom_in_button.pack(side="left", padx=(2, 10))
        
        # Refresh button
        self.refresh_button = ttk.Button(toolbar, text="Refresh", command=self.refresh)
        self.refresh_button.pack(side="right")
        
        # Page jump
        ttk.Label(toolbar, text="Go to page:").pack(side="right", padx=(20, 5))
        self.page_entry = ttk.Entry(toolbar, width=5)
        self.page_entry.pack(side="right", padx=5)
        self.page_entry.bind("<Return>", self._on_page_entry)
        
        # Go button
        self.go_button = ttk.Button(toolbar, text="Go", command=self._go_to_page, state="disabled")
        self.go_button.pack(side="right", padx=(0, 5))
    
    def _on_page_entry(self, event):
        """Handle page entry submission."""
        self._go_to_page()
    
    def _go_to_page(self):
        """Go to the page specified in the entry."""
        try:
            page_num = int(self.page_entry.get())
            if 1 <= page_num <= self.total_pages:
                self.current_page = page_num
                self._update_page_display()
        except ValueError:
            pass  # Ignore invalid input
    
    def _on_zoom(self, event):
        """Handle zoom with mouse wheel."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def _on_zoom_in(self, event):
        """Handle zoom in with mouse wheel (Linux)."""
        self.zoom_in()
    
    def _on_zoom_out(self, event):
        """Handle zoom out with mouse wheel (Linux)."""
        self.zoom_out()
    
    def _create_placeholder(self):
        """Create a placeholder display when no PDF is loaded."""
        self.canvas.delete("all")
        
        # Clear page cache
        self.page_images.clear()
        self.page_sizes.clear()
        
        # Reset page info
        self.current_page = 1
        self.total_pages = 1
        self.zoom_level = 1.0
        
        # Update UI
        self.page_label.configure(text="Page 1 of 1")
        self.zoom_label.configure(text="100%")
        self._disable_toolbar()
        
        # Draw placeholder
        width, height = 600, 800
        self.canvas.configure(scrollregion=(0, 0, width, height))
        
        # Background
        self.canvas.create_rectangle(0, 0, width, height, fill="white", outline="gray")
        
        # Placeholder text
        self.canvas.create_text(
            width // 2, height // 2 - 50,
            text="PDF Preview",
            font=("Arial", 24, "bold"),
            fill="gray"
        )
        
        self.canvas.create_text(
            width // 2, height // 2,
            text="No PDF document loaded",
            font=("Arial", 16),
            fill="lightgray"
        )
        
        self.canvas.create_text(
            width // 2, height // 2 + 50,
            text="Open a .tex file with an associated .pdf to preview it here",
            font=("Arial", 12),
            fill="lightgray"
        )
    
    def load_pdf(self, pdf_path):
        """
        Load a PDF file for preview.
        
        Args:
            pdf_path (str): Path to the PDF file
        """
        if not os.path.exists(pdf_path):
            debug_console.log(f"PDF file not found: {pdf_path}", level='ERROR')
            self._create_placeholder()
            return
            
        self.pdf_path = pdf_path
        debug_console.log(f"Loading PDF: {pdf_path}", level='INFO')
        
        try:
            # Import pdf2image here to avoid issues if not installed
            from pdf2image import convert_from_path
            
            # Get page count using PyPDF2
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            self.total_pages = len(reader.pages)
            
            debug_console.log(f"PDF has {self.total_pages} pages", level='INFO')
            
            # Reset to first page
            self.current_page = 1
            
            # Enable toolbar
            self._enable_toolbar()
            
            # Render first page
            self._render_page()
            
        except ImportError as e:
            debug_console.log(f"PDF rendering libraries not available: {e}", level='ERROR')
            self._show_pdf_info()
        except Exception as e:
            debug_console.log(f"Error loading PDF: {e}", level='ERROR')
            self._create_placeholder()
    
    def _show_pdf_info(self):
        """Show PDF information when rendering is not available."""
        self.canvas.delete("all")
        
        width, height = 600, 400
        self.canvas.configure(scrollregion=(0, 0, width, height))
        
        # Background
        self.canvas.create_rectangle(0, 0, width, height, fill="white", outline="gray")
        
        # Title
        self.canvas.create_text(
            width // 2, 50,
            text="PDF Preview",
            font=("Arial", 24, "bold"),
            fill="black"
        )
        
        # PDF info
        if self.pdf_path:
            filename = os.path.basename(self.pdf_path)
            self.canvas.create_text(
                width // 2, 120,
                text=f"File: {filename}",
                font=("Arial", 14),
                fill="black"
            )
            
            self.canvas.create_text(
                width // 2, 160,
                text=f"Path: {self.pdf_path}",
                font=("Arial", 12),
                fill="gray"
            )
            
            self.canvas.create_text(
                width // 2, 200,
                text=f"Pages: {self.total_pages}",
                font=("Arial", 12),
                fill="black"
            )
        
        # Install message
        self.canvas.create_text(
            width // 2, 300,
            text="To enable full PDF rendering, install required packages:",
            font=("Arial", 12),
            fill="blue"
        )
        
        self.canvas.create_text(
            width // 2, 330,
            text="pip install pdf2image Pillow PyPDF2",
            font=("Courier", 12),
            fill="red"
        )
    
    def _render_page(self):
        """Render the current page."""
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            return
            
        try:
            from pdf2image import convert_from_path
            
            # Check if page is already cached
            cache_key = (self.current_page, self.zoom_level)
            if cache_key in self.page_images:
                self._display_page_image(self.page_images[cache_key])
                return
            
            # Convert PDF page to image
            # We use a lower DPI for better performance, will be scaled by zoom
            dpi = int(100 * self.zoom_level)
            images = convert_from_path(
                self.pdf_path,
                first_page=self.current_page,
                last_page=self.current_page,
                dpi=min(dpi, 200),  # Cap DPI for performance
                grayscale=False
            )
            
            if images:
                # Cache the image
                self.page_images[cache_key] = images[0]
                self._display_page_image(images[0])
                
        except ImportError:
            self._show_pdf_info()
        except Exception as e:
            debug_console.log(f"Error rendering page: {e}", level='ERROR')
            self._show_pdf_info()
    
    def _display_page_image(self, image):
        """Display a page image on the canvas."""
        self.canvas.delete("all")
        
        # Convert PIL image to PhotoImage
        photo = ImageTk.PhotoImage(image)
        
        # Store reference to prevent garbage collection
        self.current_photo = photo
        
        # Get image dimensions
        width, height = image.size
        
        # Configure scroll region
        self.canvas.configure(scrollregion=(0, 0, width, height))
        
        # Display image
        self.canvas.create_image(0, 0, anchor="nw", image=photo)
        
        # Update page label
        self.page_label.configure(text=f"Page {self.current_page} of {self.total_pages}")
        
        # Update zoom label
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_label.configure(text=f"{zoom_percent}%")
    
    def _enable_toolbar(self):
        """Enable toolbar buttons when PDF is loaded."""
        self.prev_button.configure(state="normal")
        self.next_button.configure(state="normal")
        self.zoom_out_button.configure(state="normal")
        self.zoom_in_button.configure(state="normal")
        self.go_button.configure(state="normal")
    
    def _disable_toolbar(self):
        """Disable toolbar buttons when no PDF is loaded."""
        self.prev_button.configure(state="disabled")
        self.next_button.configure(state="disabled")
        self.zoom_out_button.configure(state="disabled")
        self.zoom_in_button.configure(state="disabled")
        self.go_button.configure(state="disabled")
    
    def previous_page(self):
        """Navigate to the previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self._render_page()
    
    def next_page(self):
        """Navigate to the next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._render_page()
    
    def zoom_in(self):
        """Increase the zoom level."""
        if self.zoom_level < 3.0:  # Max 300%
            self.zoom_level *= 1.2
            self._clear_page_cache()
            self._render_page()
    
    def zoom_out(self):
        """Decrease the zoom level."""
        if self.zoom_level > 0.2:  # Min 20%
            self.zoom_level /= 1.2
            self._clear_page_cache()
            self._render_page()
    
    def _clear_page_cache(self):
        """Clear the page image cache."""
        self.page_images.clear()
    
    def refresh(self):
        """Refresh the PDF display."""
        if self.pdf_path:
            debug_console.log("Refreshing PDF preview", level='INFO')
            self._clear_page_cache()
            self.load_pdf(self.pdf_path)
    
    def synchronize_with_editor(self, line_number):
        """
        Synchronize the PDF view with a specific line in the editor.
        
        Args:
            line_number (int): Line number in the LaTeX editor
        """
        debug_console.log(f"Synchronizing PDF with editor line {line_number}", level='DEBUG')
        # In a full implementation, this would scroll to the relevant page/position
    
    def get_widget(self):
        """
        Get the main widget for this viewer.
        
        Returns:
            ttk.Frame: The main frame containing the viewer
        """
        return self.frame